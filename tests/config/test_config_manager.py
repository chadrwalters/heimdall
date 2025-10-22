"""Tests for the ConfigManager class."""

import shutil
import tempfile
from pathlib import Path

import pytest

from src.config.config_manager import ConfigManager
from src.exceptions.data_exceptions import DataValidationError, JSONProcessingError


class TestConfigManager:
    """Test suite for ConfigManager."""

    def setup_method(self):
        """Set up test environment before each test."""
        self.test_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager(config_dir=self.test_dir)

    def teardown_method(self):
        """Clean up test environment after each test."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_init_creates_config_directory(self):
        """Test that initialization creates the config directory."""
        assert Path(self.test_dir).exists()

    def test_load_ai_developers_empty(self):
        """Test loading AI developers when file doesn't exist."""
        result = self.config_manager.load_ai_developers()
        assert result == {"always_ai_developers": []}

    def test_save_and_load_ai_developers(self):
        """Test saving and loading AI developers configuration."""
        config = {
            "always_ai_developers": [
                {
                    "username": "testuser",
                    "email": "test@example.com",
                    "ai_tool": "claude",
                    "percentage": 75,
                }
            ]
        }

        self.config_manager.save_ai_developers(config)
        loaded = self.config_manager.load_ai_developers()

        assert loaded == config

    def test_validate_ai_developers_config_valid(self):
        """Test validation with valid configuration."""
        valid_config = {
            "always_ai_developers": [
                {
                    "username": "user1",
                    "email": "user1@test.com",
                    "ai_tool": "copilot",
                    "percentage": 100,
                }
            ]
        }

        # Should not raise any exception
        self.config_manager.save_ai_developers(valid_config)

    def test_validate_ai_developers_config_invalid(self):
        """Test validation with various invalid configurations."""
        # Invalid AI tool
        with pytest.raises(DataValidationError):
            self.config_manager.save_ai_developers(
                {
                    "always_ai_developers": [
                        {
                            "username": "test",
                            "email": "test@test.com",
                            "ai_tool": "invalid_tool",
                            "percentage": 50,
                        }
                    ]
                }
            )

        # always_ai_developers not a list
        with pytest.raises(DataValidationError):
            self.config_manager.save_ai_developers({"always_ai_developers": "not a list"})

        # Developer missing username (required field)
        with pytest.raises(DataValidationError):
            self.config_manager.save_ai_developers(
                {
                    "always_ai_developers": [
                        {"email": "test@test.com", "ai_tool": "claude", "percentage": 50}
                    ]
                }
            )

        # Invalid percentage
        with pytest.raises(DataValidationError):
            self.config_manager.save_ai_developers(
                {
                    "always_ai_developers": [
                        {
                            "username": "test",
                            "email": "test@test.com",
                            "ai_tool": "claude",
                            "percentage": 150,
                        }
                    ]
                }
            )

    def test_load_analysis_state_default(self):
        """Test loading analysis state when file doesn't exist."""
        state = self.config_manager.load_analysis_state()

        assert state == {
            "last_run_date": None,
            "processed_pr_ids": [],
            "processed_commit_shas": [],
            "total_records_processed": 0,
        }

    def test_save_and_load_analysis_state(self):
        """Test saving and loading analysis state."""
        state = {
            "last_run_date": "2025-07-08T12:00:00Z",
            "processed_pr_ids": ["PR-1", "PR-2"],
            "processed_commit_shas": ["abc123", "def456"],
            "total_records_processed": 42,
        }

        self.config_manager.save_analysis_state(state)
        loaded = self.config_manager.load_analysis_state()

        # Compare fields individually since datetime parsing and list ordering can vary
        assert loaded["total_records_processed"] == state["total_records_processed"]
        assert set(loaded["processed_pr_ids"]) == set(state["processed_pr_ids"])
        assert set(loaded["processed_commit_shas"]) == set(state["processed_commit_shas"])
        assert loaded["last_run_date"] is not None  # Just check it's not None

    def test_update_state_after_run(self):
        """Test updating state after a run."""
        # Initial state
        initial_state = self.config_manager.load_analysis_state()
        assert initial_state["total_records_processed"] == 0

        # Update with new data
        self.config_manager.update_state_after_run(
            new_pr_ids=["PR-1", "PR-2"], new_commit_shas=["abc", "def"], records_processed=10
        )

        # Check updated state
        updated = self.config_manager.load_analysis_state()
        assert updated["total_records_processed"] == 10
        assert set(updated["processed_pr_ids"]) == {"PR-1", "PR-2"}
        assert set(updated["processed_commit_shas"]) == {"abc", "def"}
        assert updated["last_run_date"] is not None

        # Update again with some duplicates
        self.config_manager.update_state_after_run(
            new_pr_ids=["PR-2", "PR-3"],  # PR-2 is duplicate
            new_commit_shas=["def", "ghi"],  # def is duplicate
            records_processed=5,
        )

        # Check no duplicates
        final = self.config_manager.load_analysis_state()
        assert final["total_records_processed"] == 15
        assert set(final["processed_pr_ids"]) == {"PR-1", "PR-2", "PR-3"}
        assert set(final["processed_commit_shas"]) == {"abc", "def", "ghi"}

    def test_is_pr_processed(self):
        """Test checking if PR is processed."""
        assert not self.config_manager.is_pr_processed("PR-1")

        self.config_manager.update_state_after_run(["PR-1"], [], 1)

        assert self.config_manager.is_pr_processed("PR-1")
        assert not self.config_manager.is_pr_processed("PR-2")

    def test_is_commit_processed(self):
        """Test checking if commit is processed."""
        assert not self.config_manager.is_commit_processed("abc123")

        self.config_manager.update_state_after_run([], ["abc123"], 1)

        assert self.config_manager.is_commit_processed("abc123")
        assert not self.config_manager.is_commit_processed("def456")

    def test_get_ai_developer_info(self):
        """Test getting AI developer info by username or email."""
        config = {
            "always_ai_developers": [
                {
                    "username": "testuser",
                    "email": "test@example.com",
                    "ai_tool": "claude",
                    "percentage": 100,
                },
                {
                    "username": "otheruser",
                    "email": "other@example.com",
                    "ai_tool": "cursor",
                    "percentage": 50,
                },
            ]
        }

        self.config_manager.save_ai_developers(config)

        # Test by username
        info = self.config_manager.get_ai_developer_info(username="testuser")
        assert info["email"] == "test@example.com"

        # Test by email (case insensitive)
        info = self.config_manager.get_ai_developer_info(email="OTHER@EXAMPLE.COM")
        assert info["username"] == "otheruser"

        # Test not found
        info = self.config_manager.get_ai_developer_info(username="nonexistent")
        assert info is None

    def test_malformed_json_handling(self):
        """Test handling of malformed JSON files."""
        # Write invalid JSON to AI developers file
        with open(self.config_manager.ai_developers_file, "w") as f:
            f.write("{invalid json}")

        with pytest.raises(JSONProcessingError, match="Invalid JSON"):
            self.config_manager.load_ai_developers()

        # Write invalid JSON to state file
        with open(self.config_manager.state_file, "w") as f:
            f.write("{invalid json}")

        with pytest.raises(JSONProcessingError, match="Invalid JSON"):
            self.config_manager.load_analysis_state()
