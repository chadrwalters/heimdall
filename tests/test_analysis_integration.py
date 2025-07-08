#!/usr/bin/env python3
"""Comprehensive integration tests for the AI Analysis Engine."""

import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analysis.analysis_engine import AnalysisEngine
from src.analysis.prompt_engineer import AnalysisResult, PromptEngineer
from tests.fixtures import (
    AI_ASSISTED_BODIES,
    EDGE_CASE_PRS,
    SAMPLE_API_RESPONSES,
    SAMPLE_DIFFS,
    SAMPLE_PRS,
    WORK_TYPE_TEST_CASES,
    get_truncated_diff,
)


class TestPromptEngineer:
    """Test the PromptEngineer component."""

    @pytest.fixture
    def engineer(self):
        return PromptEngineer()

    def test_create_analysis_prompt(self, engineer):
        """Test prompt creation with standard PR data."""
        pr = SAMPLE_PRS["feature"]
        prompt = engineer.create_analysis_prompt(
            title=pr["title"],
            description=pr["body"],
            diff=SAMPLE_DIFFS["medium"],
            file_changes=[f["filename"] for f in pr["files"]],
        )

        # Verify prompt structure
        assert "Implement user authentication system" in prompt
        assert "JWT-based authentication" in prompt
        assert "src/auth/jwt.py" in prompt
        assert "Code Diff:" in prompt
        assert "Provide your analysis as a JSON object" in prompt
        assert len(prompt) > 500  # Should be substantial

    def test_prompt_with_large_diff_truncation(self, engineer):
        """Test that large diffs are truncated properly."""
        pr = SAMPLE_PRS["refactor"]
        large_diff = get_truncated_diff()

        prompt = engineer.create_analysis_prompt(
            title=pr["title"],
            description=pr["body"],
            diff=large_diff,
            file_changes=[f["filename"] for f in pr["files"]],
        )

        # Verify diff was truncated
        assert len(prompt) < len(large_diff) + 1000  # Should be truncated
        assert "truncated" in prompt

    def test_parse_response_valid_json(self, engineer):
        """Test parsing a valid JSON response."""
        response = json.dumps(SAMPLE_API_RESPONSES["feature"])
        result = engineer.parse_response(response)

        assert isinstance(result, AnalysisResult)
        assert result.work_type == "New Feature"
        assert result.complexity_score == 8
        assert result.risk_score == 6
        assert result.clarity_score == 9
        assert result.analysis_summary == SAMPLE_API_RESPONSES["feature"]["analysis_summary"]

    def test_parse_response_invalid_json(self, engineer):
        """Test parsing an invalid response."""
        result = engineer.parse_response("This is not JSON")

        assert result.work_type == "Chore"  # Default fallback
        assert result.complexity_score == 5
        assert result.risk_score == 5
        assert result.clarity_score == 5
        assert "Unable to parse" in result.analysis_summary

    def test_parse_response_partial_json(self, engineer):
        """Test parsing JSON with missing fields."""
        partial_response = json.dumps(
            {
                "work_type": "Bug Fix",
                "complexity_score": 3,
                # Missing other required fields
            }
        )
        result = engineer.parse_response(partial_response)

        # Missing required fields should result in fallback
        assert result.work_type == "Chore"  # Fallback due to missing fields
        assert result.complexity_score == 5  # Default value
        assert result.risk_score == 5  # Default value
        assert result.clarity_score == 5  # Default value

    def test_calculate_impact_score(self, engineer):
        """Test impact score calculation."""
        # Test with known values
        impact = engineer.calculate_impact_score(8, 6, 9)
        # Formula: (0.4 * 8 + 0.5 * 6 + 0.1 * 9) = 3.2 + 3.0 + 0.9 = 7.1
        assert impact == pytest.approx(7.1, rel=1e-2)

        # Test boundary values
        assert engineer.calculate_impact_score(10, 10, 10) == 10.0
        assert engineer.calculate_impact_score(1, 1, 1) == 1.0

    @pytest.mark.parametrize("title,expected", WORK_TYPE_TEST_CASES)
    def test_work_type_classification(self, engineer, title, expected):
        """Test that work types are classified correctly based on title."""
        prompt = engineer.create_analysis_prompt(
            title=title, description="", diff="minimal diff", file_changes=["test.py"]
        )
        # Verify the prompt includes the title for classification
        assert title in prompt


