# Changelog - Metrics Simplification

## Version 2.1 - Hermod AI Usage Tracking (2025-10-22)

### 🤖 New Feature: Hermod

**Hermod** is a new standalone CLI tool for tracking AI assistant usage across development teams.

#### Features Added
- ✅ **Auto-Detection**: Automatically detects developer from git configuration
- ✅ **Dual Collection**: Collects usage from both Claude Code (ccusage) and Codex (ccusage-codex)
- ✅ **Flexible Time Ranges**: Configurable collection period (default: 7 days)
- ✅ **Multiple Output Formats**: Rich terminal tables or JSON for automation
- ✅ **Justfile Integration**: Seamless integration with existing dispatcher pattern
- ✅ **Privacy-First**: Manual submission model - developers control their data

#### Implementation Details
- **Package Structure**: `src/hermod/` with modular components
  - `cli.py` - Typer-based CLI interface with Rich output
  - `collector.py` - Usage data collection from external tools
  - `dependencies.py` - External dependency checking
  - `git_detector.py` - Developer auto-detection from git config
- **Test Coverage**: 23 comprehensive tests (16 unit + 7 integration)
- **Documentation**: Complete installation and usage guide in `docs/hermod-installation.md`

#### Usage Examples
```bash
# Auto-detect developer and collect usage
just ai-usage collect

# Specify developer and time period
just ai-usage collect Chad 14

# Complete pipeline (collect → ingest → charts)
just ai-usage pipeline
```

#### Justfile Commands
- `just ai-usage collect [developer] [days=7]` - Collect usage data
- `just ai-usage ingest` - Ingest submissions with deduplication
- `just ai-usage charts [output=charts]` - Generate cost/token charts
- `just ai-usage pipeline [dev] [days=7]` - Complete workflow

#### Files Added
- `src/hermod/__init__.py` - Package initialization
- `src/hermod/cli.py` - CLI implementation
- `src/hermod/collector.py` - Data collection logic
- `src/hermod/dependencies.py` - Dependency checking
- `src/hermod/git_detector.py` - Developer auto-detection
- `tests/hermod/test_cli.py` - CLI tests (4 tests)
- `tests/hermod/test_collector.py` - Collector tests (3 tests)
- `tests/hermod/test_dependencies.py` - Dependency tests (4 tests)
- `tests/hermod/test_git_detector.py` - Git detection tests (5 tests)
- `tests/integration/test_hermod_e2e.py` - Integration tests (8 tests)
- `docs/hermod-installation.md` - Complete documentation

#### Dependencies Added
- `typer>=0.12.3` - CLI framework
- `rich>=13.7.0` - Terminal formatting

#### Documentation Updates
- Added Hermod section to README.md
- Created comprehensive installation guide
- Updated justfile help text

---

## Version 2.0 - Metrics-Only System (2025-10-22)

### 🎯 Major Changes

**System Transformation**: Simplified from AI-powered analysis platform to focused metrics visualization system.

### ✨ New Features

#### Data Extraction
- ✅ **Branch Tracking**: Added `on_main_branch` field to filter commits merged to main/dev branches
- ✅ **Developer Name Unification**: Config-based system (`config/developer_names.json`) maps git names, GitHub handles, and Linear names to canonical names
- ✅ **Deduplication**: Prevents duplicate commits in extracted data

#### Visualization
- ✅ **12 Production Charts**: Complete set of daily/weekly commit and PR visualizations
  - Commit charts: daily/weekly count (stacked & cumulative) and size (cumulative)
  - PR charts: daily/weekly count (stacked & cumulative) and size (cumulative)
- ✅ **High-Resolution Output**: 300 DPI PNG charts for presentations
- ✅ **Developer Attribution**: Consistent color coding across all charts

#### Automation
- ✅ **Daily Update Script**: `scripts/daily_update.sh` for automated extraction and chart generation
- ✅ **Comprehensive Documentation**: `AUTOMATION.md` with cron examples and best practices

### 📝 Documentation Updates

#### New Documentation
- ✅ `CHARTS_README.md` - Complete chart generation and interpretation guide
- ✅ `AUTOMATION.md` - Automation setup with cron examples
- ✅ `CHANGELOG.md` - This changelog

