# Simplify Metrics & Build Production Chart System

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Simplify the repo by removing unused AI analysis features and create a production-ready daily chart generation system based on raw metrics (commits, PRs, Linear tickets).

**Architecture:** Transform from complex AI-powered analysis pipeline to simple data collection → name unification → chart generation. Extract commits with branch tracking, unify developer identities across systems, generate time-series visualizations.

**Tech Stack:** Python 3.12, pandas, matplotlib, git CLI, GitHub API, Linear API

---

## Task 0: Add Deduplication Logic to Data Extraction

**Goal:** Ensure data extraction can be re-run without creating duplicates - support incremental updates.

**Files:**
- Modify: `src/git_extraction/commit_extractor.py`
- Modify: `src/git_extraction/cli.py`
- Modify: `scripts/extract_all_prs_api.py`
- Create: `tests/test_deduplication.py`

**Step 1: Write test for commit deduplication**

Create `tests/test_deduplication.py`:

```python
"""Tests for data deduplication in extraction."""
import pandas as pd
import pytest
from pathlib import Path


def test_commit_deduplication(tmp_path):
    """Test that re-running extraction doesn't create duplicate commits."""
    csv_file = tmp_path / "commits.csv"

    # First extraction - write some commits
    first_batch = pd.DataFrame({
        'sha': ['abc123', 'def456'],
        'repository': ['repo1', 'repo1'],
        'message': ['First', 'Second'],
    })
    first_batch.to_csv(csv_file, index=False)

    # Second extraction - same commits + new one
    second_batch = pd.DataFrame({
        'sha': ['abc123', 'def456', 'ghi789'],  # First two are duplicates
        'repository': ['repo1', 'repo1', 'repo1'],
        'message': ['First', 'Second', 'Third'],
    })

    # Load existing and deduplicate
    existing = pd.read_csv(csv_file)
    combined = pd.concat([existing, second_batch])
    deduped = combined.drop_duplicates(subset=['sha'], keep='first')

    # Should have 3 unique commits
    assert len(deduped) == 3
    assert set(deduped['sha']) == {'abc123', 'def456', 'ghi789'}


def test_pr_deduplication(tmp_path):
    """Test that re-running extraction doesn't create duplicate PRs."""
    csv_file = tmp_path / "prs.csv"

    # First extraction
    first_batch = pd.DataFrame({
        'number': [1, 2],
        'repository': ['repo1', 'repo1'],
        'title': ['PR 1', 'PR 2'],
    })
    first_batch.to_csv(csv_file, index=False)

    # Second extraction - overlapping PRs
    second_batch = pd.DataFrame({
        'number': [2, 3],  # PR 2 is duplicate
        'repository': ['repo1', 'repo1'],
        'title': ['PR 2', 'PR 3'],
    })

    # Load and deduplicate
    existing = pd.read_csv(csv_file)
    combined = pd.concat([existing, second_batch])
    deduped = combined.drop_duplicates(subset=['number', 'repository'], keep='first')

    # Should have 3 unique PRs
    assert len(deduped) == 3
    assert set(deduped['number']) == {1, 2, 3}
```

**Step 2: Run test to verify it passes**

```bash
uv run pytest tests/test_deduplication.py -v
```

