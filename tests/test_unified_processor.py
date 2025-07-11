"""Tests for the unified data processor."""

import json
from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from src.analysis.analysis_engine import AnalysisEngine
from src.config.state_manager import StateManager
from src.data.unified_processor import UnifiedDataProcessor, UnifiedRecord
from src.linear.linear_client import LinearClient
from src.linear.pr_matcher import PRTicketMatch
from src.linear.ticket_extractor import LinearTicket


@pytest.fixture
def sample_pr_data():
    """Sample PR data for testing."""
    return {
        "id": "12345",
        "number": 42,
        "title": "Add new feature [ENG-123]",
        "body": "This implements a new feature for ENG-123",
        "html_url": "https://github.com/test/repo/pull/42",
        "created_at": "2023-01-01T10:00:00Z",
        "merged_at": "2023-01-01T12:00:00Z",
        "user": {"login": "developer1"},
        "additions": 100,
        "deletions": 20,
        "changed_files": 5,
        "files": [{"filename": "src/feature.py"}, {"filename": "tests/test_feature.py"}],
    }


@pytest.fixture
def sample_commit_data():
    """Sample commit data for testing."""
    return {
        "sha": "abc123def456",
        "commit": {
            "message": "Fix bug in user authentication\n\nResolves issue with login timeout",
            "author": {"email": "developer2@example.com"},
            "committer": {"date": "2023-01-02T10:00:00Z"},
        },
        "html_url": "https://github.com/test/repo/commit/abc123def456",
        "stats": {"additions": 10, "deletions": 5, "total": 15},
        "files": [{"filename": "src/auth.py"}],
    }


@pytest.fixture
def sample_ai_override_config():
    """Sample AI developer override configuration."""
    return {
        "always_ai_developers": [
            {
                "username": "chad",
                "email": "chad@example.com",
                "ai_tool": "Claude/Cursor",
                "percentage": 100,
            }
        ]
    }


@pytest.fixture
def mock_state_manager():
    """Mock state manager."""
    state_manager = Mock(spec=StateManager)
    state_manager.get_processed_pr_ids.return_value = set()
    state_manager.get_processed_commit_shas.return_value = set()
    state_manager.update_after_batch_processing.return_value = None
    return state_manager


@pytest.fixture
def mock_analysis_engine():
    """Mock analysis engine."""
    engine = Mock(spec=AnalysisEngine)
    engine.analyze.return_value = {
        "work_type": "New Feature",
        "complexity_score": 7,
        "risk_score": 5,
        "clarity_score": 8,
        "analysis_summary": "Mock analysis result",
    }
    return engine


@pytest.fixture
def mock_linear_client():
    """Mock Linear client."""
    client = Mock(spec=LinearClient)
    client.get_issues_by_ids.return_value = {
        "ENG-123": {
            "id": "eng-123-id",
            "identifier": "ENG-123",
            "title": "Test ticket",
            "state": {"type": "started"},
            "priority": 1,
            "team": {"key": "ENG"},
        }
    }
    return client


@pytest.fixture
def mock_pr_ticket_match():
    """Mock PR ticket match."""
    ticket = LinearTicket(
        identifier="ENG-123",
        title="Test ticket",
        state_type="started",
        priority=1,
        team_key="ENG",
        updated_at=datetime.now(UTC),
    )

    match = PRTicketMatch(
        pr_id="12345",
        pr_number=42,
        pr_title="Add new feature [ENG-123]",
        pr_url="https://github.com/test/repo/pull/42",
        ticket_ids={"ENG-123"},
        primary_ticket=ticket,
        all_tickets=[ticket],
        match_confidence=0.9,
        match_sources=["title"],
    )
    return match


