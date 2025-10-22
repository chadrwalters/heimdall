"""Tests for AI usage data collection."""

import pytest
import subprocess
from unittest.mock import patch, MagicMock
from datetime import datetime
from hermod.collector import collect_usage, save_submission, run_command, COMMAND_TIMEOUT_SECONDS


def test_collect_usage_success() -> None:
    """Test successful data collection."""
    with patch("hermod.collector.run_command") as mock_run:
        # Mock ccusage response
        mock_run.side_effect = [
            {"daily": [{"date": "2025-01-22", "cost": 1.50}], "totals": {"totalCost": 1.50}},
            {"daily": [{"date": "2025-01-22", "cost": 2.00}], "totals": {"totalCost": 2.00}},
        ]

        data = collect_usage("Chad", days=7)

        assert data["metadata"]["developer"] == "Chad"
        assert data["metadata"]["date_range"]["days"] == 7
        assert "claude_code" in data
        assert "codex" in data
        assert data["claude_code"]["totals"]["totalCost"] == 1.50
        assert data["codex"]["totals"]["totalCost"] == 2.00


def test_collect_usage_handles_errors() -> None:
    """Test collection continues when one tool fails."""
    with patch("hermod.collector.run_command") as mock_run:
        # First call succeeds, second fails
        mock_run.side_effect = [
            {"daily": [], "totals": {}},
            {},  # Empty dict indicates error
        ]

        data = collect_usage("Chad", days=7)

        assert data["claude_code"] == {"daily": [], "totals": {}}
        assert data["codex"] == {}


def test_save_submission() -> None:
    """Test saving submission to file."""
    import tempfile
    from pathlib import Path

    test_data = {
        "metadata": {"developer": "Chad", "collected_at": "2025-01-22T10:00:00"},
        "claude_code": {},
        "codex": {},
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = save_submission(test_data, "Chad", output_dir=Path(tmpdir))

        assert output_path.exists()
        assert "ai_usage_Chad_" in output_path.name
        assert output_path.suffix == ".json"

        # Verify content
        import json

        with open(output_path) as f:
            loaded = json.load(f)
        assert loaded["metadata"]["developer"] == "Chad"


def test_run_command_validates_allowed_commands() -> None:
    """Test that only allowed commands can be run."""
    with pytest.raises(ValueError, match="Command not allowed"):
        run_command(["malicious-command", "--arg"])


def test_run_command_validates_empty_command() -> None:
    """Test that empty command list is rejected."""
    with pytest.raises(ValueError, match="Command not allowed"):
        run_command([])


def test_run_command_validates_dangerous_arguments() -> None:
    """Test that dangerous shell characters are rejected."""
    dangerous_commands = [
        ["ccusage", "daily", "; rm -rf /"],
        ["ccusage", "daily", "| cat /etc/passwd"],
        ["ccusage", "daily", "& background-task"],
        ["ccusage", "daily", "$(malicious)"],
        ["ccusage", "daily", "`whoami`"],
    ]

    for cmd in dangerous_commands:
        with pytest.raises(ValueError, match="Invalid argument contains dangerous characters"):
            run_command(cmd)


def test_run_command_success() -> None:
    """Test successful command execution."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.stdout = '{"daily": [], "totals": {}}'
        mock_run.return_value = mock_result

        result = run_command(["ccusage", "daily", "--json"])

        assert result == {"daily": [], "totals": {}}
        mock_run.assert_called_once()
        # Verify timeout is set
        assert mock_run.call_args[1]["timeout"] == COMMAND_TIMEOUT_SECONDS


def test_run_command_timeout() -> None:
    """Test command timeout handling."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired("ccusage", COMMAND_TIMEOUT_SECONDS)

        result = run_command(["ccusage", "daily"])

        assert result == {}


def test_run_command_invalid_json() -> None:
    """Test handling of invalid JSON response."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.stdout = "not valid json"
        mock_run.return_value = mock_result

        result = run_command(["ccusage", "daily"])

        assert result == {}


def test_run_command_non_dict_response() -> None:
    """Test validation rejects non-dict JSON responses."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.stdout = '["list", "not", "dict"]'
        mock_run.return_value = mock_result

        with pytest.raises(ValueError, match="Expected dict response"):
            run_command(["ccusage", "daily"])
