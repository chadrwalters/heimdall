# Hermod - AI Usage Collection Tool

## Overview

Hermod is a CLI tool for collecting AI usage data from Claude Code (`ccusage`) and Codex (`ccusage-codex`). It automatically detects the developer from git configuration and generates structured JSON files for usage tracking.

## Features

- **Auto-Detection**: Automatically detects developer name from git config using `developer_names.json` mappings
- **Dual Collection**: Collects usage data from both Claude Code and Codex
- **Flexible Time Ranges**: Configure collection period (default: 7 days)
- **Multiple Output Formats**: Terminal tables with Rich or JSON for automation
- **Justfile Integration**: Seamlessly integrates with project's justfile dispatcher pattern

## Prerequisites

### Required External Tools

1. **ccusage** - Claude Code usage tracking CLI
   ```bash
   npm install -g @anthropics/ccusage
   ```

2. **ccusage-codex** - Codex usage tracking CLI
   ```bash
   npm install -g codex-usage-cli
   ```

3. **Git Configuration** - Must have git user.email or user.name configured
   ```bash
   git config user.email "your.email@example.com"
   git config user.name "Your Name"
   ```

## Installation

### 1. Install Package Dependencies

The project uses UV for package management:

```bash
# Install with UV
uv pip install -e .
```

This installs:
- Hermod CLI (`hermod` command)
- All dependencies (typer, rich, etc.)

### 2. Verify Installation

Check that hermod is available:

```bash
hermod --version
```

### 3. Verify Dependencies

Test that external dependencies are installed:

```bash
hermod collect  # Will error with helpful message if dependencies missing
```

## Configuration

### Developer Name Mapping

Hermod uses `config/developer_names.json` to map git emails/names to canonical developer names:

```json
{
  "email_to_canonical": {
    "chad@degreeanalytics.com": "Chad",
    "jeremiah@degreeanalytics.com": "Jeremiah"
  },
  "name_to_canonical": {
    "chad walters": "Chad",
    "jeremiah moses": "Jeremiah"
  }
}
```

**To add your mapping:**
1. Find your git email: `git config user.email`
2. Add mapping to `config/developer_names.json`
3. Commit the change so team members are mapped consistently

### Auto-Detection Fallback

If no mapping found, Hermod falls back to:
1. Git user.email username (before @ sign)
2. Git user.name

## Usage

### CLI Commands

#### Basic Collection (Auto-Detect Developer)

```bash
hermod collect
```

Auto-detects developer from git config and collects last 7 days.

#### Specify Developer

```bash
hermod collect --developer Chad
```

#### Custom Time Period

```bash
hermod collect --days 14
```

#### JSON Output (for automation)

```bash
hermod collect --json
```

#### All Options

```bash
hermod collect --developer Jeremiah --days 30 --json
```

### Justfile Commands

The project provides convenient justfile commands:

#### Auto-Detection

```bash
just ai-usage collect
```

#### With Developer

```bash
just ai-usage collect Chad 7
```

#### Complete Pipeline (collect → ingest → charts)

```bash
just ai-usage pipeline
just ai-usage pipeline Jeremiah 14
```

## Output

### File Structure

Usage data is saved to:

```
data/ai_usage/submissions/
  ai_usage_{developer}_{date}_{timestamp}.json
```

Example: `ai_usage_Chad_20251022_20251022_114155.json`

### JSON Format

```json
{
  "metadata": {
    "developer": "Chad",
    "collected_at": "2025-10-22T11:41:55.123456",
    "date_range": {
      "start": "2025-10-15",
      "end": "2025-10-22",
      "days": 7
    },
    "version": "1.0"
  },
  "claude_code": {
    "daily": [...],
    "totals": {
      "totalCost": 334.09,
      "totalTokens": 12500000
    }
  },
  "codex": {
    "daily": [...],
    "totals": {
      "totalCost": 50.25,
      "totalTokens": 2500000
    }
  }
}
```

### Terminal Output

When not using `--json`, Hermod displays:

```
✓ Successfully collected usage data for Chad
Date range: 2025-10-15 to 2025-10-22
Output file: data/ai_usage/submissions/ai_usage_Chad_20251022_20251022_114155.json

       Usage Summary
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Tool        ┃ Total Cost ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ Claude Code │ $334.09    │
│ Codex       │ $50.25     │
│ Total       │ $384.34    │
└─────────────┴────────────┘
```

## Integration Workflow

### Manual Submission (Phase 1)

1. **Collect**: Run `just ai-usage collect` weekly
2. **Share**: Send generated JSON file to team lead
3. **Ingest**: Team lead runs `just ai-usage ingest` to deduplicate and merge
4. **Visualize**: Generate charts with `just ai-usage charts`

### Future: Automated Submission (Phase 2)

Future versions will support:
- Direct submission to central API
- Automatic weekly collection
- Real-time cost dashboards
- Team-wide analytics

## Troubleshooting

### "Dependencies not installed"

```bash
# Install missing tools
npm install -g @anthropics/ccusage
npm install -g codex-usage-cli
```

### "Git user.email not configured"

```bash
git config user.email "your.email@example.com"
```

### "Failed to detect developer"

Add your email/name mapping to `config/developer_names.json`:

```json
{
  "email_to_canonical": {
    "your.email@example.com": "YourName"
  }
}
```

### No Usage Data Returned

- Verify ccusage/ccusage-codex are working: `ccusage daily --json`
- Check time period has activity: adjust `--days` parameter
- Ensure tools are configured for your user

## Development

### Running Tests

```bash
# All hermod tests
pytest tests/hermod/ -v

# Specific test files
pytest tests/hermod/test_cli.py -v
pytest tests/hermod/test_git_detector.py -v
pytest tests/hermod/test_collector.py -v
```

### Package Structure

```
src/hermod/
  __init__.py           # Package metadata
  cli.py               # Typer CLI interface
  collector.py         # Usage data collection
  dependencies.py      # External dependency checking
  git_detector.py      # Developer auto-detection

tests/hermod/
  test_cli.py          # CLI integration tests
  test_collector.py    # Collection logic tests
  test_dependencies.py # Dependency checker tests
  test_git_detector.py # Git detection tests
```

### Adding New Features

1. Write failing tests (TDD)
2. Implement minimal code to pass
3. Commit changes
4. Update documentation

## FAQ

### Why separate from main metrics?

Hermod is intentionally standalone:
- No dependency on Linear/GitHub APIs
- Simple, focused functionality
- Easy to package and distribute
- Can be used in any project

### Why manual submission (Phase 1)?

Phase 1 focuses on:
- Establishing collection patterns
- Validating data structure
- Building team habits
- Privacy and transparency

Phase 2 will add automation once patterns are proven.

### What about privacy?

All data:
- Stays on your machine until you share
- You control when to submit
- Team lead handles aggregation
- No automatic transmission

### Can I use this without the main framework?

Yes! Hermod is standalone:

```bash
# Just install hermod dependencies
pip install typer rich

# Use directly
python -m hermod.cli collect
```

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review test files for usage examples
3. Open issue in project repository
4. Ask team lead for assistance
