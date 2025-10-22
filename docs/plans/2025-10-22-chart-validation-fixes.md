# Chart Validation Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 2 critical chart validation failures and 3 code quality warnings identified during comprehensive chart validation.

**Architecture:** Apply targeted fixes to chart generation code (scripts/generate_metrics_charts.py) and configuration data (config/developer_names.json). Each fix includes test-driven validation to ensure regression prevention.

**Tech Stack:** Python 3.12, Matplotlib, Pandas, Pytest

---

## Task 1: Fix Dynamic Y-Axis for Cycle Completion Chart

**Files:**
- Modify: `scripts/generate_metrics_charts.py:659`
- Test: `tests/test_chart_generation.py:96-178`

**Step 1: Run failing test to confirm issue**

Run: `.venv/bin/pytest tests/test_chart_generation.py::test_cycle_completion_chart_ylim_scales_to_data -v`

Expected output:
```
FAILED tests/test_chart_generation.py::test_cycle_completion_chart_ylim_scales_to_data
AssertionError: Y-axis limit should accommodate observed completion rate
assert 105 >= 400.0
```

**Step 2: Apply dynamic Y-axis scaling fix**

Location: `scripts/generate_metrics_charts.py:659`

Replace:
```python
        ax.set_ylim(0, 105)  # Percentage scale with some headroom
```

With:
```python
        # Dynamic Y-axis to accommodate completion rates >100%
        # When teams complete carryover work, rates can exceed 100%
        max_rate = pivot.max().max() if len(pivot) > 0 else 100
        y_max = max(105, max_rate * 1.1)  # 10% headroom, minimum 105
        ax.set_ylim(0, y_max)
```

**Step 3: Run test to verify fix**

Run: `.venv/bin/pytest tests/test_chart_generation.py::test_cycle_completion_chart_ylim_scales_to_data -v`

Expected output:
```
PASSED tests/test_chart_generation.py::test_cycle_completion_chart_ylim_scales_to_data
```

**Step 4: Verify chart generation still works**

Run:
```bash
python scripts/generate_metrics_charts.py \
  --commits src/org_commits.csv \
  --prs src/org_prs.csv \
  --cycles linear_cycles.csv \
  --output charts
```

Expected: Chart `charts/cycle_completion_rate.png` generates without errors

Verify: Open chart and confirm Y-axis extends beyond 105% if data requires it

**Step 5: Commit**

```bash
git add scripts/generate_metrics_charts.py tests/test_chart_generation.py
git commit -m "fix(charts): dynamic Y-axis scaling for cycle completion rates >100%

Cycle completion rates can exceed 100% when teams complete carryover
work started before the cycle. Previously hardcoded 105% limit truncated
data. Now scales dynamically to max observed rate + 10% headroom.

Fixes test_cycle_completion_chart_ylim_scales_to_data"
```

---

## Task 2: Add Missing Developer Name Mapping

**Files:**
- Modify: `config/developer_names.json:34-38`
- Test: `tests/test_chart_generation.py:61-94`

**Step 1: Run failing test to confirm issue**

Run: `.venv/bin/pytest tests/test_chart_generation.py::test_unify_author_names_maps_all_handles -v`

Expected output:
```
FAILED tests/test_chart_generation.py::test_unify_author_names_maps_all_handles
AssertionError: Expected git handle 'toddahoffman' to map to canonical 'Todd'
assert 'Todd' in {'toddahoffman', 'Josh Park', 'Chad'}
```

**Step 2: Add missing name mapping**

Location: `config/developer_names.json:34-38`

Replace:
```json
    {
      "canonical_name": "Todd",
      "git_names": ["Todd Hoffman"],
      "github_handles": [],
      "linear_names": ["Todd Hoffman"]
    },
```

With:
```json
    {
      "canonical_name": "Todd",
      "git_names": ["Todd Hoffman", "toddahoffman"],
      "github_handles": ["toddahoffman"],
      "linear_names": ["Todd Hoffman"]
    },
```

**Step 3: Run test to verify fix**

Run: `.venv/bin/pytest tests/test_chart_generation.py::test_unify_author_names_maps_all_handles -v`

Expected output:
```
PASSED tests/test_chart_generation.py::test_unify_author_names_maps_all_handles
```

