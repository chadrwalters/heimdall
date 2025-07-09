# North Star Metrics - Usage Guide

Complete guide for using the North Star Metrics framework across different user personas and use cases.

## Table of Contents

1. [User Personas](#user-personas)
2. [Main Execution Script](#main-execution-script)
3. [Common Workflows](#common-workflows)
4. [Advanced Usage](#advanced-usage)
5. [Output Analysis](#output-analysis)
6. [Scheduling & Automation](#scheduling--automation)
7. [Best Practices](#best-practices)

## User Personas

### VPE/CTO (Strategic View)

**Primary Goals**: ROI measurement, AI adoption tracking, strategic decision making

**Key Commands**:
```bash
# Monthly organizational analysis
python main.py --org company --mode full --days 30 --output-dir monthly-report

# AI adoption metrics
grep "ai_assisted.*true" unified_pilot_data.csv | wc -l

# Process compliance overview
python -c "
import pandas as pd
df = pd.read_csv('unified_pilot_data.csv')
compliance = df['process_compliant'].mean() * 100
print(f'Process compliance: {compliance:.1f}%')
"
```

**Key Metrics**:
- AI-assisted work percentage
- Process compliance rates
- Impact score trends
- Developer productivity metrics

### Engineering Managers (Tactical View)

**Primary Goals**: Team performance, sprint planning, resource allocation

**Key Commands**:
```bash
# Team-specific analysis (last 2 weeks)
python main.py --org company --mode full --days 14 --output-dir team-metrics

# Developer comparison
python -c "
import pandas as pd
df = pd.read_csv('developer_metrics.csv')
print(df.groupby('Author')[['AvgComplexity', 'AvgImpactScore', 'AIUsageRate']].mean())
"

# Sprint retrospective data
python main.py --org company --mode incremental --log-level INFO
```

**Key Metrics**:
- Individual developer metrics
- Complexity distribution
- PR size trends
- AI tool effectiveness

### Individual Contributors (Personal View)

**Primary Goals**: Personal productivity tracking, skill development, contribution visibility

**Key Commands**:
```bash
# Personal impact review
python -c "
import pandas as pd
df = pd.read_csv('unified_pilot_data.csv')
my_work = df[df['author'].str.contains('your-email', case=False)]
print(f'Your impact score: {my_work[\"impact_score\"].mean():.2f}')
print(f'AI assistance rate: {my_work[\"ai_assisted\"].mean()*100:.1f}%')
"

# Recent contributions
just pilot company  # Quick 7-day view
```

**Key Metrics**:
- Personal impact scores
- Work type distribution
- AI assistance patterns
- Process compliance

## Main Execution Script

The `main.py` script is the primary interface for running the analysis pipeline.

### Basic Syntax

```bash
python main.py --org ORGANIZATION [OPTIONS]
```

### Execution Modes

#### 1. Pilot Mode (Default)
```bash
# 7-day analysis for quick insights
python main.py --org company --mode pilot

# Custom pilot duration
python main.py --org company --mode pilot --days 14
```

#### 2. Incremental Mode
```bash
# Process only new data since last run
python main.py --org company --mode incremental

# Force reprocessing of recent data
python main.py --org company --mode incremental --force
```

#### 3. Full Mode
```bash
# Complete historical analysis
python main.py --org company --mode full --days 90

# Large-scale analysis with custom settings
python main.py --org company --mode full --days 365 --max-workers 10 --output-dir yearly-analysis
```

### Common Options

| Option | Description | Example |
|--------|-------------|---------|
| `--org` | GitHub organization (required) | `--org mycompany` |
| `--mode` | Analysis mode | `--mode incremental` |
| `--days` | Days to analyze | `--days 30` |
| `--output-dir` | Output directory | `--output-dir ./results` |
| `--log-level` | Logging verbosity | `--log-level DEBUG` |
| `--log-file` | Log to file | `--log-file analysis.log` |
| `--dry-run` | Test without processing | `--dry-run` |
| `--skip-extraction` | Use existing data | `--skip-extraction` |
| `--skip-analysis` | Extract only | `--skip-analysis` |
| `--max-workers` | Parallel processing | `--max-workers 10` |
| `--force` | Reprocess existing data | `--force` |

### Error Recovery

The script includes automatic error recovery:

```bash
# If a run fails, restart with checkpoints
python main.py --org company --mode pilot
# Will automatically resume from last checkpoint

# Force fresh start (ignores checkpoints)
python main.py --org company --mode pilot --force
```

## Common Workflows

### 1. Initial Organization Setup

```bash
# Step 1: Test environment
python main.py --org company --dry-run

# Step 2: Small pilot
python main.py --org company --mode pilot --days 3

# Step 3: Review results
ls -la *.csv
head -5 unified_pilot_data.csv

# Step 4: Full pilot
python main.py --org company --mode pilot

# Step 5: Configure AI developers
edit config/ai_developers.json
```

### 2. Regular Monitoring

```bash
# Daily incremental update
python main.py --org company --mode incremental --log-file daily.log

# Weekly team review
python main.py --org company --mode pilot --days 7 --output-dir weekly

# Monthly strategic review
python main.py --org company --mode full --days 30 --output-dir monthly
```

### 3. Sprint Analysis

```bash
# Sprint start (baseline)
python main.py --org company --mode pilot --days 14 --output-dir sprint-baseline

# Sprint end (comparison)
python main.py --org company --mode incremental --output-dir sprint-results

# Compare results
python scripts/compare_sprints.py sprint-baseline/ sprint-results/
```

### 4. Developer Onboarding Analysis

```bash
# New hire impact tracking
python main.py --org company --mode full --days 90 --output-dir onboarding-analysis

# Focus on specific developer
python -c "
import pandas as pd
df = pd.read_csv('onboarding-analysis/unified_pilot_data.csv')
new_hire = df[df['author'].str.contains('new-hire-email')]
print(new_hire.groupby(pd.to_datetime(df['date']).dt.week)['impact_score'].mean())
"
```

### 5. AI Adoption Study

```bash
# Comprehensive AI analysis
python main.py --org company --mode full --days 180 --output-dir ai-study

# AI adoption trends
python -c "
import pandas as pd
import matplotlib.pyplot as plt
df = pd.read_csv('ai-study/unified_pilot_data.csv')
df['date'] = pd.to_datetime(df['date'])
weekly_ai = df.groupby([df['date'].dt.to_period('W'), 'ai_assisted']).size().unstack()
weekly_ai.plot(kind='area', stacked=True)
plt.savefig('ai-adoption-trend.png')
"
```

## Advanced Usage

### Custom Analysis Pipeline

```bash
# Extract only
python main.py --org company --skip-analysis --days 30

# Analyze existing data with custom settings
python main.py --org company --skip-extraction --max-workers 15

# Partial pipeline with custom output
python main.py --org company --mode pilot --output-dir custom-analysis --log-level DEBUG
```

### Configuration Overrides

```bash
# Use custom config directory
python main.py --org company --config-dir ./custom-config

# Different AI developer settings per analysis
cp config/ai_developers.json config/ai_developers_team_a.json
python main.py --org company --config-dir config-team-a
```

### Performance Tuning

```bash
# High-performance settings for large organizations
python main.py --org large-company \
  --mode full \
  --days 90 \
  --max-workers 20 \
  --log-level WARNING \
  --output-dir bulk-analysis

# Memory-conscious settings
python main.py --org company \
  --mode incremental \
  --max-workers 2 \
  --log-level ERROR
```

### Integration with External Systems

```bash
# Export to data warehouse
python main.py --org company --mode incremental
python scripts/export_to_warehouse.py unified_pilot_data.csv

# Slack notifications
python main.py --org company --mode pilot 2>&1 | \
  python scripts/send_to_slack.py

# Custom reporting
python main.py --org company --mode pilot --output-dir reports/$(date +%Y-%m-%d)
python scripts/generate_dashboard.py reports/$(date +%Y-%m-%d)
```

## Output Analysis

### Understanding Output Files

#### 1. `unified_pilot_data.csv` - Main Results
```csv
repository,date,author,source_type,work_type,complexity_score,risk_score,clarity_score,impact_score,ai_assisted,linear_ticket_id,process_compliant
myapp,2025-01-15,dev@company.com,PR,New Feature,8,6,9,7.4,true,ENG-123,true
```

Key fields:
- **impact_score**: Calculated as 40% complexity + 50% risk + 10% clarity
- **ai_assisted**: Boolean indicating AI tool usage
- **process_compliant**: Whether linked to Linear ticket

#### 2. `developer_metrics.csv` - Aggregated Metrics
```csv
Author,Period,CommitFrequency,PRFrequency,AIUsageRate,AvgPRSize,AvgComplexity,AvgImpactScore
dev@company.com,2025-W03,2.5,1.2,0.85,4.2,6.8,7.1
```

#### 3. `org_prs.csv` and `org_commits.csv` - Raw Data
These contain the original GitHub data before AI analysis.

### Analysis Examples

#### Impact Score Distribution
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('unified_pilot_data.csv')

# Impact score by work type
impact_by_type = df.groupby('work_type')['impact_score'].mean()
impact_by_type.plot(kind='bar')
plt.title('Average Impact Score by Work Type')
plt.show()
```

#### AI Assistance Correlation
```python
# Compare AI-assisted vs manual work
ai_work = df[df['ai_assisted'] == True]['impact_score'].mean()
manual_work = df[df['ai_assisted'] == False]['impact_score'].mean()
print(f"AI-assisted impact: {ai_work:.2f}")
print(f"Manual work impact: {manual_work:.2f}")
```

#### Process Compliance Analysis
```python
# Compliance by team/author
compliance = df.groupby('author')['process_compliant'].mean().sort_values()
print("Process compliance by developer:")
print(compliance)
```

## Scheduling & Automation

### GitHub Actions (Recommended)

The included workflow `.github/workflows/scheduled-analysis.yml` provides:

```yaml
# Daily scheduled runs
schedule:
  - cron: '0 6 * * *'  # 6 AM UTC daily

# Manual triggers
workflow_dispatch:
  inputs:
    organization:
      description: 'GitHub organization'
      required: true
```

**Setup**:
1. Add repository secrets: `ANTHROPIC_API_KEY`, `LINEAR_API_KEY`
2. Set repository variable: `GITHUB_ORG`
3. Workflow runs automatically

### Cron Jobs

```bash
# Set up cron scheduling
just schedule-setup

# Edit cron configuration
crontab -e

# Add daily run at 6 AM
0 6 * * * /path/to/metrics/scripts/schedule_analysis.sh >/dev/null 2>&1

# Add Monday-Friday at 8 AM
0 8 * * 1-5 /path/to/metrics/scripts/schedule_analysis.sh --mode incremental
```

### Custom Scheduling Scripts

```bash
# Create custom scheduling wrapper
cat > my_analysis.sh << 'EOF'
#!/bin/bash
cd /path/to/metrics
source .venv/bin/activate

# Run analysis
python main.py --org mycompany --mode incremental --log-file logs/$(date +%Y%m%d).log

# Send results somewhere
if [ $? -eq 0 ]; then
    echo "Analysis completed successfully" | mail -s "North Star Success" team@company.com
else
    echo "Analysis failed - check logs" | mail -s "North Star Failed" admin@company.com
fi
EOF

chmod +x my_analysis.sh
```

## Best Practices

### 1. Start Small
- Begin with 3-7 day pilots
- Test with one repository first
- Gradually increase scope

### 2. Regular Incremental Updates
- Run daily incremental updates
- Weekly full pilots for teams
- Monthly comprehensive analysis for leadership

### 3. Data Quality
- Verify AI developer configurations
- Spot-check AI classifications
- Monitor process compliance trends

### 4. Performance Optimization
- Use appropriate worker counts (5-10 for most cases)
- Monitor API rate limits
- Schedule large runs during off-hours

### 5. Error Handling
- Use log files for production runs
- Set up monitoring/alerting
- Keep checkpoint files for recovery

### 6. Security
- Rotate API keys regularly
- Use environment variables, not hardcoded keys
- Limit repository access as needed

### 7. Cost Management
- Monitor Anthropic API usage
- Use incremental mode for routine updates
- Consider batch processing for large analyses

### Example Production Workflow

```bash
#!/bin/bash
# Production daily workflow

set -euo pipefail

# Configuration
ORG="mycompany"
OUTPUT_DIR="/data/north-star/$(date +%Y/%m/%d)"
LOG_FILE="/logs/north-star/daily-$(date +%Y%m%d).log"

# Create directories
mkdir -p "$(dirname "$OUTPUT_DIR")"
mkdir -p "$(dirname "$LOG_FILE")"

# Activate environment
cd /opt/north-star-metrics
source .venv/bin/activate

# Run analysis
python main.py \
  --org "$ORG" \
  --mode incremental \
  --output-dir "$OUTPUT_DIR" \
  --log-file "$LOG_FILE" \
  --log-level INFO

# Verify results
if [ -f "$OUTPUT_DIR/unified_pilot_data.csv" ]; then
    RECORD_COUNT=$(tail -n +2 "$OUTPUT_DIR/unified_pilot_data.csv" | wc -l)
    echo "✅ Success: Processed $RECORD_COUNT records"
    
    # Send to data warehouse
    python scripts/export_to_warehouse.py "$OUTPUT_DIR/unified_pilot_data.csv"
    
    # Generate daily report
    python scripts/daily_report.py "$OUTPUT_DIR"
    
else
    echo "❌ Error: No results generated"
    exit 1
fi
```

---

For more information:
- [Setup Guide](setup-guide.md) - Initial installation and configuration
- [Configuration Reference](configuration-reference.md) - Detailed settings
- [API Reference](api-reference.md) - Integration details
- [Troubleshooting Guide](troubleshooting.md) - Common issues and solutions