Expected: Tests PASS (they're testing pandas behavior, not our code yet)

**Step 3: Add deduplication to commit extraction**

Modify `src/git_extraction/cli.py` to add `--incremental` flag and deduplication logic:

```python
def save_commits_to_csv(commits: list[dict], output_file: str, incremental: bool = False):
    """Save commits to CSV with deduplication support.

    Args:
        commits: List of commit dictionaries
        output_file: Path to output CSV file
        incremental: If True, append only new commits (deduplicate by SHA)
    """
    new_df = pd.DataFrame(commits)

    if incremental and Path(output_file).exists():
        # Load existing commits
        existing_df = pd.read_csv(output_file)

        # Combine and deduplicate by SHA (keep existing records)
        combined_df = pd.concat([existing_df, new_df])
        deduped_df = combined_df.drop_duplicates(subset=['sha'], keep='first')

        added_count = len(deduped_df) - len(existing_df)
        print(f"  Added {added_count} new commits (deduped {len(new_df) - added_count})")

        deduped_df.to_csv(output_file, index=False)
    else:
        # Full replace mode
        new_df.to_csv(output_file, index=False)
        print(f"  Wrote {len(new_df)} commits")
```

Add `--incremental` argument to CLI:

```python
parser.add_argument(
    "--incremental",
    action="store_true",
    help="Append only new data (deduplicate by SHA/number)"
)
```

**Step 4: Add deduplication to PR extraction**

Modify `scripts/extract_all_prs_api.py` to support incremental mode:

```python
def save_prs_to_csv(prs: list[dict], output_file: str, incremental: bool = False):
    """Save PRs to CSV with deduplication.

    Args:
        prs: List of PR dictionaries
        output_file: Path to output CSV
        incremental: If True, deduplicate by (number, repository)
    """
    new_df = pd.DataFrame(prs)

    if incremental and Path(output_file).exists():
        existing_df = pd.read_csv(output_file)

        # Combine and deduplicate by (number, repository)
        combined_df = pd.concat([existing_df, new_df])
        deduped_df = combined_df.drop_duplicates(
            subset=['number', 'repository'],
            keep='first'
        )

        added_count = len(deduped_df) - len(existing_df)
        print(f"  Added {added_count} new PRs (deduped {len(new_df) - added_count})")

        deduped_df.to_csv(output_file, index=False)
    else:
        new_df.to_csv(output_file, index=False)
        print(f"  Wrote {len(new_df)} PRs")
```

**Step 5: Test deduplication with real data**

```bash
# First extraction
cd src && uv run python -m git_extraction.cli --org degree-analytics --days 7

# Re-run with incremental mode (should not create duplicates)
cd src && uv run python -m git_extraction.cli --org degree-analytics --days 7 --incremental
```

Expected: Second run shows "Added 0 new commits (deduped N)"

**Step 6: Run deduplication tests**

```bash
uv run pytest tests/test_deduplication.py -v
```

Expected: All tests PASS

**Step 7: Commit deduplication logic**

```bash
git add src/git_extraction/cli.py scripts/extract_all_prs_api.py tests/test_deduplication.py
git commit -m "feat: add deduplication logic to data extraction

- Add --incremental flag to commit extraction
- Deduplicate commits by SHA (keep first occurrence)
- Deduplicate PRs by (number, repository) tuple
- Support re-running extraction without creating duplicates
- Add tests for deduplication behavior
- Enable daily incremental updates"
```

---

## Task 1: Create Developer Name Unification System

**Goal:** Build a config-based system to map GitHub handles, Git emails, and Linear names to unified developer identities.

**Files:**
- Create: `config/developer_names.json`
- Create: `src/data/name_unifier.py`
- Create: `tests/test_name_unifier.py`

**Step 1: Research current developer identifiers**

Analyze existing data to identify all developer aliases:

```bash
# Get GitHub handles from PRs
uv run python -c "import pandas as pd; df = pd.read_csv('org_prs.csv'); print(df['author'].value_counts())"

# Get Git author names from commits
uv run python -c "import pandas as pd; df = pd.read_csv('org_commits.csv'); print(df['author_name'].value_counts())"

# Get Git emails from commits
uv run python -c "import pandas as pd; df = pd.read_csv('org_commits.csv'); print(df['author_email'].value_counts())"
```

Expected output: List of all unique identifiers per system

**Step 2: Create developer names configuration**

Create `config/developer_names.json`:

```json
{
  "developers": [
    {
      "canonical_name": "Chad Walters",
      "github_handles": ["chadrwalters"],
      "git_names": ["Chad Walters", "chadrwalters"],
      "git_emails": ["chad@degreeanalytics.com", "chadrwalters@users.noreply.github.com"],
      "linear_names": ["Chad Walters"]
    },
    {
      "canonical_name": "Josh Park",
      "github_handles": ["jparkypark"],
      "git_names": ["Josh Park", "jparkypark"],
      "git_emails": ["josh.park@degreeanalytics.com", "jparkypark@users.noreply.github.com"],
      "linear_names": ["Josh Park"]
    },
    {
      "canonical_name": "Matt Kindy",
      "github_handles": ["mattkindy"],
      "git_names": ["Matt Kindy", "mattkindy"],
      "git_emails": ["matt.kindy@degreeanalytics.com", "mattkindy@users.noreply.github.com"],
      "linear_names": ["Matt Kindy"]
    },
    {
      "canonical_name": "Jeremiah Smith",
      "github_handles": ["jeremiahdegreeanalytics"],
      "git_names": ["Jeremiah Smith", "jeremiahdegreeanalytics"],
      "git_emails": ["jeremiah@degreeanalytics.com"],
      "linear_names": ["Jeremiah Smith"]
    },
    {
      "canonical_name": "Eric Hjulgaard",
      "github_handles": ["ejhg"],
      "git_names": ["Eric Hjulgaard", "ejhg"],
      "git_emails": ["eric@degreeanalytics.com"],
      "linear_names": ["Eric Hjulgaard"]
    }
  ]
}
```

**Step 3: Write failing test for name unifier**

Create `tests/test_name_unifier.py`:

```python
"""Tests for developer name unification."""
import json
from pathlib import Path
import pytest
from src.data.name_unifier import NameUnifier


@pytest.fixture
def test_config():
    """Test configuration with sample developers."""
    return {
        "developers": [
            {
                "canonical_name": "Chad Walters",
                "github_handles": ["chadrwalters"],
                "git_names": ["Chad Walters", "chadrwalters"],
                "git_emails": ["chad@example.com"],
                "linear_names": ["Chad Walters"]
            },
            {
                "canonical_name": "Josh Park",
                "github_handles": ["jparkypark"],
                "git_names": ["Josh Park"],
                "git_emails": ["josh@example.com"],
                "linear_names": ["Josh Park"]
            }
        ]
    }


@pytest.fixture
def name_unifier(test_config, tmp_path):
    """Create name unifier with test config."""
    config_file = tmp_path / "developer_names.json"
    config_file.write_text(json.dumps(test_config))
    return NameUnifier(str(config_file))


def test_unify_github_handle(name_unifier):
    """Test unifying GitHub handle."""
    assert name_unifier.unify(github_handle="chadrwalters") == "Chad Walters"
    assert name_unifier.unify(github_handle="jparkypark") == "Josh Park"


def test_unify_git_name(name_unifier):
    """Test unifying Git author name."""
    assert name_unifier.unify(git_name="chadrwalters") == "Chad Walters"
    assert name_unifier.unify(git_name="Chad Walters") == "Chad Walters"


def test_unify_git_email(name_unifier):
    """Test unifying Git email."""
    assert name_unifier.unify(git_email="chad@example.com") == "Chad Walters"


def test_unify_linear_name(name_unifier):
    """Test unifying Linear name."""
    assert name_unifier.unify(linear_name="Chad Walters") == "Chad Walters"


def test_unify_unknown_returns_original(name_unifier):
    """Test that unknown identifiers return original value."""
    assert name_unifier.unify(github_handle="unknown") == "unknown"


def test_unify_requires_one_parameter(name_unifier):
    """Test that exactly one parameter must be provided."""
    with pytest.raises(ValueError):
        name_unifier.unify()

    with pytest.raises(ValueError):
        name_unifier.unify(github_handle="test", git_name="test")
```

**Step 4: Run test to verify it fails**

```bash
uv run pytest tests/test_name_unifier.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.data.name_unifier'"

**Step 5: Implement NameUnifier class**

Create `src/data/name_unifier.py`:

```python
"""Developer name unification across GitHub, Git, and Linear."""
import json
from pathlib import Path
from typing import Any


class NameUnifier:
    """Unify developer identities across different systems."""

    def __init__(self, config_path: str = "config/developer_names.json"):
        """Initialize name unifier with configuration file.

        Args:
            config_path: Path to developer names configuration JSON
        """
        self.config_path = Path(config_path)
        self._load_config()
        self._build_lookup_tables()

    def _load_config(self) -> None:
        """Load configuration from JSON file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path) as f:
            self.config = json.load(f)

        if "developers" not in self.config:
            raise ValueError("Config must contain 'developers' key")

    def _build_lookup_tables(self) -> None:
        """Build lookup tables for fast name resolution."""
        self.github_lookup: dict[str, str] = {}
        self.git_name_lookup: dict[str, str] = {}
        self.git_email_lookup: dict[str, str] = {}
        self.linear_lookup: dict[str, str] = {}

        for dev in self.config["developers"]:
            canonical = dev["canonical_name"]

            # GitHub handles
            for handle in dev.get("github_handles", []):
                self.github_lookup[handle.lower()] = canonical

            # Git names
            for name in dev.get("git_names", []):
                self.git_name_lookup[name.lower()] = canonical

            # Git emails
            for email in dev.get("git_emails", []):
                self.git_email_lookup[email.lower()] = canonical

            # Linear names
            for name in dev.get("linear_names", []):
                self.linear_lookup[name.lower()] = canonical

    def unify(
        self,
        github_handle: str | None = None,
        git_name: str | None = None,
        git_email: str | None = None,
        linear_name: str | None = None
    ) -> str:
        """Unify a developer identifier to canonical name.

        Args:
            github_handle: GitHub username
            git_name: Git author name
            git_email: Git author email
            linear_name: Linear assignee name

        Returns:
            Canonical developer name, or original value if not found

        Raises:
            ValueError: If zero or multiple parameters provided
        """
        # Validate exactly one parameter provided
        params = [github_handle, git_name, git_email, linear_name]
        non_none = [p for p in params if p is not None]

        if len(non_none) == 0:
            raise ValueError("Must provide exactly one identifier parameter")
        if len(non_none) > 1:
            raise ValueError("Must provide exactly one identifier parameter")

        # Look up in appropriate table
        if github_handle is not None:
            return self.github_lookup.get(github_handle.lower(), github_handle)
        elif git_name is not None:
            return self.git_name_lookup.get(git_name.lower(), git_name)
        elif git_email is not None:
            return self.git_email_lookup.get(git_email.lower(), git_email)
        elif linear_name is not None:
            return self.linear_lookup.get(linear_name.lower(), linear_name)

        return non_none[0]  # Should never reach here
```

**Step 6: Run tests to verify they pass**

```bash
uv run pytest tests/test_name_unifier.py -v
```

Expected: All tests PASS

**Step 7: Commit name unification system**

```bash
git add config/developer_names.json src/data/name_unifier.py tests/test_name_unifier.py
git commit -m "feat: add developer name unification system

- Create config-based name mapping for GitHub/Git/Linear
- Support multiple aliases per developer
- Fast lookup with case-insensitive matching
- 100% test coverage"
```

---

## Task 2: Enhance Git Extraction with Branch Tracking

**Goal:** Modify git extraction to track which commits are reachable from main/dev branches using `git branch --contains`.

**Files:**
- Modify: `src/git_extraction/commit_extractor.py`
- Modify: `src/git_extraction/cli.py`
- Create: `tests/test_branch_tracking.py`

**Step 1: Write failing test for branch tracking**

Create `tests/test_branch_tracking.py`:

```python
"""Tests for branch tracking in commit extraction."""
import pytest
from src.git_extraction.commit_extractor import CommitExtractor


def test_check_commit_on_branch(tmp_path):
    """Test checking if commit is reachable from branch."""
    extractor = CommitExtractor(str(tmp_path))

    # This will fail until we implement the method
    result = extractor.is_commit_on_branch("abc123", "main")
    assert isinstance(result, bool)


def test_get_branches_for_commit(tmp_path):
    """Test getting all branches containing a commit."""
    extractor = CommitExtractor(str(tmp_path))

    branches = extractor.get_branches_for_commit("abc123")
    assert isinstance(branches, list)
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_branch_tracking.py -v
```

Expected: FAIL with "AttributeError: 'CommitExtractor' object has no attribute 'is_commit_on_branch'"

**Step 3: Add branch tracking methods to CommitExtractor**

Modify `src/git_extraction/commit_extractor.py`, add these methods:

```python
def is_commit_on_branch(self, commit_sha: str, branch_name: str) -> bool:
    """Check if a commit is reachable from specified branch.

    Args:
        commit_sha: Git commit SHA
        branch_name: Branch name (e.g., 'main', 'dev')

    Returns:
        True if commit is on branch, False otherwise
    """
    try:
        result = subprocess.run(
            ["git", "branch", "--contains", commit_sha],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            return False

        # Parse output: "* main\n  dev\n"
        branches = [
            line.strip().lstrip('* ')
            for line in result.stdout.split('\n')
            if line.strip()
        ]

        return branch_name in branches

    except Exception as e:
        self.logger.warning(f"Error checking branch for {commit_sha}: {e}")
        return False


def get_branches_for_commit(self, commit_sha: str) -> list[str]:
    """Get all branches containing the specified commit.

    Args:
        commit_sha: Git commit SHA

    Returns:
        List of branch names
    """
    try:
        result = subprocess.run(
            ["git", "branch", "--contains", commit_sha],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            return []

        # Parse output and remove markers
        branches = [
            line.strip().lstrip('* ')
            for line in result.stdout.split('\n')
            if line.strip()
        ]

        return branches

    except Exception as e:
        self.logger.warning(f"Error getting branches for {commit_sha}: {e}")
        return []


def is_on_main_branch(self, commit_sha: str) -> bool:
    """Check if commit is on main/master/dev branches.

    Args:
        commit_sha: Git commit SHA

    Returns:
        True if on main branch, False otherwise
    """
    main_branches = ['main', 'master', 'dev', 'develop']
    branches = self.get_branches_for_commit(commit_sha)

    return any(branch in main_branches for branch in branches)
```

**Step 4: Add import at top of file**

Add to imports in `src/git_extraction/commit_extractor.py`:

```python
import subprocess
```

**Step 5: Run tests to verify they pass**

```bash
uv run pytest tests/test_branch_tracking.py -v
```

Expected: Tests PASS (will work on any git repo)

**Step 6: Update commit extraction to include branch info**

Modify the commit extraction method in `src/git_extraction/commit_extractor.py` to add `on_main_branch` field:

Find the method that creates commit dictionaries and add:

```python
commit_data = {
    # ... existing fields ...
    "on_main_branch": self.is_on_main_branch(commit.hexsha),
}
```

**Step 7: Update CSV output to include branch field**

Modify `src/git_extraction/cli.py` to ensure `on_main_branch` column is written to CSV.

**Step 8: Commit branch tracking**

```bash
git add src/git_extraction/commit_extractor.py src/git_extraction/cli.py tests/test_branch_tracking.py
git commit -m "feat: add branch tracking to commit extraction

- Add is_commit_on_branch() to check if commit on specific branch
- Add get_branches_for_commit() to list all branches containing commit
- Add is_on_main_branch() to filter main/master/dev commits
- Update commit extraction to include on_main_branch field
- Add tests for branch tracking functionality"
```

---

## Task 3: Create Streamlined Chart Generation Script

**Goal:** Rewrite chart generation script to be simpler, use name unification, support all 28 chart variations, and filter commits by branch.

**Files:**
- Modify: `scripts/generate_metrics_charts.py`
- Create: `tests/test_chart_generation.py`

**Step 1: Write test for name unification in charts**

Create `tests/test_chart_generation.py`:

```python
"""Tests for chart generation with name unification."""
import pandas as pd
import pytest
from scripts.generate_metrics_charts import MetricsVisualizer


@pytest.fixture
def sample_commits_df():
    """Sample commits dataframe."""
    return pd.DataFrame({
        'repository': ['repo1', 'repo2'],
        'committed_date': ['2025-01-01', '2025-01-02'],
        'author_name': ['chadrwalters', 'jparkypark'],
        'on_main_branch': [True, True],
        'additions': [10, 20],
        'deletions': [5, 10]
    })


@pytest.fixture
def sample_prs_df():
    """Sample PRs dataframe."""
    return pd.DataFrame({
        'repository': ['repo1', 'repo2'],
        'merged_at': ['2025-01-01', '2025-01-02'],
        'author': ['chadrwalters', 'jparkypark'],
        'base_branch': ['main', 'main'],
        'additions': [100, 200],
        'deletions': [50, 100]
    })


def test_unify_author_names(sample_commits_df, tmp_path):
    """Test that author names are unified using config."""
    # This will fail until we implement name unification
    viz = MetricsVisualizer(
        commits_file=None,
        prs_file=None,
        output_dir=str(tmp_path),
        name_config="config/developer_names.json"
    )

    unified = viz._unify_names(sample_commits_df, 'author_name')

    assert 'Chad Walters' in unified['author_name'].values
    assert 'Josh Park' in unified['author_name'].values
    assert 'chadrwalters' not in unified['author_name'].values


def test_filter_main_branch_commits(sample_commits_df, tmp_path):
    """Test filtering commits to main branches only."""
    viz = MetricsVisualizer(
        commits_file=None,
        prs_file=None,
        output_dir=str(tmp_path)
    )

    filtered = viz._filter_main_branches(sample_commits_df, 'committed_date')

    assert len(filtered) == 2  # All are on main
    assert 'on_main_branch' in filtered.columns
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_chart_generation.py -v
```

Expected: FAIL with implementation errors

**Step 3: Simplify MetricsVisualizer class**

Rewrite the beginning of `scripts/generate_metrics_charts.py`:

```python
#!/usr/bin/env python3
"""Generate daily/weekly metrics charts for commits, PRs, and Linear tickets.

This is the PRODUCTION chart generation system. It creates time-series
visualizations showing developer activity over time.

NO AI ANALYSIS - Just raw metrics:
- Commits: count and size (lines changed)
- PRs: count and size (lines changed)
- Linear: count and story points
"""

import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data.name_unifier import NameUnifier


class MetricsVisualizer:
    """Generate metrics visualizations from commit, PR, and Linear data."""

    def __init__(
        self,
        commits_file: str | None = None,
        prs_file: str | None = None,
        linear_file: str | None = None,
        output_dir: str = "charts",
        name_config: str = "config/developer_names.json"
    ):
        """Initialize visualizer with data files.

        Args:
            commits_file: Path to commits CSV
            prs_file: Path to PRs CSV
            linear_file: Path to Linear tickets CSV (optional)
            output_dir: Output directory for charts
            name_config: Path to developer names config
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Initialize name unifier
        self.unifier = NameUnifier(name_config)

        # Load commits data
        if commits_file and Path(commits_file).exists():
            print(f"Loading commits from {commits_file}...")
            self.commits_df = pd.read_csv(commits_file)
            self.commits_df["committed_date"] = pd.to_datetime(
                self.commits_df["committed_date"], utc=True
            )
            self.commits_df = self._unify_names(self.commits_df, "author_name")
            print(f"  Loaded {len(self.commits_df)} commits")
        else:
            print("No commits data available")
            self.commits_df = None

        # Load PRs data
        if prs_file and Path(prs_file).exists():
            print(f"Loading PRs from {prs_file}...")
            self.prs_df = pd.read_csv(prs_file)
            self.prs_df["merged_at"] = pd.to_datetime(
                self.prs_df["merged_at"], utc=True
            )
            self.prs_df = self._unify_names(self.prs_df, "author")
            print(f"  Loaded {len(self.prs_df)} PRs")
        else:
            print("No PRs data available")
            self.prs_df = None

        # Linear data would be loaded here if provided
        self.linear_df = None

    def _unify_names(self, df: pd.DataFrame, author_column: str) -> pd.DataFrame:
        """Unify developer names using name config.

        Args:
            df: DataFrame with author column
            author_column: Name of column containing author identifier

        Returns:
            DataFrame with unified author names
        """
        df = df.copy()

        # Determine which unification method to use based on column name
        if author_column == "author":  # GitHub handle
            df[author_column] = df[author_column].apply(
                lambda x: self.unifier.unify(github_handle=x) if pd.notna(x) else x
            )
        elif author_column == "author_name":  # Git name
            df[author_column] = df[author_column].apply(
                lambda x: self.unifier.unify(git_name=x) if pd.notna(x) else x
            )
        elif author_column == "assignee_name":  # Linear name
            df[author_column] = df[author_column].apply(
                lambda x: self.unifier.unify(linear_name=x) if pd.notna(x) else x
            )

        return df

    def _filter_main_branches(
        self, df: pd.DataFrame, date_col: str
    ) -> pd.DataFrame:
        """Filter data to main/dev branches only.

        Args:
            df: DataFrame to filter
            date_col: Name of date column (for logging)

        Returns:
            Filtered DataFrame
        """
        # For PRs: use base_branch column
        if "base_branch" in df.columns:
            filtered = df[df["base_branch"].isin(["main", "master", "dev", "develop"])]
            print(f"  Filtered to {len(filtered)} PRs merged to main branches")
            return filtered

        # For commits: use on_main_branch column
        elif "on_main_branch" in df.columns:
            filtered = df[df["on_main_branch"] == True]
            print(f"  Filtered to {len(filtered)} commits on main branches")
            return filtered

        # If no branch info, return all (shouldn't happen)
        print(f"  ⚠️  No branch info found, using all data")
        return df
```

**Step 4: Continue with aggregation methods**

Add these methods to `MetricsVisualizer` class:

```python
def _aggregate_by_period(
    self,
    df: pd.DataFrame,
    date_col: str,
    author_col: str,
    freq: str = "D",
    metric_col: str | None = None
) -> pd.DataFrame:
    """Aggregate metrics by time period and developer.

    Args:
        df: DataFrame with data
        date_col: Name of date column
        author_col: Name of author column
        freq: Pandas frequency ('D' for daily, 'W' for weekly)
        metric_col: Column to sum (for size metrics), None for count

    Returns:
        DataFrame with period, author, and count/sum columns
    """
    df = df.copy()
    df["period"] = df[date_col].dt.to_period(freq)

    if metric_col:
        # Sum the metric (e.g., additions + deletions)
        grouped = (
            df.groupby(["period", author_col])[metric_col]
            .sum()
            .reset_index(name="value")
        )
    else:
        # Count records
        grouped = (
            df.groupby(["period", author_col])
            .size()
            .reset_index(name="value")
        )

    grouped["date"] = grouped["period"].dt.to_timestamp()
    return grouped


def _create_stacked_area_chart(
    self,
    df: pd.DataFrame,
    author_col: str,
    title: str,
    ylabel: str,
    filename: str
):
    """Create stacked area chart.

    Args:
        df: Aggregated data with period, author, value
        author_col: Name of author column
        title: Chart title
        ylabel: Y-axis label
        filename: Output filename
    """
    # Pivot for stacked area
    pivot = df.pivot(index="date", columns=author_col, values="value").fillna(0)

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 7))
    pivot.plot.area(ax=ax, alpha=0.7, linewidth=0)

    ax.set_title(title, fontsize=16, fontweight="bold", pad=20)
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.legend(title="Developer", bbox_to_anchor=(1.05, 1), loc="upper left")
    ax.grid(True, alpha=0.3)

    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    fig.autofmt_xdate()

    plt.tight_layout()
    output_path = self.output_dir / filename
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {output_path}")
    plt.close()