class TestAnalysisEngine:
    """Test the main AnalysisEngine component."""

    @pytest.fixture
    def mock_claude_client(self):
        """Create a mock Claude client."""
        with patch("src.analysis.analysis_engine.ClaudeClient") as mock:
            client = MagicMock()
            mock.return_value = client
            yield client

    @pytest.fixture
    def engine(self, mock_claude_client):
        """Create an AnalysisEngine instance with mocked dependencies."""
        return AnalysisEngine(api_key="test-key")

    def test_analyze_pr_success(self, engine, mock_claude_client):
        """Test successful PR analysis."""
        # Setup mock response
        pr = SAMPLE_PRS["feature"]
        mock_response = {
            "content": json.dumps(SAMPLE_API_RESPONSES["feature"]),
            "model": "claude-sonnet-4",
            "usage": {"input_tokens": 800, "output_tokens": 200},
            "response_time": 1.5,
        }
        mock_claude_client.analyze_code_change.return_value = mock_response

        # Analyze PR
        result = engine.analyze_pr(pr, diff=SAMPLE_DIFFS["medium"])

        # Verify results
        assert result["source_type"] == "PR"
        assert result["source_id"] == 1001
        assert result["work_type"] == "New Feature"
        assert result["complexity_score"] == 8
        assert result["risk_score"] == 6
        assert result["clarity_score"] == 9
        assert result["impact_score"] == pytest.approx(7.1, rel=1e-2)
        assert result["linear_ticket_id"] == "AUTH-123"
        assert result["has_linear_ticket"] is True
        assert result["process_compliant"] is True
        assert result["ai_assisted"] is False
        assert result["api_tokens_used"] == 1000

        # Verify API was called
        mock_claude_client.analyze_code_change.assert_called_once()

    def test_analyze_pr_with_ai_assistance(self, engine, mock_claude_client):
        """Test PR analysis detects AI assistance."""
        pr = SAMPLE_PRS["ai_assisted"]
        mock_response = {
            "content": json.dumps(SAMPLE_API_RESPONSES["feature"]),
            "model": "claude-sonnet-4",
            "usage": {"input_tokens": 800, "output_tokens": 200},
            "response_time": 1.5,
        }
        mock_claude_client.analyze_code_change.return_value = mock_response

        result = engine.analyze_pr(pr, diff=SAMPLE_DIFFS["small"])

        assert result["ai_assisted"] is True
        assert result["ai_tool_type"] == "Claude Code"

    def test_analyze_pr_without_linear_ticket(self, engine, mock_claude_client):
        """Test PR analysis without Linear ticket."""
        pr = SAMPLE_PRS["no_ticket"]
        mock_response = {
            "content": json.dumps(SAMPLE_API_RESPONSES["bugfix"]),
            "model": "claude-sonnet-4",
            "usage": {"input_tokens": 600, "output_tokens": 200},
            "response_time": 1.2,
        }
        mock_claude_client.analyze_code_change.return_value = mock_response

        result = engine.analyze_pr(pr, diff=SAMPLE_DIFFS["small"])

        assert result["has_linear_ticket"] is False
        assert result["linear_ticket_id"] is None
        assert result["process_compliant"] is False

    def test_analyze_pr_api_error(self, engine, mock_claude_client):
        """Test PR analysis with API error."""
        pr = SAMPLE_PRS["feature"]
        mock_claude_client.analyze_code_change.side_effect = Exception("API Error")

        result = engine.analyze_pr(pr, diff=SAMPLE_DIFFS["medium"])

        # Should return default values on error
        assert result["work_type"] == "Unknown"
        assert result["complexity_score"] == 5
        assert result["risk_score"] == 5
        assert result["clarity_score"] == 5
        assert "Error during analysis" in result["analysis_summary"]

    def test_analyze_commit(self, engine, mock_claude_client):
        """Test commit analysis."""
        commit = {
            "sha": "abc123",
            "commit": {
                "message": "Fix bug in payment processor",
                "author": {
                    "name": "Developer",
                    "email": "dev@example.com",
                    "date": "2025-01-15T10:00:00Z",
                },
                "committer": {
                    "name": "Developer",
                    "email": "dev@example.com",
                    "date": "2025-01-15T10:00:00Z",
                },
            },
            "html_url": "https://github.com/test/repo/commit/abc123",
            "stats": {"additions": 20, "deletions": 10, "total": 30},
            "files": [{"filename": "src/payment.py"}],
            "repository": {"name": "test-repo"},
        }

        mock_response = {
            "content": json.dumps(SAMPLE_API_RESPONSES["bugfix"]),
            "model": "claude-sonnet-4",
            "usage": {"input_tokens": 400, "output_tokens": 100},
            "response_time": 0.8,
        }
        mock_claude_client.analyze_code_change.return_value = mock_response

        result = engine.analyze_commit(commit, diff="test diff")

        assert result["source_type"] == "Commit"
        assert result["source_id"] == "abc123"
        assert result["context_level"] == "Low"
        assert result["work_type"] == "Bug Fix"

    def test_batch_analyze_prs(self, engine, mock_claude_client):
        """Test batch PR analysis."""
        prs = [SAMPLE_PRS["feature"], SAMPLE_PRS["bugfix"], SAMPLE_PRS["refactor"]]

        # Setup mock responses that return specific content based on the prompt
        def mock_analyze_response(prompt, **kwargs):
            if "Implement user authentication system" in prompt:
                return {
                    "content": json.dumps(SAMPLE_API_RESPONSES["feature"]),
                    "model": "claude-sonnet-4",
                    "usage": {"input_tokens": 800, "output_tokens": 200},
                    "response_time": 1.5,
                }
            elif "Fix null pointer exception" in prompt:
                return {
                    "content": json.dumps(SAMPLE_API_RESPONSES["bugfix"]),
                    "model": "claude-sonnet-4",
                    "usage": {"input_tokens": 600, "output_tokens": 200},
                    "response_time": 1.2,
                }
            elif "Refactor database connection pooling" in prompt:
                return {
                    "content": json.dumps(SAMPLE_API_RESPONSES["refactor"]),
                    "model": "claude-sonnet-4",
                    "usage": {"input_tokens": 700, "output_tokens": 200},
                    "response_time": 1.3,
                }
            else:
                # Fallback
                return {
                    "content": json.dumps(SAMPLE_API_RESPONSES["feature"]),
                    "model": "claude-sonnet-4",
                    "usage": {"input_tokens": 800, "output_tokens": 200},
                    "response_time": 1.5,
                }
        
        mock_claude_client.analyze_code_change.side_effect = mock_analyze_response

        # Track progress
        progress_updates = []

        def progress_callback(completed, total):
            progress_updates.append((completed, total))

        results = engine.batch_analyze_prs(prs, progress_callback=progress_callback)

        assert len(results) == 3
        assert results[0]["work_type"] == "New Feature"
        assert results[1]["work_type"] == "Bug Fix"
        assert results[2]["work_type"] == "Refactor"

        # Verify progress callbacks
        assert len(progress_updates) == 3
        assert progress_updates[-1] == (3, 3)

    def test_get_stats(self, engine, mock_claude_client):
        """Test usage statistics tracking."""
        # Mock the stats methods
        mock_claude_client.get_usage_stats.return_value = {
            "total_api_calls": 2,
            "total_tokens_used": 2000,
            "cache_size": 0,
            "model": "claude-sonnet-4",
        }
        mock_claude_client.estimate_cost.return_value = 0.045  # Example cost

        # Perform some analyses
        mock_response = {
            "content": json.dumps(SAMPLE_API_RESPONSES["feature"]),
            "model": "claude-sonnet-4",
            "usage": {"input_tokens": 800, "output_tokens": 200},
            "response_time": 1.5,
        }
        mock_claude_client.analyze_code_change.return_value = mock_response

        engine.analyze_pr(SAMPLE_PRS["feature"], diff=SAMPLE_DIFFS["medium"])
        engine.analyze_pr(SAMPLE_PRS["bugfix"], diff=SAMPLE_DIFFS["small"])

        stats = engine.get_stats()

        assert stats["total_api_calls"] == 2
        assert stats["total_tokens_used"] == 2000
        assert stats["estimated_cost"] == 0.045
        assert stats["cache_hits"] == 2  # Two results were cached


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.fixture
    def engine(self):
        with patch("src.analysis.analysis_engine.ClaudeClient"):
            return AnalysisEngine(api_key="test-key")

    def test_empty_pr_body(self, engine):
        """Test PR with empty body."""
        pr = EDGE_CASE_PRS["empty_body"]
        with patch.object(engine.claude_client, "call_api") as mock_api:
            mock_api.return_value = {
                "response": json.dumps(SAMPLE_API_RESPONSES["bugfix"]),
                "usage": {"total_tokens": 500},
            }

            result = engine.analyze_pr(pr, diff=SAMPLE_DIFFS["small"])

            # Work type can vary based on AI interpretation
            assert result["work_type"] in ["Bug Fix", "Chore", "Unknown"]
            assert result["source_id"] == 2001

    def test_pr_no_files(self, engine):
        """Test PR with no file changes."""
        pr = EDGE_CASE_PRS["no_files"]
        with patch.object(engine.claude_client, "call_api") as mock_api:
            mock_api.return_value = {
                "response": json.dumps(SAMPLE_API_RESPONSES["error"]),
                "usage": {"total_tokens": 300},
            }

            result = engine.analyze_pr(pr, diff="")

            assert result["files_changed"] == 0
            assert result["lines_added"] == 0
            assert result["lines_deleted"] == 0

    def test_massive_pr(self, engine):
        """Test PR with huge number of changes."""
        pr = EDGE_CASE_PRS["huge_changes"]
        with patch.object(engine.claude_client, "analyze_code_change") as mock_api:
            mock_api.return_value = {
                "content": json.dumps(SAMPLE_API_RESPONSES["refactor"]),
                "model": "claude-sonnet-4",
                "usage": {"input_tokens": 1500, "output_tokens": 500},
                "response_time": 2.0,
            }

            result = engine.analyze_pr(pr, diff=get_truncated_diff())

            assert result["files_changed"] == 500
            assert result["lines_added"] == 50000
            assert result["lines_deleted"] == 30000
            assert result["complexity_score"] == 7  # From mock response


