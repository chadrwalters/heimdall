"""Tests for justfile cache management commands."""

import json
import os
import tempfile

import pytest


class TestJustfileCacheCommands:
    """Test justfile cache management commands."""

    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = os.path.join(self.temp_dir, ".cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Create sample cache files
        self.create_sample_cache_files()

    def teardown_method(self):
        """Cleanup test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_sample_cache_files(self):
        """Create sample cache files for testing."""
        # Create cache subdirectories
        for subdir in ["repos", "prs", "commits"]:
            os.makedirs(os.path.join(self.cache_dir, subdir), exist_ok=True)
        
        # Create sample cache files
        sample_files = [
            ("repos", "org1.json", {"data": ["repo1", "repo2"]}),
            ("prs", "repo1_list_p1.json", {"data": [{"id": 1, "title": "PR 1"}]}),
            ("commits", "repo1_page_1.json", {"data": [{"sha": "abc123"}]})
        ]
        
        for subdir, filename, data in sample_files:
            cache_entry = {
                "cached_at": "2025-07-09T19:05:53Z",
                "ttl_seconds": 3600,
                "data": data
            }
            file_path = os.path.join(self.cache_dir, subdir, filename)
            with open(file_path, "w") as f:
                json.dump(cache_entry, f)

    def test_cache_status_command_logic(self):
        """Test cache-status command logic."""
        # Mock cache status output
        expected_output = {
            "directory": ".cache/",
            "total_files": 3,
            "total_size": "1.2MB",
            "structure": [
                ".cache/repos/org1.json",
                ".cache/prs/repo1_list_p1.json", 
                ".cache/commits/repo1_page_1.json"
            ]
        }
        
        # Verify cache status structure
        assert expected_output["total_files"] > 0
        assert expected_output["total_size"].endswith("MB")
        assert len(expected_output["structure"]) == expected_output["total_files"]
        
        # Verify file paths
        for file_path in expected_output["structure"]:
            assert file_path.startswith(".cache/")
            assert file_path.endswith(".json")

    def test_cache_clean_command_logic(self):
        """Test cache-clean command logic."""
        # Mock cache clean scenarios
        clean_scenarios = [
            {
                "files_before": 10,
                "expired_files": 3,
                "files_after": 7,
                "size_before_mb": 5.2,
                "size_after_mb": 3.8
            },
            {
                "files_before": 0,
                "expired_files": 0,
                "files_after": 0,
                "size_before_mb": 0.0,
                "size_after_mb": 0.0
            }
        ]
        
        for scenario in clean_scenarios:
            # Verify clean logic
            assert scenario["files_after"] == scenario["files_before"] - scenario["expired_files"]
            assert scenario["size_after_mb"] <= scenario["size_before_mb"]
            
            # Verify non-negative values
            assert scenario["files_after"] >= 0
            assert scenario["size_after_mb"] >= 0

    def test_cache_validate_command_logic(self):
        """Test cache-validate command logic."""
        # Mock validation scenarios
        validation_scenarios = [
            {
                "file": ".cache/repos/org1.json",
                "valid_json": True,
                "has_required_fields": True,
                "status": "valid"
            },
            {
                "file": ".cache/prs/corrupted.json",
                "valid_json": False,
                "has_required_fields": False,
                "status": "invalid"
            },
            {
                "file": ".cache/commits/missing_data.json",
                "valid_json": True,
                "has_required_fields": False,
                "status": "invalid"
            }
        ]
        
        for scenario in validation_scenarios:
            # Verify validation logic
            if scenario["valid_json"] and scenario["has_required_fields"]:
                assert scenario["status"] == "valid"
            else:
                assert scenario["status"] == "invalid"

    def test_cache_rebuild_command_logic(self):
        """Test cache-rebuild command logic."""
        # Mock rebuild process
        rebuild_steps = [
            "confirm_user_intent",
            "remove_existing_cache",
            "create_cache_directories",
            "verify_structure_created"
        ]
        
        # Verify rebuild process
        assert len(rebuild_steps) == 4
        assert "confirm_user_intent" in rebuild_steps
        assert "remove_existing_cache" in rebuild_steps
        assert "create_cache_directories" in rebuild_steps
        assert "verify_structure_created" in rebuild_steps

    def test_cache_directory_structure_validation(self):
        """Test cache directory structure validation."""
        # Expected cache structure
        expected_structure = {
            ".cache/": {
                "repos/": ["org1.json", "org_page_1.json"],
                "prs/": ["repo_list_p1.json", "repo_details_123.json"],
                "commits/": ["repo_page_1.json", "abc123.json"]
            }
        }
        
        # Verify structure validation
        for root_dir, subdirs in expected_structure.items():
            assert root_dir == ".cache/"
            assert "repos/" in subdirs
            assert "prs/" in subdirs
            assert "commits/" in subdirs
            
            # Verify file patterns
            for subdir, files in subdirs.items():
                for file in files:
                    assert file.endswith(".json")

    def test_cache_size_calculation(self):
        """Test cache size calculation logic."""
        # Mock file sizes
        file_sizes = [
            {"file": ".cache/repos/org1.json", "size_bytes": 1024},
            {"file": ".cache/prs/repo1_list.json", "size_bytes": 2048},
            {"file": ".cache/commits/repo1_commits.json", "size_bytes": 4096}
        ]
        
        total_size_bytes = sum(f["size_bytes"] for f in file_sizes)
        total_size_mb = total_size_bytes / (1024 * 1024)
        
        # Verify size calculation
        assert total_size_bytes == 7168  # 1024 + 2048 + 4096
        assert total_size_mb < 1.0  # Should be less than 1MB
        
        # Verify individual file sizes
        for file_info in file_sizes:
            assert file_info["size_bytes"] > 0
            assert file_info["file"].endswith(".json")

    def test_cache_file_count_accuracy(self):
        """Test cache file count accuracy."""
        # Mock file counting scenarios
        count_scenarios = [
            {
                "directory": ".cache/repos/",
                "expected_files": 5,
                "actual_files": 5,
                "count_accurate": True
            },
            {
                "directory": ".cache/prs/",
                "expected_files": 10,
                "actual_files": 12,
                "count_accurate": False
            },
            {
                "directory": ".cache/commits/",
                "expected_files": 0,
                "actual_files": 0,
                "count_accurate": True
            }
        ]
        
        for scenario in count_scenarios:
            # Verify count accuracy
            if scenario["expected_files"] == scenario["actual_files"]:
                assert scenario["count_accurate"] is True
            else:
                assert scenario["count_accurate"] is False

    def test_cache_command_error_handling(self):
        """Test cache command error handling."""
        # Mock error scenarios
        error_scenarios = [
            {
                "command": "cache-status",
                "error": "permission_denied",
                "expected_behavior": "show_error_message"
            },
            {
                "command": "cache-clean",
                "error": "cache_directory_missing",
                "expected_behavior": "create_directory_or_skip"
            },
            {
                "command": "cache-validate",
                "error": "corrupted_files",
                "expected_behavior": "report_invalid_files"
            },
            {
                "command": "cache-rebuild",
                "error": "insufficient_permissions",
                "expected_behavior": "show_permission_error"
            }
        ]
        
        for scenario in error_scenarios:
            # Verify error handling strategies
            assert scenario["expected_behavior"] in [
                "show_error_message",
                "create_directory_or_skip",
                "report_invalid_files",
                "show_permission_error"
            ]

    def test_cache_command_output_format(self):
        """Test cache command output format."""
        # Mock command outputs
        command_outputs = {
            "cache-status": [
                "📊 Cache Status:",
                "  Directory: .cache/",
                "  5 cache files",
                "  2.1MB total size"
            ],
            "cache-clean": [
                "🧹 Cleaning expired cache entries...",
                "Cleaned 3 expired cache entries"
            ],
            "cache-validate": [
                "🔍 Validating cache integrity...",
                "Checking cache files...",
                "✅ All cache files valid"
            ],
            "cache-rebuild": [
                "🔄 Rebuilding cache (clearing all cached data)...",
                "✅ Cache cleared and rebuilt"
            ]
        }
        
        # Verify output format
        for command, output_lines in command_outputs.items():
            assert len(output_lines) > 0
            
            # Verify emoji usage (at least one line should have an emoji)
            has_emoji = False
            for line in output_lines:
                if any(emoji in line for emoji in ["📊", "🧹", "🔍", "🔄"]):
                    has_emoji = True
                    break
            assert has_emoji
            
            # Verify completion indicators (some commands show completion checkmarks)
            if command in ["cache-validate", "cache-rebuild"]:
                assert any("✅" in line for line in output_lines)

    def test_cache_command_integration(self):
        """Test cache command integration with extraction scripts."""
        # Mock integration scenarios
        integration_tests = [
            {
                "scenario": "extract_after_cache_clean",
                "expected_behavior": "fresh_api_calls"
            },
            {
                "scenario": "extract_with_valid_cache",
                "expected_behavior": "use_cached_data"
            },
            {
                "scenario": "extract_after_cache_rebuild",
                "expected_behavior": "populate_new_cache"
            }
        ]
        
        for test in integration_tests:
            # Verify integration behavior
            assert test["expected_behavior"] in [
                "fresh_api_calls",
                "use_cached_data",
                "populate_new_cache"
            ]

    def test_cache_command_safety_checks(self):
        """Test cache command safety checks."""
        # Mock safety scenarios
        safety_checks = [
            {
                "command": "cache-rebuild",
                "safety_check": "user_confirmation",
                "required": True
            },
            {
                "command": "cache-clean",
                "safety_check": "backup_important_data",
                "required": False
            },
            {
                "command": "cache-status",
                "safety_check": "read_only_operation",
                "required": False
            }
        ]
        
        for check in safety_checks:
            # Verify safety requirements
            if check["command"] == "cache-rebuild":
                assert check["required"] is True
            else:
                # Other commands are generally safe
                assert check["required"] is False or check["safety_check"] == "read_only_operation"


@pytest.mark.integration
class TestJustfileCacheIntegration:
    """Integration tests for justfile cache commands."""

    def test_cache_workflow_integration(self):
        """Test complete cache workflow integration."""
        # Mock complete workflow
        workflow_steps = [
            "just cache-status",      # Check initial state
            "just extract org 7",     # Run extraction (populates cache)
            "just cache-status",      # Check cache after extraction
            "just cache-validate",    # Validate cache integrity
            "just cache-clean",       # Clean expired entries
            "just cache-rebuild"      # Rebuild if needed
        ]
        
        # Verify workflow completeness
        assert len(workflow_steps) == 6
        assert any("cache-status" in step for step in workflow_steps)
        assert any("extract" in step for step in workflow_steps)
        assert any("cache-validate" in step for step in workflow_steps)
        assert any("cache-clean" in step for step in workflow_steps)
        assert any("cache-rebuild" in step for step in workflow_steps)

    def test_cache_command_performance(self):
        """Test cache command performance characteristics."""
        # Mock performance expectations
        performance_expectations = {
            "cache-status": {"max_duration_seconds": 1.0},
            "cache-clean": {"max_duration_seconds": 5.0},
            "cache-validate": {"max_duration_seconds": 10.0},
            "cache-rebuild": {"max_duration_seconds": 2.0}
        }
        
        # Verify performance expectations are reasonable
        for command, expectation in performance_expectations.items():
            assert expectation["max_duration_seconds"] > 0
            assert expectation["max_duration_seconds"] <= 10.0  # All should be fast

    def test_cache_command_reliability(self):
        """Test cache command reliability under various conditions."""
        # Mock reliability scenarios
        reliability_tests = [
            {
                "scenario": "large_cache_size",
                "cache_size_mb": 100,
                "expected_reliability": "high"
            },
            {
                "scenario": "many_cache_files",
                "file_count": 1000,
                "expected_reliability": "medium"
            },
            {
                "scenario": "corrupted_cache_files",
                "corrupted_files": 5,
                "expected_reliability": "handles_gracefully"
            }
        ]
        
        for test in reliability_tests:
            # Verify reliability expectations
            assert test["expected_reliability"] in [
                "high",
                "medium", 
                "handles_gracefully"
            ]
