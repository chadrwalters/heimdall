# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║              GitHub Linear Metrics - Activity-Based Commands                ║
# ║                                                                              ║
# ║ 🎯 Focus: Extract data → Generate charts                                    ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
#
# 📖 QUICK START:
#   just env setup          - Initial environment setup
#   just env verify-apis    - Test API connections
#   just extract github <org> 30  - Extract GitHub data
#   just chart metrics commits.csv prs.csv  - Generate charts
#   just help               - Show all commands by activity
#
# 🔧 ACTIVITY NAMESPACES:
#   extract  - Data extraction (GitHub, Linear)
#   chart    - Visualization generation
#   test     - Testing operations
#   quality  - Code quality checks
#   cache    - Cache management
#   env      - Environment setup

# Variables
PY_VERSION := "3.11"
CHARTS_DIR := "charts"
DATA_DIR := "data"
ANALYSIS_DIR := "analysis_results"
LOGS_DIR := "logs"

# Colors for output
RED := "\\033[0;31m"
GREEN := "\\033[0;32m"
YELLOW := "\\033[1;33m"
BLUE := "\\033[0;34m"
NC := "\\033[0m" # No Color

# Default - show help
_default:
    @just help

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                                  HELP SYSTEM                                 ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Show all commands organized by activity
help:
    @echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    @echo "║                 GitHub Linear Metrics - Activity Commands                   ║"
    @echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    @echo ""
    @echo "🚀 QUICK START:"
    @echo "  just env setup                    Set up environment from scratch"
    @echo "  just env verify-apis              Verify GitHub, Linear, Anthropic APIs"
    @echo "  just extract github <org> [days]  Extract GitHub data (default: 7 days)"
    @echo "  just chart metrics <csv> <csv>    Generate metrics charts"
    @echo ""
    @echo "📊 EXTRACT - Data Extraction:"
    @echo "  just extract github <org> [days=7]          Extract GitHub commits + PRs"
    @echo "  just extract github-commits <org> [days=30] Extract commits only"
    @echo "  just extract github-prs <org> [days=30]     Extract PRs only"
    @echo "  just extract linear <org> [days=30]         Extract Linear tickets"
    @echo "  just extract linear-cycles <team> [output]  Extract Linear cycle data"
    @echo "  just extract list-repos <org>               List organization repos"
    @echo ""
    @echo "📈 CHART - Visualization Generation:"
    @echo "  just chart metrics <commits> <prs> [output=charts]       Generate metrics charts"
    @echo "  just chart all <commits> <prs> <cycles> [output=charts]  Generate all charts (with cycles)"
    @echo ""
    @echo "🧪 TEST - Testing Operations:"
    @echo "  just test all             All tests with coverage"
    @echo "  just test unit            Unit tests only"
    @echo "  just test integration     Integration tests only"
    @echo "  just test github          GitHub integration tests"
    @echo "  just test linear          Linear integration tests"
    @echo "  just test extraction      Extraction pipeline tests"
    @echo ""
    @echo "✨ QUALITY - Code Quality:"
    @echo "  just quality lint         Lint with ruff"
    @echo "  just quality format       Format with ruff"
    @echo "  just quality typecheck    Type check with mypy"
    @echo "  just quality check        All quality checks"
    @echo "  just quality coverage     Coverage report"
    @echo ""
    @echo "💾 CACHE - Cache Management:"
    @echo "  just cache status         Show cache statistics (API + Git)"
    @echo "  just cache clean [org]    Clean cache (optionally for specific org)"
    @echo "  just cache rebuild [org]  Rebuild cache (optionally for specific org)"
    @echo "  just cache validate       Validate cache integrity"
    @echo ""
    @echo "🔧 ENV - Environment Management:"
    @echo "  just env setup            Initial setup with UV and dependencies"
    @echo "  just env dev-setup        Install development dependencies"
    @echo "  just env check            Check environment variables status"
    @echo "  just env verify-apis      Test all API connections"
    @echo "  just env validate-config  Validate configuration files"
    @echo "  just env status           Show UV environment details"
    @echo "  just env clean            Clean build artifacts"
    @echo "  just env fresh-start      Complete reset and setup"
    @echo ""
    @echo "💡 COMMON WORKFLOWS:"
    @echo "  Setup:       just env setup → just env verify-apis"
    @echo "  Extract:     just extract github org-name 30"
    @echo "  Visualize:   just chart metrics commits.csv prs.csv"
    @echo "  Development: just test all → just quality check"

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                           ENVIRONMENT & SETUP                               ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Initial project setup with comprehensive validation
setup:
    @echo "🚀 Setting up GitHub Linear Metrics project..."
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @echo "🔍 Checking prerequisites..."
    @which uv > /dev/null || (echo "❌ uv not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh" && exit 1)
    @echo "✅ UV found: $(uv --version)"
    @echo ""
    @echo "📦 Setting up project with UV..."
    @uv sync
    @echo "✅ Dependencies installed and virtual environment ready"
    @echo ""
    @echo "📁 Creating necessary directories..."
    @mkdir -p {{ANALYSIS_DIR}} {{LOGS_DIR}}
    @echo "✅ Project directories created"
    @echo ""
    @echo "🧪 Running setup validation..."
    @uv run python --version > /dev/null && echo "✅ Python environment working" || echo "❌ Python environment issue"
    @uv run python -c "import logging; print('✅ Built-in imports working')" 2>/dev/null || echo "❌ Import issues detected"
    @echo ""
    @echo "✅ Setup complete!"
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @echo "🎯 Next steps:"
    @echo "  1. Set up environment variables (copy .env.example to .env)"
    @echo "  2. Run 'just env-check' to verify configuration"
    @echo "  3. Run 'just verify-apis' to test API connections"
    @echo "  4. Run 'just uv-status' to see detailed UV environment info"
    @echo "  5. Run 'just extract-test your-org' to validate extraction works"

