"""Tests for external dependency checking."""
import pytest
from unittest.mock import patch, MagicMock
from hermod.dependencies import check_ccusage_installed, check_all_dependencies


def test_check_ccusage_installed_success():
    """Test detecting installed ccusage."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "/usr/local/bin/ccusage\n"
        mock_run.return_value = mock_result

        is_installed = check_ccusage_installed()
        assert is_installed is True


def test_check_ccusage_installed_missing():
    """Test detecting missing ccusage."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        is_installed = check_ccusage_installed()
        assert is_installed is False


def test_check_all_dependencies_success():
    """Test when all dependencies are installed."""
    with patch("hermod.dependencies.check_ccusage_installed", return_value=True):
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            result = check_all_dependencies()
            assert result == {"ccusage": True, "ccusage-codex": True}


def test_check_all_dependencies_missing():
    """Test when dependencies are missing."""
    with patch("hermod.dependencies.check_ccusage_installed", return_value=False):
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_run.return_value = mock_result

            result = check_all_dependencies()
            assert result == {"ccusage": False, "ccusage-codex": False}