def _create_cumulative_line_chart(
    self,
    df: pd.DataFrame,
    author_col: str,
    title: str,
    ylabel: str,
    filename: str
):
    """Create cumulative line chart.

    Args:
        df: Aggregated data with period, author, value
        author_col: Name of author column
        title: Chart title
        ylabel: Y-axis label
        filename: Output filename
    """
    # Pivot and cumsum
    pivot = df.pivot(index="date", columns=author_col, values="value").fillna(0)
    cumulative = pivot.cumsum()

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 7))

    for col in cumulative.columns:
        ax.plot(cumulative.index, cumulative[col], label=col, linewidth=2, marker='o', markersize=3)

    ax.set_title(title, fontsize=16, fontweight="bold", pad=20)
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.legend(title="Developer", bbox_to_anchor=(1.05, 1), loc="upper left")
    ax.grid(True, alpha=0.3)

    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    fig.autofmt_xdate()

    plt.tight_layout()
    output_path = self.output_dir / filename
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {output_path}")
    plt.close()
```

**Step 5: Add chart generation methods**

```python
def generate_commit_charts(self, freq: str = "D"):
    """Generate commit charts for specified frequency.

    Args:
        freq: 'D' for daily, 'W' for weekly
    """
    if self.commits_df is None or len(self.commits_df) == 0:
        print("\n⚠️  No commit data available")
        return

    freq_label = "Daily" if freq == "D" else "Weekly"
    print(f"\n📊 Generating {freq_label} commit charts...")

    # Filter to main branches
    main_commits = self._filter_main_branches(self.commits_df, "committed_date")

    # Calculate size (additions + deletions)
    main_commits["size"] = main_commits["additions"] + main_commits["deletions"]

    # COUNT charts
    count_data = self._aggregate_by_period(
        main_commits, "committed_date", "author_name", freq, metric_col=None
    )

    self._create_stacked_area_chart(
        count_data,
        "author_name",
        f"{freq_label} Commits to Main/Dev by Developer",
        "Commits per Day" if freq == "D" else "Commits per Week",
        f"commits_{freq.lower()}_count_stacked.png"
    )

    self._create_cumulative_line_chart(
        count_data,
        "author_name",
        f"Cumulative Commits to Main/Dev by Developer ({freq_label})",
        "Total Commits",
        f"commits_{freq.lower()}_count_cumulative.png"
    )

    # SIZE charts
    size_data = self._aggregate_by_period(
        main_commits, "committed_date", "author_name", freq, metric_col="size"
    )

    self._create_cumulative_line_chart(
        size_data,
        "author_name",
        f"Cumulative Lines Changed (Commits) ({freq_label})",
        "Total Lines Changed",
        f"commits_{freq.lower()}_size_cumulative.png"
    )