# Install development dependencies
dev-setup:
    @echo "🛠️ Installing development dependencies..."
    @uv sync --group dev
    @echo "✅ Development dependencies installed"

# Show environment variables status with security
env-check:
    @echo "📋 Environment Variables Status:"
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @if [ -n "${GITHUB_TOKEN:-}" ]; then echo "GitHub Token: {{GREEN}}✅ Set{{NC}} (length: $${#GITHUB_TOKEN})"; else echo "GitHub Token: {{RED}}❌ Not set{{NC}}"; fi
    @if [ -n "${LINEAR_API_KEY:-}${LINEAR_TOKEN:-}" ]; then echo "Linear API Key: {{GREEN}}✅ Set{{NC}}"; else echo "Linear API Key: {{RED}}❌ Not set{{NC}}"; fi
    @if [ -n "${ANTHROPIC_API_KEY:-}" ]; then echo "Anthropic API Key: {{GREEN}}✅ Set{{NC}}"; else echo "Anthropic API Key: {{RED}}❌ Not set{{NC}}"; fi
    @if [ -n "${ORGANIZATION_NAME:-}" ]; then echo "Organization: {{GREEN}}✅ Set{{NC}} (${ORGANIZATION_NAME})"; else echo "Organization: {{YELLOW}}⚠️ Not set{{NC}} (optional)"; fi
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Verify all API connections with detailed output
verify-apis:
    @echo "🔍 Verifying API connections..."
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @uv run python scripts/verify_apis.py

# Validate configuration files
validate-config:
    @echo "🔧 Validating configuration..."
    @uv run python scripts/test_config.py

# Show UV environment status and configuration
uv-status:
    @echo "🔍 UV Environment Status:"
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @echo "📦 UV Installation:"
    @uv --version || echo "❌ UV not installed"
    @echo ""
    @echo "🔧 Project Environment:"
    @if [ -d ".venv" ]; then echo "✅ Virtual environment: .venv/"; else echo "❌ No virtual environment found"; fi
    @echo "📍 Environment Python:"
    @uv run python --version 2>/dev/null || echo "❌ UV environment not working"
    @echo "📍 Environment location:"
    @uv run python -c "import sys; print(f'  {sys.executable}')" 2>/dev/null || echo "❌ Cannot determine Python path"
    @echo ""
    @echo "📊 Dependencies:"
    @if [ -f "pyproject.toml" ]; then echo "✅ pyproject.toml found"; else echo "❌ No pyproject.toml"; fi
    @if [ -f "uv.lock" ]; then echo "✅ uv.lock found"; else echo "⚠️  No uv.lock file"; fi
    @echo ""
    @echo "🧪 Import Test:"
    @uv run python -c "import logging; print('✅ Built-in logging module works')" 2>/dev/null || echo "❌ Import issues detected"
    @uv run python -c "from src.structured_logging import structured_logger; print('✅ Project modules work')" 2>/dev/null || echo "❌ Project import issues"