#### Updated Documentation
- ✅ `README.md` - Completely rewritten to reflect metrics-only system
- ✅ `docs/INDEX.md` - Simplified documentation hub
- ✅ `pyproject.toml` - Removed AI dependencies

### 🗑️ Removed Features

#### AI Analysis (Removed)
- ❌ Anthropic Claude integration
- ❌ Complexity scoring (1-10 scale)
- ❌ Risk assessment
- ❌ Clarity metrics
- ❌ Impact scoring (40% complexity + 50% risk + 10% clarity)
- ❌ Work type classification (Feature, Bug Fix, Refactor, etc.)
- ❌ AI assistance detection

#### Removed Files
- ❌ `src/analysis/` directory (entire AI analysis engine)
- ❌ `src/config/analysis_config.py`
- ❌ `src/exceptions/analysis_exceptions.py`
- ❌ `docs/ai-detection-methodology.md`
- ❌ Related test files for AI analysis

#### Removed Dependencies
- ❌ `anthropic>=0.40.0` - AI analysis library

### 🔧 Technical Improvements

#### Performance
- ✅ Git-based extraction maintains 85-90% API call reduction
- ✅ Intelligent caching system (753 MB cache, 97 repos)
- ✅ Fast chart generation (5-10 seconds for all 12 charts)

#### Data Quality
- ✅ CSV outputs with proper structure
- ✅ Branch tracking for accurate metrics
- ✅ Developer name unification for consistency

### 📊 What This System Now Does

**Focus**: Simple, production-ready metrics tracking

**Capabilities**:
1. Extract commits and PRs from GitHub organization
2. Filter to main/dev branch activity only
3. Unify developer names across sources
4. Generate 12 time-series visualization charts

**Use Cases**:
- Weekly team reviews
- Monthly progress reports
- Sprint retrospectives
- Stakeholder updates

### 🚀 Workflows

#### Quick Start
```bash
# Extract last 30 days
uv run python -m git_extraction.cli --org your-org --days 30

# Generate charts
uv run python scripts/generate_metrics_charts.py \
  --commits src/org_commits.csv \
  --prs src/org_prs.csv \
  --output charts
```

#### Automation
```bash
# Manual run
ORGANIZATION_NAME=your-org ./scripts/daily_update.sh

# Cron (daily at 6 AM)
0 6 * * * cd /path/to/project && ORGANIZATION_NAME=org ./scripts/daily_update.sh
```

### 📈 Validation Results

**System Status**: All components operational ✅

**Test Results**:
- Data Extraction: Working (97 repos, 294-day range)
- Branch Tracking: Functional (`on_main_branch` field)
- Chart Generation: Complete (12/12 charts)
- Developer Unification: Configured
- API Integration: GitHub ✅ Linear ✅

**Performance**:
- Cache: 753 MB (97 repos)
- API efficiency: 85-90% reduction
- Rate limit: 215/5000 used (4%)

### 🔄 Migration Notes

**For Existing Users**:

1. **Configuration**: Add developer name mapping in `config/developer_names.json`
2. **Dependencies**: Run `uv sync` to update dependencies (removes anthropic)
3. **Extraction**: Re-run extraction to get `on_main_branch` field
4. **Charts**: Use new chart generation script

**Breaking Changes**:
- AI analysis features removed (no migration path)
- Impact scores no longer generated
- Work type classification no longer available
- `analysis_results.csv` no longer generated
- `developer_metrics.csv` structure changed

### 📚 Documentation

- [README.md](README.md) - Main project overview
- [CHARTS_README.md](CHARTS_README.md) - Chart documentation
- [AUTOMATION.md](AUTOMATION.md) - Automation guide
- [docs/INDEX.md](docs/INDEX.md) - Documentation hub

### 🎯 Next Steps

**Recommended**:
1. Configure developer name mapping
2. Run extraction for desired time period
3. Generate charts and review metrics
4. Set up daily automation if desired

**Future Enhancements** (Potential):
- Dashboard web interface
- Additional chart types
- Export to other formats (PDF, CSV summaries)
- Integration with other project management tools

---

## Version 1.x - AI-Powered Analysis (Deprecated)

Previous version included comprehensive AI-powered analysis with Claude integration.
See git history for details.
