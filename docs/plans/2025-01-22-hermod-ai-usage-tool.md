# Hermod AI Usage Collection Tool Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create "Hermod" - a standalone CLI tool that developers can install from this repo to collect their Claude Code (ccusage) and Codex (ccusage-codex) AI usage data and generate JSON files they can send to you. You'll manually ingest them with a separate command.

**Architecture:** Python CLI using Typer (following Huginn pattern) that auto-detects developer from git config, collects 7 days of usage data by default, and generates JSON files. Manual file sharing workflow (Slack/email) followed by manual ingestion command.

**Tech Stack:** Python 3.11+, Typer, Rich, existing collect_ai_usage.py logic

**Phase 1 (This Plan):** Core collection tool + manual workflow
**Phase 2 (Future):** Git auto-commit + GitHub Actions automation

---

## Task 1: Create Package Structure

**Files:**
- Create: `src/hermod/__init__.py`
- Create: `src/hermod/cli.py`
- Create: `src/hermod/collector.py`
- Create: `src/hermod/git_detector.py`
- Create: `tests/hermod/__init__.py`
- Create: `tests/hermod/test_git_detector.py`

**Step 1: Write the failing test for git detection**

Create `tests/hermod/__init__.py`:
```python
"""Hermod AI usage collection tool tests."""
```

Create `tests/hermod/test_git_detector.py`:
```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/hermod/test_git_detector.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'hermod'"

**Step 3: Create git_detector module with minimal implementation**

Create `src/hermod/__init__.py`:
```python
"""Hermod - AI usage collection tool for developers."""
__version__ = "0.1.0"
```

Create `src/hermod/git_detector.py`:
```python
"""Git configuration detection for developer identification."""
import json
import subprocess
from pathlib import Path
from typing import Optional


