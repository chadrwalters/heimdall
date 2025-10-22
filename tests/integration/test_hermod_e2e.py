"""End-to-end integration tests for Hermod.

These tests verify the complete collection workflow using real external dependencies.
"""
import json
import subprocess
from pathlib import Path
import pytest


def check_dependency(cmd: str) -> bool:
    """Check if external dependency is available."""
    try:
        result = subprocess.run(
            ["which", cmd],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False


# Skip all tests in this file if dependencies not available
ccusage_available = check_dependency("ccusage")
ccusage_codex_available = check_dependency("ccusage-codex")

skip_if_no_ccusage = pytest.mark.skipif(
    not ccusage_available,
    reason="ccusage not installed (npm install -g @anthropics/ccusage)"
)

skip_if_no_codex = pytest.mark.skipif(
    not ccusage_codex_available,
    reason="ccusage-codex not installed (npm install -g codex-usage-cli)"
)


@pytest.fixture
def cleanup_test_files():
    """Clean up any test submission files after test."""
    yield
    # Clean up test submissions
    submissions_dir = Path("data/ai_usage/submissions")
    if submissions_dir.exists():
        for file in submissions_dir.glob("ai_usage_TestUser_*.json"):
            file.unlink()


@skip_if_no_ccusage
def test_cli_collect_with_real_dependencies(cleanup_test_files):
    """Test collection with real ccusage tools installed."""
    # Run hermod collect with test developer
    result = subprocess.run(
        ["uv", "run", "hermod", "collect", "--developer", "TestUser", "--days", "7"],
        capture_output=True,
        text=True
    )

    # Should succeed
    assert result.returncode == 0, f"Command failed: {result.stderr}"

    # Check output contains expected elements
    assert "TestUser" in result.stdout
    assert "Successfully collected" in result.stdout or "✓" in result.stdout

    # Verify JSON file was created
    submissions_dir = Path("data/ai_usage/submissions")
    test_files = list(submissions_dir.glob("ai_usage_TestUser_*.json"))
    assert len(test_files) > 0, "No submission file created"

    # Verify JSON structure
    with open(test_files[0]) as f:
        data = json.load(f)

    assert "metadata" in data
    assert data["metadata"]["developer"] == "TestUser"
    assert "date_range" in data["metadata"]
    assert "claude_code" in data
    assert "codex" in data


@skip_if_no_ccusage
def test_cli_json_output(cleanup_test_files):
    """Test JSON output mode."""
    result = subprocess.run(
        ["uv", "run", "hermod", "collect", "--developer", "TestUser", "--days", "3", "--json"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0

    # Parse JSON output
    output = json.loads(result.stdout)
    assert output["developer"] == "TestUser"
    assert output["days"] == 3
    assert "claude_code" in output
    assert "codex" in output


def test_cli_missing_dependencies():
    """Test error handling when dependencies are missing."""
    # Mock missing dependencies by using a subprocess that will fail
    # We can't easily mock this in an e2e test, so we'll skip
    # The unit tests already cover this scenario
    pytest.skip("Covered by unit tests - requires mocking")


@skip_if_no_ccusage
def test_justfile_integration(cleanup_test_files):
    """Test collection via justfile."""
    result = subprocess.run(
        ["just", "ai-usage", "collect", "TestUser", "7"],
        capture_output=True,
        text=True,
        cwd=Path.cwd()
    )

    # Should succeed
    assert result.returncode == 0, f"Justfile command failed: {result.stderr}"

    # Check output contains expected elements
    assert "TestUser" in result.stdout
    assert "Collecting" in result.stdout or "📊" in result.stdout

    # Verify file was created
    submissions_dir = Path("data/ai_usage/submissions")
    test_files = list(submissions_dir.glob("ai_usage_TestUser_*.json"))
    assert len(test_files) > 0


@skip_if_no_ccusage
def test_auto_detection_from_git(cleanup_test_files):
    """Test auto-detection of developer from git config."""
    # This will use the actual git config from the environment
    result = subprocess.run(
        ["uv", "run", "hermod", "collect", "--days", "3"],
        capture_output=True,
        text=True
    )

    # Should succeed (will detect from git config)
    assert result.returncode == 0

    # Should have detected some developer name
    assert "Successfully collected" in result.stdout or "✓" in result.stdout

    # Verify file was created (we don't know the exact name)
    submissions_dir = Path("data/ai_usage/submissions")
    assert submissions_dir.exists()

    # Should have at least one submission file
    submission_files = list(submissions_dir.glob("ai_usage_*_*.json"))
    assert len(submission_files) > 0


def test_cli_version():
    """Test version flag works."""
    result = subprocess.run(
        ["uv", "run", "hermod", "--version"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "0.1.0" in result.stdout or "Hermod" in result.stdout


def test_cli_help():
    """Test help output."""
    result = subprocess.run(
        ["uv", "run", "hermod", "--help"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "hermod" in result.stdout.lower()
    assert "collect" in result.stdout.lower()


def test_collect_help():
    """Test collect command help."""
    result = subprocess.run(
        ["uv", "run", "hermod", "collect", "--help"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "collect" in result.stdout.lower()
    assert "developer" in result.stdout.lower()
    assert "days" in result.stdout.lower()
