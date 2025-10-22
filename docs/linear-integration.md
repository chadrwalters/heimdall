# 🔗 Linear Integration Guide

Complete guide to extracting and visualizing Linear cycle/sprint data alongside GitHub metrics.

## Overview

The Linear integration adds sprint/cycle tracking capabilities to the GitHub metrics system. This enables:
- **Velocity tracking**: Measure story points and issue count per cycle
- **Completion rates**: Track started vs completed work
- **Developer breakdown**: Individual contributions within cycles
- **Cross-correlation**: Compare planned work (Linear) with actual work (GitHub)

## Architecture

### Data Flow
```
Linear API → extract_linear_cycles.py → linear_cycles.csv → generate_metrics_charts.py → cycle_*.png
```

### Generated Outputs
- `linear_cycles.csv` - Raw cycle data with issue details
- `cycle_issues_started.png` - Issues started per cycle (grouped bar chart)
- `cycle_points_started.png` - Story points started per cycle
- `cycle_issues_completed.png` - Issues completed per cycle
- `cycle_points_completed.png` - Story points completed per cycle

## Quick Start

### 1. Set up Linear API Access

Add to your `.env` file:
```bash
LINEAR_API_KEY=lin_api_xxxxxxxxxxxxxxxx  # From Linear settings
```

Verify connection:
```bash
just verify-apis  # Should show Linear: ✅ Connected
```

### 2. Extract Cycle Data

```bash
# Extract cycles for ENG team
just extract-linear-cycles ENG

# Extract for different team
just extract-linear-cycles PRODUCT

# Custom output file
just extract-linear-cycles ENG output=my_cycles.csv
```

This creates `linear_cycles.csv` with columns:
- `cycle_id`, `cycle_number`, `cycle_name`
- `cycle_start`, `cycle_end`
- `issue_identifier`, `assignee_name`, `estimate`
- `state_type`, `completed_at`

### 3. Generate Cycle Charts

```bash
# Generate only cycle charts
uv run python scripts/generate_metrics_charts.py \
  --cycles linear_cycles.csv \
  --output charts

# Or generate ALL charts (GitHub + Linear)
just generate-charts-all src/org_commits.csv src/org_prs.csv linear_cycles.csv charts
```

### 4. Full Pipeline

```bash
# Complete pipeline with Linear integration
just pipeline-with-linear your-org 30 ENG
```

This runs:
1. GitHub data extraction (30 days)
2. Linear cycle data extraction (ENG team)
3. AI analysis on GitHub data
4. Comprehensive report generation
5. All 16 charts (12 GitHub + 4 Linear)

## Understanding the Metrics

### Issues Started vs Completed

**Issues Started**: Issues with `createdAt` date within the cycle period
- Measures work added to the cycle
- Helps track cycle planning accuracy
- Shows new work coming in

**Issues Completed**: Issues with `completedAt` date within cycle AND `state_type == "completed"`
- Measures actual delivery
- Tracks cycle completion rate
- Shows team velocity

### Story Points Tracking

Story points provide a size-adjusted view of velocity:
- **Points Started**: Sum of `estimate` field for started issues
- **Points Completed**: Sum of `estimate` for completed issues
- Missing estimates treated as 0 (excluded from point calculations)

### Velocity Analysis

Compare started vs completed to understand:
- **Over-commitment**: More started than completed = taking on too much
- **Under-estimation**: Completed significantly less than started
- **Healthy flow**: Started ≈ Completed = predictable velocity
- **Unplanned work**: Completed issues not started in cycle = reactive work

## Chart Interpretation

### Grouped Bar Charts

Each chart shows:
- **X-axis**: Cycle numbers (Cycle 1, Cycle 2, etc.)
- **Y-axis**: Count (issues) or Sum (story points)
- **Grouped bars**: One bar per developer per cycle
- **Colors**: Consistent with GitHub commit/PR charts

### Reading the Charts

**cycle_issues_started.png**:
- Shows planning capacity per cycle
- Higher bars = more issues planned
- Developer breakdown shows work distribution

**cycle_issues_completed.png**:
- Shows actual delivery per cycle
- Compare with started to see completion rate
- Gaps indicate blocked or carried-over work

**cycle_points_started.png & cycle_points_completed.png**:
- Size-adjusted velocity metrics
- More accurate than issue count for velocity
- Accounts for different issue complexities

## Configuration

### Developer Name Mapping

The system uses `config/developer_names.json` to unify names:

```json
{
  "developers": [
    {
      "canonical_name": "Chad Walters",
      "git_names": ["Chad Walters", "chadrwalters"],
      "github_handles": ["chadrwalters"],
      "linear_names": ["Chad Walters"]
    }
  ]
}
```

**Important**: Add `linear_names` array for each developer to ensure proper attribution in cycle charts.

### Color Consistency

Developer colors are automatically assigned using a deterministic hash:
- Same color across commits, PRs, and cycle charts
- Consistent across chart regenerations
- Based on canonical name (from developer_names.json)

## Advanced Usage

### Multi-Team Analysis

Extract and compare multiple teams:

```bash
# Extract each team separately
just extract-linear-cycles ENG eng_cycles.csv
just extract-linear-cycles PRODUCT product_cycles.csv

# Generate separate charts
uv run python scripts/generate_metrics_charts.py --cycles eng_cycles.csv --output eng_charts
uv run python scripts/generate_metrics_charts.py --cycles product_cycles.csv --output product_charts
```

### Custom Time Ranges

Linear API returns all cycles by default. Filter in CSV if needed:

```bash
# Extract all cycles
just extract-linear-cycles ENG all_cycles.csv

# Filter to recent cycles
uv run python -c "
import pandas as pd
df = pd.read_csv('all_cycles.csv')
df['cycle_start'] = pd.to_datetime(df['cycle_start'])
recent = df[df['cycle_start'] >= '2024-01-01']
recent.to_csv('recent_cycles.csv', index=False)
"
```

### Combining with GitHub Data

Cross-reference Linear issues with GitHub PRs:

```python
import pandas as pd

# Load data
cycles = pd.read_csv('linear_cycles.csv')
prs = pd.read_csv('src/org_prs.csv')

# Extract issue IDs from PR titles (e.g., "[ENG-123]" or "ENG-456:")
prs['linear_id'] = prs['title'].str.extract(r'(ENG-\d+)')

# Join with cycle data
merged = prs.merge(cycles, left_on='linear_id', right_on='issue_identifier', how='inner')

# Analyze correlation
print(f"PRs with Linear tickets: {len(merged)} / {len(prs)}")
```

## Troubleshooting

### No Cycles Extracted

**Error**: `⚠️  No cycles found for team: ENG`

**Solutions**:
- Verify team key is correct (usually 2-3 letters)
- Check Linear API key has access to the team
- Confirm team has cycles/sprints created in Linear
- Try without team filter: modify script to fetch all cycles

### Missing Assignees

**Warning**: `No cycle data with valid assignees`

**Causes**:
- Issues not assigned to anyone
- Assignee names don't match `developer_names.json`

**Solutions**:
- Update `linear_names` in `config/developer_names.json`
- Check Linear issue assignments
- Review unassigned work volume

### Color Collisions

If two developers have the same color:

**Solution**: Expand color palette in `src/data/developer_colors.py`:
```python
COLOR_PALETTE = [
    # Add more distinct colors here
    "#ff6b6b", "#4ecdc4", "#45b7d1", # etc.
]
```

### Missing Story Points

**Issue**: `cycle_points_*.png` shows very low values

**Cause**: Issues lack `estimate` field in Linear

**Solution**:
- Add story point estimates in Linear
- Re-extract cycle data after estimates are added
- Consider using issue count metrics instead

## API Details

### Linear GraphQL Schema

The extraction uses these Linear API queries:

**Cycles Query**:
```graphql
query {
  cycles(filter: {team: {key: {eq: "ENG"}}}) {
    nodes {
      id, number, name
      startsAt, endsAt, completedAt
      team { id, key, name }
    }
  }
}
```

**Cycle Issues Query**:
```graphql
query GetCycleIssues($cycleId: String!) {
  cycle(id: $cycleId) {
    issues {
      nodes {
        id, identifier, title, estimate
        assignee { name }
        state { type }
        completedAt, createdAt
      }
    }
  }
}
```

### Rate Limiting

Linear API has rate limits:
- **Rate limit**: ~1000 requests/hour
- **Complexity**: Each query has complexity score
- **Pagination**: Handled automatically (100 items per page)

The extraction script handles pagination and respects rate limits automatically.

## Best Practices

### Regular Extraction

Extract cycle data regularly to track trends:

```bash
# Weekly extraction
0 9 * * 1 cd /path/to/project && just extract-linear-cycles ENG weekly_cycles.csv
```

### Compare Periods

Track velocity trends over time:

```bash
# Extract Q1 cycles
just extract-linear-cycles ENG q1_cycles.csv

# Extract Q2 cycles
just extract-linear-cycles ENG q2_cycles.csv

# Compare velocity between quarters
```

### Integrate with Dashboards

Use generated charts in:
- **Confluence pages**: Embed PNG files
- **Slack reports**: Automated weekly metrics
- **Executive dashboards**: Velocity and delivery tracking
- **Retrospectives**: Cycle performance analysis

## Limitations

### Current Limitations
- Only supports single team extraction per command (run multiple times for multiple teams)
- Requires manual name mapping in developer_names.json
- No automatic Linear → GitHub PR correlation (manual cross-reference required)
- Charts show all cycles (no built-in filtering by date range)

### Future Enhancements
- Multi-team extraction in single command
- Automatic name matching across systems
- Built-in Linear ↔ GitHub correlation
- Interactive charts with drill-down
- Cycle-over-cycle comparison charts

## Support

For issues or questions:
1. Check `just verify-apis` for connectivity
2. Review `config/developer_names.json` for name mapping
3. Verify Linear API permissions
4. Check extraction logs for detailed error messages

## Related Documentation

- [Developer Name Configuration](../config/developer_names.json)
- [Chart Generation Guide](../CHARTS_README.md)
- [Justfile Commands](../justfile)
- [Linear API Integration Summary](linear-integration-summary.md)