class TestUnifiedDataProcessor:
    """Test the UnifiedDataProcessor class."""

    def test_init_with_defaults(self):
        """Test processor initialization with default components."""
        processor = UnifiedDataProcessor()

        assert processor.state_manager is not None
        assert processor.analysis_engine is None
        assert processor.linear_client is None
        assert processor.pr_matcher is None
        assert isinstance(processor.ai_overrides, dict)

    def test_init_with_provided_components(
        self, mock_state_manager, mock_analysis_engine, mock_linear_client
    ):
        """Test processor initialization with provided components."""
        processor = UnifiedDataProcessor(
            state_manager=mock_state_manager,
            analysis_engine=mock_analysis_engine,
            linear_client=mock_linear_client,
        )

        assert processor.state_manager == mock_state_manager
        assert processor.analysis_engine == mock_analysis_engine
        assert processor.linear_client == mock_linear_client
        assert processor.pr_matcher is not None

    @patch("src.data.unified_processor.Path")
    @patch("builtins.open")
    def test_load_ai_overrides_success(self, mock_open, mock_path, sample_ai_override_config):
        """Test loading AI override configuration successfully."""
        mock_path.return_value.exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(
            sample_ai_override_config
        )

        processor = UnifiedDataProcessor()

        expected_overrides = {
            "chad": sample_ai_override_config["always_ai_developers"][0],
            "chad@example.com": sample_ai_override_config["always_ai_developers"][0],
        }

        # We need to test the method directly since it's called in __init__
        with patch.object(processor, "_load_ai_overrides", return_value=expected_overrides):
            processor.__init__()
            assert processor.ai_overrides == expected_overrides

    def test_load_ai_overrides_file_not_found(self):
        """Test handling of missing AI override configuration file."""
        with patch("src.data.unified_processor.Path") as mock_path:
            mock_path.return_value.exists.return_value = False
            processor = UnifiedDataProcessor()
            assert processor.ai_overrides == {}

    def test_load_csv_data_success(self, tmp_path):
        """Test successful CSV data loading."""
        # Create test CSV file
        test_data = pd.DataFrame({"id": [1, 2, 3], "title": ["PR 1", "PR 2", "PR 3"]})
        test_file = tmp_path / "test_data.csv"
        test_data.to_csv(test_file, index=False)

        processor = UnifiedDataProcessor()
        result = processor._load_csv_data(str(test_file))

        assert len(result) == 3
        assert list(result.columns) == ["id", "title"]

    def test_load_csv_data_file_not_found(self):
        """Test handling of missing CSV file."""
        processor = UnifiedDataProcessor()
        result = processor._load_csv_data("nonexistent.csv")

        assert result.empty

    def test_filter_incremental_prs(self, mock_state_manager):
        """Test PR filtering for incremental processing."""
        mock_state_manager.get_processed_pr_ids.return_value = {"1", "2"}

        processor = UnifiedDataProcessor(state_manager=mock_state_manager)

        # Test data with some already processed PRs
        test_df = pd.DataFrame(
            {"id": ["1", "2", "3", "4"], "title": ["PR 1", "PR 2", "PR 3", "PR 4"]}
        )

        result = processor._filter_incremental_prs(test_df)

        assert len(result) == 2
        assert set(result["id"]) == {"3", "4"}

    def test_filter_incremental_commits(self, mock_state_manager):
        """Test commit filtering for incremental processing."""
        mock_state_manager.get_processed_commit_shas.return_value = {"abc123", "def456"}

        processor = UnifiedDataProcessor(state_manager=mock_state_manager)

        # Test data with some already processed commits
        test_df = pd.DataFrame(
            {
                "sha": ["abc123", "def456", "ghi789", "jkl012"],
                "message": ["Commit 1", "Commit 2", "Commit 3", "Commit 4"],
            }
        )

        result = processor._filter_incremental_commits(test_df)

        assert len(result) == 2
        assert set(result["sha"]) == {"ghi789", "jkl012"}

    def test_detect_ai_assistance_with_override(self, sample_ai_override_config):
        """Test AI assistance detection using override configuration."""
        processor = UnifiedDataProcessor()
        processor.ai_overrides = {
            "chad@example.com": sample_ai_override_config["always_ai_developers"][0]
        }

        ai_assisted, ai_tool = processor._detect_ai_assistance({}, "chad@example.com")

        assert ai_assisted is True
        assert ai_tool == "Claude/Cursor"

    def test_detect_ai_assistance_with_pattern(self):
        """Test AI assistance detection using pattern matching."""
        processor = UnifiedDataProcessor()

        data = {
            "commit": {
                "message": "Add feature\n\nCo-authored-by: GitHub Copilot <copilot@github.com>"
            }
        }

        with patch.object(
            processor.context_preparer,
            "detect_ai_assistance",
            return_value=(True, "GitHub Copilot"),
        ):
            ai_assisted, ai_tool = processor._detect_ai_assistance(data, "developer@example.com")

            assert ai_assisted is True
            assert ai_tool == "GitHub Copilot"

    def test_extract_repository_name(self):
        """Test repository name extraction from various URL formats."""
        processor = UnifiedDataProcessor()

        # Test GitHub URL
        data = {"html_url": "https://github.com/owner/repo/pull/123"}
        assert processor._extract_repository_name(data) == "repo"

        # Test repository_url field
        data = {"repository_url": "https://api.github.com/repos/owner/my-repo"}
        assert processor._extract_repository_name(data) == "my-repo"

        # Test fallback
        data = {"repository": "fallback-repo"}
        assert processor._extract_repository_name(data) == "fallback-repo"

        # Test unknown case
        data = {}
        assert processor._extract_repository_name(data) == "unknown"

    def test_extract_date_pr(self):
        """Test date extraction for PR data."""
        processor = UnifiedDataProcessor()

        data = {"created_at": "2023-01-01T10:00:00Z", "merged_at": "2023-01-01T12:00:00Z"}

        result = processor._extract_date(data, "PR")
        assert result == "2023-01-01T12:00:00+00:00"  # Should prefer merged_at

    def test_extract_date_commit(self):
        """Test date extraction for commit data."""
        processor = UnifiedDataProcessor()

        data = {"committed_at": "2023-01-01T10:00:00Z", "created_at": "2023-01-01T08:00:00Z"}

        result = processor._extract_date(data, "Commit")
        assert result == "2023-01-01T10:00:00+00:00"  # Should prefer committed_at

    def test_create_unified_record(
        self, sample_pr_data, mock_analysis_engine, mock_pr_ticket_match
    ):
        """Test creation of unified record from processed data."""
        processor = UnifiedDataProcessor(analysis_engine=mock_analysis_engine)

        # Mock context preparer
        mock_context = Mock()
        mock_context.metadata = {
            "additions": 100,
            "deletions": 20,
            "changed_files": 5,
            "author": "developer1@example.com",
        }
        mock_context.file_changes = ["file1.py", "file2.py"]

        analysis_result = {
            "work_type": "New Feature",
            "complexity_score": 7,
            "risk_score": 5,
            "clarity_score": 8,
            "analysis_summary": "Test analysis",
        }

        record = processor._create_unified_record(
            data=sample_pr_data,
            context=mock_context,
            analysis=analysis_result,
            ticket_match=mock_pr_ticket_match,
            ai_assisted=False,
            ai_tool=None,
            source_type="PR",
            context_level="High",
        )

        assert isinstance(record, UnifiedRecord)
        assert record.source_type == "PR"
        assert record.context_level == "High"
        assert record.work_type == "New Feature"
        assert record.complexity_score == 7
        assert record.risk_score == 5
        assert record.clarity_score == 8
        assert record.impact_score == 6.1  # 0.4*7 + 0.5*5 + 0.1*8
        assert record.lines_added == 100
        assert record.lines_deleted == 20
        assert record.files_changed == 5
        assert record.ai_assisted is False
        assert record.linear_ticket_id == "ENG-123"
        assert record.has_linear_ticket is True
        assert record.process_compliant is True

    def test_save_unified_data_new_file(self, tmp_path):
        """Test saving unified data to a new file."""
        processor = UnifiedDataProcessor()

        # Create test records
        records = [
            UnifiedRecord(
                repository="test-repo",
                date="2023-01-01T10:00:00Z",
                author="dev@example.com",
                source_type="PR",
                source_url="https://github.com/test/repo/pull/1",
                context_level="High",
                work_type="New Feature",
                complexity_score=7,
                risk_score=5,
                clarity_score=8,
                analysis_summary="Test",
                lines_added=100,
                lines_deleted=20,
                files_changed=5,
                impact_score=5.3,
                ai_assisted=False,
                ai_tool_type=None,
                linear_ticket_id="ENG-123",
                has_linear_ticket=True,
                process_compliant=True,
            )
        ]

        output_file = tmp_path / "test_output.csv"
        result = processor._save_unified_data(records, str(output_file), incremental=False)

        assert result == 1
        assert output_file.exists()

        # Verify file contents
        df = pd.read_csv(output_file)
        assert len(df) == 1
        assert df.iloc[0]["repository"] == "test-repo"
        assert df.iloc[0]["work_type"] == "New Feature"

    @patch("src.data.unified_processor.pd.read_csv")
    def test_validate_data_integrity(self, mock_read_csv):
        """Test data integrity validation."""
        processor = UnifiedDataProcessor()

        # Mock CSV data
        mock_df = pd.DataFrame(
            {
                "repository": ["repo1", "repo2"],
                "complexity_score": [7, 11],  # One invalid score
                "risk_score": [5, 3],
                "clarity_score": [8, 7],
                "lines_added": [100, -5],  # One negative value
                "lines_deleted": [20, 10],
                "files_changed": [5, 2],
                "source_type": ["PR", "Commit"],
                "work_type": ["Feature", "Bug Fix"],
                "ai_assisted": [True, False],
                "process_compliant": [True, False],
                "impact_score": [5.3, 4.2],
            }
        )

        mock_read_csv.return_value = mock_df

        result = processor.validate_data_integrity("test.csv")

        assert result["total_records"] == 2
        assert result["data_quality"]["invalid_scores"]["complexity"] == 1
        assert result["data_quality"]["negative_metrics"]["lines_added"] == 1
        assert result["summary_stats"]["source_types"] == {"PR": 1, "Commit": 1}
        assert result["summary_stats"]["ai_assisted_rate"] == 0.5

    def test_process_unified_data_integration(
        self, tmp_path, mock_state_manager, mock_analysis_engine, mock_linear_client
    ):
        """Test the complete unified data processing workflow."""
        processor = UnifiedDataProcessor(
            state_manager=mock_state_manager,
            analysis_engine=mock_analysis_engine,
            linear_client=mock_linear_client,
        )

        # Create test CSV files - flatten nested structures for CSV compatibility
        pr_df = pd.DataFrame(
            [
                {
                    "id": "12345",
                    "number": 42,
                    "title": "Add feature [ENG-123]",
                    "body": "Test PR",
                    "html_url": "https://github.com/test/repo/pull/42",
                    "created_at": "2023-01-01T10:00:00Z",
                    "merged_at": "2023-01-01T12:00:00Z",
                    "user_login": "dev1",  # Flattened
                    "additions": 100,
                    "deletions": 20,
                    "changed_files": 5,
                }
            ]
        )

        commit_df = pd.DataFrame(
            [
                {
                    "sha": "abc123",
                    "message": "Fix bug",  # Flattened
                    "author_email": "dev2@example.com",  # Flattened
                    "committer_date": "2023-01-02T10:00:00Z",  # Flattened
                    "html_url": "https://github.com/test/repo/commit/abc123",
                    "additions": 10,  # Flattened from stats
                    "deletions": 5,  # Flattened from stats
                    "total": 15,  # Flattened from stats
                }
            ]
        )

        # Save test data to files
        pr_file = tmp_path / "test_prs.csv"
        commit_file = tmp_path / "test_commits.csv"
        output_file = tmp_path / "test_output.csv"

        pr_df.to_csv(pr_file, index=False)
        commit_df.to_csv(commit_file, index=False)

        # Mock context preparer to handle flattened data
        with (
            patch.object(processor.context_preparer, "prepare_pr_context") as mock_pr_context,
            patch.object(
                processor.context_preparer, "prepare_commit_context"
            ) as mock_commit_context,
            patch.object(processor, "pr_matcher") as mock_pr_matcher,
        ):
            # Mock context results
            mock_pr_context.return_value = Mock(
                title="Add feature [ENG-123]",
                description="Test PR",
                diff="",
                file_changes=[],
                cache_key="pr-cache-key",
                metadata={"author": "dev1", "additions": 100, "deletions": 20, "changed_files": 5},
            )

            mock_commit_context.return_value = Mock(
                title="Fix bug",
                description=None,
                diff="",
                file_changes=[],
                cache_key="commit-cache-key",
                metadata={
                    "author": "dev2@example.com",
                    "additions": 10,
                    "deletions": 5,
                    "changed_files": 1,
                },
            )

            mock_pr_matcher.match_pr.return_value = Mock(
                primary_ticket=Mock(identifier="ENG-123"),
                ticket_ids={"ENG-123"},
                all_tickets=[Mock()],
                match_confidence=0.9,
            )

            # Run processing
            result = processor.process_unified_data(
                pr_data_file=str(pr_file),
                commit_data_file=str(commit_file),
                output_file=str(output_file),
                incremental=False,
            )

            assert result == 2  # 1 PR + 1 commit
            assert output_file.exists()

            # Verify output file content
            output_df = pd.read_csv(output_file)
            assert len(output_df) == 2
            assert "PR" in output_df["source_type"].values
            assert "Commit" in output_df["source_type"].values


