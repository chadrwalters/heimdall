# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                  North Star Metrics Development Justfile                    ║
# ║                                                                              ║
# ║ 🌟 AI-powered engineering impact analytics framework                        ║
# ║ 📊 Analyzes code changes across organizations for complexity/risk insights  ║
# ║ 🔗 Integrates GitHub, Linear, and Anthropic Claude APIs                     ║
# ║ 📈 Generates actionable metrics for engineering productivity                 ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
#
# 📖 QUICK START:
#   just setup           - Set up development environment from scratch
#   just env-check       - Verify API keys and environment status
#   just pilot <org>     - Run 7-day pilot analysis for organization
#   just help            - Show detailed help and command groups
#
# 🔧 COMMON WORKFLOWS:
#   Setup:      just setup → just env-check → just verify-apis
#   Analysis:   just pilot <org> → just pipeline <org> 30
#   Testing:    just test → just test-unit → just test-integration
#   Quality:    just lint → just format → just coverage
#
# 📋 Type 'just' or 'just help' to see all available commands organized by category

# Variables
PY_VERSION := "3.11"
VENV_DIR := ".venv"
ANALYSIS_DIR := "analysis_results"
LOGS_DIR := "logs"

# Colors for output
RED := "\\033[0;31m"
GREEN := "\\033[0;32m"
YELLOW := "\\033[1;33m"
BLUE := "\\033[0;34m"
PURPLE := "\\033[0;35m"
CYAN := "\\033[0;36m"
NC := "\\033[0m" # No Color