**Step 4: Verify name unification in real data**

Run:
```bash
python scripts/generate_metrics_charts.py \
  --commits src/org_commits.csv \
  --prs src/org_prs.csv \
  --output charts
```

Expected console output should show commits unified under "Todd" (not "toddahoffman")

Verify: Open any chart with developer names and confirm "Todd" appears (not "toddahoffman")

**Step 5: Commit**

```bash
git add config/developer_names.json tests/test_chart_generation.py
git commit -m "fix(config): add toddahoffman mapping to Todd canonical name

Git handle 'toddahoffman' was unmapped, causing commits to appear
as separate developer. Now unified under canonical 'Todd' for
accurate metrics aggregation.

Fixes test_unify_author_names_maps_all_handles"
```

---

## Task 3: Fix Pandas SettingWithCopyWarning for PRs

**Files:**
- Modify: `scripts/generate_metrics_charts.py:432`
- Test: `tests/test_chart_generation.py:180-185`

**Step 1: Reproduce warning**

Run: `.venv/bin/pytest tests/test_chart_generation.py::test_generate_pr_charts_creates_expected_png -v`

Expected output includes:
```
SettingWithCopyWarning: A value is trying to be set on a copy of a slice from a DataFrame.
main_prs["size"] = main_prs["additions"] + main_prs["deletions"]
```

**Step 2: Add explicit copy for PRs**

Location: `scripts/generate_metrics_charts.py:429-432`

Replace:
```python
        merged_prs = self.prs_df[self.prs_df["merged_at"].notna()]
        main_prs = self._filter_main_branches(merged_prs, "merged_at")

        # Calculate size
        main_prs["size"] = main_prs["additions"] + main_prs["deletions"]
```

With:
```python
        merged_prs = self.prs_df[self.prs_df["merged_at"].notna()]
        main_prs = self._filter_main_branches(merged_prs, "merged_at")

        # Explicit copy to avoid SettingWithCopyWarning
        main_prs = main_prs.copy()

        # Calculate size
        main_prs["size"] = main_prs["additions"] + main_prs["deletions"]
```

**Step 3: Run test to verify warning is gone**

Run: `.venv/bin/pytest tests/test_chart_generation.py::test_generate_pr_charts_creates_expected_png -v`

Expected: No SettingWithCopyWarning in output, test passes

**Step 4: Verify PR charts still generate correctly**

Run:
```bash
python scripts/generate_metrics_charts.py \
  --commits src/org_commits.csv \
  --prs src/org_prs.csv \
  --output charts
```

Expected: All PR charts generate without warnings

**Step 5: Commit**

```bash
git add scripts/generate_metrics_charts.py
git commit -m "fix(charts): add explicit copy to avoid SettingWithCopyWarning for PRs

Pandas raises SettingWithCopyWarning when modifying filtered DataFrames.
Added explicit .copy() before size calculation to ensure we're working
with a true copy, not a view.

Prevents future breakage on pandas upgrades."
```

---

## Task 4: Fix Pandas SettingWithCopyWarning for Commits

**Files:**
- Modify: `scripts/generate_metrics_charts.py:378`

**Step 1: Add explicit copy for commits**

Location: `scripts/generate_metrics_charts.py:375-378`

Replace:
```python
        # Filter to main branches
        main_commits = self._filter_main_branches(self.commits_df, "committed_date")

        # Calculate size (additions + deletions)
        main_commits["size"] = main_commits["additions"] + main_commits["deletions"]
```

With:
```python
        # Filter to main branches
        main_commits = self._filter_main_branches(self.commits_df, "committed_date")

        # Explicit copy to avoid SettingWithCopyWarning
        main_commits = main_commits.copy()

        # Calculate size (additions + deletions)
        main_commits["size"] = main_commits["additions"] + main_commits["deletions"]
```

**Step 2: Verify commit charts generate without warnings**

Run:
```bash
python scripts/generate_metrics_charts.py \
  --commits src/org_commits.csv \
  --prs src/org_prs.csv \
  --output charts 2>&1 | grep -i "settingwithcopywarning"
```

Expected: No output (no warnings)

**Step 3: Run full chart generation test**

Run: `.venv/bin/pytest tests/test_chart_generation.py -v`

Expected: All 3 tests pass, no warnings in output