# Test and fix import conflicts
fix-imports:
    @echo "🔧 Testing and fixing import conflicts..."
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @echo "🧪 Testing built-in modules:"
    @uv run python -c "import logging, json, os, sys, datetime; print('✅ All built-in modules working')" || echo "❌ Built-in module import issues"
    @echo ""
    @echo "🧪 Testing project modules:"
    @uv run python -c "from src.structured_logging.structured_logger import get_structured_logger; print('✅ structured_logging module working')" || echo "❌ structured_logging import issues"
    @uv run python -c "from src.analysis.claude_client import ClaudeClient; print('✅ analysis modules working')" || echo "❌ analysis module import issues"
    @uv run python -c "from src.git_extraction.simple_cli import main; print('✅ git_extraction modules working')" || echo "❌ git_extraction import issues"
    @echo ""
    @echo "📋 Import Conflict Check Results:"
    @if uv run python -c "import logging; from src.structured_logging import structured_logger; print('✅ No import conflicts detected')" 2>/dev/null; then \
        echo "✅ All imports working correctly - no conflicts found"; \
    else \
        echo "❌ Import conflicts detected - see troubleshooting guide:"; \
        echo "   docs/troubleshooting/import-conflicts.md"; \
    fi

# Run test extraction to validate setup
extract-test org="test-org":
    @echo "🧪 Running test extraction for {{org}}..."
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @echo "ℹ️ This runs a minimal test extraction to validate setup"
    @if [ "{{org}}" = "test-org" ]; then \
        echo "⚠️  Using default test organization name"; \
        echo "   Usage: just extract-test your-actual-org-name"; \
    fi
    @echo ""
    @echo "🔍 Pre-flight checks:"
    @just env-check
    @echo ""
    @echo "🚀 Running test extraction (1 day, simplified):"
    @cd src && uv run python -m git_extraction.simple_cli --org {{org}} --days 1 || echo "❌ Test extraction failed"
    @echo ""
    @echo "📄 Generated files:"
    @ls -la org_*.csv 2>/dev/null | head -5 || echo "No test files generated"
    @echo ""
    @echo "✅ Test extraction complete"

# Clean up temporary files and artifacts
cleanup-temp:
    @echo "🧹 Cleaning up temporary files and artifacts..."
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @echo "🗑️ Removing temporary files:"
    @find . -name "*.pyc" -delete && echo "  ✅ Removed Python bytecode files"
    @find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null && echo "  ✅ Removed __pycache__ directories" || true
    @rm -f basic_extract.py extract_data.py simple_extract.py 2>/dev/null && echo "  ✅ Removed temporary wrapper scripts" || true
    @rm -rf .pytest_cache/ 2>/dev/null && echo "  ✅ Removed pytest cache" || true
    @rm -rf build/ dist/ *.egg-info/ 2>/dev/null && echo "  ✅ Removed build artifacts" || true
    @echo ""
    @echo "📁 Cleaning analysis outputs (keeping important files):"
    @find . -name "test_*.csv" -delete 2>/dev/null && echo "  ✅ Removed test CSV files" || true
    @find . -name "*_temp.csv" -delete 2>/dev/null && echo "  ✅ Removed temporary CSV files" || true
    @find . -name "debug_*.log" -delete 2>/dev/null && echo "  ✅ Removed debug log files" || true
    @echo ""
    @echo "🔧 UV cache status:"
    @echo "  Current cache size: $(du -sh ~/.cache/uv 2>/dev/null | cut -f1 || echo 'N/A')"
    @echo "  Run 'uv cache clean' to clean UV cache if needed"
    @echo ""
    @echo "✅ Cleanup complete"

# Clean build artifacts and temporary files
clean:
    @echo "🧹 Cleaning build artifacts..."
    @rm -rf build/ dist/ *.egg-info/ .pytest_cache/ __pycache__/
    @find . -name "*.pyc" -delete
    @find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    @echo "✅ Clean complete"

# Complete reset and setup
fresh-start:
    @echo "🔄 Performing fresh start..."
    @just clean
    @just setup
    @echo "✅ Fresh start complete"

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                        DATA EXTRACTION & ANALYSIS                          ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Extract data for organization using UV-powered git-based approach
extract org days="7":
    @echo "📊 Extracting data for {{org}} (last {{days}} days) using UV-powered git-based approach..."
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @if [ {{days}} -gt 90 ]; then echo "⚠️ Large extraction ({{days}} days) - this may take a while"; fi
    @uv run python -c "import sys; sys.exit(0 if '{{org}}' and len('{{org}}') > 0 else 1)" || (echo "❌ Organization name required" && exit 1)
    @echo "🔍 Pre-extraction validation:"
    @echo "  Organization: {{org}}"
    @echo "  Days: {{days}}"
    @echo "  UV environment: $(uv run python --version)"
    @echo ""
    @echo "🚀 Starting extraction..."
    @cd src && uv run python -m git_extraction.simple_cli --org {{org}} --days {{days}}
    @echo ""
    @echo "📄 Generated files:"
    @ls -la org_*.csv 2>/dev/null || echo "No output files generated"
    @echo "✅ Extraction complete for {{org}}"