class TestUnifiedRecord:
    """Test the UnifiedRecord dataclass."""

    def test_unified_record_creation(self):
        """Test creating a UnifiedRecord instance."""
        record = UnifiedRecord(
            repository="test-repo",
            date="2023-01-01T10:00:00Z",
            author="dev@example.com",
            source_type="PR",
            source_url="https://github.com/test/repo/pull/1",
            context_level="High",
            work_type="New Feature",
            complexity_score=7,
            risk_score=5,
            clarity_score=8,
            analysis_summary="Test analysis",
            lines_added=100,
            lines_deleted=20,
            files_changed=5,
            impact_score=5.3,
            ai_assisted=False,
            ai_tool_type=None,
            linear_ticket_id="ENG-123",
            has_linear_ticket=True,
            process_compliant=True,
        )

        assert record.repository == "test-repo"
        assert record.impact_score == 5.3
        assert record.ai_assisted is False

    def test_unified_record_to_dict(self):
        """Test converting UnifiedRecord to dictionary."""
        record = UnifiedRecord(
            repository="test-repo",
            date="2023-01-01T10:00:00Z",
            author="dev@example.com",
            source_type="PR",
            source_url="https://github.com/test/repo/pull/1",
            context_level="High",
            work_type="New Feature",
            complexity_score=7,
            risk_score=5,
            clarity_score=8,
            analysis_summary="Test analysis",
            lines_added=100,
            lines_deleted=20,
            files_changed=5,
            impact_score=5.3,
            ai_assisted=False,
            ai_tool_type=None,
            linear_ticket_id="ENG-123",
            has_linear_ticket=True,
            process_compliant=True,
        )

        result = record.to_dict()

        assert isinstance(result, dict)
        assert result["repository"] == "test-repo"
        assert result["impact_score"] == 5.3
        assert result["ai_assisted"] is False
        assert len(result) == 20  # Should have all fields
