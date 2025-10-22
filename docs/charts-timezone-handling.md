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
