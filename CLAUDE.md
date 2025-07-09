# 🌟 North Star Metrics - Engineering Impact Analytics

<!-- Auto-attached modular components -->
@docs/claude-components/safety-rules.md
@docs/claude-components/justfile-workflow.md
@docs/claude-components/verification-standards.md
@docs/claude-components/metrics-analysis-guide.md
@docs/claude-components/github-linear-workflow.md

## 🎯 PROJECT OVERVIEW

**North Star Metrics** is a comprehensive framework for tracking and analyzing engineering impact across organizations. It provides data-driven visibility into development work by analyzing commits and pull requests using AI to classify work types and measure impact.

### Core Capabilities
- **Multi-Repository Analysis**: Analyzes ALL active repositories in an organization
- **AI-Powered Classification**: Automatic work type categorization with complexity/risk scoring
- **Linear Integration**: Correlates code changes with planned work tickets
- **Impact Measurement**: Weighted scoring system for engineering contributions
- **Process Insights**: Identifies workflow improvement opportunities

## 📍 CRITICAL RESOURCE REFERENCES

```
┌─────────────────────────────────────────────────────┐
│ 📍 ESSENTIAL NAVIGATION                               │
├─────────────────────────────────────────────────────┤
│ • justfile - All standardized commands              │
│ • docs/INDEX.md - Complete documentation hub        │
│ • docs/setup/quick-start.md - Getting started       │
│ • docs/workflows/analysis-pipeline.md - Main flow   │
│ • docs/troubleshooting/ - Common issues & solutions │
│ • config/ - Configuration management                │
└─────────────────────────────────────────────────────┘
```

## 🚀 QUICK START WORKFLOWS

### First Time Setup
```bash
just setup                    # Initialize environment
just env-check                # Verify configuration
just verify-apis              # Test API connections
```

### Standard Analysis Workflow
```bash
just pilot your-org-name      # 7-day pilot analysis
just pipeline your-org-name 30  # Full 30-day analysis
just analyze results.csv      # Process extracted data
```

### Development Workflow
```bash
just test                     # Run all tests
just test-unit               # Quick unit tests
just test-integration        # API integration tests
```

## 🔍 ANALYSIS INTERPRETATION

### Impact Score System (1-10 scale)
- **Formula**: 40% complexity + 50% risk + 10% clarity
- **1-3**: Low impact (minor changes, bug fixes)
- **4-6**: Moderate impact (feature work, refactoring)
- **7-8**: High impact (major features, architecture)
- **9-10**: Critical impact (foundational changes)

### Work Type Categories
- **New Feature**: Net new functionality
- **Bug Fix**: Correcting existing issues  
- **Refactor**: Code improvement without feature changes
- **Testing**: Test additions or improvements
- **Documentation**: Documentation updates
- **Chore**: Maintenance tasks, dependency updates

## 📊 KEY OUTPUTS

### Generated Reports
- **Unified Analysis**: `analysis_results.csv` - All repositories combined
- **Developer Metrics**: `developer_metrics.csv` - Individual contributor analysis
- **Process Compliance**: Linear ticket correlation rates
- **Impact Distribution**: Work type and complexity analysis

### Monitoring Dashboards
- **API Health**: Connection status for GitHub/Linear/Anthropic
- **Data Quality**: Extraction completeness and accuracy
- **Analysis Performance**: Processing speed and success rates
- **Usage Patterns**: Organization-wide adoption metrics

## 🎯 OPTIMIZATION FOCUS AREAS

### Process Improvements
- **Ticket Discipline**: Improve GitHub ↔ Linear correlation
- **Impact Visibility**: Surface high-impact engineering work
- **Team Insights**: Understand work distribution patterns
- **Quality Metrics**: Track code complexity and risk trends

### Technical Enhancements
- **Analysis Accuracy**: Continuously improve AI classifications
- **Performance**: Optimize for large-scale organizational analysis
- **Integration**: Expand Linear and GitHub integration capabilities
- **Automation**: Reduce manual intervention in analysis pipeline

## 🔄 CONTINUOUS IMPROVEMENT

### Regular Analysis Cadence
- **Weekly**: Health checks with pilot analysis
- **Monthly**: Full pipeline analysis for trends
- **Quarterly**: Historical analysis for strategic planning
- **Ad-hoc**: Project-specific analysis for decisions

### Feedback Integration
- **Classification Review**: Validate AI work type assignments
- **Threshold Tuning**: Calibrate impact scoring for context
- **Scope Expansion**: Add repositories as they become relevant
- **Process Refinement**: Improve ticket correlation workflows

---

## 🎮 DEVELOPMENT CONTEXT

### Architecture Overview
- **src/analysis/**: Core AI analysis engine
- **src/data/**: Data processing and metrics aggregation
- **src/linear/**: Linear API integration and ticket matching
- **scripts/**: Automation and testing utilities
- **docs/**: Comprehensive documentation and guides

### Testing Philosophy
- **Unit Tests**: Core logic validation
- **Integration Tests**: API connectivity and data flow
- **End-to-End Tests**: Complete workflow validation
- **Performance Tests**: Large-scale processing validation

### Key Dependencies
- **Anthropic Claude**: AI analysis and classification
- **GitHub API**: Repository and PR data extraction
- **Linear API**: Ticket correlation and process insights
- **Python Ecosystem**: FastAPI, Pandas, asyncio for processing

---

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing existing files to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.