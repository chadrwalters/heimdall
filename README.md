# GitHub Linear Metrics

**AI-powered developer productivity analysis platform** that integrates GitHub commit data with Linear ticket management for comprehensive development insights.

---

## 🚀 Quick Start

```bash
# Setup environment and verify APIs
just setup
just env-check
just verify-apis

# Run your first analysis
just pilot your-organization-name
```

**Generated Files:**
- **org_prs.csv**: Raw GitHub data extraction
- **analysis_results.csv**: AI-analyzed metrics with complexity/risk scores
- **developer_metrics.csv**: Individual contributor analysis

---

## 📊 What It Analyzes

### Core Metrics
- **Work Type Classification**: Feature, Bug Fix, Refactor, Testing, Documentation, Chore
- **Impact Scoring**: Complexity (40%) + Risk (50%) + Clarity (10%) = 1-10 scale
- **Linear Integration**: Correlates commits with Linear tickets for process compliance
- **Developer Productivity**: Individual and team contribution patterns

### AI-Powered Analysis
- **Commit Classification**: Automatically categorizes work types using Claude AI
- **Complexity Assessment**: Analyzes code changes for technical complexity
- **Risk Evaluation**: Identifies high-risk changes and technical debt
- **Quality Insights**: Code clarity and maintainability metrics

---

## 🎯 Use Cases

### Engineering Management
- **Team Productivity**: Track velocity and work distribution
- **Process Compliance**: Monitor GitHub ↔ Linear ticket correlation
- **Impact Visibility**: Surface high-value engineering contributions
- **Quality Trends**: Track code complexity and risk over time

### Individual Contributors
- **Personal Metrics**: Understand your development patterns
- **Impact Measurement**: Quantify technical contributions
- **Growth Tracking**: Monitor complexity and quality improvements

### Organizational Insights
- **Cross-Team Analysis**: Compare productivity patterns
- **Resource Allocation**: Data-driven planning and staffing
- **Process Optimization**: Identify workflow improvement opportunities

---

## 🛠️ Development Workflows

### Analysis Commands
```bash
# Quick 7-day analysis
just pilot organization-name

# Extended analysis
just pipeline organization-name 30

# Re-analyze existing data
just analyze organization-name existing_data.csv

# Generate comprehensive reports
just generate-reports analysis_results.csv
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
just quality-check
```

### System Management
```bash
# Health monitoring
just status
just health

# Cache management
just cache-status
just git-status

# Performance analysis
just extract-stats organization-name
```

---

## ⚙️ Configuration

### Required Environment Variables
```bash
# GitHub API access
GITHUB_TOKEN=your_github_token_here

# Linear integration
LINEAR_API_KEY=your_linear_api_key_here

# AI analysis
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional: default organization
ORGANIZATION_NAME=your-org-name
```

### Configuration Files
- **config/ai_developers.json**: AI developer identification patterns
- **config/analysis_state.json**: Analysis state tracking
- **config/schedule.conf**: Automated analysis scheduling

---

## 📈 Understanding Results

### Impact Score Scale (1-10)
- **1-3**: Low impact (minor changes, bug fixes)
- **4-6**: Moderate impact (feature work, refactoring)
- **7-8**: High impact (major features, architecture)
- **9-10**: Critical impact (foundational changes)

### Work Type Categories
- **New Feature**: Net new functionality development
- **Bug Fix**: Issue resolution and corrections
- **Refactor**: Code improvement without feature changes
- **Testing**: Test additions and improvements
- **Documentation**: Documentation updates and maintenance
- **Chore**: Dependency updates, tooling, maintenance

### Linear Integration Metrics
- **Ticket Correlation Rate**: Percentage of commits linked to Linear tickets
- **Process Compliance**: Adherence to planned work vs. ad-hoc changes
- **Sprint Alignment**: Actual work vs. sprint planning accuracy

---

## 🏗️ Architecture

### Core Components
- **Git-Based Extraction**: Revolutionary approach reducing API calls by 85-90%
- **AI Analysis Engine**: Claude-powered work classification and scoring
- **Linear Integration**: Automatic ticket correlation and process insights
- **Caching System**: Intelligent caching for performance optimization

### Technology Stack
- **Python 3.11+**: Core analysis engine
- **FastAPI**: REST API for integration and automation
- **Git**: Direct repository analysis for performance
- **Anthropic Claude**: AI-powered commit analysis
- **Linear API**: Ticket correlation and workflow insights

---

## 📚 Documentation

### Quick Navigation
- **📖 [Complete Documentation Hub](docs/INDEX.md)** - Navigate all documentation
- **🚀 [Setup Guide](docs/setup-guide.md)** - Detailed environment setup
- **📊 [Usage Guide](docs/usage-guide.md)** - Analysis workflows and interpretation
- **🔧 [Configuration Reference](docs/configuration-reference.md)** - Complete configuration options

### Specialized Guides
- **🤖 [AI Detection Methodology](docs/ai-detection-methodology.md)** - How AI classification works
- **🔗 [Linear Integration Summary](docs/linear-integration-summary.md)** - Linear API integration details
- **✅ [Validation Procedures](docs/validation-procedures.md)** - Testing and quality assurance

---

## 🤝 Contributing

### Development Setup
```bash
# Initial setup
just setup
just dev-setup

# Verify environment
just env-check
just verify-apis

# Run tests
just test
just quality-check
```

### Development Workflow
1. **Setup Environment**: `just setup && just dev-setup`
2. **Make Changes**: Follow existing patterns and conventions
3. **Test Changes**: `just test && just quality-check`
4. **Validate APIs**: `just test-integration`
5. **Submit Changes**: Create pull request with analysis validation

---

## 🔒 Security & Privacy

### Data Protection
- **API Key Security**: Keys never logged or exposed in outputs
- **Local Processing**: All analysis performed locally
- **Minimal Data Collection**: Only analyzes commit metadata and diffs
- **No Code Storage**: Repository content not permanently stored

### Privacy Considerations
- **Opt-in Analysis**: Explicit organization selection required
- **Configurable Scope**: Control which repositories are analyzed
- **Data Retention**: Local control over analysis data lifecycle

---

## 📊 Performance

### Git-Based Extraction Benefits
- **85-90% API Reduction**: Dramatically reduced rate limiting
- **Faster Analysis**: Local git operations vs. API calls
- **Better Reliability**: No network dependencies for cached data
- **Cost Efficiency**: Reduced API usage and infrastructure costs

### Benchmarking
```bash
# Performance analysis
just extract-stats organization-name
just benchmark-extraction organization-name

# Load testing
just test-load-quick
just test-load-full
```

---

## 🆘 Support

### Common Issues
- **Setup Problems**: See [Setup Guide](docs/setup-guide.md)
- **API Issues**: Run `just verify-apis` for diagnostics
- **Performance**: Check `just cache-status` and `just git-status`
- **Analysis Errors**: Review logs with `just logs` command

### Getting Help
- **Environment Check**: `just env-check`
- **System Health**: `just health`
- **Documentation**: [Complete Documentation Hub](docs/INDEX.md)
- **Troubleshooting**: [Validation Procedures](docs/validation-procedures.md)

---

**🎯 Ready to start?** Run `just setup` to begin analyzing your organization's developer productivity!