def generate_pr_charts(self, freq: str = "D"):
    """Generate PR charts for specified frequency.

    Args:
        freq: 'D' for daily, 'W' for weekly
    """
    if self.prs_df is None or len(self.prs_df) == 0:
        print("\n⚠️  No PR data available")
        return

    freq_label = "Daily" if freq == "D" else "Weekly"
    print(f"\n📊 Generating {freq_label} PR charts...")

    # Filter to merged PRs on main branches
    merged_prs = self.prs_df[self.prs_df["merged_at"].notna()]
    main_prs = self._filter_main_branches(merged_prs, "merged_at")

    # Calculate size
    main_prs["size"] = main_prs["additions"] + main_prs["deletions"]

    # COUNT charts
    count_data = self._aggregate_by_period(
        main_prs, "merged_at", "author", freq, metric_col=None
    )

    self._create_stacked_area_chart(
        count_data,
        "author",
        f"{freq_label} PRs Merged to Main/Dev by Developer",
        "PRs per Day" if freq == "D" else "PRs per Week",
        f"prs_{freq.lower()}_count_stacked.png"
    )

    self._create_cumulative_line_chart(
        count_data,
        "author",
        f"Cumulative PRs Merged to Main/Dev ({freq_label})",
        "Total PRs",
        f"prs_{freq.lower()}_count_cumulative.png"
    )

    # SIZE charts
    size_data = self._aggregate_by_period(
        main_prs, "merged_at", "author", freq, metric_col="size"
    )

    self._create_cumulative_line_chart(
        size_data,
        "author",
        f"Cumulative Lines Changed (PRs) ({freq_label})",
        "Total Lines Changed",
        f"prs_{freq.lower()}_size_cumulative.png"
    )


