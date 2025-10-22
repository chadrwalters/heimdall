"""Tests for Hermod CLI."""
import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from hermod.cli import app


@pytest.fixture
def runner():
    """CLI test runner."""
    return CliRunner()


def test_collect_command_with_defaults(runner):
    """Test collect command with default values."""
    with patch("hermod.cli.detect_developer", return_value="Chad"):
        with patch("hermod.cli.check_all_dependencies", return_value={"ccusage": True, "ccusage-codex": True}):
            with patch("hermod.cli.collect_usage") as mock_collect:
                with patch("hermod.cli.save_submission") as mock_save:
                    from pathlib import Path
                    mock_save.return_value = Path("test.json")
                    mock_collect.return_value = {
                        "metadata": {
                            "developer": "Chad",
                            "date_range": {"start": "2025-01-15", "end": "2025-01-22"}
                        },
                        "claude_code": {"totals": {"totalCost": 1.5}},
                        "codex": {"totals": {"totalCost": 2.0}}
                    }

                    result = runner.invoke(app, ["collect"])

                    assert result.exit_code == 0
                    assert "Chad" in result.stdout
                    mock_collect.assert_called_once_with("Chad", 7)


def test_collect_command_with_custom_developer(runner):
    """Test collect command with explicit developer."""
    with patch("hermod.cli.check_all_dependencies", return_value={"ccusage": True, "ccusage-codex": True}):
        with patch("hermod.cli.collect_usage") as mock_collect:
            with patch("hermod.cli.save_submission") as mock_save:
                from pathlib import Path
                mock_save.return_value = Path("test.json")
                mock_collect.return_value = {
                    "metadata": {
                        "developer": "Jeremiah",
                        "date_range": {"start": "2025-01-15", "end": "2025-01-22"}
                    },
                    "claude_code": {"totals": {"totalCost": 1.5}},
                    "codex": {"totals": {"totalCost": 2.0}}
                }

                result = runner.invoke(app, ["collect", "--developer", "Jeremiah"])

                assert result.exit_code == 0
                mock_collect.assert_called_once_with("Jeremiah", 7)


def test_collect_command_missing_dependencies(runner):
    """Test collect command when dependencies are missing."""
    with patch("hermod.cli.detect_developer", return_value="Chad"):
        with patch("hermod.cli.check_all_dependencies", return_value={"ccusage": False, "ccusage-codex": True}):
            result = runner.invoke(app, ["collect"])

            assert result.exit_code == 1
            assert "not installed" in result.stdout.lower()


def test_collect_command_json_output(runner):
    """Test JSON output mode."""
    with patch("hermod.cli.detect_developer", return_value="Chad"):
        with patch("hermod.cli.check_all_dependencies", return_value={"ccusage": True, "ccusage-codex": True}):
            with patch("hermod.cli.collect_usage") as mock_collect:
                with patch("hermod.cli.save_submission") as mock_save:
                    from pathlib import Path
                    mock_save.return_value = Path("test.json")
                    test_data = {
                        "metadata": {"developer": "Chad"},
                        "claude_code": {"totals": {"totalCost": 1.5}},
                        "codex": {"totals": {"totalCost": 2.0}}
                    }
                    mock_collect.return_value = test_data

                    result = runner.invoke(app, ["collect", "--json"])

                    assert result.exit_code == 0
                    import json
                    output = json.loads(result.stdout)
                    assert output["developer"] == "Chad"