# Default task - shows organized help instead of raw list
_default:
    @just help

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                            HELP & COMMAND GROUPS                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Show organized help with command groups and common workflows
help:
    @echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    @echo "║                    North Star Metrics Development Commands                  ║"
    @echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    @echo ""
    @echo "🚀 QUICK START:"
    @echo "  setup                  Set up development environment from scratch"
    @echo "  env-check              Check environment variables and API keys status"
    @echo "  verify-apis            Test connectivity to GitHub, Linear, and Anthropic APIs"
    @echo "  pilot <org>            Run 7-day pilot analysis for organization"
    @echo "  help                   Show this detailed help"
    @echo ""
    @echo "🔧 ENVIRONMENT & SETUP:"
    @echo "  setup                  Initial project setup with Python venv and dependencies"
    @echo "  dev-setup             Install development dependencies and tools"
    @echo "  env-check             Show environment variables status"
    @echo "  verify-apis           Verify all API connections (GitHub, Linear, Anthropic)"
    @echo "  validate-config       Validate configuration files and settings"
    @echo "  clean                 Clean build artifacts and temporary files"
    @echo "  fresh-start           Complete reset and setup (clean → setup)"
    @echo ""
    @echo "📊 DATA EXTRACTION & ANALYSIS:"
    @echo "  Extraction Commands:"
    @echo "    extract <org> [days]        Extract data for organization (default: 7 days)"
    @echo "    extract-incremental <org>   Extract only new data since last run"
    @echo "    list-repos <org>           List all repositories for organization"
    @echo "    extract-repo <org/repo>     Extract data for specific repository"
    @echo ""
    @echo "  Analysis Commands:"
    @echo "    pilot <org>                Run 7-day pilot analysis (extract + analyze)"
    @echo "    pipeline <org> <days>      Full pipeline: extract → analyze → generate reports"
    @echo "    analyze [input]            Analyze extracted data (default: org_prs.csv)"
    @echo "    reanalyze <input>          Re-run analysis on existing data"
    @echo ""
    @echo "  Report Generation:"
    @echo "    generate-reports <input>   Generate comprehensive reports from analysis"
    @echo "    export-metrics <input>     Export metrics in various formats"
    @echo "    compare-periods <org>      Compare different time periods"
    @echo ""
    @echo "🧪 TESTING & QUALITY (Coverage Always Included):"
    @echo "  Core Testing:"
    @echo "    test                   Run all tests with coverage"
    @echo "    test-unit             Run unit tests only"
    @echo "    test-integration      Run integration tests with APIs"
    @echo "    test-watch            Run tests in watch mode"
    @echo ""
    @echo "  Specialized Testing:"
    @echo "    test-linear           Test Linear API integration"
    @echo "    test-github           Test GitHub API integration"
    @echo "    test-anthropic        Test Anthropic API integration"
    @echo "    test-analysis         Test analysis engine"
    @echo "    test-gh-analyzer      Test GitHub Actions analyzer"
    @echo "    test-extraction       Test data extraction pipeline"
    @echo ""
    @echo "  Quality Assurance:"
    @echo "    lint                  Run linting with ruff"
    @echo "    format                Format code with ruff"
    @echo "    typecheck             Run type checking with mypy"
    @echo "    coverage              Generate test coverage report"
    @echo "    quality-check         Run full quality suite (lint + format + typecheck)"
    @echo ""
    @echo "🔍 MONITORING & DEBUGGING:"
    @echo "  System Health:"
    @echo "    status                Show system status and health"
    @echo "    health                Check API health and connectivity"
    @echo "    logs [service]        Show logs for specific service"
    @echo "    debug-extraction      Debug extraction issues"
    @echo "    debug-analysis        Debug analysis issues"
    @echo ""
    @echo "  Data Management:"
    @echo "    validate-data <file>  Validate data file integrity"
    @echo "    repair-data <file>    Attempt to repair corrupted data"
    @echo "    backup-data           Backup analysis data"
    @echo "    restore-data          Restore from backup"
    @echo ""
    @echo "📈 ADVANCED OPERATIONS:"
    @echo "  Automation:"
    @echo "    schedule-analysis <org>    Setup scheduled analysis"
    @echo "    run-scheduled             Run scheduled analysis jobs"
    @echo "    update-github-actions     Update GitHub Actions workflows"
    @echo ""
    @echo "  Performance:"
    @echo "    benchmark <org>           Benchmark analysis performance"
    @echo "    profile-analysis <input>  Profile analysis performance"
    @echo "    optimize-extraction       Optimize extraction performance"
    @echo ""
    @echo "🔐 SECURITY & SAFETY:"
    @echo "  🚨 NEVER run destructive operations without confirmation"
    @echo "  🔑 API keys are never logged or exposed"
    @echo "  💾 Data is automatically backed up before major operations"
    @echo "  🛡️ All operations include safety checks and validation"
    @echo ""
    @echo "💡 COMMON WORKFLOWS:"
    @echo "  First Time Setup:    just setup → just env-check → just verify-apis"
    @echo "  Quick Analysis:      just pilot organization-name"
    @echo "  Full Analysis:       just pipeline organization-name 30"
    @echo "  Development:         just test → just quality-check"
    @echo "  Debugging:           just health → just logs → just debug-extraction"
    @echo ""
    @echo "📚 DOCUMENTATION:"
    @echo "  docs/INDEX.md         Complete documentation hub"
    @echo "  docs/setup/           Setup and configuration guides"
    @echo "  docs/workflows/       Analysis workflows and procedures"
    @echo "  docs/troubleshooting/ Common issues and solutions"
    @echo ""
    @echo "🆘 EMERGENCY PROCEDURES:"
    @echo "  just health           Check if system is responding"
    @echo "  just clean            Clean up corrupted state"
    @echo "  just fresh-start      Complete reset and reinstall"
    @echo "  just backup-data      Backup data before major operations"

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                           ENVIRONMENT & SETUP                               ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Initial project setup with safety checks
setup:
    @echo "🚀 Setting up North Star Metrics project..."
    @echo "🔍 Checking Python version..."
    @python --version | grep -E "3\.(11|12|13)" || (echo "❌ Python 3.11+ required" && exit 1)
    @echo "📦 Creating virtual environment..."
    @if [ ! -d "{{VENV_DIR}}" ]; then python -m venv {{VENV_DIR}}; fi
    @echo "📚 Installing dependencies..."
    @{{VENV_DIR}}/bin/pip install --upgrade pip
    @{{VENV_DIR}}/bin/pip install -e .
    @echo "📁 Creating necessary directories..."
    @mkdir -p {{ANALYSIS_DIR}} {{LOGS_DIR}}
    @echo "✅ Setup complete!"
    @echo "🎯 Next steps:"
    @echo "  1. Set up environment variables (see .env.example)"
    @echo "  2. Run 'just env-check' to verify configuration"
    @echo "  3. Run 'just verify-apis' to test API connections"