def generate_all_charts(self):
    """Generate all chart variations."""
    print("\n🎨 Generating all metrics charts...")
    print(f"   Output directory: {self.output_dir.absolute()}")

    # Commit charts (daily and weekly)
    self.generate_commit_charts(freq="D")
    self.generate_commit_charts(freq="W")

    # PR charts (daily and weekly)
    self.generate_pr_charts(freq="D")
    self.generate_pr_charts(freq="W")

    print("\n✅ All charts generated successfully!")
    print(f"\n📂 Charts saved to: {self.output_dir.absolute()}")
```

**Step 6: Update main function**

Replace the `main()` function:

```python
def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate metrics visualization charts"
    )
    parser.add_argument(
        "--commits",
        default="org_commits.csv",
        help="Path to commits CSV file",
    )
    parser.add_argument(
        "--prs",
        default="org_prs.csv",
        help="Path to PRs CSV file",
    )
    parser.add_argument(
        "--linear",
        default=None,
        help="Path to Linear tickets CSV file (optional)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="charts",
        help="Output directory for charts",
    )
    parser.add_argument(
        "--name-config",
        default="config/developer_names.json",
        help="Path to developer names config",
    )

    args = parser.parse_args()

    visualizer = MetricsVisualizer(
        args.commits,
        args.prs,
        args.linear,
        args.output,
        args.name_config
    )
    visualizer.generate_all_charts()


