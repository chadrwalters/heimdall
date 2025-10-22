# Heimdall Documentation Hub

## Purpose
Central navigation hub for Heimdall - a comprehensive engineering observability framework for tracking developer productivity across organizations.

## When to Use This
- Finding specific documentation quickly
- Understanding chart generation and workflows
- Onboarding new team members
- Setting up data extraction and visualization

**Keywords:** navigation, index, documentation map, getting started, heimdall, engineering observability

Welcome to the comprehensive documentation hub for **Heimdall** - named after the all-seeing Norse god, Heimdall provides complete visibility into engineering metrics and team activity through commits and pull requests.

**🏗️ Current Status**: Production-ready engineering observability framework
**📅 Last Updated**: 2025-10-22
**🔧 Latest Updates**: Rebranded to Heimdall, focus on comprehensive observability

---

## 🚀 Quick Start Paths

Choose your path based on your role and immediate needs:

| Role | Primary Goal | Start Here | Time to Productive |
|------|-------------|------------|-------------------|
| **Engineering Manager** | Track team activity and velocity | [Chart Documentation](../CHARTS_README.md) | 10 minutes |
| **Developer** | Set up and run extraction | [Setup Guide](./setup-guide.md) | 15 minutes |
| **Team Lead** | Generate weekly/monthly reports | [Chart Documentation](../CHARTS_README.md) | 10 minutes |
| **DevOps Engineer** | Automate data extraction | [Setup Guide](./setup-guide.md) | 20 minutes |
| **New Team Member** | Understand the system | [README](../README.md) | 10 minutes |

---

## 📚 Core Documentation

### Getting Started
- **[README](../README.md)** - Main project overview and quick start ⭐
- **[CHARTS_README](../CHARTS_README.md)** - Chart generation and interpretation ⭐
- **[Setup Guide](./setup-guide.md)** - Environment configuration and API setup
- **[Configuration Reference](./configuration-reference.md)** - Configuration options and settings

### Usage & Workflows
- **[Usage Guide](./usage-guide.md)** - Practical usage examples and workflows
- **[Validation Procedures](./validation-procedures.md)** - Testing and validation
- **[Linear Integration Summary](./linear-integration-summary.md)** - Optional Linear ticket correlation

### Development
- **[Justfile Usage](./justfile-usage.md)** - Command reference and automation
- **[Justfile Implementation](./justfile-implementation.md)** - Command implementation details

---

## 🎯 Key Workflows

### Data Extraction
```bash
# Setup and verify
just setup
just env-check
just verify-apis

# Extract data (30 days)
uv run python -m git_extraction.cli --org your-org --days 30
```

### Chart Generation
```bash
# Generate all 12 charts
uv run python scripts/generate_metrics_charts.py \
  --commits src/org_commits.csv \
  --prs src/org_prs.csv \
  --output charts
```

### Testing
```bash
just test                   # Run all tests
just test-unit             # Quick unit tests
just test-integration      # API integration tests
```

---

## 📊 What This System Does

### Core Capabilities
- **Data Extraction**: Pull commits and PRs from GitHub organization
- **Branch Tracking**: Filter to main/dev branch activity only
- **Developer Attribution**: Unify developer names across git/GitHub/Linear
- **Visualization**: Generate 12 time-series charts showing team activity

### Generated Outputs
- **Commit Charts**: Daily/weekly commit counts and lines changed
- **PR Charts**: Daily/weekly PR counts and lines changed
- **CSV Data**: Raw extracted data for custom analysis
- **High-Res Charts**: 300 DPI PNG files for presentations

---

## ⚙️ Configuration

### Required Environment Variables
```bash
# GitHub API access (required)
GITHUB_TOKEN=your_github_token_here

# Linear integration (optional)
LINEAR_API_KEY=your_linear_api_key_here
```

### Developer Name Unification
Configure `config/developer_names.json` to map developer identities:
```json
{
  "developers": [
    {
      "canonical_name": "Developer Name",
      "git_names": ["git_name_1", "git_name_2"],
      "github_handle": "github_handle"
    }
  ]
}
```

---

## 🔍 Troubleshooting

### Common Issues
- **Setup Problems**: Run `just env-check` and `just verify-apis`
- **API Issues**: Verify GitHub token has organization access
- **Missing Data**: Check repository permissions
- **Chart Errors**: Verify CSV file format and content

### Getting Help
- **Environment Check**: `just env-check`
- **API Verification**: `just verify-apis`
- **System Health**: Check logs with `just logs` (if available)

---

## 📈 System Features

### Performance
- **Git-Based Extraction**: 85-90% reduction in API calls
- **Intelligent Caching**: Faster repeated extractions
- **Local Processing**: No external AI services required
- **Scales**: Handles 100+ repositories

### Key Features
- **Branch Tracking**: Shows only work merged to main/dev
- **Developer Unification**: Consistent attribution across sources
- **Flexible Timeframes**: Extract any date range (7, 30, 90+ days)
- **High-Quality Output**: 300 DPI charts for presentations

---

## 🔗 External Resources

### API Documentation
- **[GitHub API](https://docs.github.com/en/rest)** - GitHub REST API reference
- **[Linear API](https://developers.linear.app/docs/graphql/working-with-the-graphql-api)** - Linear GraphQL API guide

### Framework Dependencies
- **[Just Command Runner](https://github.com/casey/just)** - Command automation tool
- **[UV Package Manager](https://github.com/astral-sh/uv)** - Fast Python package manager

---

**🚀 Ready to get started?** Jump to the [README](../README.md) or [CHARTS_README](../CHARTS_README.md) to begin!