# Install development dependencies
dev-setup:
    @echo "🛠️ Installing development dependencies..."
    @{{VENV_DIR}}/bin/pip install -e ".[dev]"
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
    @{{VENV_DIR}}/bin/python scripts/verify_apis.py

# Validate configuration files
validate-config:
    @echo "🔧 Validating configuration..."
    @{{VENV_DIR}}/bin/python scripts/test_config.py

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
    @rm -rf {{VENV_DIR}}
    @just setup
    @echo "✅ Fresh start complete"

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                        DATA EXTRACTION & ANALYSIS                          ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Extract data for organization with safety checks
extract org days="7":
    @echo "📊 Extracting data for {{org}} (last {{days}} days)..."
    @if [ {{days}} -gt 90 ]; then echo "⚠️ Large extraction ({{days}} days) - this may take a while"; fi
    @{{VENV_DIR}}/bin/python -c "import sys; sys.exit(0 if '{{org}}' and len('{{org}}') > 0 else 1)" || (echo "❌ Organization name required" && exit 1)
    @./scripts/extraction/run_extraction.sh --org {{org}} --days {{days}}

# Run incremental extraction
extract-incremental org:
    @echo "📊 Running incremental extraction for {{org}}..."
    @./scripts/extraction/run_extraction.sh --org {{org}} --incremental

# List all repositories for organization
list-repos org:
    @echo "📋 Listing repositories for {{org}}..."
    @./scripts/extraction/list_repos.sh {{org}}

# Extract data for specific repository
extract-repo repo days="7":
    @echo "📊 Extracting data for repository {{repo}} (last {{days}} days)..."
    @./scripts/extraction/run_extraction.sh --repo {{repo}} --days {{days}}

# Run 7-day pilot analysis with comprehensive checks
pilot org:
    @echo "🚀 Running 7-day pilot analysis for {{org}}..."
    @echo "🔍 Pre-flight checks..."
    @just verify-apis
    @echo "📊 Extracting data..."
    @just extract {{org}} 7
    @echo "🧠 Running analysis..."
    @just analyze
    @echo "📈 Generating reports..."
    @just generate-reports
    @echo "✅ Pilot analysis complete for {{org}}"

# Full pipeline analysis
pipeline org days:
    @echo "🔄 Running full pipeline for {{org}} ({{days}} days)..."
    @if [ {{days}} -gt 60 ]; then echo "⚠️ Large pipeline ({{days}} days) - this may take significant time"; fi
    @echo "🔍 Pre-flight checks..."
    @just verify-apis
    @echo "📊 Extracting data..."
    @just extract {{org}} {{days}}
    @echo "🧠 Running analysis..."
    @just analyze
    @echo "📈 Generating reports..."
    @just generate-reports
    @echo "✅ Pipeline complete for {{org}}"

# Analyze extracted data
analyze input="org_prs.csv":
    @echo "🧠 Running AI analysis on {{input}}..."
    @if [ ! -f "{{input}}" ]; then echo "❌ Input file {{input}} not found"; exit 1; fi
    @{{VENV_DIR}}/bin/python main.py --input {{input}}

# Re-run analysis on existing data
reanalyze input:
    @echo "🔄 Re-running analysis on {{input}}..."
    @just analyze {{input}}

# Generate comprehensive reports
generate-reports input="analysis_results.csv":
    @echo "📈 Generating reports from {{input}}..."
    @{{VENV_DIR}}/bin/python scripts/generate_reports.py {{input}}

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                             TESTING & QUALITY                              ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Run all tests with coverage
test:
    @echo "🧪 Running all tests with coverage..."
    @{{VENV_DIR}}/bin/python -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

