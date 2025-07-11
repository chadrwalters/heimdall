# 🚀 North Star Metrics - Quick Start Guide

Welcome to North Star Metrics! This guide will get you up and running in 5 minutes.

## 📋 Prerequisites

1. **Install Just** (our command runner):
   ```bash
   brew install just    # macOS
   ```

2. **Install Other Tools**:
   - Python 3.12+
   - UV package manager
   - GitHub CLI (`gh`)

## 🔧 Setup (2 minutes)

1. **Clone and Setup**:
   ```bash
   git clone <repo-url>
   cd metrics
   just setup
   ```

2. **Configure API Keys**:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys:
   # - GITHUB_TOKEN
   # - LINEAR_API_KEY  
   # - ANTHROPIC_API_KEY
   ```

3. **Verify Everything Works**:
   ```bash
   just env-check      # Check environment
   just verify-apis    # Test API connections
   ```

## 🎯 Run Your First Analysis

```bash
just pilot your-org-name
```

This will:
1. Extract 7 days of GitHub data from your organization
2. Run AI analysis on all PRs and commits
3. Generate CSV reports with insights

## 📊 View Results

Check these files after the pilot completes:
- `org_prs.csv` - Pull request data
- `org_commits.csv` - Commit data  
- `unified_pilot_data.csv` - AI-enriched analysis

## 🔍 What's Next?

```bash
just               # See all available commands
just help-workflows # Learn common workflows
just next          # Start working on development tasks
```

## 🆘 Need Help?

- Run `just` to see all commands
- Check `docs/` directory for detailed documentation
- Use `just env-check` to diagnose setup issues

---

**Remember**: Always use `just` commands for all project interactions!