def get_git_user_email() -> str:
    """Get user email from git config.

    Returns:
        Email address from git config

    Raises:
        RuntimeError: If git email is not configured
    """
    try:
        result = subprocess.run(
            ["git", "config", "user.email"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        raise RuntimeError(
            "Git user.email not configured. Run: git config --global user.email 'you@example.com'"
        )


def get_git_user_name() -> Optional[str]:
    """Get user name from git config.

    Returns:
        User name from git config, or None if not configured
    """
    try:
        result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def load_developer_mappings() -> dict:
    """Load developer name mappings from config file.

    Returns:
        Dictionary with email_to_name and name_to_canonical mappings
    """
    config_path = Path(__file__).parent.parent.parent / "config" / "developer_names.json"

    with open(config_path) as f:
        config = json.load(f)

    # Build lookup maps
    email_to_canonical = {}
    name_to_canonical = {}

    for dev in config["developers"]:
        canonical = dev["canonical_name"]

        # Map linear emails (many contain email addresses)
        for linear_name in dev.get("linear_names", []):
            if "@" in linear_name:
                email_to_canonical[linear_name.lower()] = canonical

        # Map git names
        for git_name in dev.get("git_names", []):
            name_to_canonical[git_name.lower()] = canonical

    return {
        "email_to_canonical": email_to_canonical,
        "name_to_canonical": name_to_canonical
    }


def detect_developer() -> str:
    """Detect developer canonical name from git configuration.

    Returns:
        Canonical developer name

    Raises:
        RuntimeError: If git is not configured
    """
    mappings = load_developer_mappings()

    # Try email first (most reliable)
    email = get_git_user_email()
    canonical = mappings["email_to_canonical"].get(email.lower())
    if canonical:
        return canonical

    # Try git name
    git_name = get_git_user_name()
    if git_name:
        canonical = mappings["name_to_canonical"].get(git_name.lower())
        if canonical:
            return canonical

    # Fallback to email username
    return email.split("@")[0]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/hermod/test_git_detector.py -v`
Expected: PASS (all 5 tests)

**Step 5: Commit**

```bash
git add src/hermod/ tests/hermod/
git commit -m "feat(hermod): add git configuration detection for developer identification"
```

---

## Task 2: Create Dependency Checker

**Files:**
- Create: `src/hermod/dependencies.py`
- Create: `tests/hermod/test_dependencies.py`

**Step 1: Write the failing test**

Create `tests/hermod/test_dependencies.py`:
```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/hermod/test_dependencies.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'hermod.dependencies'"

**Step 3: Write minimal implementation**

Create `src/hermod/dependencies.py`:
```python
"""External dependency checking for ccusage tools."""
import subprocess
from typing import Dict


def check_ccusage_installed() -> bool:
    """Check if ccusage is installed and available on PATH.

    Returns:
        True if ccusage is installed, False otherwise
    """
    result = subprocess.run(
        ["which", "ccusage"],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def check_ccusage_codex_installed() -> bool:
    """Check if ccusage-codex is installed and available on PATH.

    Returns:
        True if ccusage-codex is installed, False otherwise
    """
    result = subprocess.run(
        ["which", "ccusage-codex"],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def check_all_dependencies() -> Dict[str, bool]:
    """Check all required external dependencies.

    Returns:
        Dictionary mapping tool name to installed status
    """
    return {
        "ccusage": check_ccusage_installed(),
        "ccusage-codex": check_ccusage_codex_installed()
    }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/hermod/test_dependencies.py -v`
Expected: PASS (all 4 tests)

**Step 5: Commit**

```bash
git add src/hermod/dependencies.py tests/hermod/test_dependencies.py
git commit -m "feat(hermod): add dependency checking for ccusage tools"
```

---

## Task 3: Create Collector Module

**Files:**
- Create: `tests/hermod/test_collector.py`
- Modify: `src/hermod/collector.py`

**Step 1: Write the failing test**

Create `tests/hermod/test_collector.py`:
```python
"""Tests for AI usage data collection."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from hermod.collector import collect_usage, save_submission


def test_collect_usage_success():
    """Test successful data collection."""
    with patch("hermod.collector.run_command") as mock_run:
        # Mock ccusage response
        mock_run.side_effect = [
            {"daily": [{"date": "2025-01-22", "cost": 1.50}], "totals": {"totalCost": 1.50}},
            {"daily": [{"date": "2025-01-22", "cost": 2.00}], "totals": {"totalCost": 2.00}}
        ]

        data = collect_usage("Chad", days=7)

        assert data["metadata"]["developer"] == "Chad"
        assert data["metadata"]["date_range"]["days"] == 7
        assert "claude_code" in data
        assert "codex" in data
        assert data["claude_code"]["totals"]["totalCost"] == 1.50
        assert data["codex"]["totals"]["totalCost"] == 2.00


def test_collect_usage_handles_errors():
    """Test collection continues when one tool fails."""
    with patch("hermod.collector.run_command") as mock_run:
        # First call succeeds, second fails
        mock_run.side_effect = [
            {"daily": [], "totals": {}},
            {}  # Empty dict indicates error
        ]

        data = collect_usage("Chad", days=7)

        assert data["claude_code"] == {"daily": [], "totals": {}}
        assert data["codex"] == {}


def test_save_submission():
    """Test saving submission to file."""
    import tempfile
    from pathlib import Path

    test_data = {
        "metadata": {"developer": "Chad", "collected_at": "2025-01-22T10:00:00"},
        "claude_code": {},
        "codex": {}
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/hermod/test_collector.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'hermod.collector'"

**Step 3: Write minimal implementation**

Create `src/hermod/collector.py`:
```python
"""AI usage data collection from ccusage and ccusage-codex."""
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any


def run_command(cmd: list[str]) -> Dict[str, Any]:
    """Run command and return parsed JSON output.

    Args:
        cmd: Command and arguments to run

    Returns:
        Parsed JSON output, or empty dict on error
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return {}


def collect_usage(developer: str, days: int = 7) -> Dict[str, Any]:
    """Collect usage data from both ccusage and ccusage-codex.

    Args:
        developer: Developer canonical name
        days: Number of days to collect (default: 7)

    Returns:
        Combined usage data with metadata
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    since_str = start_date.strftime("%Y%m%d")

    # Collect Claude Code usage
    claude_data = run_command([
        "ccusage", "daily", "--json", "--since", since_str
    ])

    # Collect Codex usage
    codex_data = run_command([
        "ccusage-codex", "daily", "--json", "--since", since_str
    ])

    # Combine with metadata
    return {
        "metadata": {
            "developer": developer,
            "collected_at": datetime.now().isoformat(),
            "date_range": {
                "start": start_date.date().isoformat(),
                "end": end_date.date().isoformat(),
                "days": days
            },
            "version": "1.0"
        },
        "claude_code": claude_data,
        "codex": codex_data
    }


def save_submission(
    data: Dict[str, Any],
    developer: str,
    output_dir: Path = None
) -> Path:
    """Save submission data to JSON file.

    Args:
        data: Usage data to save
        developer: Developer name for filename
        output_dir: Output directory (default: data/ai_usage/submissions)

    Returns:
        Path to saved file
    """
    if output_dir is None:
        output_dir = Path("data/ai_usage/submissions")

    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_str = datetime.now().strftime("%Y%m%d")
    output_file = output_dir / f"ai_usage_{developer}_{date_str}_{timestamp}.json"

    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)

    return output_file
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/hermod/test_collector.py -v`
Expected: PASS (all 3 tests)

**Step 5: Commit**

```bash
git add src/hermod/collector.py tests/hermod/test_collector.py
git commit -m "feat(hermod): add usage data collection and saving"
```

---

## Task 4: Create CLI with Typer

**Files:**
- Create: `tests/hermod/test_cli.py`
- Create: `src/hermod/cli.py`
- Modify: `pyproject.toml`

**Step 1: Write the failing test**

Create `tests/hermod/test_cli.py`:
```python
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
                    mock_collect.return_value = {"metadata": {"developer": "Chad"}}

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
                mock_collect.return_value = {"metadata": {"developer": "Jeremiah"}}

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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/hermod/test_cli.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'hermod.cli'"

**Step 3: Write minimal implementation**

Create `src/hermod/cli.py`:
```python
"""Hermod CLI - AI usage collection tool."""
import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from hermod.collector import collect_usage, save_submission
from hermod.dependencies import check_all_dependencies
from hermod.git_detector import detect_developer

app = typer.Typer(
    name="hermod",
    help="AI usage collection tool for developers",
    add_completion=False
)
console = Console()


@app.command()
def collect(
    days: int = typer.Option(7, help="Days of usage to collect"),
    developer: Optional[str] = typer.Option(None, help="Developer name (auto-detected if not provided)"),
    output_dir: Optional[Path] = typer.Option(None, help="Output directory path"),
    json_output: bool = typer.Option(False, "--json", help="JSON output format"),
):
    """Collect AI usage data from ccusage and ccusage-codex."""

    # Auto-detect developer from git config if not provided
    if not developer:
        try:
            developer = detect_developer()
        except RuntimeError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)

    # Check dependencies
    deps = check_all_dependencies()
    missing = [name for name, installed in deps.items() if not installed]

    if missing:
        console.print(f"[red]Error: Required tools not installed: {', '.join(missing)}[/red]")
        console.print("\n[yellow]Install with:[/yellow]")
        for tool in missing:
            console.print(f"  npm install -g {tool}")
        raise typer.Exit(1)

    # Collect data
    if not json_output:
        console.print(f"[cyan]📊 Collecting AI usage for {developer} (last {days} days)...[/cyan]")

    try:
        data = collect_usage(developer, days)
    except Exception as e:
        console.print(f"[red]Error collecting usage data: {e}[/red]")
        raise typer.Exit(1)

    # Save to file
    try:
        output_path = save_submission(data, developer, output_dir)
    except Exception as e:
        console.print(f"[red]Error saving submission: {e}[/red]")
        raise typer.Exit(1)

    # Output results
    if json_output:
        output = {
            "developer": developer,
            "days": days,
            "output_file": str(output_path),
            "claude_code_cost": data.get("claude_code", {}).get("totals", {}).get("totalCost", 0),
            "codex_cost": data.get("codex", {}).get("totals", {}).get("totalCost", 0)
        }
        console.print_json(data=output)
    else:
        console.print(f"\n[green]✅ Usage data collected: {output_path}[/green]")

        claude_totals = data.get("claude_code", {}).get("totals", {})
        codex_totals = data.get("codex", {}).get("totals", {})

        if claude_totals:
            console.print(f"   💰 Claude Code: ${claude_totals.get('totalCost', 0):.2f}")
        if codex_totals:
            console.print(f"   💰 Codex: ${codex_totals.get('totalCost', 0):.2f}")


@app.callback()
def version_callback(
    version: bool = typer.Option(False, "--version", help="Show version")
):
    """Show version information."""
    if version:
        from hermod import __version__
        console.print(f"Hermod {__version__}")
        raise typer.Exit()


if __name__ == "__main__":
    app()
```

**Step 4: Update pyproject.toml to add CLI entry point and dependencies**

Modify `pyproject.toml`:
```toml
[project]
name = "north-star-metrics"
version = "0.1.0"
description = "Engineering Impact Framework for data-driven visibility into development work"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "pandas>=2.2.0",
    # ... existing dependencies ...
]

[project.scripts]
hermod = "hermod.cli:app"

[project.optional-dependencies]
hermod = [
    "typer>=0.12.3",
    "rich>=13.7.0",
]

# ... rest of file ...
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/hermod/test_cli.py -v`
Expected: PASS (all 4 tests)

**Step 6: Commit**

```bash
git add src/hermod/cli.py tests/hermod/test_cli.py pyproject.toml
git commit -m "feat(hermod): add CLI with typer and rich output"
```

---

## Task 5: Add Justfile Commands and Ingestion

**Files:**
- Modify: `justfile`
- Create: `scripts/ingest_ai_usage.py`
- Create: `tests/test_ingestion.py`

**Step 1: Write the failing test for ingestion**

Create `tests/test_ingestion.py`:
```python
"""Tests for AI usage ingestion."""
import pytest
import json
import shutil
from pathlib import Path
from unittest.mock import patch


def test_ingest_submissions(tmp_path):
    """Test ingesting submission files."""
    # Import after we create the module
    from scripts.ingest_ai_usage import ingest_submissions

    # Set up test directories
    submissions_dir = tmp_path / "submissions"
    ingested_dir = tmp_path / "ingested"
    submissions_dir.mkdir()

    # Create test submission
    test_submission = {
        "metadata": {"developer": "Chad", "collected_at": "2025-01-22T10:00:00"},
        "claude_code": {"totals": {"totalCost": 1.5}},
        "codex": {"totals": {"totalCost": 2.0}}
    }
    submission_file = submissions_dir / "ai_usage_Chad_20250122_100000.json"
    with open(submission_file, "w") as f:
        json.dump(test_submission, f)

    # Mock the directories
    with patch("scripts.ingest_ai_usage.Path") as mock_path:
        mock_path.return_value.glob.return_value = [submission_file]

        # Run ingestion
        moved_files = ingest_submissions(submissions_dir, ingested_dir)

        assert len(moved_files) == 1
        assert ingested_dir / "ai_usage_Chad_20250122_100000.json" in moved_files


def test_ingest_no_submissions(tmp_path):
    """Test ingestion with no submissions."""
    from scripts.ingest_ai_usage import ingest_submissions

    submissions_dir = tmp_path / "submissions"
    ingested_dir = tmp_path / "ingested"
    submissions_dir.mkdir()

    moved_files = ingest_submissions(submissions_dir, ingested_dir)
    assert len(moved_files) == 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_ingestion.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Create ingestion script**

Create `scripts/ingest_ai_usage.py`:
```python
#!/usr/bin/env python3
"""Ingest AI usage submissions into processed data.

Moves JSON files from submissions/ to ingested/.
"""
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List


def ingest_submissions(
    submissions_dir: Path = None,
    ingested_dir: Path = None
) -> List[Path]:
    """Process all pending AI usage submissions.

    Args:
        submissions_dir: Directory containing submissions (default: data/ai_usage/submissions)
        ingested_dir: Directory for ingested files (default: data/ai_usage/ingested)

    Returns:
        List of paths to ingested files
    """
    if submissions_dir is None:
        submissions_dir = Path("data/ai_usage/submissions")
    if ingested_dir is None:
        ingested_dir = Path("data/ai_usage/ingested")

    ingested_dir.mkdir(parents=True, exist_ok=True)

    if not submissions_dir.exists():
        print("No submissions directory found")
        return []

    # Find all submission files
    submissions = list(submissions_dir.glob("ai_usage_*.json"))

    if not submissions:
        print("No submissions to process")
        return []

    print(f"📊 Processing {len(submissions)} submissions...")

    moved_files = []
    for submission_file in submissions:
        print(f"  Processing {submission_file.name}...")

        # Read and validate submission
        try:
            with open(submission_file) as f:
                data = json.load(f)

            # Basic validation
            if "metadata" not in data or "developer" not in data["metadata"]:
                print(f"    ⚠️  Skipping invalid submission: {submission_file.name}")
                continue

        except json.JSONDecodeError:
            print(f"    ⚠️  Skipping invalid JSON: {submission_file.name}")
            continue

        # Move to ingested
        dest = ingested_dir / submission_file.name
        shutil.move(str(submission_file), str(dest))
        moved_files.append(dest)

        print(f"    ✅ Moved to ingested/")

    print(f"\n✅ Ingested {len(moved_files)} submissions")
    return moved_files


def main():
    """Main entry point."""
    ingest_submissions()


if __name__ == "__main__":
    main()
```

Make it executable:
```bash
chmod +x scripts/ingest_ai_usage.py
```

**Step 4: Add justfile commands using dispatcher pattern**

Add to `justfile` at appropriate location:
```justfile
# ============================================================================
# AI Usage Collection (Hermod)
# ============================================================================

# Hermod CLI dispatcher (following huginn/muninn pattern)
[group('ai-usage')]
hermod command *args:
    @bash -lc 'set -euo pipefail; sub="$1"; shift; cmd=( hermod "$sub" ); if [ "$#" -gt 0 ]; then cmd+=("$@"); fi; "${cmd[@]}"' -- {{command}} {{args}}

# Manual ingestion (not a hermod CLI command - runs Python script directly)
[group('ai-usage')]
[doc('Ingest submitted AI usage data (run by repo owner)')]
hermod-ingest:
    @echo "📊 Ingesting AI usage submissions..."
    @python scripts/ingest_ai_usage.py
```

**Usage Examples:**
```bash
# Using dispatcher pattern for CLI commands
just hermod collect --days 7         # Collect 7 days of usage
just hermod collect --days 14        # Collect 14 days
just hermod collect --json           # JSON output mode
just hermod --help                   # Show hermod help
just hermod --version                # Show version

# Manual ingestion (separate recipe)
just hermod-ingest                   # Process submitted files
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/test_ingestion.py -v`
Expected: PASS (all 2 tests)

**Step 6: Test justfile commands with dispatcher pattern**

Run: `just hermod --version`
Expected: Shows hermod version

Run: `just hermod collect --days 7`
Expected: Collects 7 days of data (will fail gracefully if ccusage not installed, showing helpful error)

Run: `just hermod --help`
Expected: Shows hermod CLI help with available commands

**Step 7: Commit**

```bash
git add justfile scripts/ingest_ai_usage.py tests/test_ingestion.py
git commit -m "feat(hermod): add justfile commands and manual ingestion script"
```

---

## Task 6: Create Installation Documentation

**Files:**
- Create: `docs/hermod-installation.md`
- Modify: `README.md`

**Step 1: Create detailed installation guide**

Create `docs/hermod-installation.md`:
```markdown
# Hermod Installation Guide

Hermod is a lightweight CLI tool for collecting AI usage data (Claude Code and Codex) that you can send to the metrics team.

## Prerequisites

- Python 3.11+
- Git configured with your email
- npm (for ccusage tools)

## Installation

### For Developers (Install Tool Only)

```bash
# One-time install from GitHub
uv pip install git+https://github.com/degree-analytics/github_linear_metrics

# Verify installation
hermod --version
```

### Install Dependencies

```bash
# Install ccusage and ccusage-codex
npm install -g ccusage ccusage-codex

# Verify dependencies
hermod --version
```

## Usage

### Basic Collection

```bash
# Collect 7 days of usage (auto-detects your name from git config)
hermod collect

# Custom time period
hermod collect --days 14

# Specify developer explicitly
hermod collect --developer "Your Name" --days 7
```

### Output Location

Files are saved to: `data/ai_usage/submissions/ai_usage_{developer}_{date}_{timestamp}.json`

### JSON Output for Automation

```bash
# Get structured output
hermod collect --json

# Parse with jq
hermod collect --json | jq '.claude_code_cost'
```

## Sharing Data

After collection, send the generated JSON file to the metrics team via:
- Slack
- Email
- Or place in a shared folder

## Workflow

1. **Weekly Collection**: Run `hermod collect` once per week
2. **Share File**: Send the generated JSON to metrics team
3. **Team Ingests**: Metrics team runs `just hermod-ingest` to process submissions

## Troubleshooting

### Git Email Not Configured

```bash
# Configure git
git config --global user.email "you@degreeanalytics.com"
git config --global user.name "Your Name"
```

### ccusage Not Found

```bash
# Install ccusage tools
npm install -g ccusage ccusage-codex

# Check installation
which ccusage
which ccusage-codex
```

### Developer Name Not Detected

```bash
# Use explicit name
hermod collect --developer "Your Name"
```

## For Repository Owners

If you manage the metrics repository:

```bash
# Verify hermod installation
just hermod --version

# After receiving submissions, ingest them
just hermod-ingest
```

## Architecture

Hermod follows the naming pattern of our other tools:
- **Huginn**: Intelligence gathering (git/PR analysis)
- **Muninn**: Memory and monitoring (observability)
- **Hermod**: Messenger (usage data collection and delivery)

Named after the Norse messenger god who gathers and delivers information.
```

**Step 2: Update main README with Hermod section**

Add to `README.md` after the Quick Start section:
```markdown
## 📊 AI Usage Tracking with Hermod

Developers can install Hermod to collect their Claude Code and Codex usage data:

### Quick Install

```bash
# One-time install
uv pip install git+https://github.com/degree-analytics/github_linear_metrics

# Install dependencies
npm install -g ccusage ccusage-codex
```

### Usage

```bash
# Collect usage (auto-detects your name)
hermod collect

# Share the generated JSON file with the metrics team
```

**Repository owners can ingest submissions with:** `just hermod-ingest`

**See [Hermod Installation Guide](docs/hermod-installation.md) for complete documentation.**
```

**Step 3: Commit**

```bash
git add docs/hermod-installation.md README.md
git commit -m "docs(hermod): add installation and usage documentation"
```

---

## Task 7: End-to-End Testing

**Files:**
- Create: `tests/integration/__init__.py`
- Create: `tests/integration/test_hermod_e2e.py`

**Step 1: Write end-to-end integration test**

Create `tests/integration/__init__.py` if it doesn't exist:
```python
"""Integration tests for Hermod."""
```

Create `tests/integration/test_hermod_e2e.py`:
```python
"""End-to-end integration tests for Hermod."""
import pytest
import json
from pathlib import Path
from typer.testing import CliRunner
from hermod.cli import app


@pytest.fixture
def runner():
    """CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary output directory for tests."""
    output_dir = tmp_path / "ai_usage" / "submissions"
    output_dir.mkdir(parents=True)
    return output_dir


def test_full_collection_workflow(runner, temp_output_dir, monkeypatch):
    """Test complete collection workflow from CLI to file."""
    # Set up mocks
    from unittest.mock import patch, MagicMock

    with patch("hermod.cli.detect_developer", return_value="TestUser"):
        with patch("hermod.cli.check_all_dependencies", return_value={"ccusage": True, "ccusage-codex": True}):
            with patch("hermod.collector.run_command") as mock_run:
                # Mock ccusage responses
                mock_run.side_effect = [
                    {
                        "daily": [{"date": "2025-01-22", "cost": 1.50, "tokens": 1000}],
                        "totals": {"totalCost": 1.50, "totalTokens": 1000}
                    },
                    {
                        "daily": [{"date": "2025-01-22", "cost": 2.00, "tokens": 2000}],
                        "totals": {"totalCost": 2.00, "totalTokens": 2000}
                    }
                ]

                # Run collection
                result = runner.invoke(app, [
                    "collect",
                    "--developer", "TestUser",
                    "--days", "7",
                    "--output-dir", str(temp_output_dir)
                ])

                # Verify success
                assert result.exit_code == 0
                assert "TestUser" in result.stdout
                assert "✅" in result.stdout

                # Verify file was created
                submissions = list(temp_output_dir.glob("ai_usage_TestUser_*.json"))
                assert len(submissions) == 1

                # Verify content
                with open(submissions[0]) as f:
                    data = json.load(f)

                assert data["metadata"]["developer"] == "TestUser"
                assert data["metadata"]["date_range"]["days"] == 7
                assert data["claude_code"]["totals"]["totalCost"] == 1.50
                assert data["codex"]["totals"]["totalCost"] == 2.00


def test_json_output_format(runner):
    """Test JSON output format for automation."""
    from unittest.mock import patch

    with patch("hermod.cli.detect_developer", return_value="TestUser"):
        with patch("hermod.cli.check_all_dependencies", return_value={"ccusage": True, "ccusage-codex": True}):
            with patch("hermod.cli.collect_usage") as mock_collect:
                with patch("hermod.cli.save_submission") as mock_save:
                    mock_save.return_value = Path("test.json")
                    mock_collect.return_value = {
                        "metadata": {"developer": "TestUser"},
                        "claude_code": {"totals": {"totalCost": 1.5}},
                        "codex": {"totals": {"totalCost": 2.0}}
                    }

                    result = runner.invoke(app, ["collect", "--json"])

                    assert result.exit_code == 0

                    # Parse JSON output
                    output = json.loads(result.stdout)
                    assert output["developer"] == "TestUser"
                    assert output["claude_code_cost"] == 1.5
                    assert output["codex_cost"] == 2.0
```

**Step 2: Run integration tests**

Run: `pytest tests/integration/test_hermod_e2e.py -v`
Expected: PASS (all 2 tests)

**Step 3: Run all tests to ensure nothing broke**

Run: `pytest tests/hermod/ -v`
Expected: PASS (all tests)

**Step 4: Commit**

```bash
git add tests/integration/test_hermod_e2e.py
git commit -m "test(hermod): add end-to-end integration tests"
```

---

## Task 8: Final Testing and Documentation

**Step 1: Install and test hermod locally**

```bash
# Install in development mode
uv pip install -e .

# Verify installation
hermod --version

# Test help
hermod --help

# Test collection (will fail without ccusage, but should show error)
hermod collect
```

Expected: Tool runs, shows helpful errors if dependencies missing

**Step 2: Test justfile commands with dispatcher pattern**

```bash
# Test hermod CLI via dispatcher
just hermod --version
just hermod --help
just hermod collect --days 1

# Test manual ingestion
just hermod-ingest
```

Expected: All commands work correctly

**Step 3: Run full test suite**

```bash
pytest tests/ -v
```

Expected: All tests pass

**Step 4: Update CHANGELOG**

Add to `CHANGELOG.md`:
```markdown
## [Unreleased]

### Added
- **Hermod**: New CLI tool for developers to collect AI usage data
  - Auto-detects developer from git config
  - Collects Claude Code (ccusage) and Codex (ccusage-codex) data
  - JSON output mode for automation
  - Manual file sharing workflow (Phase 1)
  - Justfile dispatcher pattern: `just hermod <command>` (following huginn/muninn pattern)
  - Manual ingestion command: `just hermod-ingest` (repository owners only)
  - Manual ingestion script for processing submitted files
- Comprehensive installation documentation in `docs/hermod-installation.md`

### Future (Phase 2)
- Git auto-commit functionality
- GitHub Actions automation
```

**Step 5: Final commit**

```bash
git add CHANGELOG.md
git commit -m "docs(hermod): update changelog for v0.1.0 release"
```

---

## Verification Checklist

Before considering Phase 1 complete:

- [ ] All tests pass: `pytest tests/ -v`
- [ ] Hermod installs: `uv pip install -e .`
- [ ] CLI runs: `hermod --version`
- [ ] Help works: `hermod collect --help`
- [ ] Justfile dispatcher works: `just hermod --version`, `just hermod collect --days 7`
- [ ] Manual ingestion works: `just hermod-ingest`
- [ ] Documentation is complete: `docs/hermod-installation.md`
- [ ] README updated with Hermod section
- [ ] Manual ingestion script works
- [ ] All code committed with good messages

## Next Steps

**Phase 1 (This Plan) - Manual Workflow:**
1. **Test with real ccusage**: Install ccusage/ccusage-codex and test real data collection
2. **Developer onboarding**: Share installation guide with team
3. **Manual sharing**: Developers send JSON files via Slack/email
4. **Manual ingestion**: Repository owner runs `just hermod-ingest`
5. **Chart integration**: Update chart generation to use ingested AI usage data

**Phase 2 (Future) - Automation:**
1. **Git auto-commit**: Add `--commit` flag to commit submissions directly
2. **GitHub Actions**: Automated daily ingestion workflow
3. **Auto-push**: Developers can push directly to repo
4. **Slack notifications**: Alert when submissions processed
5. **Cost alerts**: Notify when usage is unusually high