# Run unit tests only
test-unit:
    @echo "🧪 Running unit tests..."
    @{{VENV_DIR}}/bin/python -m pytest tests/ -v -k "not integration" --cov=src --cov-report=term-missing

# Run integration tests only
test-integration:
    @echo "🧪 Running integration tests..."
    @{{VENV_DIR}}/bin/python -m pytest tests/ -v -k "integration" --cov=src --cov-report=term-missing

# Run load tests for performance validation
test-load *ARGS:
    @echo "⚡ Running load tests..."
    @{{VENV_DIR}}/bin/python scripts/run_load_tests.py {{ARGS}}

# Run quick load test with default parameters
test-load-quick:
    @echo "⚡ Running quick load test..."
    @{{VENV_DIR}}/bin/python scripts/run_load_tests.py --test-type analysis --requests 50 --concurrent 5

# Run comprehensive load test suite
test-load-full:
    @echo "⚡ Running comprehensive load tests..."
    @{{VENV_DIR}}/bin/python scripts/run_load_tests.py --test-type all --requests 200 --concurrent 15 --output load_test_report.json

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                               API & SERVICES                                 ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Start the FastAPI development server
api-dev:
    @echo "🚀 Starting FastAPI development server..."
    @{{VENV_DIR}}/bin/uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload

# Start the FastAPI production server
api-prod:
    @echo "🚀 Starting FastAPI production server..."
    @{{VENV_DIR}}/bin/uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --workers 4

# Generate OpenAPI documentation
api-docs:
    @echo "📖 Generating OpenAPI documentation..."
    @{{VENV_DIR}}/bin/python -c "from src.api.app import app; import json; print(json.dumps(app.openapi(), indent=2))" > api_docs.json
    @echo "📖 OpenAPI documentation saved to api_docs.json"

# Test API endpoints
api-test:
    @echo "🧪 Testing API endpoints..."
    @{{VENV_DIR}}/bin/python -m pytest tests/ -v -k "api" --cov=src --cov-report=term-missing

# Run tests in watch mode
test-watch:
    @echo "🧪 Running tests in watch mode..."
    @{{VENV_DIR}}/bin/python -m pytest tests/ -v --cov=src -f

# Test specific API integrations
test-linear:
    @echo "🔗 Testing Linear integration..."
    @{{VENV_DIR}}/bin/python scripts/test_linear_integration.py

test-github:
    @echo "🐙 Testing GitHub integration..."
    @{{VENV_DIR}}/bin/python scripts/test_github_integration.py

test-anthropic:
    @echo "🧠 Testing Anthropic integration..."
    @{{VENV_DIR}}/bin/python scripts/test_analysis_integration.py

test-analysis:
    @echo "🧠 Testing analysis engine..."
    @{{VENV_DIR}}/bin/python scripts/test_analysis_integration.py

test-gh-analyzer:
    @echo "🤖 Testing GitHub Actions analyzer..."
    @{{VENV_DIR}}/bin/python scripts/test_github_action_analyzer.py

test-extraction:
    @echo "📊 Testing data extraction..."
    @./scripts/test_extraction.sh

# Quality assurance commands
lint:
    @echo "🔍 Running linting with ruff..."
    @{{VENV_DIR}}/bin/python -m ruff check src/ tests/ scripts/

format:
    @echo "🎨 Formatting code with ruff..."
    @{{VENV_DIR}}/bin/python -m ruff format src/ tests/ scripts/

typecheck:
    @echo "🔍 Running type checking with mypy..."
    @{{VENV_DIR}}/bin/python -m mypy src/

coverage:
    @echo "📊 Generating test coverage report..."
    @{{VENV_DIR}}/bin/python -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
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
    @{{VENV_DIR}}/bin/python scripts/debug_extraction.py

# Debug analysis issues
debug-analysis:
    @echo "🔍 Debugging analysis issues..."
    @{{VENV_DIR}}/bin/python scripts/debug_analysis.py

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                             SAFETY HELPERS                                 ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Validate data file integrity
validate-data file:
    @echo "🔍 Validating data file {{file}}..."
    @{{VENV_DIR}}/bin/python scripts/validation/check_data_quality.py {{file}}

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