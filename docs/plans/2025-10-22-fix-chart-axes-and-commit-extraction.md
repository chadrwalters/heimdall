# Fix Chart Axes and Commit Extraction Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix chart generation to display proper date axes and fix commit extraction to capture all commits (not just PR merges) to main/dev branches.

**Architecture:** The system has two components that need fixes: (1) git_extraction which currently only extracts PR merge commits instead of all commits to main/dev, and (2) generate_metrics_charts.py which has hard-coded x-axis date formatting causing only one date to show for 30-day spans.

**Tech Stack:** Python 3.12, GitPython, Pandas, Matplotlib, pytest

---

## Issues Identified

1. **Commit Extraction Bug**: `git_extractor.py` only calls `get_pr_commits()` which extracts PR merge commits, not all commits to main/dev branches
2. **X-Axis Date Formatting**: Chart script uses fixed `WeekdayLocator(interval=2)` causing sparse date labels on 30-day charts
3. **Test Coverage**: No tests verify commit extraction gets all commits vs just PR merges

---

### Task 1: Fix Commit Extraction Logic

**Files:**
- Modify: `src/git_extraction/git_extractor.py:172-223`
- Modify: `src/git_extraction/commit_extractor.py:23-100`
- Test: `tests/git_extraction/test_commit_extractor.py`

**Step 1: Write failing test for all commits extraction**

Create `tests/git_extraction/test_commit_extractor.py` (or add to existing):

```python
def test_get_commits_since_includes_all_main_branch_commits(tmp_path):
    """Test that get_commits_since returns ALL commits to main, not just PR merges."""
    # Create test repo with direct commits and PR merges
    repo = git.Repo.init(tmp_path)
    
    # Create main branch with direct commit
    (tmp_path / "file1.txt").write_text("initial")
    repo.index.add(["file1.txt"])
    commit1 = repo.index.commit("Direct commit to main")
    
    # Create feature branch with PR merge
    repo.git.checkout("-b", "feature")
    (tmp_path / "file2.txt").write_text("feature")
    repo.index.add(["file2.txt"])
    feature_commit = repo.index.commit("Feature work")
    
    # Merge back to main (creates merge commit)
    repo.git.checkout("main")
    repo.git.merge("feature", "--no-ff", "-m", "Merge PR #1")
    
    # Add another direct commit after merge
    (tmp_path / "file3.txt").write_text("post-merge")
    repo.index.add(["file3.txt"])
    commit3 = repo.index.commit("Another direct commit")
    
    # Extract commits
    config = GitExtractionConfig()
    extractor = CommitExtractor(config)
    commits = extractor.get_commits_since(str(tmp_path), since_date="2000-01-01")
    
    # Should get ALL 4 commits: 2 direct + 1 feature + 1 merge
    assert len(commits) == 4
    commit_messages = [c['message'] for c in commits]
    assert "Direct commit to main" in commit_messages
    assert "Another direct commit" in commit_messages
    assert "Feature work" in commit_messages
    assert "Merge PR #1" in commit_messages
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/git_extraction/test_commit_extractor.py::test_get_commits_since_includes_all_main_branch_commits -v`

Expected: Test setup may fail initially (repo creation). Fix test setup first, then expect assertion to fail showing current implementation only gets PR merges.

**Step 3: Fix git_extractor.py to use get_commits_since**

In `src/git_extraction/git_extractor.py`, modify `extract_commits_data()` method (around line 172):

```python
def extract_commits_data(self, org: str, repos: List[str], days_back: int = 7) -> pd.DataFrame:
    """Extract commit data using local git repositories.
    
    Args:
        org: Organization name
        repos: List of repository names
        days_back: Number of days to go back
        
    Returns:
        DataFrame with commit data
    """
    logger.info(f"Extracting commit data for {len(repos)} repositories ({days_back} days)")
    
    since_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).isoformat()
    all_commits = []
    
    for repo in repos:
        try:
            # Clone or update repository
            repo_path = self.repo_service.clone_or_update_repo(org, repo, self.github_token)
            
            # CHANGED: Use get_commits_since to get ALL commits, not just PR merges
            commits = self.repo_service.get_commits_since(
                repo_path,
                since_commit=None,  # Start from date, not last analyzed commit
                since_date=since_date
            )
            
            # Filter to main/dev branches only
            main_branch_commits = [
                c for c in commits 
                if c.get('on_main_branch', False)
            ]
            
            # Add repository name to each commit
            for commit in main_branch_commits:
                commit['repository'] = repo
                commit['organization'] = org
            
            all_commits.extend(main_branch_commits)
            
            logger.info(f"Extracted {len(main_branch_commits)} commits from {repo}")
            
        except ValidationError as e:
            logger.error(f"Input validation failed for {repo}: {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error extracting commits from {repo}: {e}")
            continue
    
    # Convert to DataFrame (rest of method unchanged)
    if all_commits:
        df = pd.DataFrame(all_commits)
        # ... existing DataFrame processing ...
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/git_extraction/test_commit_extractor.py::test_get_commits_since_includes_all_main_branch_commits -v`