# Extract ONLY git commits (test git extraction separately)
extract-commits org days="30":
    @echo "📊 Extracting GIT COMMITS for {{org}} ({{days}} days)..."
    @uv run python scripts/test_commits_extraction.py {{org}} {{days}}

# Extract ONLY PRs via GitHub API (test PR extraction separately)
extract-prs org days="30":
    @echo "📊 Extracting GITHUB PRs for {{org}} ({{days}} days)..."
    @uv run python scripts/test_prs_extraction.py {{org}} {{days}}

# Extract ONLY Linear tickets
extract-linear org days="30":
    @echo "📊 Extracting LINEAR tickets for {{org}} ({{days}} days)..."
    @uv run python scripts/test_linear_extraction.py {{org}} {{days}}

# Extract Linear cycle data for team
extract-linear-cycles team="ENG" output="linear_cycles.csv":
    @echo "📊 Extracting Linear cycle data for team {{team}}..."
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @echo "  Team: {{team}}"
    @echo "  Output: {{output}}"
    @echo ""
    @uv run python scripts/extract_linear_cycles.py --team {{team}} --output {{output}}
    @echo ""
    @if [ -f "{{output}}" ]; then \
        echo "✅ Cycle data extracted to {{output}}"; \
        wc -l {{output}} | awk '{print "  📄 " $$1-1 " cycle issues extracted"}'; \
    else \
        echo "❌ Extraction failed - no output file generated"; \
    fi

# Run incremental extraction (automatically handled by git-based approach)
extract-incremental org:
    @echo "📊 Running incremental extraction for {{org}}..."
    @echo "ℹ️ Git-based extraction automatically handles incremental updates"
    @cd src && uv run python -m git_extraction.cli --org {{org}} --days 1

# List all repositories for organization
list-repos org:
    @echo "📋 Listing repositories for {{org}}..."
    @uv run python -c "import os, sys; sys.path.insert(0, 'src'); from git.git_extractor import GitDataExtractor; extractor = GitDataExtractor(os.getenv('GITHUB_TOKEN')); repos = extractor.get_organization_repos('{{org}}'); [print(f'{repo[\"name\"]} - {repo[\"description\"] or \"No description\"}') for repo in repos]"

# Extract data for specific repository
extract-repo repo days="7":
    @echo "📊 Extracting data for repository {{repo}} (last {{days}} days)..."
    @echo "ℹ️ Single repo extraction: specify as org/repo format"
    @uv run python -c "org, repo_name = '{{repo}}'.split('/'); print(f'Extracting {org}/{repo_name}...')"
    @uv run python scripts/extraction/extract_git.py --org $(echo "{{repo}}" | cut -d'/' -f1) --days {{days}}

# Run 7-day pilot analysis with comprehensive checks
pilot org:
    @echo "🚀 Running 7-day pilot analysis for {{org}}..."
    @echo "🔍 Pre-flight checks..."
    @just verify-apis
    @echo "📊 Extracting data (git-based)..."
    @just extract {{org}} 7
    @echo "🧠 Running analysis..."
    @just analyze {{org}}
    @echo "📈 Generating reports..."
    @just generate-reports
    @echo "✅ Pilot analysis complete for {{org}} (git-based extraction used)"

# Full pipeline analysis
pipeline org days:
    @echo "🔄 Running full pipeline for {{org}} ({{days}} days)..."
    @if [ {{days}} -gt 60 ]; then echo "⚠️ Large pipeline ({{days}} days) - this may take significant time"; fi
    @echo "🔍 Pre-flight checks..."
    @just verify-apis
    @echo "📊 Extracting data (git-based)..."
    @just extract {{org}} {{days}}
    @echo "🧠 Running analysis..."
    @just analyze {{org}}
    @echo "📈 Generating reports..."
    @just generate-reports
    @echo "✅ Pipeline complete for {{org}} (git-based extraction used)"

