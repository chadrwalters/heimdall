# Metrics Visualization Enhancements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Standardize developer name display across all charts, implement consistent developer color schemes, fix weekly chart x-axis formatting, and integrate Linear cycle data for comprehensive sprint metrics.

**Architecture:** Enhance existing visualization system with unified developer identity management, color persistence across all chart types, weekly aggregation improvements, and new Linear cycle extraction/visualization modules.

**Tech Stack:** Python, Pandas, Matplotlib, Linear GraphQL API, existing NameUnifier system

---

## Task 1: Update Developer Names Configuration

**Files:**
- Modify: `config/developer_names.json`

**Step 1: Identify all developers from current data**

Run: `cd /Users/chadwalters/source/work/github_linear_metrics && cat src/org_commits.csv | cut -d',' -f2 | tail -n +2 | sort | uniq`

Expected: List of all git names (chadrwalters, ejhg, jeremiahdegreeanalytics, jparkypark, mattkindy)

**Step 2: Update configuration with all developers**

Add all developers with their canonical names:

```json
{
  "developers": [
    {
      "canonical_name": "Chad Walters",
      "git_names": ["chadrwalters", "Chad Walters"],
      "github_handles": ["chadrwalters"],
      "linear_names": ["Chad Walters"]
    },
    {
      "canonical_name": "EJ",
      "git_names": ["ejhg"],
      "github_handles": ["ejhg"],
      "linear_names": ["EJ", "ejhg"]
    },
    {
      "canonical_name": "Jeremiah",
      "git_names": ["jeremiahdegreeanalytics"],
      "github_handles": ["jeremiahdegreeanalytics"],
      "linear_names": ["Jeremiah"]
    },
    {
      "canonical_name": "JP",
      "git_names": ["jparkypark"],
      "github_handles": ["jparkypark"],
      "linear_names": ["JP", "jparkypark"]
    },
    {
      "canonical_name": "Matt Kindy",
      "git_names": ["mattkindy"],
      "github_handles": ["mattkindy"],
      "linear_names": ["Matt Kindy", "mattkindy"]
    }
  ]
}
```

**Step 3: Verify configuration loads correctly**

Run: `cd /Users/chadwalters/source/work/github_linear_metrics && uv run python -c "from src.data.name_unifier import NameUnifier; u = NameUnifier(); print(u.unify(git_name='chadrwalters'))"`

Expected: `Chad Walters`

**Step 4: Commit changes**

```bash
git add config/developer_names.json
git commit -m "feat: add complete developer name mappings for all team members"
```

---

## Task 2: Add Developer Color Mapping System

**Files:**
- Create: `src/data/developer_colors.py`
- Create: `tests/unit/test_developer_colors.py`

**Step 1: Write failing test**

Create `tests/unit/test_developer_colors.py`:

```python
"""Tests for developer color mapping system."""
import pytest
from src.data.developer_colors import DeveloperColorMapper


def test_color_mapper_initialization():
    """Test color mapper initializes with config."""
    mapper = DeveloperColorMapper("config/developer_names.json")
    assert mapper is not None


def test_get_color_for_developer():
    """Test getting consistent color for developer."""
    mapper = DeveloperColorMapper("config/developer_names.json")

    color1 = mapper.get_color("Chad Walters")
    color2 = mapper.get_color("Chad Walters")

    assert color1 == color2
    assert isinstance(color1, str)
    assert color1.startswith("#")


def test_get_color_map():
    """Test getting full color map."""
    mapper = DeveloperColorMapper("config/developer_names.json")

    color_map = mapper.get_color_map(["Chad Walters", "EJ", "JP"])

    assert len(color_map) == 3
    assert "Chad Walters" in color_map
    assert "EJ" in color_map
    assert "JP" in color_map
    assert all(c.startswith("#") for c in color_map.values())


def test_colors_are_consistent_across_instances():
    """Test colors remain consistent across instances."""
    mapper1 = DeveloperColorMapper("config/developer_names.json")
    mapper2 = DeveloperColorMapper("config/developer_names.json")

    color1 = mapper1.get_color("Chad Walters")
    color2 = mapper2.get_color("Chad Walters")

    assert color1 == color2
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/chadwalters/source/work/github_linear_metrics && uv run pytest tests/unit/test_developer_colors.py -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'src.data.developer_colors'"

**Step 3: Write minimal implementation**

Create `src/data/developer_colors.py`:

```python
"""Developer color mapping system for consistent visualization."""
import json
import hashlib
from pathlib import Path
from typing import Dict