Expected: PASS - now extracts all commits

**Step 5: Run integration test with real extraction**

Run: `cd src && uv run python -m git_extraction.cli --org degree-analytics --days 7 2>&1 | grep "Commits extracted"`

Expected: Should show > 0 commits extracted (not just PRs)

**Step 6: Commit**

```bash
git add src/git_extraction/git_extractor.py tests/git_extraction/test_commit_extractor.py
git commit -m "fix: extract all commits to main/dev, not just PR merges"
```

---

### Task 2: Fix Chart X-Axis Date Formatting

**Files:**
- Modify: `scripts/generate_metrics_charts.py:209-212`
- Modify: `scripts/generate_metrics_charts.py:254-256`
- Test: Manual verification with generated charts

**Step 1: Write test for date axis formatting**

Create `tests/test_chart_generation.py`:

```python
import pandas as pd
from datetime import datetime, timedelta
from scripts.generate_metrics_charts import MetricsVisualizer

def test_chart_shows_multiple_date_labels_for_30_day_span(tmp_path):
    """Test that charts show multiple date labels across 30-day timespan."""
    # Create test PR data spanning 30 days
    dates = [datetime.now() - timedelta(days=i) for i in range(30, 0, -1)]
    prs_data = []
    for i, date in enumerate(dates):
        prs_data.append({
            'repository': 'test/repo',
            'pr_number': i,
            'author': 'testuser',
            'merged_at': date.isoformat() + 'Z',
            'base_branch': 'main',
            'additions': 10,
            'deletions': 5
        })
    
    prs_csv = tmp_path / "test_prs.csv"
    pd.DataFrame(prs_data).to_csv(prs_csv, index=False)
    
    # Create minimal config
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "developer_names.json").write_text('{"developers": []}')
    
    # Generate charts
    output_dir = tmp_path / "charts"
    visualizer = MetricsVisualizer(
        commits_file=None,
        prs_file=str(prs_csv),
        output_dir=str(output_dir),
        name_config=str(config_dir / "developer_names.json")
    )
    visualizer.generate_pr_charts(freq="D")
    
    # Verify chart file was created
    chart_file = output_dir / "prs_d_count_stacked.png"
    assert chart_file.exists()
    
    # Manual verification: Open chart and verify multiple dates on x-axis
    # (Automated verification would require image analysis library)
    print(f"Chart generated: {chart_file}")
    print("MANUAL: Verify chart shows multiple date labels (not just one)")
```

**Step 2: Run test to document current behavior**

Run: `pytest tests/test_chart_generation.py::test_chart_shows_multiple_date_labels_for_30_day_span -v -s`

Expected: PASS but prints note to manually verify (will show issue)

**Step 3: Fix date locator to be dynamic based on data range**

In `scripts/generate_metrics_charts.py`, modify `_create_stacked_area_chart` (around line 209):

```python
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
    
    # CHANGED: Dynamic date formatting based on data range
    date_range = (pivot.index.max() - pivot.index.min()).days
    if date_range <= 7:
        # Weekly or less: show every day
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    elif date_range <= 30:
        # Monthly: show every 3-5 days
        interval = max(1, date_range // 7)  # Aim for ~7 labels
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=interval))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    elif date_range <= 90:
        # Quarterly: show weekly
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    else:
        # Longer periods: show monthly
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    
    fig.autofmt_xdate()
    
    plt.tight_layout()
    output_path = self.output_dir / filename
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {output_path}")
    plt.close()
```

**Step 4: Apply same fix to cumulative line charts**