# Full pipeline with Linear cycle integration
pipeline-with-linear org days team="ENG":
    @echo "🔄 Running full pipeline with Linear integration for {{org}} ({{days}} days)..."
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @if [ {{days}} -gt 60 ]; then echo "⚠️  Large pipeline ({{days}} days) - this may take significant time"; fi
    @echo ""
    @echo "🔍 Pre-flight checks..."
    @just verify-apis
    @echo ""
    @echo "📊 Step 1/5: Extracting GitHub data (git-based)..."
    @just extract {{org}} {{days}}
    @echo ""
    @echo "📊 Step 2/5: Extracting Linear cycle data..."
    @just extract-linear-cycles {{team}} linear_cycles.csv
    @echo ""
    @echo "🧠 Step 3/5: Running AI analysis..."
    @just analyze {{org}}
    @echo ""
    @echo "📈 Step 4/5: Generating comprehensive reports..."
    @just generate-reports
    @echo ""
    @echo "📊 Step 5/5: Generating all charts (including cycles)..."
    @just generate-charts-all src/org_commits.csv src/org_prs.csv linear_cycles.csv charts
    @echo ""
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @echo "✅ Complete pipeline finished for {{org}}"
    @echo ""
    @echo "📂 Outputs:"
    @echo "  📄 GitHub data: src/org_commits.csv, src/org_prs.csv"
    @echo "  📄 Linear data: linear_cycles.csv"
    @echo "  📄 Analysis: analysis_results.csv"
    @echo "  📊 Charts: charts/*.png"

# Analyze extracted data
analyze org input="org_prs.csv":
    @echo "🧠 Running AI analysis on {{input}}..."
    @if [ ! -f "{{input}}" ]; then echo "❌ Input file {{input}} not found"; exit 1; fi
    @uv run python main.py --org {{org}} --input {{input}}

# Re-run analysis on existing data
reanalyze org input:
    @echo "🔄 Re-running analysis on {{input}}..."
    @just analyze {{org}} {{input}}

# Generate comprehensive reports
generate-reports input="analysis_results.csv":
    @echo "📈 Generating reports from {{input}}..."
    @uv run python scripts/generate_reports.py {{input}}

# Generate metrics visualization charts
generate-charts commits="src/org_commits.csv" prs="src/org_prs.csv" output="charts":
    @echo "📊 Generating metrics charts..."
    @echo "  Commits: {{commits}}"
    @echo "  PRs: {{prs}}"
    @echo "  Output: {{output}}"
    @uv run python scripts/generate_metrics_charts.py --commits {{commits}} --prs {{prs}} --output {{output}}
    @echo "✅ Charts generated in {{output}}/"