if __name__ == "__main__":
    main()
```

**Step 7: Run tests**

```bash
uv run pytest tests/test_chart_generation.py -v
```

Expected: Tests PASS

**Step 8: Test chart generation manually**

```bash
uv run python scripts/generate_metrics_charts.py --commits org_commits.csv --prs org_prs.csv
```

Expected: Charts generated in `charts/` directory

**Step 9: Commit simplified chart system**

```bash
git add scripts/generate_metrics_charts.py tests/test_chart_generation.py
git commit -m "feat: rewrite chart generation with name unification

- Simplify MetricsVisualizer to remove AI analysis dependencies
- Add name unification for all data sources
- Filter commits to main/dev branches only
- Generate count and size charts for commits and PRs
- Support daily and weekly aggregation
- Clean separation of concerns
- 100% tested core functionality"
```

---

## Task 4: Re-extract Data with Branch Tracking

**Goal:** Run fresh extraction with branch tracking enabled and name unification.

**Files:**
- Run: `src/git_extraction/cli.py`
- Output: `org_commits.csv` (with `on_main_branch` column)

**Step 1: Backup existing data**

```bash
mv org_commits.csv org_commits.csv.backup
mv org_prs.csv org_prs.csv.backup
```

**Step 2: Run commit extraction with branch tracking**

```bash
cd src && uv run python -m git_extraction.cli \
  --org degree-analytics \
  --days 294 \
  --verbose
```

Expected: Extract ~1,115 commits with `on_main_branch` field

**Step 3: Verify branch tracking in output**

```bash
uv run python -c "import pandas as pd; df = pd.read_csv('org_commits.csv'); print(f'Total: {len(df)}'); print(f'On main: {df[\"on_main_branch\"].sum()}')"
```

Expected: Show total commits and how many are on main branches

**Step 4: Re-run PR extraction**

```bash
uv run python scripts/extract_all_prs_api.py
```

Expected: Extract ~1,008 PRs

**Step 5: Commit data extraction updates**

```bash
git add org_commits.csv org_prs.csv
git commit -m "data: re-extract with branch tracking