In `scripts/generate_metrics_charts.py`, modify `_create_cumulative_line_chart` (around line 254) with identical date range logic:

```python
def _create_cumulative_line_chart(
    self,
    df: pd.DataFrame,
    author_col: str,
    title: str,
    ylabel: str,
    filename: str
):
    """Create cumulative line chart."""
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
    
    # CHANGED: Same dynamic date formatting as stacked area
    date_range = (cumulative.index.max() - cumulative.index.min()).days
    if date_range <= 7:
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    elif date_range <= 30:
        interval = max(1, date_range // 7)
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=interval))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    elif date_range <= 90:
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    else:
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    
    fig.autofmt_xdate()
    
    plt.tight_layout()
    output_path = self.output_dir / filename
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {output_path}")
    plt.close()
```

**Step 5: Test with real data**

Run: `uv run python scripts/generate_metrics_charts.py --prs src/org_prs.csv --output charts`

Expected: Charts generated with multiple date labels visible on x-axis

**Step 6: Verify charts visually**

Run: `open charts/prs_d_count_stacked.png` (macOS) or equivalent

Expected: X-axis shows multiple dates spanning the 30-day period (approximately every 4-5 days)

**Step 7: Commit**

```bash
git add scripts/generate_metrics_charts.py tests/test_chart_generation.py
git commit -m "fix: dynamic x-axis date labels based on data range"
```

---

### Task 3: Extract Full Year Data and Generate Charts

**Files:**
- Run: Command-line extraction and chart generation
- Verify: Generated CSV files and charts

**Step 1: Clean existing state and CSVs**

Run: `rm -f org_commits.csv org_prs.csv src/org_commits.csv src/org_prs.csv`

Expected: Old CSV files removed

**Step 2: Extract 295 days (beginning of 2025 to now)**

Run: `cd src && uv run python -m git_extraction.cli --org degree-analytics --days 295 2>&1 | tee extraction.log`

Expected: 
- "Commits extracted: N" where N > 0 (not just 1)
- "PRs extracted: 41" (or similar)
- Files created: `org_commits.csv`, `org_prs.csv`

**Step 3: Verify CSV data**

Run: 
```bash
wc -l org_commits.csv org_prs.csv
head -2 org_commits.csv
```

Expected:
- Commits CSV has > 2 lines (header + data)
- Has columns: repository, sha, author_name, committed_date, additions, deletions, on_main_branch

**Step 4: Generate all charts**

Run: `cd .. && uv run python scripts/generate_metrics_charts.py --commits src/org_commits.csv --prs src/org_prs.csv --output charts`

Expected:
- 12 charts generated (6 commit + 6 PR)
- No errors about missing columns
- X-axis labels visible across timespan

**Step 5: Verify charts show proper date ranges**

Run: `open charts/prs_d_count_stacked.png charts/commits_d_count_stacked.png`

Expected:
- X-axis shows multiple date labels spanning full period
- Data visible across the timespan (not just one spike)
- Legend shows developer names

**Step 6: Document success**

Run: 
```bash
echo "✅ Chart Generation Fixed - $(date)" >> docs/plans/2025-10-22-fix-verification.md
ls -lh charts/*.png >> docs/plans/2025-10-22-fix-verification.md
```

Expected: Verification document created with chart file sizes

---

## Verification Checklist

After completing all tasks:

- [ ] Test passes: `test_get_commits_since_includes_all_main_branch_commits`
- [ ] Extraction finds > 0 commits (not just 1)
- [ ] Charts generated without column errors
- [ ] X-axis shows multiple date labels (not just one)
- [ ] Both commit and PR charts display properly
- [ ] Documentation updated with verification results

---

## Known Edge Cases

1. **Empty repositories**: Extraction should handle repos with no commits gracefully
2. **Very short time periods** (< 7 days): Should show daily labels
3. **Very long time periods** (> 1 year): Should show monthly labels
4. **Single data point**: Chart should still render with one date visible

---

## Dependencies

- Python 3.12+
- UV package manager
- GitPython library
- Pandas, Matplotlib
- pytest (for testing)

---

## Rollback Plan

If issues occur:

1. Revert commit extraction changes: `git revert <commit-sha>`
2. Use old PR-only extraction temporarily
3. Regenerate charts with just PR data: `uv run python scripts/generate_metrics_charts.py --prs src/org_prs.csv --output charts`