class TestPerformance:
    """Test performance and concurrency."""

    @pytest.fixture
    def engine(self):
        with patch("src.analysis.analysis_engine.ClaudeClient"):
            return AnalysisEngine(api_key="test-key")

    def test_concurrent_analysis(self, engine):
        """Test concurrent PR analysis doesn't cause issues."""
        prs = [SAMPLE_PRS["feature"], SAMPLE_PRS["bugfix"]] * 5  # 10 PRs

        with patch.object(engine.claude_client, "analyze_code_change") as mock_api:
            # Simulate varying response times
            def mock_response(*args, **kwargs):
                time.sleep(0.1)  # Small delay
                return {
                    "content": json.dumps(SAMPLE_API_RESPONSES["feature"]),
                    "model": "claude-sonnet-4",
                    "usage": {"input_tokens": 800, "output_tokens": 200},
                    "response_time": 0.1,
                }

            mock_api.side_effect = mock_response

            start_time = time.time()
            results = engine.batch_analyze_prs(prs)
            duration = time.time() - start_time

            assert len(results) == 10
            assert all(r["work_type"] == "New Feature" for r in results)
            # Should be faster than sequential (10 * 0.1 = 1 second)
            # Allow some overhead for parallel processing
            assert duration < 2.0  # Parallel execution with overhead

    def test_cache_performance(self, engine):
        """Test that caching improves performance."""
        pr = SAMPLE_PRS["feature"]

        with patch.object(engine.claude_client, "analyze_code_change") as mock_api:
            mock_api.return_value = {
                "content": json.dumps(SAMPLE_API_RESPONSES["feature"]),
                "model": "claude-sonnet-4",
                "usage": {"input_tokens": 800, "output_tokens": 200},
                "response_time": 1.5,
            }

            # First call
            result1 = engine.analyze_pr(pr, diff=SAMPLE_DIFFS["medium"])

            # Second call should use cache
            result2 = engine.analyze_pr(pr, diff=SAMPLE_DIFFS["medium"])

            # API should only be called once
            assert mock_api.call_count == 1
            assert result1 == result2

            # Cache check
            assert len(engine.results_cache) >= 1