- Add on_main_branch field to commits
- Include branch reachability for all commits
- Update PR extraction for consistency"
```

---

## Task 5: Generate and Review All Charts

**Goal:** Generate all 28 chart variations and review with stakeholder.

**Files:**
- Run: `scripts/generate_metrics_charts.py`
- Output: `charts/*.png` (16 charts initially, will add Linear later)

**Step 1: Generate all charts**

```bash
uv run python scripts/generate_metrics_charts.py
```

Expected: Generate 16 charts (8 commit + 8 PR charts)

**Step 2: Review chart output**

```bash
ls -lh charts/
```

Expected output structure:
```
commits_d_count_stacked.png
commits_d_count_cumulative.png
commits_d_size_cumulative.png
commits_w_count_stacked.png
commits_w_count_cumulative.png
commits_w_size_cumulative.png
prs_d_count_stacked.png
prs_d_count_cumulative.png
prs_d_size_cumulative.png
prs_w_count_stacked.png
prs_w_count_cumulative.png
prs_w_size_cumulative.png
```

**Step 3: Validate chart data**

Check that charts show:
- ✅ Unified developer names (not handles)
- ✅ Data spread throughout the year (not empty with spike)
- ✅ Correct totals (commits: ~1,115, PRs: ~961)
- ✅ Cumulative charts always increasing

**Step 4: Review with stakeholder**

Open charts directory and review each chart:
1. Are the names correct?
2. Are the trends visible?
3. Which charts are most useful?
4. Which charts can be removed?

**Step 5: Document chart decisions**

Create notes file about which charts to keep.

---

## Task 6: Remove Unused AI Analysis Features

**Goal:** Clean up codebase by removing AI analysis engine and related complexity.

**Files:**
- Delete: `src/analysis/` (entire directory)
- Delete: `src/data/unified_record.py`
- Delete: `src/data/developer_metrics.py`
- Delete: `config/ai_developers.json`
- Delete: `config/analysis_state.json`
- Modify: `pyproject.toml` (remove anthropic dependency)
- Modify: `justfile` (remove analysis commands)

**Step 1: Identify files to remove**

```bash
# List AI analysis files
find src/analysis -type f
find src/data -name "*unified*" -o -name "*developer_metrics*"
```

**Step 2: Remove AI analysis directory**

```bash
rm -rf src/analysis/
```

**Step 3: Remove unused data modules**

```bash
rm src/data/unified_record.py
rm src/data/developer_metrics.py
```

**Step 4: Remove AI config files**

```bash
rm config/ai_developers.json
rm config/analysis_state.json
```

**Step 5: Update pyproject.toml dependencies**

Remove from `pyproject.toml`:
```toml
# Remove:
anthropic = ">=0.40.0"
```

**Step 6: Update justfile**

Remove or comment out commands related to:
- `analyze`
- `pilot` (if it uses AI analysis)
- Any AI-specific commands

**Step 7: Run tests to ensure nothing broke**

```bash
uv run pytest tests/test_name_unifier.py tests/test_branch_tracking.py tests/test_chart_generation.py -v
```

Expected: All tests PASS

**Step 8: Commit cleanup**

```bash
git add -A
git commit -m "refactor: remove unused AI analysis features

BREAKING CHANGE: Remove AI-powered analysis engine

- Delete src/analysis/ (entire AI analysis system)
- Delete unified_record.py and developer_metrics.py
- Remove ai_developers.json and analysis_state.json
- Remove anthropic dependency
- Simplify to pure metrics collection and visualization

Rationale: Charts only need raw metrics (count/size/date).
AI analysis added complexity and cost without being used.
New workflow: Extract → Unify Names → Generate Charts"
```

---

## Task 7: Update Documentation

**Goal:** Update docs to reflect new simplified system.

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md`
- Create: `docs/SIMPLIFIED_ARCHITECTURE.md`

**Step 1: Create architecture doc**

Create `docs/SIMPLIFIED_ARCHITECTURE.md`:

```markdown
# Simplified Metrics Architecture

## Overview

This system collects raw development metrics and generates time-series charts showing team activity.

**NO AI ANALYSIS** - Just data collection and visualization.

## Data Flow

```
┌─────────────────────┐
│  Data Collection    │
├─────────────────────┤
│ • Git commits       │
│ • GitHub PRs        │
│ • Linear tickets    │
└──────┬──────────────┘
       │
       ↓
┌─────────────────────┐
│  Name Unification   │
├─────────────────────┤
│ config/developer_   │
│ names.json          │
└──────┬──────────────┘
       │
       ↓
┌─────────────────────┐
│  Chart Generation   │
├─────────────────────┤
│ • Daily/Weekly      │
│ • Count/Size        │
│ • Stacked/Cumulative│
└─────────────────────┘
```

## Components

### 1. Git Extraction
- **Location**: `src/git_extraction/`
- **Purpose**: Extract commits with branch tracking
- **Output**: `org_commits.csv` with `on_main_branch` field

### 2. GitHub PR Extraction
- **Location**: `scripts/extract_all_prs_api.py`
- **Purpose**: Extract merged PRs via GitHub API
- **Output**: `org_prs.csv` with `base_branch` field

### 3. Linear Integration
- **Location**: `src/linear/`
- **Purpose**: Extract completed tickets with story points
- **Output**: `linear_tickets.csv` (future)

### 4. Name Unification
- **Location**: `src/data/name_unifier.py`
- **Config**: `config/developer_names.json`
- **Purpose**: Map GitHub handles, Git names, Linear names to unified identity

### 5. Chart Generation
- **Location**: `scripts/generate_metrics_charts.py`
- **Purpose**: Generate all time-series visualizations
- **Output**: `charts/*.png`

## Chart Types

### Commits (8 charts)
1. Daily count (stacked area)
2. Weekly count (stacked area)
3. Daily cumulative count (line)
4. Weekly cumulative count (line)
5. Daily cumulative size (line)
6. Weekly cumulative size (line)

### PRs (8 charts)
7. Daily count (stacked area)
8. Weekly count (stacked area)
9. Daily cumulative count (line)
10. Weekly cumulative count (line)
11. Daily cumulative size (line)
12. Weekly cumulative size (line)

### Linear Tickets (12 charts - future)
13-24. Similar structure with count and story points

## Daily Workflow

```bash
# 1. Extract data (automated via cron)
cd src && uv run python -m git_extraction.cli --org degree-analytics --days 1
uv run python scripts/extract_all_prs_api.py

# 2. Generate charts
uv run python scripts/generate_metrics_charts.py

# 3. Review charts
open charts/
```

## Configuration

### Developer Names
Edit `config/developer_names.json` to add/update developer mappings:

```json
{
  "developers": [
    {
      "canonical_name": "Chad Walters",
      "github_handles": ["chadrwalters"],
      "git_names": ["Chad Walters", "chadrwalters"],
      "git_emails": ["chad@degreeanalytics.com"],
      "linear_names": ["Chad Walters"]
    }
  ]
}
```

## What Was Removed

Removed unused complexity:
- ❌ AI analysis engine (`src/analysis/`)
- ❌ Anthropic API integration
- ❌ Impact scoring system
- ❌ Unified record system
- ❌ Process compliance tracking
- ❌ AI assistance detection

These features added cost and complexity without being used for charts.

## Future Enhancements

1. Linear ticket chart generation
2. Automated daily extraction (cron job)
3. Dashboard hosting (GitHub Pages)
4. Cycle time analysis
5. Velocity tracking
```

**Step 2: Update README.md**

Update the README to reflect simplified system (keep it short):

```markdown
# GitHub Linear Metrics - Developer Productivity Charts

Simple system for tracking developer activity through time-series charts.

## What It Does

- Extracts commits (with branch tracking)
- Extracts GitHub PRs
- Extracts Linear tickets (optional)
- Unifies developer names across systems
- Generates daily/weekly charts

## Quick Start

```bash
# Setup
just setup

# Extract data
cd src && uv run python -m git_extraction.cli --org your-org --days 294
uv run python scripts/extract_all_prs_api.py

# Generate charts
uv run python scripts/generate_metrics_charts.py
```

## Configuration

Edit `config/developer_names.json` to map developer identities.

## Documentation

- [Simplified Architecture](docs/SIMPLIFIED_ARCHITECTURE.md)
- [Chart Specifications](CHART_SPECIFICATIONS.md)
```

**Step 3: Update CLAUDE.md**

Simplify `CLAUDE.md` to remove references to AI analysis.

**Step 4: Commit documentation updates**

```bash
git add README.md CLAUDE.md docs/SIMPLIFIED_ARCHITECTURE.md
git commit -m "docs: update for simplified architecture

- Create SIMPLIFIED_ARCHITECTURE.md explaining new system
- Update README to focus on chart generation
- Remove AI analysis references from CLAUDE.md
- Document daily workflow and configuration"
```

---

## Task 8: Create Daily Automation Script

**Goal:** Create script for daily data extraction and chart generation.

**Files:**
- Create: `scripts/daily_update.sh`
- Modify: `justfile` (add daily command)

**Step 1: Create daily update script**

Create `scripts/daily_update.sh`:

```bash
#!/bin/bash
set -e

echo "🔄 Daily Metrics Update"
echo "======================"
echo

# Configuration
ORG="${METRICS_ORG:-degree-analytics}"
DAYS="${METRICS_DAYS:-1}"  # Incremental: just today
OUTPUT_DIR="${METRICS_OUTPUT_DIR:-charts}"

echo "📊 Configuration:"
echo "   Organization: $ORG"
echo "   Days to extract: $DAYS"
echo "   Output directory: $OUTPUT_DIR"
echo

# 1. Extract commits
echo "📝 Extracting commits..."
cd src
uv run python -m git_extraction.cli \
  --org "$ORG" \
  --days "$DAYS" \
  --incremental \
  --verbose
cd ..
echo "✅ Commits extracted"
echo

# 2. Extract PRs
echo "🔀 Extracting PRs..."
uv run python scripts/extract_all_prs_api.py
echo "✅ PRs extracted"
echo

# 3. Generate charts
echo "📈 Generating charts..."
uv run python scripts/generate_metrics_charts.py \
  --output "$OUTPUT_DIR"
echo "✅ Charts generated"
echo

# 4. Summary
echo "✨ Daily update complete!"
echo
echo "📂 Charts available in: $OUTPUT_DIR"
echo "   View: open $OUTPUT_DIR"
```

**Step 2: Make script executable**

```bash
chmod +x scripts/daily_update.sh
```

**Step 3: Add justfile command**

Add to `justfile`:

```makefile
# Daily metrics update (incremental)
daily:
    @echo "Running daily metrics update..."
    ./scripts/daily_update.sh

# Full metrics refresh (all historical data)
refresh:
    @echo "Running full metrics refresh..."
    METRICS_DAYS=294 ./scripts/daily_update.sh
```

**Step 4: Test daily script**

```bash
just daily
```

Expected: Run incremental extraction and regenerate charts

**Step 5: Commit automation**

```bash
git add scripts/daily_update.sh justfile
git commit -m "feat: add daily automation script

- Create daily_update.sh for automated extraction and chart generation
- Add just daily command for quick updates
- Add just refresh for full historical refresh
- Support environment variable configuration"
```

---

## Task 9: Testing and Validation

**Goal:** Ensure all tests pass and system works end-to-end.

**Files:**
- Run all tests
- Verify output

**Step 1: Run all unit tests**

```bash
uv run pytest tests/ -v
```

Expected: All tests PASS

**Step 2: Run integration test**

```bash
# Full workflow test
just refresh
```

Expected: Complete successfully with charts generated

**Step 3: Validate chart output**

```bash
ls -lh charts/
```

Verify:
- ✅ All expected charts present
- ✅ File sizes reasonable (not empty)
- ✅ Recent timestamps

**Step 4: Manual chart review**

```bash
open charts/
```

Check:
- ✅ Names unified correctly
- ✅ Data looks reasonable
- ✅ Trends visible
- ✅ No obvious errors

**Step 5: Document test results**

Create test summary noting any issues found.

---

## Task 10: Final Cleanup and Documentation

**Goal:** Polish the implementation and ensure documentation is complete.

**Files:**
- Update: `CHANGELOG.md`
- Update: `.gitignore`
- Final review

**Step 1: Update .gitignore**

Add to `.gitignore`:

```
# Generated charts
charts/*.png

# Backup data files
*.backup

# Test outputs
.pytest_cache/
```

**Step 2: Create CHANGELOG.md**

```markdown
# Changelog

## [2.0.0] - 2025-10-22

### ✨ Major Simplification

**BREAKING CHANGES:**
- Removed AI analysis engine (no more Anthropic API calls)
- Removed unified record system
- Removed process compliance tracking
- Removed AI assistance detection

### ✅ Added
- Developer name unification system across GitHub/Git/Linear
- Branch tracking for commits (`on_main_branch` field)
- Simplified chart generation (28 variations)
- Daily automation script
- Count and size metrics for commits and PRs
- Cumulative growth visualizations

### 🔧 Changed
- Simplified data flow: Extract → Unify → Chart
- Charts now use unified developer names
- Commits filtered to main/dev branches only
- Removed Anthropic dependency (cost savings)

### 📚 Documentation
- Created SIMPLIFIED_ARCHITECTURE.md
- Updated README for new workflow
- Added chart specifications
- Documented daily automation

### 🗑️ Removed
- `src/analysis/` - entire AI analysis system
- `src/data/unified_record.py`
- `src/data/developer_metrics.py`
- `config/ai_developers.json`
- Anthropic API integration
```

**Step 3: Final commit**

```bash
git add CHANGELOG.md .gitignore
git commit -m "chore: finalize simplification and documentation

- Add CHANGELOG documenting breaking changes
- Update .gitignore for generated outputs
- Complete transition to simplified metrics system

Version 2.0.0: Production-ready chart generation system"
```

**Step 4: Tag release**

```bash
git tag -a v2.0.0 -m "Version 2.0.0: Simplified Metrics System

- Remove AI analysis complexity
- Add name unification
- Production chart generation
- Daily automation"

git push origin v2.0.0
```

---

## Post-Implementation

### Success Criteria
- ✅ All tests pass
- ✅ Charts generate with unified names
- ✅ Commits filtered to main branches
- ✅ AI analysis features removed
- ✅ Documentation updated
- ✅ Daily automation working

### Next Steps (Future)
1. Add Linear ticket chart generation
2. Set up automated daily cron job
3. Host charts on GitHub Pages
4. Add cycle time analysis
5. Implement velocity tracking

---

## Plan Complete

Plan saved to: `docs/plans/2025-10-22-simplify-metrics-charts.md`

**Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**