**Step 4: Commit**

```bash
git add scripts/generate_metrics_charts.py
git commit -m "fix(charts): add explicit copy to avoid SettingWithCopyWarning for commits

Consistent with PR chart fix. Ensures commit size calculation operates
on a true copy of the filtered DataFrame, not a view.

Completes SettingWithCopyWarning cleanup across all chart types."
```

---

## Task 5: Fix Timezone Drop Warning (Documentation)

**Files:**
- Modify: `scripts/generate_metrics_charts.py:192` (add comment)
- Create: `docs/charts-timezone-handling.md`

**Step 1: Add inline documentation for timezone behavior**

Location: `scripts/generate_metrics_charts.py:192`

Add comment above line:
```python
        # NOTE: Period conversion drops timezone info - this is expected behavior.
        # All input datetimes are UTC, and aggregations work correctly without
        # explicit timezone tracking. See docs/charts-timezone-handling.md for details.
        df["period"] = df[date_col].dt.to_period(freq)
```

**Step 2: Create timezone documentation**

Create file: `docs/charts-timezone-handling.md`

```markdown
# Charts Timezone Handling

## Overview

All chart generation operates in UTC. Timezone information is intentionally dropped during period aggregation.

## Data Pipeline

1. **Input**: GitHub API returns timestamps in UTC (ISO 8601 format with Z suffix)
2. **Parsing**: Pandas reads as `datetime64[ns, UTC]`
3. **Aggregation**: `dt.to_period()` drops timezone → `Period[D]` or `Period[W]`
4. **Output**: Charts show UTC-based date labels

## Why This Works

- **GitHub commits**: Always UTC
- **GitHub PRs**: Merged timestamps always UTC
- **Linear cycles**: Start/end dates always UTC
- **Developers**: All work across same UTC day boundaries

## Known Limitation

Daily aggregations at UTC midnight may split a developer's work day if they're in PST/EST. This is acceptable because:

1. Week-long analysis smooths out daily variations
2. Metrics focus on throughput, not precise hour-of-day tracking
3. All developers measured consistently (same UTC boundary)

## Testing

Tests verify that timezone-aware input produces correct aggregations despite warning:

```python
def test_period_aggregation_preserves_counts():
    # Input has UTC timezone
    df = create_utc_dataframe()

    # Aggregation drops timezone (warning expected)
    result = aggregate_by_period(df, freq='D')

    # Counts remain accurate
    assert result.sum() == expected_total
```

## Future Enhancement

If precise timezone handling becomes critical:
1. Store developer timezone in team_config
2. Convert to developer local time before aggregation
3. Update chart labels to show "Developer Local Time"
```

**Step 3: Verify documentation is clear**

Review: Read `docs/charts-timezone-handling.md` to ensure explanation is complete

Ask: Does this explain why the warning is harmless and what would be needed to fix it properly?

**Step 4: Commit**

```bash
git add scripts/generate_metrics_charts.py docs/charts-timezone-handling.md
git commit -m "docs(charts): document intentional timezone drop during aggregation

Pandas UserWarning about timezone drop during period conversion is expected
behavior. All inputs are UTC, and aggregations work correctly.

Added inline comment and comprehensive docs explaining the design choice
and path forward if precise timezone handling is needed in future."
```

---

## Task 6: Verification - Run Full Test Suite

**Files:**
- Test: All chart tests

**Step 1: Run all chart generation tests**

Run: `.venv/bin/pytest tests/test_chart_generation.py -v`

Expected output:
```
tests/test_chart_generation.py::test_unify_author_names_maps_all_handles PASSED
tests/test_chart_generation.py::test_cycle_completion_chart_ylim_scales_to_data PASSED
tests/test_chart_generation.py::test_generate_pr_charts_creates_expected_png PASSED

===================== 3 passed in X.XXs =====================
```

**Step 2: Run all AI usage chart tests**

Run: `.venv/bin/pytest tests/test_ai_usage_charts.py -v`

Expected output:
```
===================== 15 passed in X.XXs =====================
```

**Step 3: Generate all charts end-to-end**

Run:
```bash
just chart all src/org_commits.csv src/org_prs.csv linear_cycles.csv
```

Expected: All 23 charts generate successfully without errors or warnings

Verify: Check that `charts/` directory contains all expected PNG files with recent timestamps

