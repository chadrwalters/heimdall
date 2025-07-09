# Analysis Pipeline Guide

## Overview
Comprehensive guide to running the North Star Metrics analysis pipeline, from data extraction to actionable insights.

## Pipeline Architecture

```
GitHub API → Data Extraction → AI Analysis → Report Generation
     ↓              ↓              ↓              ↓
Linear API → Data Processing → Impact Scoring → Developer Metrics
     ↓              ↓              ↓              ↓
Anthropic → Classification → Aggregation → Process Insights
```

## Pipeline Commands

### Quick Pilot Analysis
```bash
# 7-day pilot for initial validation
just pilot organization-name
```

**Use When**: First-time setup, testing configuration, quick health checks

### Full Pipeline Analysis
```bash
# Complete 30-day analysis
just pipeline organization-name 30
```

**Use When**: Comprehensive analysis, monthly reports, strategic insights

### Custom Analysis
```bash
# Custom extraction and analysis
just extract organization-name 90    # Extract 90 days
just analyze custom_data.csv         # Analyze specific dataset
```

**Use When**: Historical analysis, specific time periods, custom datasets

## Pipeline Stages

### Stage 1: Data Extraction
```bash
just extract organization-name 30
```

**What Happens:**
- Discovers all active repositories in organization
- Extracts PRs and commits from last 30 days
- Handles pagination and rate limiting
- Saves raw data for processing

**Outputs:**
- `org_prs.csv` - Pull request data
- `org_commits.csv` - Commit data
- `extraction_log.txt` - Processing log

### Stage 2: AI Analysis
```bash
just analyze org_prs.csv
```

**What Happens:**
- Sends code diffs to Claude AI for analysis
- Classifies work types (Feature, Bug Fix, etc.)
- Scores complexity, risk, and clarity (1-10)
- Calculates weighted impact scores
- Detects AI-assisted development

**Outputs:**
- `analysis_results.csv` - AI analysis results
- `analysis_log.txt` - Processing details

### Stage 3: Metrics Generation
```bash
just generate-metrics analysis_results.csv
```

**What Happens:**
- Aggregates individual analyses
- Creates developer-level metrics
- Calculates team and organization insights
- Generates process compliance reports

**Outputs:**
- `developer_metrics.csv` - Individual contributor analysis
- `team_metrics.csv` - Team-level aggregations
- `process_metrics.csv` - Workflow insights

## Analysis Configuration

### Time Periods
```bash
# Different analysis windows
just pilot org-name              # 7 days (quick validation)
just extract org-name 30         # 30 days (monthly review)
just extract org-name 90         # 90 days (quarterly analysis)
just extract org-name 180        # 180 days (historical trends)
```

### Scope Control
```bash
# Organization-wide analysis
just extract organization-name 30

# Repository-specific analysis
just extract-repo organization-name/repo-name 30

# Team-specific analysis (requires Linear integration)
just extract-team team-name 30
```

## Data Quality Validation

### Pre-Analysis Checks
```bash
just verify-apis                 # Test API connectivity
just validate-config             # Check configuration
just check-permissions org-name  # Verify repository access
```

### Post-Analysis Validation
```bash
just validate-results analysis_results.csv
just check-completeness org_prs.csv
just verify-metrics developer_metrics.csv
```

## Performance Optimization

### Large Organizations
```bash
# Incremental extraction
just extract-incremental org-name

# Parallel processing
just extract-parallel org-name 30 --workers 4

# Batch processing
just extract-batch org-list.txt 30
```

### Rate Limiting
```bash
# Conservative extraction (slow but reliable)
just extract org-name 30 --rate-limit conservative

# Aggressive extraction (fast but may hit limits)
just extract org-name 30 --rate-limit aggressive
```

## Error Handling

### Common Failure Points
1. **API Rate Limits**: GitHub/Linear API quota exceeded
2. **Authentication**: Invalid or expired tokens
3. **Repository Access**: Insufficient permissions
4. **Data Quality**: Incomplete or malformed data

### Recovery Procedures
```bash
# Resume failed extraction
just resume-extraction org-name

# Retry failed analysis
just retry-analysis failed_items.csv

# Repair corrupted data
just repair-data org_prs.csv
```

## Output Interpretation

### Analysis Results Structure
```csv
repository,date,author,work_type,complexity_score,risk_score,clarity_score,impact_score,analysis_summary
myapp,2025-01-15,dev@company.com,New Feature,8,6,9,7.4,"Added user authentication system"
```

### Key Metrics
- **Impact Score**: Weighted combination (40% complexity + 50% risk + 10% clarity)
- **Work Type Distribution**: Percentage breakdown of development activities
- **Developer Productivity**: Individual contributor analysis
- **Process Compliance**: Linear ticket correlation rates

### Trend Analysis
```bash
# Compare time periods
just compare-periods org-name 30 60

# Trend analysis
just analyze-trends analysis_results.csv

# Benchmark against industry
just benchmark analysis_results.csv
```

## Automation & Scheduling

### Scheduled Analysis
```bash
# Setup weekly analysis
just schedule-weekly org-name

# Monthly comprehensive analysis
just schedule-monthly org-name

# Custom schedule
just schedule-custom org-name "0 9 * * 1"  # Every Monday at 9 AM
```

### GitHub Actions Integration
```yaml
name: North Star Metrics Analysis
on:
  schedule:
    - cron: '0 9 * * 1'  # Weekly on Monday
  workflow_dispatch:

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Analysis
        run: just pipeline ${{ github.repository_owner }} 30
```

## Best Practices

### Data Collection
- **Regular Cadence**: Weekly pilot, monthly full analysis
- **Incremental Updates**: Use incremental extraction for efficiency
- **Quality Checks**: Validate data before analysis
- **Backup Strategy**: Preserve raw data for re-analysis

### Analysis Optimization
- **Scope Definition**: Clear boundaries on what to analyze
- **Time Windows**: Consistent time periods for comparability
- **Filtering**: Remove noise (bot commits, automated changes)
- **Validation**: Cross-check results with known patterns

### Report Generation
- **Standardized Formats**: Consistent CSV structures
- **Visualization**: Charts and graphs for executive summaries
- **Actionable Insights**: Clear recommendations from data
- **Historical Context**: Trend analysis and comparisons

## Troubleshooting

### Pipeline Failures
```bash
# Check pipeline status
just pipeline-status

# View detailed logs
just logs --verbose

# Debug specific stage
just debug-extraction org-name
just debug-analysis failed_items.csv
```

### Data Quality Issues
```bash
# Validate data integrity
just validate-data org_prs.csv

# Check for missing data
just check-completeness org_prs.csv

# Repair corrupted files
just repair-data org_prs.csv
```

### Performance Issues
```bash
# Profile pipeline performance
just profile-pipeline org-name 30

# Optimize extraction
just optimize-extraction org-name

# Monitor resource usage
just monitor-resources
```

## Advanced Features

### Custom Analysis Models
```bash
# Train custom classification model
just train-model training_data.csv

# Use custom model for analysis
just analyze --model custom_model.pkl org_prs.csv
```

### Integration Extensions
```bash
# JIRA integration
just analyze-jira org-name 30

# Slack reporting
just report-slack analysis_results.csv

# Dashboard updates
just update-dashboard analysis_results.csv
```

For more detailed troubleshooting, see the [Troubleshooting Guide](../troubleshooting/common-problems.md).