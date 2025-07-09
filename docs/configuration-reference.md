# North Star Metrics - Configuration Reference

Complete reference for all configuration options in the North Star Metrics framework.

## Table of Contents

1. [Environment Variables](#environment-variables)
2. [Configuration Files](#configuration-files)
3. [Command Line Options](#command-line-options)
4. [AI Developer Overrides](#ai-developer-overrides)
5. [State Management](#state-management)
6. [Scheduling Configuration](#scheduling-configuration)
7. [Performance Tuning](#performance-tuning)

## Environment Variables

### Required Variables

| Variable | Description | Example | Notes |
|----------|-------------|---------|-------|
| `GITHUB_TOKEN` | GitHub Personal Access Token | `ghp_xxxxxxxxxxxxxxxxxxxx` | Needs `repo`, `read:org`, `read:user` scopes |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude | `sk-ant-xxxxxxxxxxxxxxxxxxxx` | Required for AI analysis |

### Optional Variables

| Variable | Description | Example | Default |
|----------|-------------|---------|---------|
| `LINEAR_API_KEY` | Linear API key | `lin_api_xxxxxxxxxxxxxxxxxxxx` | None (disables Linear integration) |
| `LINEAR_TOKEN` | Alternative Linear API key name | `lin_api_xxxxxxxxxxxxxxxxxxxx` | None |
| `GITHUB_ORG` | Default GitHub organization | `mycompany` | None (must specify in commands) |

### Scheduling Environment Variables

| Variable | Description | Example | Default |
|----------|-------------|---------|---------|
| `SCHEDULE_ORG` | Default org for scheduled runs | `mycompany` | `your-org-name` |
| `SCHEDULE_MODE` | Default analysis mode | `incremental` | `incremental` |
| `SCHEDULE_LOG_LEVEL` | Default log level | `INFO` | `INFO` |
| `SCHEDULE_MAX_WORKERS` | Default worker count | `10` | `5` |

### Setting Environment Variables

#### Using .env File (Recommended)
```bash
# Create .env file in project root
cat > .env << 'EOF'
GITHUB_TOKEN=ghp_your_token_here
ANTHROPIC_API_KEY=sk-ant-your_key_here
LINEAR_API_KEY=your_linear_api_key_here
GITHUB_ORG=mycompany
EOF
```

#### Using Shell Export
```bash
export GITHUB_TOKEN="ghp_your_token_here"
export ANTHROPIC_API_KEY="sk-ant-your_key_here"
export LINEAR_API_KEY="lin_api_your_key_here"
```

#### Using System Environment
```bash
# Add to ~/.bashrc or ~/.zshrc
echo 'export GITHUB_TOKEN="ghp_your_token_here"' >> ~/.bashrc
echo 'export ANTHROPIC_API_KEY="sk-ant-your_key_here"' >> ~/.bashrc
source ~/.bashrc
```

## Configuration Files

### 1. AI Developers Configuration (`config/ai_developers.json`)

Controls AI attribution overrides for specific developers.

```json
{
  "always_ai_developers": [
    {
      "username": "chad",
      "email": "chad@company.com",
      "ai_tool": "Claude/Cursor",
      "percentage": 100
    },
    {
      "username": "sarah",
      "email": "sarah@company.com", 
      "ai_tool": "GitHub Copilot",
      "percentage": 80
    }
  ]
}
```

#### Schema
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | Yes | GitHub username (case-insensitive) |
| `email` | string | Yes | Email address (case-insensitive) |
| `ai_tool` | string | Yes | AI tool name for attribution |
| `percentage` | number | Yes | Percentage of work that's AI-assisted (0-100) |

#### Usage Notes
- Matches against both commit author email and GitHub username
- Overrides pattern-based AI detection
- Useful for developers who consistently use AI tools
- Multiple developers can be configured
- Changes take effect on next analysis run

### 2. Analysis State (`config/analysis_state.json`)

Tracks processing state for incremental updates. **Do not edit manually.**

```json
{
  "last_run_date": "2025-01-15T10:30:00Z",
  "processed_pr_ids": ["1234", "1235", "1236"],
  "processed_commit_shas": ["abc123", "def456", "ghi789"],
  "total_records_processed": 1523
}
```

#### Fields
| Field | Type | Description |
|-------|------|-------------|
| `last_run_date` | string | ISO timestamp of last successful run |
| `processed_pr_ids` | array | List of processed PR IDs |
| `processed_commit_shas` | array | List of processed commit SHAs |
| `total_records_processed` | number | Total records processed to date |

#### Management Commands
```bash
# View current state
python -c "
import json
with open('config/analysis_state.json') as f:
    state = json.load(f)
    print(f'Last run: {state[\"last_run_date\"]}')
    print(f'Total processed: {state[\"total_records_processed\"]}')
"

# Reset state (forces full reprocessing)
python -c "
import json
state = {
    'last_run_date': None,
    'processed_pr_ids': [],
    'processed_commit_shas': [],
    'total_records_processed': 0
}
with open('config/analysis_state.json', 'w') as f:
    json.dump(state, f, indent=2)
"
```

### 3. Schedule Configuration (`config/schedule.conf`)

Configuration for scheduled analysis runs.

```bash
# Copy template and customize
cp config/schedule.conf.example config/schedule.conf
```

```bash
# Example configuration
SCHEDULE_ORG="mycompany"
SCHEDULE_MODE="incremental"
SCHEDULE_LOG_LEVEL="INFO"
SCHEDULE_MAX_WORKERS="5"
SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
NOTIFICATION_EMAIL="admin@company.com"
RESULTS_RETENTION_DAYS="30"
LOGS_RETENTION_DAYS="7"
```

## Command Line Options

### Main Script (`main.py`)

```bash
python main.py --org ORGANIZATION [OPTIONS]
```

#### Required Arguments
| Option | Description | Example |
|--------|-------------|---------|
| `--org` | GitHub organization name | `--org mycompany` |

#### Execution Mode Options
| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--mode` | Analysis mode | `pilot` | `--mode incremental` |
| `--days` | Days to analyze | `7` | `--days 30` |

**Modes**:
- `pilot`: Quick analysis (default 7 days)
- `incremental`: Process only new data since last run
- `full`: Complete historical analysis

#### Output Options
| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--output-dir` | Output directory | `.` | `--output-dir ./results` |
| `--log-level` | Logging level | `INFO` | `--log-level DEBUG` |
| `--log-file` | Log file path | None | `--log-file analysis.log` |

**Log Levels**: `DEBUG`, `INFO`, `WARNING`, `ERROR`

#### Processing Options
| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--max-workers` | Parallel workers | `5` | `--max-workers 10` |
| `--config-dir` | Config directory | `config` | `--config-dir ./custom-config` |

#### Control Options
| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--dry-run` | Test without processing | `False` | `--dry-run` |
| `--skip-extraction` | Use existing data | `False` | `--skip-extraction` |
| `--skip-analysis` | Extract only | `False` | `--skip-analysis` |
| `--force` | Reprocess existing data | `False` | `--force` |

### Just Commands

All `just` commands accept parameters:

```bash
# Extract data
just extract ORGANIZATION [DAYS]
just extract mycompany 30

# Run pipeline  
just pipeline ORGANIZATION [DAYS]
just pipeline mycompany 90

# Pipeline with custom settings
just pipeline-run mycompany incremental 7 ./results false
```

## AI Developer Overrides

### Configuration

The AI developer override system allows you to specify developers whose work should always be marked as AI-assisted, regardless of pattern detection.

#### When to Use
- Developers who consistently use AI tools but don't always include attribution
- Teams experimenting with AI-first development
- Comparative analysis between AI-assisted and traditional developers
- Known AI power users (like Chad in the example)

#### Configuration Examples

**Single Developer**:
```json
{
  "always_ai_developers": [
    {
      "username": "chad",
      "email": "chad@company.com",
      "ai_tool": "Claude/Cursor",
      "percentage": 100
    }
  ]
}
```

**Multiple Developers with Different Tools**:
```json
{
  "always_ai_developers": [
    {
      "username": "alice",
      "email": "alice@company.com",
      "ai_tool": "GitHub Copilot",
      "percentage": 85
    },
    {
      "username": "bob", 
      "email": "bob@company.com",
      "ai_tool": "Claude Code",
      "percentage": 95
    },
    {
      "username": "charlie",
      "email": "charlie@company.com",
      "ai_tool": "Cursor",
      "percentage": 90
    }
  ]
}
```

**Team-Based Configuration**:
```json
{
  "always_ai_developers": [
    {
      "username": "ai-team-lead",
      "email": "lead@company.com",
      "ai_tool": "Multiple Tools",
      "percentage": 100
    },
    {
      "username": "ai-team-dev1",
      "email": "dev1@company.com", 
      "ai_tool": "Copilot + Claude",
      "percentage": 80
    }
  ]
}
```

### Pattern-Based Detection

The system also includes automatic AI detection based on commit patterns:

#### Detected Patterns
- `co-authored-by: github copilot`
- `generated with claude code`
- `🤖 generated with claude`
- `cursor.ai`
- `ai assistant`
- Various other AI tool indicators

#### Priority
1. **AI Developer Overrides** (highest priority)
2. **Pattern-Based Detection** 
3. **No AI Detection** (default)

### Validation

Test your AI developer configuration:

```bash
# Check configuration syntax
python -c "
import json
from src.config.config_manager import ConfigManager
cm = ConfigManager()
try:
    config = cm.load_ai_developers()
    print('✅ Configuration valid')
    print(f'Configured developers: {len(config[\"always_ai_developers\"])}')
    for dev in config['always_ai_developers']:
        print(f'  - {dev[\"username\"]} ({dev[\"ai_tool\"]}, {dev[\"percentage\"]}%)')
except Exception as e:
    print(f'❌ Configuration error: {e}')
"

# Test with sample data
python main.py --org test-org --dry-run
```

## State Management

### Incremental Processing

The state management system enables efficient incremental updates by tracking:

1. **Last Run Date**: When the analysis was last executed
2. **Processed IDs**: Which PRs and commits have been analyzed
3. **Record Counts**: Total records processed for statistics

### State File Location

Default: `config/analysis_state.json`

Custom location:
```bash
python main.py --org company --config-dir ./custom-config
# Uses: ./custom-config/analysis_state.json
```

### Manual State Management

#### View State
```bash
python -c "
from src.config.state_manager import StateManager
sm = StateManager()
stats = sm.get_statistics()
for key, value in stats.items():
    print(f'{key}: {value}')
"
```

#### Reset State
```bash
python -c "
from src.config.state_manager import StateManager
sm = StateManager()
sm.reset_state()
print('State reset - next run will reprocess all data')
"
```

#### Backup State
```bash
cp config/analysis_state.json config/analysis_state_backup_$(date +%Y%m%d).json
```

### Recovery Scenarios

#### Partial Run Recovery
If a run is interrupted, the system uses checkpoints:

```bash
# Run interrupted - restart automatically resumes
python main.py --org company --mode pilot
# Will load from checkpoint and continue

# Force fresh start (ignore checkpoints)
python main.py --org company --mode pilot --force
```

#### Corrupted State Recovery
```bash
# Backup corrupted state
mv config/analysis_state.json config/analysis_state_corrupted.json

# Reset to clean state
python -c "
import json
state = {
    'last_run_date': None,
    'processed_pr_ids': [],
    'processed_commit_shas': [],
    'total_records_processed': 0
}
with open('config/analysis_state.json', 'w') as f:
    json.dump(state, f, indent=2)
print('State reset')
"

# Run full analysis to rebuild state
python main.py --org company --mode full --days 30
```

## Scheduling Configuration

### GitHub Actions Configuration

File: `.github/workflows/scheduled-analysis.yml`

#### Repository Secrets (Required)
```
ANTHROPIC_API_KEY=sk-ant-your_key_here
LINEAR_API_KEY=your_linear_api_key_here  # Optional
```

#### Repository Variables
```
GITHUB_ORG=your-organization-name
```

#### Workflow Customization
```yaml
# Change schedule (currently daily at 6 AM UTC)
schedule:
  - cron: '0 6 * * *'  # Daily
  - cron: '0 8 * * 1-5'  # Weekdays only
  - cron: '0 6 * * 1'  # Weekly (Mondays)

# Change timeout
timeout-minutes: 60  # Increase for large organizations

# Add environment variables
env:
  CUSTOM_VAR: value
```

### Cron Configuration

#### Setup
```bash
# Initialize scheduling configuration
just schedule-setup

# Edit configuration
nano config/schedule.conf

# Add to crontab
crontab -e
```

#### Cron Examples
```bash
# Daily at 6 AM
0 6 * * * /path/to/metrics/scripts/schedule_analysis.sh

# Weekdays at 8 AM  
0 8 * * 1-5 /path/to/metrics/scripts/schedule_analysis.sh --mode incremental

# Weekly full analysis (Sundays at 2 AM)
0 2 * * 0 /path/to/metrics/scripts/schedule_analysis.sh --mode full --days 7

# Monthly comprehensive analysis (1st of month at 1 AM)
0 1 1 * * /path/to/metrics/scripts/schedule_analysis.sh --mode full --days 30
```

#### Custom Scheduling Script
```bash
#!/bin/bash
# Custom scheduling wrapper

# Load environment
source /path/to/metrics/.env

# Custom notifications
SLACK_WEBHOOK="your-webhook-url"

# Run analysis
cd /path/to/metrics
if python main.py --org company --mode incremental; then
    curl -X POST -H 'Content-type: application/json' \
        --data '{"text":"✅ North Star analysis completed successfully"}' \
        "$SLACK_WEBHOOK"
else
    curl -X POST -H 'Content-type: application/json' \
        --data '{"text":"❌ North Star analysis failed - check logs"}' \
        "$SLACK_WEBHOOK"
fi
```

## Performance Tuning

### Worker Configuration

| Organization Size | Recommended Workers | Memory Usage | Processing Time |
|------------------|-------------------|--------------|-----------------|
| Small (< 100 repos) | 3-5 | 2-4 GB | 5-15 minutes |
| Medium (100-500 repos) | 5-10 | 4-8 GB | 15-45 minutes |
| Large (500+ repos) | 10-20 | 8-16 GB | 45+ minutes |

```bash
# Small organization
python main.py --org small-company --max-workers 3

# Large organization
python main.py --org large-company --max-workers 15 --log-level WARNING
```

### API Rate Limiting

#### GitHub API
- **Rate Limit**: 5,000 requests/hour for authenticated requests
- **Recommendation**: Stay under 4,000/hour to leave buffer
- **Monitoring**: Check rate limit status

```bash
# Check current rate limit
gh api rate_limit
```

#### Anthropic API
- **Rate Limit**: Varies by plan (check console)
- **Cost**: ~$0.01-0.10 per analyzed PR/commit
- **Monitoring**: Track usage in Anthropic console

### Memory Optimization

For large organizations:

```bash
# Reduce memory usage
python main.py --org large-company \
  --max-workers 5 \
  --log-level ERROR \
  --mode incremental

# Process in smaller batches
python main.py --org large-company --days 7  # Weekly batches
python main.py --org large-company --days 14  # Bi-weekly batches
```

### Disk Space Management

```bash
# Clean old checkpoints (automatic)
# Keeps latest 3 checkpoints by default

# Manual cleanup
find . -name "checkpoint_*.json" -mtime +7 -delete

# Archive old results
mkdir -p archive/$(date +%Y/%m)
mv *_$(date -d "last month" +%Y%m)*.csv archive/$(date +%Y/%m)/
```

### Network Optimization

For unstable connections:

```bash
# Enable retry logic (built-in)
# Use smaller worker counts to reduce concurrent connections
python main.py --org company --max-workers 2

# Use incremental mode to minimize data transfer
python main.py --org company --mode incremental
```

---

For more information:
- [Setup Guide](setup-guide.md) - Installation instructions
- [Usage Guide](usage-guide.md) - Common workflows and examples
- [Troubleshooting Guide](troubleshooting.md) - Problem resolution