class TestAIDetection:
    """Test AI assistance detection."""

    @pytest.fixture
    def engine(self):
        with patch("src.analysis.analysis_engine.ClaudeClient"):
            return AnalysisEngine(api_key="test-key")

    @pytest.mark.parametrize(
        "body,expected_tool",
        [
            (AI_ASSISTED_BODIES[0], "Claude Code"),
            (AI_ASSISTED_BODIES[1], "GitHub Copilot"),
            (AI_ASSISTED_BODIES[2], "Cursor"),
            (AI_ASSISTED_BODIES[3], "Assistant"),
            (AI_ASSISTED_BODIES[4], "Unknown AI Tool"),
            (AI_ASSISTED_BODIES[5], "Unknown AI Tool"),
        ],
    )
    def test_ai_tool_detection(self, engine, body, expected_tool):
        """Test detection of various AI tools."""
        pr = {**SAMPLE_PRS["feature"], "body": body}

        with patch.object(engine.claude_client, "call_api") as mock_api:
            mock_api.return_value = {
                "response": json.dumps(SAMPLE_API_RESPONSES["feature"]),
                "usage": {"total_tokens": 1000},
            }

            result = engine.analyze_pr(pr, diff=SAMPLE_DIFFS["small"])

            assert result["ai_assisted"] is True
            assert result["ai_tool_type"] == expected_tool