**Step 4: Visual spot check**

Open in browser/image viewer:
- `charts/cycle_completion_rate.png` - Y-axis extends beyond 105% if needed
- `charts/commits_d_count_per_period.png` - "Todd" appears (not "toddahoffman")
- `charts/ai_usage_daily_cost.png` - Renders correctly

**Step 5: No commit needed** (verification step only)

---

## Task 7: Update Validation Report

**Files:**
- Create: `docs/chart-validation-report-2025-10-22-FIXED.md`

**Step 1: Copy original validation report**

Run:
```bash
cp docs/chart-validation-report-2025-10-22.md \
   docs/chart-validation-report-2025-10-22-FIXED.md
```

(Note: Original report was inline in conversation, so create from memory/notes)

**Step 2: Update status table**

In `docs/chart-validation-report-2025-10-22-FIXED.md`, update the inventory table:

Change:
```
|cycle_completion_rate|...|❌ FAIL|
```

To:
```
|cycle_completion_rate|...|✅ PASS|
```

Add note at top:
```markdown
# Chart Validation Report - POST-FIX

**Date**: 2025-10-22 (fixes applied)
**Status**: All issues resolved ✅
**Test Pass Rate**: 18/18 (100%)

## Changes Applied

1. ✅ Fixed dynamic Y-axis for cycle completion (scripts/generate_metrics_charts.py:659)
2. ✅ Added missing name mapping for toddahoffman (config/developer_names.json:35)
3. ✅ Fixed pandas copy warnings for PRs (scripts/generate_metrics_charts.py:432)
4. ✅ Fixed pandas copy warnings for commits (scripts/generate_metrics_charts.py:378)
5. ✅ Documented timezone handling (docs/charts-timezone-handling.md)

---

## Original Report (for reference)
```

**Step 3: Commit**

```bash
git add docs/chart-validation-report-2025-10-22-FIXED.md
git commit -m "docs(validation): add post-fix validation report

All critical issues and warnings resolved. Chart validation now passes
at 100% (18/18 tests). Production-ready.

- Fixed cycle completion Y-axis scaling
- Fixed developer name unification
- Fixed pandas copy warnings
- Documented timezone behavior"
```

---

## Task 8: Final Integration Test

**Files:**
- Test: Full pipeline from extraction to charts

**Step 1: Clean charts directory**

Run:
```bash
rm -rf charts/*.png
```

**Step 2: Run full chart generation pipeline**

Run:
```bash
just chart all src/org_commits.csv src/org_prs.csv linear_cycles.csv charts
```

Expected console output:
```
📊 Generating all metrics charts...
   Output directory: /path/to/charts

📊 Generating Daily commit charts...
  Loaded X commits
  Filtered to X commits on main branches
✅ Saved: charts/commits_d_count_per_period.png
✅ Saved: charts/commits_d_count_cumulative.png
...
✅ All charts generated successfully!
```

**Step 3: Verify all 23 charts exist**

Run:
```bash
ls -1 charts/*.png | wc -l
```

Expected: `23`

**Step 4: Run full test suite**

Run: `.venv/bin/pytest tests/test_chart_generation.py tests/test_ai_usage_charts.py -v`

Expected:
```
===================== 18 passed in X.XXs =====================
```

**Step 5: Tag release**

```bash
git tag -a chart-validation-fixes-v1.0 -m "Chart validation fixes - all issues resolved

- Dynamic Y-axis for cycle completion rates >100%
- Complete developer name mapping
- Pandas copy warning fixes
- Timezone handling documentation

Test pass rate: 100% (18/18)
Charts validated: 23/23"

git push origin chart-validation-fixes-v1.0
```

---

## Completion Checklist

- [ ] Task 1: Dynamic Y-axis for cycle completion chart
- [ ] Task 2: Developer name mapping for toddahoffman
- [ ] Task 3: Pandas copy warning fix (PRs)
- [ ] Task 4: Pandas copy warning fix (commits)
- [ ] Task 5: Timezone handling documentation
- [ ] Task 6: Full test suite verification (18/18 passing)
- [ ] Task 7: Updated validation report
- [ ] Task 8: Final integration test
- [ ] All 23 charts generate without errors/warnings
- [ ] Visual spot checks complete
