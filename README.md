# North Star Metrics

Engineering Impact Framework for data-driven visibility into development work across the organization.

## Overview

Project North Star is a comprehensive framework designed to provide data-driven visibility into development work. It analyzes commits and pull requests across all organization repositories, using AI to classify work types and measure impact, with special focus on understanding how AI tools are transforming development velocity and quality.

## 🚀 Quick Start

**➡️ New to the project? Start with our [5-minute Quick Start Guide](QUICKSTART.md)!**

This project uses [Just](https://github.com/casey/just) as the command runner. All interactions should go through the Justfile for consistency and ease of use.

### Prerequisites

- Python 3.11+
- [Just](https://github.com/casey/just) command runner
- UV package manager
- GitHub CLI (`gh`) authenticated
- Git

### Install Just

```bash
# macOS
brew install just

# Linux
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to /usr/local/bin
```

### Setup Project

```bash
# Clone the repository
git clone <repo-url>
cd metrics

# Run initial setup
just setup

# Check environment status
just env-check

# Verify API connections
just verify-apis
```

### Configure Environment

Create a `.env` file with your API keys:

```bash
GITHUB_TOKEN=your_github_token
LINEAR_API_KEY=your_linear_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

## 📋 Core Commands

**Always use `just` commands for all interactions with the project.**

### See Available Commands

```bash
just
```

### Common Workflows

```bash
# Run a 7-day pilot analysis
just pilot your-org-name

# Run full pipeline (30 days)
just pipeline your-org-name 30

# Extract data only
just extract your-org-name 7

# Run analysis on existing data
just analyze

# Use the main pipeline script directly
python main.py --org your-org-name --mode pilot
python main.py --org your-org-name --mode incremental
python main.py --org your-org-name --mode full --days 30

# Show next task to work on
just next
```

### Task Management

```bash
# Show next task
just task-next

# Start working on a task
just task-start 6

# Complete a task
just task-done 6

# Show task progress
just task-progress

# Show today's progress
just today
```

### Testing

```bash
# Run all tests
just test

# Run specific test suites
just test-unit
just test-integration
just test-linear
just test-gh-analyzer
```

### Development

```bash
# Run code quality checks
just quality

# Format code
just format

# Run linting
just lint

# Watch for changes and run tests
just watch

# Show project statistics
just stats
```

## 🔧 Key Features

### 1. Multi-Repository Analysis
- Analyzes ALL active repositories in your organization
- Dual-channel processing (PRs and commits)
- Deduplication logic to prevent double-counting

### 2. AI-Powered Classification
- Work type categorization (Feature, Bug Fix, Refactor, etc.)
- Complexity, risk, and clarity scoring (1-10 scale)
- Impact score calculation
- AI-assistance detection (Copilot, Claude, Cursor)

### 3. Linear Integration
- Automatic ticket extraction from PR titles/bodies
- Process compliance tracking
- Team-level metrics aggregation

### 4. GitHub Actions Bot
- Real-time PR analysis
- Automatic commenting with scores
- Label application based on analysis

### 5. Unified Output
- Comprehensive CSV format
- Incremental update support
- State management for efficient processing

### 6. Comprehensive Execution Pipeline
- Main execution script with full orchestration
- Error recovery with checkpoint system
- Comprehensive logging and monitoring
- Scheduled execution support (cron/GitHub Actions)

## 📁 Project Structure

```
metrics/
├── main.py               # Main execution script (NEW!)
├── justfile              # All commands (START HERE!)
├── src/                  # Core source code
│   ├── analysis/         # AI analysis engine
│   ├── config/           # Configuration management
│   ├── data/             # Data processing components
│   └── linear/           # Linear API integration
├── scripts/              # Utility scripts
│   ├── extraction/       # GitHub data extraction
│   ├── schedule_analysis.sh  # Cron scheduling script
│   └── *.py              # Various tools
├── tests/                # Test suite
├── docs/                 # Documentation
├── config/               # Configuration files
│   ├── ai_developers.json # AI developer overrides
│   └── analysis_state.json # Processing state
└── .github/workflows/    # GitHub Actions
```

## 🎯 Common Use Cases

### Running a Pilot Study

```bash
# 1. Check your setup
just env-check

# 2. Verify APIs are working
just verify-apis

# 3. Run the pilot
just pilot your-org-name

# 4. Review results in CSV files
```

### Daily Development Workflow

```bash
# 1. Check today's progress
just today

# 2. Get next task
just next

# 3. Start working
just start-next

# 4. Run tests while developing
just watch

# 5. Check code quality
just quality

# 6. Complete the task
just task-done <task-id>
```

### Testing Changes

```bash
# Run all tests
just test

# Test specific component
just test-linear
just test-analysis

# Test PR bot locally
just test-pr-bot 123
```

## 📚 Documentation

All documentation is in the `docs/` directory:

```bash
# List all documentation
just docs-list

# Serve documentation locally
just docs-serve
```

Key documents:
- [Justfile Usage Guide](docs/justfile-usage.md) - Detailed command reference
- [Linear Integration](docs/linear-integration-summary.md) - Linear API details
- [GitHub Actions Bot](docs/github-actions-bot-summary.md) - PR analysis bot

## 🛠️ Advanced Usage

### Environment Variables

Check environment status:
```bash
just env-check
```

Required variables:
- `GITHUB_TOKEN` - GitHub personal access token
- `LINEAR_API_KEY` or `LINEAR_TOKEN` - Linear API key  
- `ANTHROPIC_API_KEY` - Anthropic API key

### Incremental Updates

After initial extraction, run incremental updates:
```bash
just extract-incremental your-org-name
```

### Custom Time Periods

Extract specific date ranges:
```bash
just extract your-org-name 30  # Last 30 days
just extract your-org-name 90  # Last 90 days
```

## 🤝 Contributing

1. Always use `just` commands for consistency
2. Run `just quality` before committing
3. Add new commands to the Justfile for repeated tasks
4. Document new features in the `docs/` directory

## 📊 Metrics and Output

The system generates several CSV files:

- `org_commits.csv` - Raw commit data
- `org_prs.csv` - Pull request metadata
- `unified_pilot_data.csv` - Enriched analysis output
- `developer_metrics.csv` - Developer-level aggregations

Each record includes:
- Work classification and scores
- AI-assistance detection
- Linear ticket linkage
- Impact metrics

## 🚨 Troubleshooting

```bash
# Check environment setup
just env-check

# Verify API connections
just verify-apis

# Run tests
just test

# Clean generated files
just clean
```

## 📝 License

[License information here]

---

**Remember: Always use `just` commands!** Type `just` to see all available commands.
