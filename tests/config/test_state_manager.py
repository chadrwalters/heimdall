"""Tests for the StateManager class."""

import json
import shutil
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

from src.config.state_manager import StateManager


class TestStateManager:
    """Test suite for StateManager."""

    def setup_method(self):
        """Set up test environment before each test."""
        self.test_dir = tempfile.mkdtemp()
        self.state_file = Path(self.test_dir) / "test_state.json"
        self.state_manager = StateManager(state_file=str(self.state_file))

    def teardown_method(self):
        """Clean up test environment after each test."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_init_creates_state_file(self):
        """Test that initialization creates the state file with defaults."""
        assert self.state_file.exists()

        with open(self.state_file) as f:
            state = json.load(f)

        assert state == {
            "last_run_date": None,
            "processed_pr_ids": [],
            "processed_commit_shas": [],
            "total_records_processed": 0,
        }

    def test_get_last_run_date_none(self):
        """Test getting last run date when it's None."""
        assert self.state_manager.get_last_run_date() is None

    def test_get_last_run_date_valid(self):
        """Test getting last run date when it exists."""
        # Set a last run date
        test_date = datetime(2025, 7, 8, 10, 30, 0)
        state = {
            "last_run_date": test_date.isoformat() + "Z",
            "processed_pr_ids": [],
            "processed_commit_shas": [],
            "total_records_processed": 0,
        }

        with open(self.state_file, "w") as f:
            json.dump(state, f)

        result = self.state_manager.get_last_run_date()
        assert result.replace(tzinfo=None) == test_date

    def test_get_date_range_for_incremental_update_first_run(self):
        """Test date range calculation for first run."""
        start_date, end_date = self.state_manager.get_date_range_for_incremental_update()

        # Should be 7 days by default
        expected_diff = timedelta(days=7)
        actual_diff = end_date - start_date

        # Allow small difference for test execution time
        assert abs((actual_diff - expected_diff).total_seconds()) < 1

    def test_get_date_range_for_incremental_update_subsequent_run(self):
        """Test date range calculation for subsequent runs."""
        # Set a last run date
        last_run = datetime.now(UTC) - timedelta(days=3)
        state = {
            "last_run_date": last_run.isoformat().replace("+00:00", "Z"),
            "processed_pr_ids": [],
            "processed_commit_shas": [],
            "total_records_processed": 0,
        }

        with open(self.state_file, "w") as f:
            json.dump(state, f)

        start_date, end_date = self.state_manager.get_date_range_for_incremental_update()

        # Start should be last run minus 1 day
        expected_start = last_run - timedelta(days=1)
        assert abs((start_date - expected_start).total_seconds()) < 1

    def test_processed_ids_operations(self):
        """Test operations on processed IDs."""
        # Initially empty
        assert len(self.state_manager.get_processed_pr_ids()) == 0
        assert len(self.state_manager.get_processed_commit_shas()) == 0

        # Mark some as processed
        self.state_manager.mark_pr_processed("PR-1")
        self.state_manager.mark_commit_processed("abc123")

        assert self.state_manager.is_pr_processed("PR-1")
        assert self.state_manager.is_commit_processed("abc123")
        assert not self.state_manager.is_pr_processed("PR-2")
        assert not self.state_manager.is_commit_processed("def456")

        # Mark same ID again (should not duplicate)
        self.state_manager.mark_pr_processed("PR-1")
        assert len(self.state_manager.get_processed_pr_ids()) == 1

    def test_update_after_batch_processing(self):
        """Test batch update functionality."""
        pr_ids = ["PR-1", "PR-2", "PR-3"]
        commit_shas = ["abc", "def", "ghi"]

        self.state_manager.update_after_batch_processing(pr_ids, commit_shas, 10)

        # Check state
        stats = self.state_manager.get_statistics()
        assert stats["total_prs_processed"] == 3
        assert stats["total_commits_processed"] == 3
        assert stats["total_records_processed"] == 10
        assert stats["last_run_date"] is not None

        # Update again with some duplicates
        new_prs = ["PR-2", "PR-4"]  # PR-2 is duplicate
        new_commits = ["def", "jkl"]  # def is duplicate

        self.state_manager.update_after_batch_processing(new_prs, new_commits, 5)

        # Check no duplicates
        stats = self.state_manager.get_statistics()
        assert stats["total_prs_processed"] == 4  # Only PR-4 added
        assert stats["total_commits_processed"] == 4  # Only jkl added
        assert stats["total_records_processed"] == 15

    def test_get_statistics(self):
        """Test getting statistics."""
        # Initial stats
        stats = self.state_manager.get_statistics()
        assert stats["last_run_date"] is None
        assert stats["total_prs_processed"] == 0
        assert stats["total_commits_processed"] == 0
        assert stats["total_records_processed"] == 0
        assert stats["days_since_last_run"] is None

        # Add some data
        self.state_manager.update_after_batch_processing(["PR-1"], ["abc"], 1)

        stats = self.state_manager.get_statistics()
        assert stats["last_run_date"] is not None
        assert stats["total_prs_processed"] == 1
        assert stats["total_commits_processed"] == 1
        assert stats["total_records_processed"] == 1
        assert stats["days_since_last_run"] == 0

    def test_reset_state(self):
        """Test resetting state."""
        # Add some data
        self.state_manager.update_after_batch_processing(["PR-1"], ["abc"], 10)

        # Verify data exists
        stats = self.state_manager.get_statistics()
        assert stats["total_records_processed"] == 10

        # Reset
        self.state_manager.reset_state()

        # Verify reset
        stats = self.state_manager.get_statistics()
        assert stats["last_run_date"] is None
        assert stats["total_prs_processed"] == 0
        assert stats["total_commits_processed"] == 0
        assert stats["total_records_processed"] == 0

    def test_concurrent_updates(self):
        """Test that state updates don't lose data when called rapidly."""
        # This is a basic test - in production you'd want proper locking

        for i in range(5):
            self.state_manager.mark_pr_processed(f"PR-{i}")
            self.state_manager.mark_commit_processed(f"commit-{i}")

        assert len(self.state_manager.get_processed_pr_ids()) == 5
        assert len(self.state_manager.get_processed_commit_shas()) == 5