# Generate all metrics charts including Linear cycles
generate-charts-all commits="src/org_commits.csv" prs="src/org_prs.csv" cycles="" output="charts":
    @echo "📊 Generating comprehensive metrics charts..."
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @echo "  Commits: {{commits}}"
    @echo "  PRs: {{prs}}"
    @if [ -n "{{cycles}}" ]; then echo "  Cycles: {{cycles}}"; fi
    @echo "  Output: {{output}}"
    @echo ""
    @if [ -n "{{cycles}}" ] && [ -f "{{cycles}}" ]; then \
        uv run python scripts/generate_metrics_charts.py --commits {{commits}} --prs {{prs}} --cycles {{cycles}} --output {{output}}; \
    else \
        uv run python scripts/generate_metrics_charts.py --commits {{commits}} --prs {{prs}} --output {{output}}; \
    fi
    @echo ""
    @echo "📈 Generated charts:"
    @ls -1 {{output}}/*.png 2>/dev/null | wc -l | awk '{print "  ✅ " $$1 " charts generated"}' || echo "  ❌ No charts generated"

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                             TESTING & QUALITY                              ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Run all tests with coverage
test:
    @echo "🧪 Running all tests with coverage..."
    @uv run python -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

# Run unit tests only
test-unit:
    @echo "🧪 Running unit tests..."
    @uv run python -m pytest tests/ -v -k "not integration" --cov=src --cov-report=term-missing

# Run integration tests only
test-integration:
    @echo "🧪 Running integration tests..."
    @uv run python -m pytest tests/ -v -k "integration" --cov=src --cov-report=term-missing

# Run load tests for performance validation
test-load *ARGS:
    @echo "⚡ Running load tests..."
    @uv run python scripts/run_load_tests.py {{ARGS}}

# Run quick load test with default parameters
test-load-quick:
    @echo "⚡ Running quick load test..."
    @uv run python scripts/run_load_tests.py --test-type analysis --requests 50 --concurrent 5

# Run comprehensive load test suite
test-load-full:
    @echo "⚡ Running comprehensive load tests..."
    @uv run python scripts/run_load_tests.py --test-type all --requests 200 --concurrent 15 --output load_test_report.json

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                               API & SERVICES                                 ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Start the FastAPI development server
api-dev:
    @echo "🚀 Starting FastAPI development server..."
    @uv run uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload

# Start the FastAPI production server
api-prod:
    @echo "🚀 Starting FastAPI production server..."
    @uv run uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --workers 4

# Generate OpenAPI documentation
api-docs:
    @echo "📖 Generating OpenAPI documentation..."
    @uv run python -c "from src.api.app import app; import json; print(json.dumps(app.openapi(), indent=2))" > api_docs.json
    @echo "📖 OpenAPI documentation saved to api_docs.json"

# Test API endpoints
api-test:
    @echo "🧪 Testing API endpoints..."
    @uv run python -m pytest tests/ -v -k "api" --cov=src --cov-report=term-missing

# Run tests in watch mode
test-watch:
    @echo "🧪 Running tests in watch mode..."
    @uv run python -m pytest tests/ -v --cov=src -f

# Test specific API integrations
test-linear:
    @echo "🔗 Testing Linear integration..."
    @uv run python scripts/test_linear_integration.py

test-github:
    @echo "🐙 Testing GitHub integration..."
    @uv run python scripts/test_github_integration.py

test-anthropic:
    @echo "🧠 Testing Anthropic integration..."
    @uv run python scripts/test_analysis_integration.py

test-analysis:
    @echo "🧠 Testing analysis engine..."
    @uv run python scripts/test_analysis_integration.py

test-gh-analyzer:
    @echo "🤖 Testing GitHub Actions analyzer..."
    @uv run python scripts/test_github_action_analyzer.py

test-extraction:
    @echo "📊 Testing data extraction..."
    @./scripts/test_extraction.sh

# Quality assurance commands
lint:
    @echo "🔍 Running linting with ruff..."
    @uv run python -m ruff check src/ tests/ scripts/

format:
    @echo "🎨 Formatting code with ruff..."
    @uv run python -m ruff format src/ tests/ scripts/

typecheck:
    @echo "🔍 Running type checking with mypy..."
    @uv run python -m mypy src/

coverage:
    @echo "📊 Generating test coverage report..."
    @uv run python -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
    @echo "📈 Coverage report generated in htmlcov/"

quality-check:
    @echo "🎯 Running full quality suite..."
    @just lint
    @just format
    @just typecheck
    @just coverage

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                          MONITORING & DEBUGGING                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Show system status and health
status:
    @echo "📊 System Status:"
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @just env-check
    @echo ""
    @echo "📁 Directory Status:"
    @ls -la {{ANALYSIS_DIR}}/ 2>/dev/null || echo "Analysis directory empty"
    @echo ""
    @echo "🔍 Recent Analysis Files:"
    @ls -lt {{ANALYSIS_DIR}}/*.csv 2>/dev/null | head -5 || echo "No analysis files found"

# Check API health and connectivity
health:
    @echo "🏥 Health Check:"
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @just verify-apis

# Show logs for debugging
logs service="":
    @echo "📋 Showing logs..."
    @if [ -n "{{service}}" ]; then \
        echo "Showing logs for {{service}}"; \
        cat {{LOGS_DIR}}/{{service}}.log 2>/dev/null || echo "No logs found for {{service}}"; \
    else \
        find {{LOGS_DIR}} -name "*.log" -exec echo "=== {} ===" \; -exec tail -20 {} \; 2>/dev/null || echo "No log files found"; \
    fi

# Debug extraction issues
debug-extraction:
    @echo "🔍 Debugging extraction issues..."
    @uv run python scripts/debug_extraction.py

# Debug analysis issues
debug-analysis:
    @echo "🔍 Debugging analysis issues..."
    @uv run python scripts/debug_analysis.py

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                             CACHE MANAGEMENT                               ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Git repository health check and status
git-status:
    @echo "🔍 Git Repository Health Check:"
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @uv run python -c "import sys; sys.path.insert(0, 'src'); from git.repository_service import GitRepositoryService; import os; service = GitRepositoryService(); print('📊 Repository Status:'); stats = service.get_repository_health(); print(f'  Total repositories: {stats[\"total_repos\"]}'); print(f'  Healthy repositories: {stats[\"healthy_repos\"]}'); print(f'  Corrupted repositories: {stats[\"corrupted_repos\"]}'); print(f'  Last updated: {stats[\"last_updated\"]}'); print(f'  Total disk usage: {stats[\"disk_usage\"]}'); print('\n📋 Organizations:'); [print(f'  {org}: {len(repos)} repos') for org, repos in stats[\"organizations\"].items()]; print('\n🚨 Issues:'); [print(f'  ❌ {issue}') for issue in stats[\"issues\"]] if stats[\"issues\"] else print('  ✅ No issues detected')" 2>/dev/null || echo "  (Run 'just setup' to get git repository status)"

# Clean git repositories for specific organization
git-cleanup org="":
    @echo "🧹 Git Cache Cleanup..."
    @if [ -z "{{org}}" ]; then \
        echo "❌ Organization name required"; \
        echo "Usage: just git-cleanup organization-name"; \
        exit 1; \
    fi
    @echo "This will remove all cached repositories for {{org}}. Continue? (y/N)"
    @read -r confirm && [ "$$confirm" = "y" ] || (echo "Aborted" && exit 1)
    @rm -rf .git_cache/repos/{{org}}/
    @rm -rf .git_cache/state/{{org}}_*.json
    @echo "✅ Git cache cleaned for {{org}}"
    @echo "ℹ️ Repositories will be re-cloned on next extraction"

# Force refresh git repositories for organization
git-refresh org:
    @echo "🔄 Refreshing git repositories for {{org}}..."
    @uv run python -c "import sys; sys.path.insert(0, 'src'); from git.repository_service import GitRepositoryService; import os; service = GitRepositoryService(); result = service.refresh_organization_repos('{{org}}', os.getenv('GITHUB_TOKEN')); print(f'✅ Refreshed {result[\"updated_repos\"]} repositories'); print(f'📊 Total repos: {result[\"total_repos\"]}'); print(f'⏱️ Update time: {result[\"update_time\"]:.2f}s'); [print(f'  ❌ Failed: {repo} - {error}') for repo, error in result[\"failures\"].items()] if result[\"failures\"] else print('  ✅ All repositories updated successfully')" 2>/dev/null || echo "❌ Failed to refresh repositories (run 'just setup' first)"

# Show extraction performance statistics
extract-stats org:
    @echo "📊 Extraction Performance Statistics for {{org}}:"
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @uv run python -c "import sys; sys.path.insert(0, 'src'); from git.git_extractor import GitDataExtractor; import os; extractor = GitDataExtractor(os.getenv('GITHUB_TOKEN')); stats = extractor.get_extraction_stats('{{org}}'); print(f'🔢 API Efficiency:'); print(f'  API calls made: {stats[\"api_calls_made\"]}'); print(f'  API calls avoided: {stats[\"api_calls_avoided\"]}'); print(f'  Efficiency: {stats[\"efficiency_percent\"]:.1f}% reduction'); print(f'\n⏱️ Performance:'); print(f'  Last extraction time: {stats[\"last_extraction_time\"]:.2f}s'); print(f'  Average time per repo: {stats[\"avg_time_per_repo\"]:.2f}s'); print(f'  Cache hit rate: {stats[\"cache_hit_rate\"]:.1f}%'); print(f'\n📦 Data Volume:'); print(f'  Repositories processed: {stats[\"repos_processed\"]}'); print(f'  Commits extracted: {stats[\"commits_extracted\"]}'); print(f'  PRs analyzed: {stats[\"prs_analyzed\"]}'); print(f'  Data freshness: {stats[\"data_freshness\"]}')" 2>/dev/null || echo "❌ No extraction statistics available for {{org}}"

# Benchmark git-based vs traditional extraction
benchmark-extraction org:
    @echo "⚡ Benchmarking Extraction Performance for {{org}}:"
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @uv run python -c "import sys; sys.path.insert(0, 'src'); from git.git_extractor import GitDataExtractor; import os, time; extractor = GitDataExtractor(os.getenv('GITHUB_TOKEN')); print('🚀 Running extraction benchmark...'); start_time = time.time(); result = extractor.benchmark_extraction('{{org}}', days=7); end_time = time.time(); print(f'\n📊 Benchmark Results:'); print(f'  Git-based extraction: {result[\"git_time\"]:.2f}s'); print(f'  Traditional API calls: {result[\"estimated_api_time\"]:.2f}s (estimated)'); print(f'  Performance improvement: {result[\"improvement_factor\"]:.1f}x faster'); print(f'  API calls saved: {result[\"api_calls_saved\"]}'); print(f'  Cost savings: {result[\"cost_savings_percent\"]:.1f}%'); print(f'\n💾 Storage Analysis:'); print(f'  Cache size: {result[\"cache_size_mb\"]:.1f} MB'); print(f'  Storage per repo: {result[\"storage_per_repo_mb\"]:.2f} MB'); print(f'  Break-even analysis: {result[\"break_even_extractions\"]} extractions')" 2>/dev/null || echo "❌ Benchmark failed (ensure git cache is initialized)"

# Show cache statistics (including git cache)
cache-status:
    @echo "📊 Cache Status:"
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @if [ -d ".cache" ]; then \
        echo "📁 API Cache (.cache/):"; \
        echo "  $(find .cache -name '*.json' | wc -l | tr -d ' ') cache files"; \
        echo "  $(du -sh .cache 2>/dev/null | cut -f1 || echo '0B') total size"; \
    else \
        echo "📁 API Cache (.cache/): No cache directory found"; \
    fi
    @echo ""
    @if [ -d ".git_cache" ]; then \
        echo "📁 Git Cache (.git_cache/):"; \
        echo "  $(find .git_cache/repos -type d -name '.git' | wc -l | tr -d ' ') repositories cloned"; \
        echo "  $(du -sh .git_cache 2>/dev/null | cut -f1 || echo '0B') total size"; \
        echo "  $(find .git_cache/repos -maxdepth 2 -type d | grep -v '^\\.git_cache/repos$$' | wc -l | tr -d ' ') organizations"; \
    else \
        echo "📁 Git Cache (.git_cache/): No git cache directory found"; \
    fi
    @echo ""
    @uv run python -c "import sys; sys.path.insert(0, 'src'); from git.git_extractor import GitDataExtractor; import os; extractor = GitDataExtractor(os.getenv('GITHUB_TOKEN', 'dummy')); stats = extractor.get_cache_stats(); print(f'📊 Git Cache Details:'); print(f'  Total repositories: {stats[\"total_repos\"]}'); print(f'  Total size: {stats[\"total_size_bytes\"]/1024/1024:.1f} MB'); [print(f'  {org}: {len(repos)} repos') for org, repos in stats[\"organizations\"].items()]" 2>/dev/null || echo "  (Run 'just setup' to get detailed git cache stats)"

# Clean expired cache entries (API and git cache)
cache-clean:
    @echo "🧹 Cleaning expired cache entries..."
    @if [ -d ".cache" ]; then \
        echo "Cleaning API cache..."; \
        cd scripts/extraction && source utils.sh && clean_cache; \
    else \
        echo "No API cache directory found"; \
    fi
    @echo "ℹ️ Git cache (.git_cache) is managed automatically"
    @echo "   Use 'just cache-rebuild' to force clean git cache"

# Validate cache integrity
cache-validate:
    @echo "🔍 Validating cache integrity..."
    @if [ -d ".cache" ]; then \
        echo "Checking cache files..."; \
        find .cache -name '*.json' -exec sh -c 'echo "Validating: $$1"; jq . "$$1" >/dev/null 2>&1 || echo "❌ Invalid JSON: $$1"' _ {} \; | tail -20; \
    else \
        echo "No cache directory found"; \
    fi

# Force rebuild cache (clears all cached data including git cache)
cache-rebuild:
    @echo "🔄 Rebuilding cache (clearing all cached data)..."
    @echo "This will remove ALL cached data including git repositories. Continue? (y/N)"
    @read -r confirm && [ "$$confirm" = "y" ] || (echo "Aborted" && exit 1)
    @rm -rf .cache/ .git_cache/
    @mkdir -p .cache/{repos,prs,commits}
    @mkdir -p .git_cache/{repos,state}
    @echo "✅ All caches cleared and rebuilt"

# Warm cache for upcoming analysis
cache-warm organization days="7":
    @echo "🔥 Warming cache for {{ organization }} (last {{ days }} days)..."
    @python -c "from src.analysis.analysis_engine import AnalysisEngine; from src.analysis.cache_warmer import CacheWarmer; engine = AnalysisEngine(); warmer = CacheWarmer(engine); results = warmer.warm_recent_prs('{{ organization }}', days={{ days }}); print(f'✅ Warmed {results[\"warmed_count\"]} entries'); print(f'📊 Already cached: {results[\"already_cached\"]}'); print(f'📦 Total cache size: {results[\"cache_size\"]}'); stats = warmer.get_warming_stats(); print(f'📈 Cache hit rate: {stats[\"cache_hit_rate\"]:.1%}')"

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                             SAFETY HELPERS                                 ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Validate data file integrity
validate-data file:
    @echo "🔍 Validating data file {{file}}..."
    @uv run python scripts/validation/check_data_quality.py {{file}}

# Backup analysis data
backup-data:
    @echo "💾 Backing up analysis data..."
    @mkdir -p backups
    @tar -czf backups/analysis_backup_$(date +%Y%m%d_%H%M%S).tar.gz {{ANALYSIS_DIR}}/ {{LOGS_DIR}}/
    @echo "✅ Backup complete"

# Restore from backup
restore-data:
    @echo "🔄 Restoring from backup..."
    @ls -lt backups/ | head -10
    @echo "Please specify backup file to restore"

# Emergency cleanup
emergency-cleanup:
    @echo "🚨 Emergency cleanup..."
    @echo "This will remove all analysis data and logs. Are you sure? (y/N)"
    @read -r confirm && [ "$$confirm" = "y" ] || (echo "Aborted" && exit 1)
    @rm -rf {{ANALYSIS_DIR}}/* {{LOGS_DIR}}/*
    @echo "✅ Emergency cleanup complete"