class DeveloperColorMapper:
    """Map developers to consistent colors across all visualizations."""

    # Distinct, visually appealing color palette
    COLOR_PALETTE = [
        "#1f77b4",  # Blue
        "#ff7f0e",  # Orange
        "#2ca02c",  # Green
        "#d62728",  # Red
        "#9467bd",  # Purple
        "#8c564b",  # Brown
        "#e377c2",  # Pink
        "#7f7f7f",  # Gray
        "#bcbd22",  # Olive
        "#17becf",  # Cyan
    ]

    def __init__(self, config_path: str = "config/developer_names.json"):
        """Initialize color mapper with developer configuration.

        Args:
            config_path: Path to developer names configuration JSON
        """
        self.config_path = Path(config_path)
        self._load_config()
        self._build_color_map()

    def _load_config(self) -> None:
        """Load configuration from JSON file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path) as f:
            self.config = json.load(f)

        if "developers" not in self.config:
            raise ValueError("Config must contain 'developers' key")

    def _build_color_map(self) -> None:
        """Build color map using deterministic hash-based assignment."""
        self.color_map: Dict[str, str] = {}

        # Sort developers by canonical name for deterministic ordering
        developers = sorted(
            self.config["developers"],
            key=lambda d: d["canonical_name"]
        )

        for idx, dev in enumerate(developers):
            canonical = dev["canonical_name"]
            # Use hash for deterministic but distributed color assignment
            hash_value = int(hashlib.md5(canonical.encode()).hexdigest(), 16)
            color_idx = hash_value % len(self.COLOR_PALETTE)
            self.color_map[canonical] = self.COLOR_PALETTE[color_idx]

    def get_color(self, developer_name: str) -> str:
        """Get color for a developer.

        Args:
            developer_name: Canonical developer name

        Returns:
            Hex color string (e.g., "#1f77b4")
        """
        return self.color_map.get(developer_name, "#999999")  # Gray fallback

    def get_color_map(self, developer_names: list[str]) -> Dict[str, str]:
        """Get color map for multiple developers.

        Args:
            developer_names: List of canonical developer names

        Returns:
            Dictionary mapping developer names to colors
        """
        return {name: self.get_color(name) for name in developer_names}
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/chadwalters/source/work/github_linear_metrics && uv run pytest tests/unit/test_developer_colors.py -v`

Expected: PASS (4 tests passed)

**Step 5: Commit**

```bash
git add src/data/developer_colors.py tests/unit/test_developer_colors.py
git commit -m "feat: add developer color mapping system for consistent chart colors"
```

---

## Task 3: Update Chart Generation to Use Color Mapping

**Files:**
- Modify: `scripts/generate_metrics_charts.py:27-51` (initialization)
- Modify: `scripts/generate_metrics_charts.py:179-235` (_create_line_chart)
- Modify: `scripts/generate_metrics_charts.py:236-294` (_create_cumulative_line_chart)

**Step 1: Import color mapper in chart generation**

Add after line 24 in `scripts/generate_metrics_charts.py`:

```python
from data.name_unifier import NameUnifier
from data.developer_colors import DeveloperColorMapper
```

**Step 2: Initialize color mapper in __init__**

Update `__init__` method (around line 30-51):

```python
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

    # Initialize name unifier and color mapper
    self.unifier = NameUnifier(name_config)
    self.color_mapper = DeveloperColorMapper(name_config)

    # Rest of initialization...
```

**Step 3: Update _create_line_chart to use colors**

Update method around line 179-235:

```python
def _create_line_chart(
    self,
    df: pd.DataFrame,
    author_col: str,
    title: str,
    ylabel: str,
    filename: str
):
    """Create line chart showing per-period counts.

    Args:
        df: Aggregated data with period, author, value
        author_col: Name of author column
        title: Chart title
        ylabel: Y-axis label
        filename: Output filename
    """
    # Pivot for line chart
    pivot = df.pivot(index="date", columns=author_col, values="value").fillna(0)

    # Get color map for developers in this dataset
    developers = pivot.columns.tolist()
    color_map = self.color_mapper.get_color_map(developers)

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 7))

    # Plot each developer with their assigned color
    for developer in developers:
        ax.plot(
            pivot.index,
            pivot[developer],
            label=developer,
            color=color_map[developer],
            alpha=0.8,
            linewidth=2,
            marker='o',
            markersize=4
        )

    ax.set_title(title, fontsize=16, fontweight="bold", pad=20)
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.legend(title="Developer", bbox_to_anchor=(1.05, 1), loc="upper left")
    ax.grid(True, alpha=0.3)

    # Dynamic date formatting based on number of data points
    num_points = len(pivot.index)

    if num_points <= 7:
        # Daily data for a week or less
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    elif num_points <= 10:
        # Could be weekly data (4-5 weeks) or daily data for ~10 days
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    elif num_points <= 31:
        # Daily data for a month
        interval = max(1, num_points // 10)
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=interval))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    else:
        # Longer periods
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))

    fig.autofmt_xdate()

    plt.tight_layout()
    output_path = self.output_dir / filename
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {output_path}")
    plt.close()
```

**Step 4: Update _create_cumulative_line_chart similarly**

Update method around line 236-294 with same color mapping approach:

```python
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

    # Get color map for developers in this dataset
    developers = cumulative.columns.tolist()
    color_map = self.color_mapper.get_color_map(developers)

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 7))

    for developer in developers:
        ax.plot(
            cumulative.index,
            cumulative[developer],
            label=developer,
            color=color_map[developer],
            linewidth=2,
            marker='o',
            markersize=3
        )

    ax.set_title(title, fontsize=16, fontweight="bold", pad=20)
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.legend(title="Developer", bbox_to_anchor=(1.05, 1), loc="upper left")
    ax.grid(True, alpha=0.3)

    # Dynamic date formatting based on number of data points
    num_points = len(cumulative.index)

    if num_points <= 7:
        # Daily data for a week or less
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    elif num_points <= 10:
        # Could be weekly data (4-5 weeks) or daily data for ~10 days
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    elif num_points <= 31:
        # Daily data for a month
        interval = max(1, num_points // 10)
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=interval))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    else:
        # Longer periods
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))

    fig.autofmt_xdate()

    plt.tight_layout()
    output_path = self.output_dir / filename
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {output_path}")
    plt.close()
```

**Step 5: Test chart generation with colors**

Run: `cd /Users/chadwalters/source/work/github_linear_metrics && uv run python scripts/generate_metrics_charts.py --commits src/org_commits.csv --prs src/org_prs.csv`

Expected: Charts generated successfully with consistent colors for each developer

**Step 6: Verify colors are consistent across charts**

Check that Chad Walters has the same color in commits_d_count_per_period.png and prs_d_count_per_period.png

**Step 7: Commit**

```bash
git add scripts/generate_metrics_charts.py
git commit -m "feat: apply consistent developer colors across all chart types"
```

---

## Task 4: Fix Weekly Chart X-Axis to Show Week Ranges

**Files:**
- Modify: `scripts/generate_metrics_charts.py:179-235` (_create_line_chart)
- Modify: `scripts/generate_metrics_charts.py:236-294` (_create_cumulative_line_chart)

**Step 1: Add helper method for week formatting**

Add after line 108 in `scripts/generate_metrics_charts.py`:

```python
def _format_week_axis(self, ax, dates, num_points):
    """Format x-axis to show week ranges for weekly data.

    Args:
        ax: Matplotlib axis object
        dates: DatetimeIndex of dates
        num_points: Number of data points
    """
    if num_points <= 10:
        # Weekly data - show week ranges
        labels = []
        for date in dates:
            # Calculate week start (Monday) and end (Sunday)
            week_start = date - pd.Timedelta(days=date.weekday())
            week_end = week_start + pd.Timedelta(days=6)
            labels.append(f"{week_start.strftime('%b %d')}-{week_end.strftime('%d')}")

        ax.set_xticks(range(len(dates)))
        ax.set_xticklabels(labels, rotation=45, ha='right')
    else:
        # Daily data - use existing date formatting
        if num_points <= 7:
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        elif num_points <= 31:
            interval = max(1, num_points // 10)
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=interval))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        else:
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
```

**Step 2: Update _create_line_chart to detect frequency**

Replace date formatting section (around line 209-228) with:

```python
# Determine if this is weekly or daily data
freq = df['period'].iloc[0].freq if len(df) > 0 else None
is_weekly = freq == 'W' if freq else num_points <= 10

if is_weekly:
    self._format_week_axis(ax, pivot.index, num_points)
else:
    # Dynamic date formatting for daily data
    if num_points <= 7:
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    elif num_points <= 31:
        interval = max(1, num_points // 10)
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=interval))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    else:
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))

fig.autofmt_xdate()
```

**Step 3: Update _create_cumulative_line_chart similarly**

Replace date formatting section (around line 269-286) with same logic as Step 2

**Step 4: Test weekly chart formatting**

Run: `cd /Users/chadwalters/source/work/github_linear_metrics && uv run python scripts/generate_metrics_charts.py --commits src/org_commits.csv --prs src/org_prs.csv`

Expected: Weekly charts show "Dec 18-24", "Dec 25-31" format

**Step 5: Verify weekly chart x-axis**

Check `charts/commits_w_count_per_period.png` for proper week range formatting

**Step 6: Commit**

```bash
git add scripts/generate_metrics_charts.py
git commit -m "feat: show week ranges on x-axis for weekly aggregated charts"
```

---

## Task 5: Add Linear Cycle Data Extraction

**Files:**
- Modify: `src/linear/linear_client.py:283-341` (add cycle methods)
- Create: `scripts/extract_linear_cycles.py`
- Create: `tests/unit/test_linear_cycles.py`

**Step 1: Write failing test for cycle extraction**

Create `tests/unit/test_linear_cycles.py`:

```python
"""Tests for Linear cycle extraction."""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from src.linear.linear_client import LinearClient


def test_get_cycles():
    """Test retrieving cycles from Linear."""
    with patch('src.linear.linear_client.requests.Session') as mock_session:
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "cycles": {
                    "nodes": [
                        {
                            "id": "cycle1",
                            "number": 42,
                            "name": "Sprint 42",
                            "startsAt": "2024-12-18T00:00:00.000Z",
                            "endsAt": "2024-12-31T23:59:59.999Z",
                            "completedAt": "2024-12-31T20:00:00.000Z",
                            "team": {
                                "id": "team1",
                                "key": "ENG",
                                "name": "Engineering"
                            }
                        }
                    ]
                }
            }
        }
        mock_session.return_value.post.return_value = mock_response

        client = LinearClient(api_key="test_key")
        cycles = client.get_cycles(team_key="ENG")

        assert len(cycles) == 1
        assert cycles[0]["number"] == 42
        assert cycles[0]["name"] == "Sprint 42"


def test_get_cycle_issues():
    """Test retrieving issues for a cycle."""
    with patch('src.linear.linear_client.requests.Session') as mock_session:
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "cycle": {
                    "issues": {
                        "nodes": [
                            {
                                "id": "issue1",
                                "identifier": "ENG-123",
                                "title": "Implement feature",
                                "estimate": 3,
                                "assignee": {
                                    "name": "Chad Walters"
                                },
                                "state": {
                                    "type": "completed"
                                },
                                "completedAt": "2024-12-25T10:00:00.000Z"
                            }
                        ]
                    }
                }
            }
        }
        mock_session.return_value.post.return_value = mock_response

        client = LinearClient(api_key="test_key")
        issues = client.get_cycle_issues("cycle1")

        assert len(issues) == 1
        assert issues[0]["identifier"] == "ENG-123"
        assert issues[0]["estimate"] == 3
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/chadwalters/source/work/github_linear_metrics && uv run pytest tests/unit/test_linear_cycles.py -v`

Expected: FAIL with "AttributeError: 'LinearClient' object has no attribute 'get_cycles'"

**Step 3: Add cycle methods to LinearClient**

Add after line 341 in `src/linear/linear_client.py`:

```python
def get_cycles(
    self,
    team_key: str | None = None,
    active_only: bool = False
) -> list[dict[str, Any]]:
    """Get cycles (sprints), optionally filtered by team.

    Args:
        team_key: Optional team key to filter cycles
        active_only: If True, only return active/upcoming cycles

    Returns:
        List of cycle dictionaries
    """
    filter_str = ""
    filters = []

    if team_key:
        filters.append(f'team: {{ key: {{ eq: "{team_key}" }} }}')

    if active_only:
        filters.append('isActive: { eq: true }')

    if filters:
        filter_str = f'filter: {{ {", ".join(filters)} }}'

    query = f"""
    query {{
        cycles({filter_str}, first: 100) {{
            nodes {{
                id
                number
                name
                startsAt
                endsAt
                completedAt
                team {{
                    id
                    key
                    name
                }}
                completedIssueCount
                issueCount
                progress
            }}
        }}
    }}
    """

    result = self._execute_query(query)
    cycles_data = result.get("cycles", {})
    return cycles_data.get("nodes", [])


def get_cycle_issues(self, cycle_id: str) -> list[dict[str, Any]]:
    """Get all issues for a specific cycle.

    Args:
        cycle_id: Linear cycle ID

    Returns:
        List of issue dictionaries
    """
    query = """
    query GetCycleIssues($cycleId: String!) {
        cycle(id: $cycleId) {
            issues {
                nodes {
                    id
                    identifier
                    title
                    description
                    state {
                        id
                        name
                        type
                    }
                    assignee {
                        id
                        name
                        email
                    }
                    createdAt
                    updatedAt
                    completedAt
                    priority
                    priorityLabel
                    estimate
                    team {
                        id
                        key
                        name
                    }
                    url
                }
            }
        }
    }
    """

    result = self._execute_query(query, {"cycleId": cycle_id})
    cycle_data = result.get("cycle", {})
    issues_data = cycle_data.get("issues", {})
    return issues_data.get("nodes", [])
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/chadwalters/source/work/github_linear_metrics && uv run pytest tests/unit/test_linear_cycles.py -v`

Expected: PASS (2 tests passed)

**Step 5: Create cycle extraction script**

Create `scripts/extract_linear_cycles.py`:

```python
#!/usr/bin/env python3
"""Extract Linear cycle data for metrics analysis."""
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from linear.linear_client import LinearClient
from data.name_unifier import NameUnifier


def extract_cycle_data(
    team_key: str = "ENG",
    output_file: str = "linear_cycles.csv",
    name_config: str = "config/developer_names.json"
):
    """Extract cycle data from Linear.

    Args:
        team_key: Linear team key to filter cycles
        output_file: Output CSV filename
        name_config: Path to developer names config
    """
    print(f"Extracting Linear cycles for team: {team_key}")

    # Initialize clients
    client = LinearClient()
    unifier = NameUnifier(name_config)

    # Get all cycles for team
    print("Fetching cycles...")
    cycles = client.get_cycles(team_key=team_key)
    print(f"  Found {len(cycles)} cycles")

    # Extract issues for each cycle
    all_data = []

    for cycle in cycles:
        cycle_id = cycle["id"]
        cycle_num = cycle["number"]
        cycle_name = cycle["name"]
        cycle_start = cycle["startsAt"]
        cycle_end = cycle["endsAt"]

        print(f"\nProcessing Cycle {cycle_num}: {cycle_name}")
        print(f"  Period: {cycle_start} to {cycle_end}")

        # Get issues for this cycle
        issues = client.get_cycle_issues(cycle_id)
        print(f"  Found {len(issues)} issues")

        for issue in issues:
            assignee_name = issue.get("assignee", {}).get("name")
            if assignee_name:
                assignee_name = unifier.unify(linear_name=assignee_name)

            data = {
                "cycle_id": cycle_id,
                "cycle_number": cycle_num,
                "cycle_name": cycle_name,
                "cycle_start": cycle_start,
                "cycle_end": cycle_end,
                "issue_id": issue["id"],
                "issue_identifier": issue["identifier"],
                "issue_title": issue["title"],
                "assignee_name": assignee_name,
                "estimate": issue.get("estimate"),
                "priority": issue.get("priority"),
                "state_type": issue.get("state", {}).get("type"),
                "state_name": issue.get("state", {}).get("name"),
                "created_at": issue.get("createdAt"),
                "completed_at": issue.get("completedAt"),
            }
            all_data.append(data)

    # Create DataFrame and save
    df = pd.DataFrame(all_data)
    df.to_csv(output_file, index=False)

    print(f"\n✅ Saved {len(all_data)} cycle issues to: {output_file}")

    # Print summary
    print("\nSummary by Cycle:")
    summary = df.groupby(["cycle_number", "cycle_name"]).agg({
        "issue_identifier": "count",
        "estimate": "sum"
    }).rename(columns={
        "issue_identifier": "issue_count",
        "estimate": "total_estimate"
    })
    print(summary)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract Linear cycle data")
    parser.add_argument(
        "--team",
        default="ENG",
        help="Linear team key (default: ENG)"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="linear_cycles.csv",
        help="Output CSV file"
    )
    parser.add_argument(
        "--name-config",
        default="config/developer_names.json",
        help="Developer names configuration"
    )

    args = parser.parse_args()
    extract_cycle_data(args.team, args.output, args.name_config)
```

**Step 6: Test cycle extraction script**

Run: `cd /Users/chadwalters/source/work/github_linear_metrics && chmod +x scripts/extract_linear_cycles.py && uv run python scripts/extract_linear_cycles.py --team ENG --output src/linear_cycles.csv`

Expected: CSV file created with cycle data

**Step 7: Commit**

```bash
git add src/linear/linear_client.py scripts/extract_linear_cycles.py tests/unit/test_linear_cycles.py
git commit -m "feat: add Linear cycle extraction with issue details"
```

---

## Task 6: Add Linear Cycle Chart Generation

**Files:**
- Modify: `scripts/generate_metrics_charts.py:30-80` (add linear loading)
- Modify: `scripts/generate_metrics_charts.py:403-417` (add cycle chart generation)

**Step 1: Update initialization to load Linear cycle data**

Update around line 30-80 in `scripts/generate_metrics_charts.py`:

```python
# Load Linear cycle data
if linear_file and Path(linear_file).exists():
    print(f"Loading Linear cycles from {linear_file}...")
    self.linear_df = pd.read_csv(linear_file)

    # Parse dates
    self.linear_df["cycle_start"] = pd.to_datetime(
        self.linear_df["cycle_start"], utc=True
    )
    self.linear_df["cycle_end"] = pd.to_datetime(
        self.linear_df["cycle_end"], utc=True
    )
    self.linear_df["created_at"] = pd.to_datetime(
        self.linear_df["created_at"], utc=True
    )
    self.linear_df["completed_at"] = pd.to_datetime(
        self.linear_df["completed_at"], utc=True
    )

    # Unify assignee names
    self.linear_df = self._unify_names(self.linear_df, "assignee_name")
    print(f"  Loaded {len(self.linear_df)} cycle issues")
else:
    print("No Linear cycle data available")
    self.linear_df = None
```

**Step 2: Add cycle chart generation methods**

Add after line 401 in `scripts/generate_metrics_charts.py`:

```python
def generate_linear_cycle_charts(self):
    """Generate Linear cycle charts."""
    if self.linear_df is None or len(self.linear_df) == 0:
        print("\n⚠️  No Linear cycle data available")
        return

    print("\n📊 Generating Linear cycle charts...")

    # Group by cycle and assignee
    cycle_summary = (
        self.linear_df.groupby(["cycle_number", "cycle_name", "assignee_name"])
        .agg({
            "issue_identifier": "count",
            "estimate": lambda x: x.fillna(0).sum()
        })
        .rename(columns={
            "issue_identifier": "issue_count",
            "estimate": "total_estimate"
        })
        .reset_index()
    )

    # CHART 1: Issues started per cycle (count)
    self._create_cycle_bar_chart(
        cycle_summary,
        "assignee_name",
        "issue_count",
        "Issues Started Per Cycle by Developer",
        "Issue Count",
        "linear_cycle_issues_started.png"
    )

    # CHART 2: Story points per cycle
    self._create_cycle_bar_chart(
        cycle_summary,
        "assignee_name",
        "total_estimate",
        "Story Points Per Cycle by Developer",
        "Story Points",
        "linear_cycle_points.png"
    )

    # CHART 3: Issues completed per cycle
    completed = self.linear_df[
        self.linear_df["state_type"] == "completed"
    ].copy()

    if len(completed) > 0:
        completed_summary = (
            completed.groupby(["cycle_number", "cycle_name", "assignee_name"])
            .agg({
                "issue_identifier": "count",
                "estimate": lambda x: x.fillna(0).sum()
            })
            .rename(columns={
                "issue_identifier": "issue_count",
                "estimate": "total_estimate"
            })
            .reset_index()
        )

        self._create_cycle_bar_chart(
            completed_summary,
            "assignee_name",
            "issue_count",
            "Issues Completed Per Cycle by Developer",
            "Issue Count",
            "linear_cycle_issues_completed.png"
        )

        self._create_cycle_bar_chart(
            completed_summary,
            "assignee_name",
            "total_estimate",
            "Story Points Completed Per Cycle by Developer",
            "Story Points",
            "linear_cycle_points_completed.png"
        )


def _create_cycle_bar_chart(
    self,
    df: pd.DataFrame,
    assignee_col: str,
    value_col: str,
    title: str,
    ylabel: str,
    filename: str
):
    """Create grouped bar chart for cycle metrics.

    Args:
        df: Data with cycle_number, cycle_name, assignee, and value columns
        assignee_col: Name of assignee column
        value_col: Name of value column to plot
        title: Chart title
        ylabel: Y-axis label
        filename: Output filename
    """
    # Pivot data for grouped bar chart
    pivot = df.pivot(
        index=["cycle_number", "cycle_name"],
        columns=assignee_col,
        values=value_col
    ).fillna(0)

    # Get color map for developers
    developers = pivot.columns.tolist()
    color_map = self.color_mapper.get_color_map(developers)
    colors = [color_map[dev] for dev in developers]

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 7))

    # Create grouped bar chart
    pivot.plot(
        kind="bar",
        ax=ax,
        color=colors,
        alpha=0.8,
        width=0.8
    )

    ax.set_title(title, fontsize=16, fontweight="bold", pad=20)
    ax.set_xlabel("Cycle", fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)

    # Format x-axis labels to show cycle names
    labels = [f"C{num}\n{name}" for num, name in pivot.index]
    ax.set_xticklabels(labels, rotation=45, ha="right")

    ax.legend(title="Developer", bbox_to_anchor=(1.05, 1), loc="upper left")
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    output_path = self.output_dir / filename
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {output_path}")
    plt.close()
```

**Step 3: Update generate_all_charts method**

Update around line 403-417:

```python
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

    # Linear cycle charts
    self.generate_linear_cycle_charts()

    print("\n✅ All charts generated successfully!")
    print(f"\n📂 Charts saved to: {self.output_dir.absolute()}")
```

**Step 4: Test Linear chart generation**

Run: `cd /Users/chadwalters/source/work/github_linear_metrics && uv run python scripts/generate_metrics_charts.py --commits src/org_commits.csv --prs src/org_prs.csv --linear src/linear_cycles.csv`

Expected: 4 additional Linear cycle charts generated

**Step 5: Verify Linear charts**

Check that `linear_cycle_issues_started.png`, `linear_cycle_points.png`, `linear_cycle_issues_completed.png`, and `linear_cycle_points_completed.png` exist

**Step 6: Commit**

```bash
git add scripts/generate_metrics_charts.py
git commit -m "feat: add Linear cycle chart generation with grouped bar charts"
```

---

## Task 7: Create Justfile Commands for New Workflows

**Files:**
- Modify: `justfile` (add new commands)

**Step 1: Add Linear extraction command**

Add to justfile:

```makefile
# Extract Linear cycle data
extract-linear TEAM="ENG":
    @echo "Extracting Linear cycles for team: {{TEAM}}"
    uv run python scripts/extract_linear_cycles.py --team {{TEAM}} --output src/linear_cycles.csv
```

**Step 2: Add comprehensive chart generation command**

Add to justfile:

```makefile
# Generate all charts (commits, PRs, and Linear cycles)
generate-charts-all:
    @echo "Generating all metrics charts..."
    uv run python scripts/generate_metrics_charts.py \
        --commits src/org_commits.csv \
        --prs src/org_prs.csv \
        --linear src/linear_cycles.csv \
        --output charts
```

**Step 3: Add complete pipeline command**

Add to justfile:

```makefile
# Complete pipeline: extract commits, PRs, Linear, and generate charts
pipeline-with-linear ORG DAYS TEAM="ENG":
    @echo "Running complete pipeline for {{ORG}} ({{DAYS}} days, team {{TEAM}})..."
    just extract {{ORG}} {{DAYS}}
    just extract-linear {{TEAM}}
    just generate-charts-all
    @echo "✅ Pipeline complete!"
```

**Step 4: Test new commands**

Run: `cd /Users/chadwalters/source/work/github_linear_metrics && just extract-linear ENG`

Expected: Linear cycles extracted successfully

Run: `cd /Users/chadwalters/source/work/github_linear_metrics && just generate-charts-all`

Expected: All charts including Linear generated

**Step 5: Commit**

```bash
git add justfile
git commit -m "feat: add justfile commands for Linear extraction and complete pipeline"
```

---

## Task 8: Update Documentation

**Files:**
- Modify: `CHARTS_README.md`
- Create: `docs/linear-integration.md`

**Step 1: Update CHARTS_README.md with new sections**

Add after existing chart descriptions:

```markdown
## Linear Cycle Charts

### Issues Started Per Cycle
**File**: `linear_cycle_issues_started.png`
**Description**: Grouped bar chart showing how many issues each developer was assigned in each cycle/sprint.

### Story Points Per Cycle
**File**: `linear_cycle_points.png`
**Description**: Grouped bar chart showing total story points assigned to each developer per cycle.

### Issues Completed Per Cycle
**File**: `linear_cycle_issues_completed.png`
**Description**: Grouped bar chart showing how many issues each developer completed in each cycle.

### Story Points Completed Per Cycle
**File**: `linear_cycle_points_completed.png`
**Description**: Grouped bar chart showing total story points completed by each developer per cycle.

## Color Consistency

All charts use consistent color mapping for developers across all visualization types:
- Colors are deterministically assigned based on canonical developer names
- Each developer maintains the same color in commits, PRs, and Linear charts
- Color mapping is defined in `src/data/developer_colors.py`
```

**Step 2: Create Linear integration documentation**

Create `docs/linear-integration.md`:

```markdown
# Linear Integration Guide

## Overview

This system integrates with Linear to extract cycle (sprint) data and generate comprehensive metrics about developer assignments and completions.

## Prerequisites

- Linear API key set in environment (`LINEAR_API_KEY` or `LINEAR_TOKEN`)
- Access to your Linear workspace
- Team key (e.g., "ENG" for Engineering team)

## Extracting Linear Cycle Data

### Using Justfile (Recommended)

```bash
# Extract cycles for specific team
just extract-linear ENG

# Extract and generate all charts
just pipeline-with-linear degree-analytics 30 ENG
```

### Using Script Directly

```bash
uv run python scripts/extract_linear_cycles.py --team ENG --output linear_cycles.csv
```

## Data Extracted

For each cycle, the system extracts:
- **Cycle metadata**: Number, name, start/end dates
- **Issue details**: Identifier, title, description
- **Assignments**: Who was assigned each issue
- **Estimates**: T-shirt size converted to story points
- **State tracking**: Created date, completion date, state type

## Generated Charts

### 1. Issues Started Per Cycle
Shows how many issues each developer was assigned at the start of each cycle.

### 2. Story Points Per Cycle
Shows total story points (estimates) assigned to each developer per cycle.

### 3. Issues Completed Per Cycle
Shows how many issues each developer actually completed within each cycle.

### 4. Story Points Completed Per Cycle
Shows total story points completed by each developer per cycle.

## Understanding the Metrics

### Started vs. Completed
- **Started**: Issues assigned to developer when cycle began
- **Completed**: Issues finished by developer during cycle
- Differences indicate carry-over work or mid-cycle assignments

### Story Points
Linear's estimate field uses T-shirt sizing (1, 2, 3, 5, 8, etc.).
Our system treats these directly as story points for aggregation.

## Developer Name Unification

Linear assignee names are automatically unified with Git/GitHub names using the configuration in `config/developer_names.json`. This ensures:
- Consistent names across all visualizations
- Proper correlation between code changes and Linear assignments
- Accurate attribution of work

## Troubleshooting

### No cycles found
- Verify your team key is correct (`LINEAR_API_KEY` must have access)
- Check that your Linear workspace uses cycles
- Ensure API key has read access to issues and cycles

### Missing assignees
- Some issues may not have assignees (shows as null in charts)
- Unassigned work is excluded from per-developer metrics
- Check Linear to ensure proper issue assignment

### Estimate mismatches
- Linear estimates use Fibonacci-style scale (1, 2, 3, 5, 8, 13, etc.)
- Missing estimates are treated as 0 in story point totals
- Consider setting estimation policy for your team

## Configuration

### Adding New Developers
Update `config/developer_names.json`:

```json
{
  "developers": [
    {
      "canonical_name": "Developer Name",
      "git_names": ["git-username"],
      "github_handles": ["github-handle"],
      "linear_names": ["Linear Display Name"]
    }
  ]
}
```

### Color Customization
Colors are automatically assigned but can be modified in `src/data/developer_colors.py` by updating the `COLOR_PALETTE` constant.
```

**Step 3: Commit documentation**

```bash
git add CHARTS_README.md docs/linear-integration.md
git commit -m "docs: add Linear cycle integration documentation"
```

---

## Execution Instructions

Plan complete and saved to `docs/plans/2025-01-22-metrics-visualization-enhancements.md`.

**Two execution options:**

1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration with quality gates

2. **Parallel Session (separate)** - Open new session with executing-plans skill, batch execution with checkpoints

**Which approach do you prefer?**
