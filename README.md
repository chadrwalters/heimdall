# GitHub Metrics Visualization

**Simple, production-ready metrics tracking** for developer activity across your GitHub organization.

---

## 🚀 Quick Start

```bash
# Setup environment
just setup
just env-check
just verify-apis

# Extract last 30 days of data
just extract your-organization 30

# Generate visualizations
just generate-charts
```

**Generated Files:**
- **src/org_commits.csv**: All commits with branch tracking
- **src/org_prs.csv**: All merged pull requests
- **charts/*.png**: 12 time-series visualization charts

---

## 📊 What It Tracks

### Core Metrics
- **Commit Activity**: Daily and weekly commit counts by developer
- **Pull Requests**: Merged PR tracking and attribution
- **Lines Changed**: Code additions and deletions over time
- **Branch Tracking**: Shows only work merged to main/dev branches
- **Team Contributions**: Individual and team activity patterns

### Data Sources
- **GitHub API**: Repository and PR metadata
- **Git History**: Direct git analysis for commit details
- **Linear Integration**: Ticket correlation (optional)

---

## 📈 Generated Visualizations

The system generates **12 charts** showing different views of team activity:

### Commit Charts (6 charts)
- **commits_d_count_stacked.png** - Daily commits by developer (stacked area)
- **commits_d_count_cumulative.png** - Cumulative daily commits (line chart)
- **commits_d_size_cumulative.png** - Cumulative lines changed daily
- **commits_w_count_stacked.png** - Weekly commits by developer
- **commits_w_count_cumulative.png** - Cumulative weekly commits
- **commits_w_size_cumulative.png** - Cumulative lines changed weekly

### PR Charts (6 charts)
- **prs_d_count_stacked.png** - Daily PRs merged by developer (stacked area)
- **prs_d_count_cumulative.png** - Cumulative daily PRs (line chart)
- **prs_d_size_cumulative.png** - Cumulative lines changed in PRs daily
- **prs_w_count_stacked.png** - Weekly PRs merged by developer
- **prs_w_count_cumulative.png** - Cumulative weekly PRs
- **prs_w_size_cumulative.png** - Cumulative lines changed in PRs weekly

All charts are high-resolution PNG (300 DPI) ready for presentations and reports.

---

## 🎯 Use Cases

### Engineering Management
- **Team Velocity**: Track commit and PR volume trends
- **Activity Patterns**: Understand work distribution across team
- **Sprint Reviews**: Show delivered work in main/dev branches
- **Progress Tracking**: Cumulative charts for milestone reporting

### Team Dashboards
- **Weekly Reviews**: Generate charts for team meetings
- **Monthly Reports**: Track progress over longer periods
- **Contribution Visibility**: Surface individual contributions
- **Process Insights**: Understand delivery patterns

### Planning & Reporting
- **Historical Analysis**: Review past development activity
- **Capacity Planning**: Understand team output patterns
- **Stakeholder Updates**: Visual reports of development work
- **Trend Analysis**: Identify patterns and anomalies

---

## 🤖 AI Usage Tracking (Hermod)

**Hermod** is a standalone CLI tool for tracking AI assistant usage across your team. It collects usage data from Claude Code and Codex, helping teams understand AI adoption and costs.

### Quick Start

```bash
# Auto-detect developer from git and collect usage
just ai-usage collect

# Specify developer and time period
just ai-usage collect Chad 14

# Complete pipeline: collect → ingest → charts
just ai-usage pipeline
```

### Features

- **Auto-Detection**: Automatically detects developer from git configuration
- **Dual Collection**: Tracks both Claude Code (`ccusage`) and Codex (`ccusage-codex`)
- **Flexible Time Ranges**: Configure collection period (default: 7 days)
- **Privacy-First**: Manual submission model - you control your data
- **Rich Output**: Beautiful terminal tables or JSON for automation

### Output

Generates structured JSON files with usage metrics:

```json
{
  "metadata": {
    "developer": "Chad",
    "date_range": {"start": "2025-10-15", "end": "2025-10-22", "days": 7}
  },
  "claude_code": {"totals": {"totalCost": 334.09, "totalTokens": 12500000}},
  "codex": {"totals": {"totalCost": 50.25, "totalTokens": 2500000}}
}
```

### Workflow

1. **Collect**: Run weekly to gather usage data
2. **Submit**: Share JSON file with team lead (manual)
3. **Ingest**: Team lead consolidates submissions
4. **Visualize**: Generate cost and token usage charts

### Installation

```bash
# Install npm tools (prerequisites)
npm install -g @anthropics/ccusage
npm install -g codex-usage-cli

# Hermod is already installed with the project
hermod --version
```

📖 **Full Documentation**: [docs/hermod-installation.md](docs/hermod-installation.md)

---

## 🛠️ Development Workflows

### Data Extraction
```bash
# Weekly extraction
just extract your-org 7

# Monthly extraction
just extract your-org 30

# Custom time period
just extract your-org 90
```

### Chart Generation
```bash
# Generate all charts (default: src/org_commits.csv, src/org_prs.csv → charts/)
just generate-charts

# Specify custom files and output directory
just generate-charts commits=data/commits.csv prs=data/prs.csv output=weekly_reports
```

### Testing & Quality
```bash
# Complete test suite
just test

# Quick unit tests
just test-unit

# API integration tests
just test-integration

# Quality checks
just lint
```

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
The system automatically unifies developer identities using `config/developer_names.json`:

```json
{
  "developers": [
    {
      "canonical_name": "Chad Walters",
      "git_names": ["chadrwalters", "Chad Walters"],
      "github_handle": "chadrwalters"
    }
  ]
}
```

This ensures consistent attribution across all charts by mapping:
- Git commit author names
- GitHub pull request authors
- Linear ticket assignees (if using Linear integration)

---

## 🔍 Key Features

### Branch Tracking
Charts show **only main/dev branch activity**:
- ✅ Commits merged to main, master, dev, or develop
- ❌ Feature branch work not yet delivered

This provides a clean view of **actual shipped work**.

### Developer Attribution
- Automatic name unification across git/GitHub/Linear
- Consistent color coding per developer in charts
- Handles multiple git identities per person

### Performance Optimized
- Git-based extraction reduces API calls by 85-90%
- Intelligent caching for faster repeated extractions
- Local processing - no external services required

---

## 📚 Documentation

### Quick Reference
- **[CHARTS_README.md](CHARTS_README.md)** - Chart generation and interpretation
- **[Setup Guide](docs/setup-guide.md)** - Detailed environment setup
- **[Usage Guide](docs/usage-guide.md)** - Common workflows and patterns

### Advanced Topics
- **[Linear Integration](docs/linear-integration-summary.md)** - Optional ticket correlation
- **[AI Usage Tracking (Hermod)](docs/hermod-installation.md)** - Team AI usage collection and tracking
- **[Validation Procedures](docs/validation-procedures.md)** - Testing and quality assurance
- **[Configuration Reference](docs/configuration-reference.md)** - All configuration options

---

## 🤝 Contributing

### Development Setup
```bash
# Initial setup
just setup

# Verify environment
just env-check
just verify-apis

# Run tests
just test
```

### Development Workflow
1. **Setup Environment**: `just setup`
2. **Make Changes**: Follow existing patterns
3. **Test Changes**: `just test`
4. **Validate APIs**: `just test-integration`
5. **Submit Changes**: Create pull request

---

## 🔒 Security & Privacy

### Data Protection
- **API Key Security**: Keys never logged or exposed in outputs
- **Local Processing**: All analysis performed locally
- **Minimal Data Collection**: Only commit metadata and PR info
- **No Code Storage**: Repository content not permanently stored

### Privacy Considerations
- **Opt-in Analysis**: Explicit organization selection required
- **Configurable Scope**: Control which repositories are analyzed
- **Data Retention**: Local control over data lifecycle

---

## 📊 Performance

### Git-Based Extraction Benefits
- **85-90% API Reduction**: Dramatically reduced rate limiting
- **Faster Analysis**: Local git operations vs. API calls
- **Better Reliability**: No network dependencies for cached data
- **Cost Efficiency**: Reduced API usage

### Typical Performance
- **30-day extraction**: 2-5 minutes for 10-20 repositories
- **Chart generation**: 5-10 seconds for all 12 charts
- **Organization-wide**: Scales to 100+ repositories

---

## 🆘 Support

### Common Issues
- **Setup Problems**: See [Setup Guide](docs/setup-guide.md)
- **API Issues**: Run `just verify-apis` for diagnostics
- **Missing Data**: Verify organization access permissions
- **Chart Errors**: Check CSV file format and content

### Getting Help
- **Environment Check**: `just env-check`
- **API Verification**: `just verify-apis`
- **Documentation**: [CHARTS_README.md](CHARTS_README.md)

---

**🎯 Ready to start?** Run `just setup && just verify-apis` to begin tracking your team's development activity!
