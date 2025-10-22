"""Tests for git configuration detection."""
import pytest
from unittest.mock import patch, MagicMock
from hermod.git_detector import detect_developer, get_git_user_email


def test_get_git_user_email_success():
    """Test extracting email from git config."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.stdout = "chad@degreeanalytics.com\n"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        email = get_git_user_email()
        assert email == "chad@degreeanalytics.com"
        mock_run.assert_called_once_with(
            ["git", "config", "user.email"],
            capture_output=True,
            text=True,
            check=True
        )


def test_get_git_user_email_not_configured():
    """Test handling when git email is not configured."""
    import subprocess
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "git config")

        with pytest.raises(RuntimeError, match="Git user.email not configured"):
            get_git_user_email()


def test_detect_developer_from_git_name():
    """Test detecting canonical name from git name."""
    with patch("hermod.git_detector.get_git_user_email", return_value="unknown@example.com"):
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "Chad Walters\n"
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            developer = detect_developer()
            assert developer == "Chad"


def test_detect_developer_from_email():
    """Test detecting canonical name from git email."""
    with patch("hermod.git_detector.get_git_user_email", return_value="jeremiah@degreeanalytics.com"):
        developer = detect_developer()
        assert developer == "Jeremiah"


def test_detect_developer_email_fallback():
    """Test fallback when developer not found in mappings."""
    with patch("hermod.git_detector.get_git_user_email", return_value="unknown@example.com"):
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Git name not found")

            developer = detect_developer()
            assert developer == "unknown"  # Email username fallback
