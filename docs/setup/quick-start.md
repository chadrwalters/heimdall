# Quick Start Guide

## Overview
Get the North Star Metrics framework running in under 15 minutes with this streamlined setup guide.

## Prerequisites
- Python 3.11+ installed
- Git configured
- API access to GitHub, Linear, and Anthropic Claude

## Step 1: Clone and Setup Environment

```bash
# Clone the repository
git clone https://github.com/your-org/heimdall.git
cd heimdall

# Setup Python environment and dependencies (includes GitPython)
just setup
```

**What this installs:**
- Python virtual environment (`.venv/`)
- Core dependencies including GitPython for git-based extraction
- Analysis engine and API integration libraries
- Testing and development tools

## Step 2: Configure API Keys

Create a `.env` file with your API credentials:

```bash
# Required API Keys
GITHUB_TOKEN=ghp_your_github_token_here
LINEAR_API_KEY=lin_your_linear_api_key_here
ANTHROPIC_API_KEY=sk-ant-your_anthropic_key_here

# Optional Configuration
ORGANIZATION_NAME=your-org-name
DEFAULT_ANALYSIS_DAYS=30
```

## Step 3: Verify Setup

```bash
# Check environment status
just env-check

# Test API connections
just verify-apis
```

Expected output:
```
✅ Environment Variables Status:
GitHub Token: ✅ Set
Linear API Key: ✅ Set
Anthropic API Key: ✅ Set

✅ API Verification:
GitHub API: ✅ Connected
Linear API: ✅ Connected
Anthropic API: ✅ Connected
```

## Step 4: Run Your First Analysis

```bash
# Run a 7-day pilot analysis
just pilot your-organization-name
```

This will:
- Clone repositories locally using git-based extraction (85-90% fewer API calls)
- Extract 7 days of PR and commit data from local git repositories
- Analyze code changes with AI
- Generate impact metrics
- Create sample reports

**Git-Based Architecture Benefits:**
- Dramatically reduced GitHub API usage
- Faster extraction after initial repository clone
- Offline analysis capability
- Incremental processing for efficiency

## Step 5: View Results

The analysis generates CSV files in the current directory:
- `analysis_results.csv` - Main analysis output
- `developer_metrics.csv` - Individual contributor metrics

## Next Steps

### Run Full Analysis
```bash
# Extract and analyze 30 days of data
just pipeline your-organization-name 30
```

### Explore Documentation
- **[Configuration Reference](../configuration-reference.md)** - Detailed setup options
- **[Analysis Guide](../claude-components/metrics-analysis-guide.md)** - Understanding results
- **[Usage Guide](../usage-guide.md)** - Common workflows

### Common Commands
```bash
just help                   # Show all available commands
just test                   # Run test suite
just extract org 30         # Extract 30 days of data (git-based)
just analyze data.csv       # Analyze specific dataset
just cache-status           # Check git and API cache status
just git-status             # Check git repository health
```

## Troubleshooting

### Common Issues
- **API Authentication**: Verify tokens have proper permissions
- **Rate Limiting**: Use incremental extraction for large organizations
- **Missing Data**: Check repository access permissions

### Get Help
- **[Troubleshooting Guide](../troubleshooting/common-problems.md)** - Common issues
- **[API Issues](../troubleshooting/api-issues.md)** - API-specific problems
- **[Documentation Hub](../INDEX.md)** - Complete documentation index

## Success Indicators

You're ready to go when:
- ✅ All API connections verified
- ✅ Pilot analysis completes successfully
- ✅ CSV reports generated with reasonable data
- ✅ Impact scores in expected range (1-10)

**Estimated Time**: 10-15 minutes from clone to first analysis results.