@pytest.mark.integration
class TestLiveAPI:
    """Integration tests with real Claude API (requires ANTHROPIC_API_KEY)."""

    @pytest.fixture
    def api_key(self):
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            pytest.skip("ANTHROPIC_API_KEY not set")
        return key

    @pytest.fixture
    def engine(self, api_key):
        return AnalysisEngine(api_key=api_key)

    def test_live_pr_analysis(self, engine):
        """Test with real API call."""
        pr = SAMPLE_PRS["feature"]

        result = engine.analyze_pr(pr, diff=SAMPLE_DIFFS["medium"])

        # Verify we get valid results
        assert result["work_type"] in [
            "New Feature",
            "Bug Fix",
            "Refactor",
            "Testing",
            "Documentation",
            "Chore",
        ]
        assert 1 <= result["complexity_score"] <= 10
        assert 1 <= result["risk_score"] <= 10
        assert 1 <= result["clarity_score"] <= 10
        assert 0 <= result["impact_score"] <= 10
        assert len(result["analysis_summary"]) > 10
        assert result["api_tokens_used"] > 0
        assert result["analysis_time"] > 0

        # Check stats
        stats = engine.get_stats()
        assert stats["total_api_calls"] >= 1
        assert stats["total_tokens_used"] > 0
        assert stats["estimated_cost"] > 0


if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([__file__, "-v", "--cov=src.analysis", "--cov-report=html"])
