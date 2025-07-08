"""Tests for the AI Analysis Engine."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.analysis.analysis_engine import AnalysisEngine
from src.analysis.context_preparer import ContextPreparer
from src.analysis.prompt_engineer import AnalysisResult, PromptEngineer


class TestAnalysisEngine:
    """Test cases for the AnalysisEngine."""

    @pytest.fixture
    def mock_pr_data(self):
        """Sample PR data for testing."""
        return {
            "id": 123,
            "number": 123,
            "title": "Add new authentication feature",
            "body": "This PR implements OAuth2 authentication\n\nLinear: ENG-1234",
            "user": {"login": "testuser"},
            "created_at": "2025-01-15T10:00:00Z",
            "merged_at": "2025-01-15T11:00:00Z",
            "additions": 150,
            "deletions": 30,
            "changed_files": 5,
            "html_url": "https://github.com/org/repo/pull/123",
            "base": {"ref": "main", "repo": {"name": "test-repo"}},
            "head": {"ref": "feature/auth"},
            "files": [
                {"filename": "src/auth/oauth.py"},
                {"filename": "src/auth/config.py"},
                {"filename": "tests/test_oauth.py"},
                {"filename": "requirements.txt"},
                {"filename": "README.md"},
            ],
        }

    @pytest.fixture
    def mock_commit_data(self):
        """Sample commit data for testing."""
        return {
            "sha": "abc123def456",
            "commit": {
                "message": "Fix authentication bug\n\nCo-Authored-By: GitHub Copilot",
                "author": {"email": "test@example.com", "date": "2025-01-15T10:00:00Z"},
                "committer": {"email": "test@example.com", "date": "2025-01-15T10:00:00Z"},
            },
            "stats": {"additions": 20, "deletions": 10, "total": 30},
            "html_url": "https://github.com/org/repo/commit/abc123def456",
            "repository": {"name": "test-repo"},
            "files": [{"filename": "src/auth/bugfix.py"}],
        }

    @pytest.fixture
    def sample_diff(self):
        """Sample diff for testing."""
        return """diff --git a/src/auth/oauth.py b/src/auth/oauth.py
index 1234567..abcdefg 100644
--- a/src/auth/oauth.py
+++ b/src/auth/oauth.py
@@ -10,6 +10,15 @@ class OAuthHandler:
     def __init__(self, client_id, client_secret):
         self.client_id = client_id
         self.client_secret = client_secret
+        self.token_cache = {}
+    
+    def authenticate(self, username, password):
+        # New authentication logic
+        token = self._get_token(username, password)
+        if token:
+            self.token_cache[username] = token
+            return True
+        return False
"""

    @patch("src.analysis.claude_client.Anthropic")
    def test_analyze_pr(self, mock_anthropic_class, mock_pr_data, sample_diff):
        """Test PR analysis."""
        # Mock the Anthropic client
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # Mock API response
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "work_type": "New Feature",
                        "complexity_score": 7,
                        "risk_score": 6,
                        "clarity_score": 8,
                        "analysis_summary": "Implements OAuth2 authentication with token caching",
                    }
                )
            )
        ]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        mock_client.messages.create.return_value = mock_response

        # Create engine and analyze
        engine = AnalysisEngine(api_key="test-key")
        result = engine.analyze_pr(mock_pr_data, diff=sample_diff)

        # Verify results
        assert result["source_type"] == "PR"
        assert result["source_id"] == 123
        assert result["work_type"] == "New Feature"
        assert result["complexity_score"] == 7
        assert result["risk_score"] == 6
        assert result["clarity_score"] == 8
        assert result["impact_score"] == pytest.approx(6.6)  # (0.4*7 + 0.5*6 + 0.1*8)
        assert result["linear_ticket_id"] == "ENG-1234"
        assert result["has_linear_ticket"] == True
        assert result["process_compliant"] == True
        assert result["ai_assisted"] == False

    @patch("src.analysis.claude_client.Anthropic")
    def test_analyze_commit_with_ai_detection(
        self, mock_anthropic_class, mock_commit_data, sample_diff
    ):
        """Test commit analysis with AI assistance detection."""
        # Mock the Anthropic client
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # Mock API response
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "work_type": "Bug Fix",
                        "complexity_score": 4,
                        "risk_score": 3,
                        "clarity_score": 9,
                        "analysis_summary": "Fixes authentication bug in OAuth handler",
                    }
                )
            )
        ]
        mock_response.usage.input_tokens = 80
        mock_response.usage.output_tokens = 40
        mock_client.messages.create.return_value = mock_response

        # Create engine and analyze
        engine = AnalysisEngine(api_key="test-key")
        result = engine.analyze_commit(mock_commit_data, diff=sample_diff)

        # Verify results
        assert result["source_type"] == "Commit"
        assert result["source_id"] == "abc123def456"
        assert result["work_type"] == "Bug Fix"
        assert result["ai_assisted"] == True
        assert result["ai_tool_type"] == "GitHub Copilot"
        assert result["process_compliant"] == False  # Commits are not process compliant

    def test_prompt_engineering(self):
        """Test prompt creation and response parsing."""
        engineer = PromptEngineer()

        # Test prompt creation
        prompt = engineer.create_analysis_prompt(
            title="Add user authentication",
            description="Implements JWT-based auth",
            diff="+ def authenticate(user):",
            file_changes=["auth.py", "test_auth.py"],
        )

        assert "Add user authentication" in prompt
        assert "JWT-based auth" in prompt
        assert "authenticate(user)" in prompt
        assert "auth.py" in prompt

        # Test response parsing
        response = """{
            "work_type": "New Feature",
            "complexity_score": 8,
            "risk_score": 7,
            "clarity_score": 6,
            "analysis_summary": "Adds JWT authentication"
        }"""

        result = engineer.parse_response(response)
        assert isinstance(result, AnalysisResult)
        assert result.work_type == "New Feature"
        assert result.complexity_score == 8

        # Test impact score calculation
        impact = engineer.calculate_impact_score(8, 7, 6)
        assert impact == pytest.approx(7.3)  # (0.4*8 + 0.5*7 + 0.1*6)

    def test_context_preparation(self, mock_pr_data, mock_commit_data):
        """Test context preparation."""
        preparer = ContextPreparer()

        # Test PR context
        pr_context = preparer.prepare_pr_context(mock_pr_data)
        assert pr_context.title == "Add new authentication feature"
        assert len(pr_context.file_changes) == 5
        assert pr_context.metadata["pr_id"] == 123

        # Test commit context
        commit_context = preparer.prepare_commit_context(mock_commit_data)
        assert commit_context.title == "Fix authentication bug"
        assert commit_context.metadata["commit_sha"] == "abc123def456"

        # Test AI detection
        ai_assisted, ai_tool = preparer.detect_ai_assistance(mock_commit_data)
        assert ai_assisted == True
        assert ai_tool == "GitHub Copilot"

        # Test Linear ticket extraction
        ticket_id = preparer.extract_linear_ticket_id(mock_pr_data)
        assert ticket_id == "ENG-1234"

    def test_diff_truncation(self):
        """Test diff truncation logic."""
        preparer = ContextPreparer()

        # Create a long diff
        long_diff = "diff --git a/file.py b/file.py\n" + ("+" * 5000)

        truncated = preparer._prepare_diff(long_diff, ["file.py"])
        assert len(truncated) < 4000
        assert "truncated" in truncated

    @patch("src.analysis.claude_client.Anthropic")
    def test_batch_processing(self, mock_anthropic_class, mock_pr_data):
        """Test batch PR processing."""
        # Mock the Anthropic client
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # Mock API response
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "work_type": "New Feature",
                        "complexity_score": 5,
                        "risk_score": 5,
                        "clarity_score": 5,
                        "analysis_summary": "Test analysis",
                    }
                )
            )
        ]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        mock_client.messages.create.return_value = mock_response

        # Create engine
        engine = AnalysisEngine(api_key="test-key", max_workers=2)

        # Process batch
        pr_list = [mock_pr_data.copy() for _ in range(3)]
        results = engine.batch_analyze_prs(pr_list)

        assert len(results) == 3
        assert all(r["source_type"] == "PR" for r in results)

    @patch("src.analysis.claude_client.Anthropic")
    def test_caching(self, mock_anthropic_class, mock_pr_data):
        """Test caching functionality."""
        # Mock the Anthropic client
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # Mock API response
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "work_type": "New Feature",
                        "complexity_score": 5,
                        "risk_score": 5,
                        "clarity_score": 5,
                        "analysis_summary": "Test analysis",
                    }
                )
            )
        ]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        mock_client.messages.create.return_value = mock_response

        # Create engine
        engine = AnalysisEngine(api_key="test-key")

        # First analysis should call API
        result1 = engine.analyze_pr(mock_pr_data)
        assert mock_client.messages.create.call_count == 1

        # Second analysis should use cache
        result2 = engine.analyze_pr(mock_pr_data)
        assert mock_client.messages.create.call_count == 1  # No additional call
        assert result1 == result2

        # Clear cache and analyze again
        engine.clear_cache()
        engine.analyze_pr(mock_pr_data)
        assert mock_client.messages.create.call_count == 2  # New API call
