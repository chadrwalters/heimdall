# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    Heimdall - Activity-Based Commands                       ║
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
#   extract   - Data extraction (GitHub, Linear)
#   chart     - Visualization generation
#   ai-usage  - AI usage tracking
#   test      - Testing operations
#   quality   - Code quality checks
#   cache     - Cache management
#   env       - Environment setup

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
    @echo "║                       Heimdall - Activity Commands                          ║"
    @echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    @echo ""
    @echo "🚀 QUICK START:"
    @echo "  just env setup                       Set up environment from scratch"
    @echo "  just env verify-apis                 Verify GitHub, Linear, Anthropic APIs"
    @echo "  just extract github <org> [days]     Extract GitHub data (default: 7 days)"
    @echo "  just chart metrics <csv> <csv>       Generate metrics charts"
    @echo "  just ai-usage collect [dev] [days=7] Track AI usage (auto-detects dev)"
    @echo ""
    @echo "🔧 GIT - Git Utilities:"
    @echo "  just git branch                       Show current branch"
    @echo "  just git commits [count=10]           Show recent commits with graph"
    @echo "  just git status                       Show git status (short format)"
    @echo "  just git info                         Show detailed git information"
    @echo "  just git diff [args]                  Show git diff"
    @echo ""
    @echo "🐙 GH - GitHub Utilities:"
    @echo "  just gh actions <command> [args]      GitHub Actions via huginn"
    @echo "  just gh actions-latest                View latest Actions run"
    @echo "  just gh actions-watch                 Watch Actions run in progress"
    @echo "  just gh branch-sync                   Sync branch with remote"
    @echo ""
    @echo "🔀 PR - Pull Request Operations:"
    @echo "  just pr request-review [args]         Request PR review with AI context"
    @echo "  just pr enhance [args]                Enhance PR description with AI"
    @echo "  just pr last-review <command> [args]  Show last PR review"
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
    @echo "🤖 AI-USAGE - AI Usage Tracking:"
    @echo "  just ai-usage collect [developer] [days=7]     Collect ccusage + codex data (auto-detects dev)"
    @echo "  just ai-usage ingest                            Ingest submissions with deduplication"
    @echo "  just ai-usage charts [output=charts]            Generate cost/token charts"
    @echo "  just ai-usage pipeline [dev] [days=7] [output]  Complete pipeline (collect→ingest→chart)"
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
# ║                          ENV - Environment Management                        ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Initial project setup with UV
env command *args:
    @just env-{{command}} {{args}}

# Install huginn CLI for PR and git utilities
env-install-huginn:
    @echo "📦 Installing huginn CLI from local repository..."
    @if [ -d ~/source/work/huginn ]; then \
        uv tool install ~/source/work/huginn && echo "✅ Huginn installed from ~/source/work/huginn"; \
    else \
        echo "❌ Huginn repository not found at ~/source/work/huginn"; \
        echo "   Clone from internal repo or skip PR utilities"; \
        exit 1; \
    fi
    @echo ""
    @echo "🔍 Verifying huginn installation..."
    @huginn --help >/dev/null 2>&1 && echo "✅ Huginn (v1.5.0) ready" || echo "❌ Huginn not available in PATH"

# Set up development environment from scratch
env-setup:
    @echo "🚀 Setting up Heimdall project..."
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @which uv > /dev/null || (echo "❌ uv not found. Install: curl -LsSf https://astral.sh/uv/install.sh | sh" && exit 1)
    @echo "✅ UV found: $(uv --version)"
    @echo ""
    @echo "📦 Installing dependencies..."
    @uv sync
    @echo "✅ Dependencies installed"
    @echo ""
    @just env-install-huginn
    @echo ""
    @echo "📁 Creating directories..."
    @mkdir -p {{CHARTS_DIR}} {{DATA_DIR}} logs
    @echo "✅ Directories created"
    @echo ""
    @echo "✅ Setup complete! Next steps:"
    @echo "  1. Set up .env file with API keys"
    @echo "  2. Run 'just env check' to verify configuration"
    @echo "  3. Run 'just env verify-apis' to test connections"

# Install development dependencies
env-dev-setup:
    @echo "🛠️ Installing development dependencies..."
    @uv sync --group dev
    @echo "✅ Development dependencies installed"

# Check environment variables status
env-check:
    @echo "📋 Environment Variables Status:"
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @if [ -n "${GITHUB_TOKEN:-}" ]; then echo "GitHub Token: {{GREEN}}✅ Set{{NC}}"; else echo "GitHub Token: {{RED}}❌ Not set{{NC}}"; fi
    @if [ -n "${LINEAR_API_KEY:-}${LINEAR_TOKEN:-}" ]; then echo "Linear API Key: {{GREEN}}✅ Set{{NC}}"; else echo "Linear API Key: {{RED}}❌ Not set{{NC}}"; fi
    @if [ -n "${ANTHROPIC_API_KEY:-}" ]; then echo "Anthropic API Key: {{GREEN}}✅ Set{{NC}}"; else echo "Anthropic API Key: {{RED}}❌ Not set{{NC}}"; fi

# Verify all API connections
env-verify-apis:
    @echo "🔍 Verifying API connections..."
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @uv run python scripts/verify_apis.py

# Validate configuration files
env-validate-config:
    @echo "🔧 Validating configuration..."
    @uv run python scripts/test_config.py

# Show UV environment status
env-status:
    @echo "🔍 UV Environment Status:"
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @echo "📦 UV: $(uv --version)"
    @echo "🐍 Python: $(uv run python --version)"
    @if [ -d ".venv" ]; then echo "✅ Virtual environment: .venv/"; else echo "❌ No .venv found"; fi

# Clean build artifacts
env-clean:
    @echo "🧹 Cleaning build artifacts..."
    @rm -rf build/ dist/ *.egg-info/ .pytest_cache/ __pycache__/
    @find . -name "*.pyc" -delete
    @find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    @echo "✅ Clean complete"

# Complete reset and setup
env-fresh-start:
    @echo "🔄 Performing fresh start..."
    @just env-clean
    @just env-setup
    @echo "✅ Fresh start complete"

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                          GIT - Git Utilities                                 ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Git command dispatcher
git command *args:
    @just git-{{command}} {{args}}

# Show current branch information
git-branch:
    @git rev-parse --abbrev-ref HEAD

# Show recent commits with formatting
git-commits count='10':
    @git log --oneline --decorate --graph -n {{count}}

# Show git status with enhanced formatting
git-status:
    @git status --short --branch

# Show detailed git information
git-info:
    @echo "Branch: $(git rev-parse --abbrev-ref HEAD)"
    @echo "Commit: $(git rev-parse --short HEAD)"
    @echo "Remote: $(git remote get-url origin)"
    @echo "Status:"
    @git status --short

# Show git diff with context
git-diff *args:
    @git diff {{args}}

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                          GH - GitHub Utilities                               ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# GitHub command dispatcher
gh command *args:
    @just gh-{{command}} {{args}}

# GitHub Actions operations via huginn
gh-actions command *args:
    @huginn actions {{command}} {{args}}

# View latest GitHub Actions run
gh-actions-latest:
    @gh run list --limit 1

# Watch GitHub Actions run
gh-actions-watch:
    @gh run watch

# Sync branch with remote
gh-branch-sync:
    @echo "Fetching from remote..."
    @git fetch origin
    @echo "Current branch: $(git rev-parse --abbrev-ref HEAD)"
    @echo "Commits behind: $(git rev-list --count HEAD..@{u} 2>/dev/null || echo '0')"
    @echo "Commits ahead: $(git rev-list --count @{u}..HEAD 2>/dev/null || echo '0')"

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                          PR - Pull Request Operations                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# PR command dispatcher
pr command *args:
    @just pr-{{command}} {{args}}

# Request PR reviews with AI-generated context
pr-request-review *args:
    @huginn pr request-review {{args}}

# Enhance PR description with AI analysis
pr-enhance *args:
    @huginn pr enhance {{args}}

# Show last PR review
pr-last-review command *args:
    @huginn pr-last-review {{command}} {{args}}

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                          EXTRACT - Data Extraction                          ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Extract command dispatcher
extract command *args:
    @just extract-{{command}} {{args}}

# Extract GitHub data (commits + PRs)
extract-github org days="7":
    @echo "📊 Extracting GitHub data for {{org}} (last {{days}} days)..."
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @if [ {{days}} -gt 90 ]; then echo "⚠️  Large extraction ({{days}} days) - this may take time"; fi
    @cd src && uv run python -m git_extraction.cli --org {{org}} --days {{days}}
    @echo ""
    @echo "📄 Generated files:"
    @ls -lh src/org_*.csv 2>/dev/null || echo "No output files generated"
    @echo "✅ Extraction complete"

# Extract GitHub commits only
extract-github-commits org days="30":
    @echo "📊 Extracting GitHub commits for {{org}} ({{days}} days)..."
    @uv run python scripts/test_commits_extraction.py {{org}} {{days}}

# Extract GitHub PRs only
extract-github-prs org days="30":
    @echo "📊 Extracting GitHub PRs for {{org}} ({{days}} days)..."
    @uv run python scripts/test_prs_extraction.py {{org}} {{days}}

# Extract Linear tickets
extract-linear org days="30":
    @echo "📊 Extracting Linear tickets for {{org}} ({{days}} days)..."
    @uv run python scripts/test_linear_extraction.py {{org}} {{days}}

# Extract Linear cycle data for team
extract-linear-cycles team output="linear_cycles.csv":
    @echo "📊 Extracting Linear cycle data for team {{team}}..."
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @uv run python scripts/extract_linear_cycles.py --team {{team}} --output {{output}}
    @if [ -f "{{output}}" ]; then \
        echo "✅ Extracted to {{output}}"; \
        wc -l {{output}} | awk '{print "  📄 " $$1-1 " cycle issues"}'; \
    else \
        echo "❌ Extraction failed"; \
    fi

# List all repositories for organization
extract-list-repos org:
    @echo "📋 Listing repositories for {{org}}..."
    @uv run python -c "import os, sys; sys.path.insert(0, 'src'); from git_extraction.git_extractor import GitDataExtractor; extractor = GitDataExtractor(os.getenv('GITHUB_TOKEN')); repos = extractor.get_organization_repos('{{org}}'); [print(f'{repo[\"name\"]:40} {repo[\"description\"] or \"No description\"}') for repo in repos]"

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                        CHART - Visualization Generation                     ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Chart command dispatcher
chart command *args:
    @just chart-{{command}} {{args}}

# Generate metrics charts (commits + PRs)
chart-metrics commits prs output="{{CHARTS_DIR}}":
    @echo "📊 Generating metrics charts..."
    @echo "  Commits: {{commits}}"
    @echo "  PRs: {{prs}}"
    @echo "  Output: {{output}}"
    @echo ""
    @uv run python scripts/generate_metrics_charts.py --commits {{commits}} --prs {{prs}} --output {{output}}
    @echo ""
    @ls -1 {{output}}/*.png 2>/dev/null | wc -l | awk '{print "✅ Generated " $$1 " charts in {{output}}/"}' || echo "❌ No charts generated"

# Generate all charts including Linear cycles
chart-all commits prs cycles output="{{CHARTS_DIR}}":
    @echo "📊 Generating comprehensive charts..."
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @echo "  Commits: {{commits}}"
    @echo "  PRs: {{prs}}"
    @echo "  Cycles: {{cycles}}"
    @echo "  Output: {{output}}"
    @echo ""
    @if [ -f "{{cycles}}" ]; then \
        uv run python scripts/generate_metrics_charts.py --commits {{commits}} --prs {{prs}} --cycles {{cycles}} --output {{output}}; \
    else \
        echo "⚠️  Cycles file not found, generating without cycles"; \
        uv run python scripts/generate_metrics_charts.py --commits {{commits}} --prs {{prs}} --output {{output}}; \
    fi
    @echo ""
    @ls -1 {{output}}/*.png 2>/dev/null | wc -l | awk '{print "✅ Generated " $$1 " charts in {{output}}/"}' || echo "❌ No charts generated"

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                        AI-USAGE - AI Usage Tracking                         ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# AI usage command dispatcher
ai-usage command *args:
    @just ai-usage-{{command}} {{args}}

# Collect AI usage data (ccusage + ccusage-codex) - auto-detects developer from git
ai-usage-collect developer="" days="7":
    #!/usr/bin/env bash
    set -euo pipefail
    if [ -n "{{developer}}" ]; then
        echo "📊 Collecting AI usage for {{developer}} (last {{days}} days)..."
        uv run hermod collect --developer "{{developer}}" --days {{days}}
    else
        echo "📊 Collecting AI usage (auto-detecting developer from git)..."
        uv run hermod collect --days {{days}}
    fi

# Ingest submitted AI usage data with deduplication
ai-usage-ingest:
    @echo "📥 Ingesting AI usage submissions..."
    @uv run python scripts/ingest_ai_usage.py

# Generate AI usage charts (daily/weekly cost and tokens)
ai-usage-charts output="charts":
    @echo "📊 Generating AI usage charts..."
    @uv run python scripts/generate_ai_usage_charts.py data/ai_usage/ingested {{output}}

# Complete pipeline: collect → ingest → charts (auto-detects developer if not provided)
ai-usage-pipeline developer="" days="7" output="charts":
    @just ai-usage-collect {{developer}} {{days}}
    @just ai-usage-ingest
    @just ai-usage-charts {{output}}

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                            TEST - Testing Operations                         ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Test command dispatcher
test command *args:
    @just test-{{command}} {{args}}

# Run all tests with coverage
test-all:
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

# Test GitHub integration
test-github:
    @echo "🐙 Testing GitHub integration..."
    @uv run python scripts/test_github_integration.py

# Test Linear integration
test-linear:
    @echo "🔗 Testing Linear integration..."
    @uv run python scripts/test_linear_integration.py

# Test extraction pipeline
test-extraction:
    @echo "📊 Testing extraction pipeline..."
    @./scripts/test_extraction.sh

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                          QUALITY - Code Quality Checks                      ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Quality command dispatcher
quality command *args:
    @just quality-{{command}} {{args}}

# Run linting with ruff
quality-lint:
    @echo "🔍 Linting with ruff..."
    @uv run python -m ruff check src/ tests/ scripts/

# Format code with ruff
quality-format:
    @echo "🎨 Formatting with ruff..."
    @uv run python -m ruff format src/ tests/ scripts/

# Run type checking with mypy
quality-typecheck:
    @echo "🔍 Type checking with mypy..."
    @uv run python -m mypy src/

# Run all quality checks
quality-check:
    @echo "🎯 Running full quality suite..."
    @just quality-lint
    @just quality-format
    @just quality-typecheck

# Generate coverage report
quality-coverage:
    @echo "📊 Generating coverage report..."
    @uv run python -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
    @echo "📈 Coverage report: htmlcov/index.html"

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                        CACHE - Cache Management (Unified)                   ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Cache command dispatcher
cache command *args:
    @just cache-{{command}} {{args}}

# Show cache statistics (API + Git)
cache-status:
    @echo "📊 Cache Status:"
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @if [ -d ".cache" ]; then \
        echo "📁 API Cache (.cache/):"; \
        echo "  $(find .cache -name '*.json' 2>/dev/null | wc -l | tr -d ' ') cache files"; \
        echo "  $(du -sh .cache 2>/dev/null | cut -f1 || echo '0B') total size"; \
    else \
        echo "📁 API Cache: Not found"; \
    fi
    @echo ""
    @if [ -d ".git_cache" ]; then \
        echo "📁 Git Cache (.git_cache/):"; \
        echo "  $(find .git_cache/repos -type d -name '.git' 2>/dev/null | wc -l | tr -d ' ') repositories"; \
        echo "  $(du -sh .git_cache 2>/dev/null | cut -f1 || echo '0B') total size"; \
    else \
        echo "📁 Git Cache: Not found"; \
    fi

# Clean cache (optionally for specific org)
cache-clean org="":
    @if [ -z "{{org}}" ]; then \
        echo "🧹 Cleaning all caches..."; \
        rm -rf .cache/*.json 2>/dev/null || true; \
        echo "✅ API cache cleaned"; \
        echo "ℹ️  Git cache preserved (use 'just cache rebuild' to clean)"; \
    else \
        echo "🧹 Cleaning cache for {{org}}..."; \
        rm -rf .git_cache/repos/{{org}}/ 2>/dev/null || true; \
        rm -rf .git_cache/state/{{org}}_*.json 2>/dev/null || true; \
        echo "✅ Cache cleaned for {{org}}"; \
    fi

# Rebuild cache (optionally for specific org)
cache-rebuild org="":
    @if [ -z "{{org}}" ]; then \
        echo "🔄 Rebuilding all caches..."; \
        echo "⚠️  This will remove ALL cached data. Continue? (y/N)"; \
        read -r confirm && [ "$$confirm" = "y" ] || (echo "Aborted" && exit 1); \
        rm -rf .cache/ .git_cache/; \
        mkdir -p .cache .git_cache/repos .git_cache/state; \
        echo "✅ All caches rebuilt"; \
    else \
        echo "🔄 Rebuilding cache for {{org}}..."; \
        rm -rf .git_cache/repos/{{org}}/ .git_cache/state/{{org}}_*.json; \
        echo "✅ Cache rebuilt for {{org}}"; \
        echo "ℹ️  Repositories will be re-cloned on next extraction"; \
    fi

# Validate cache integrity
cache-validate:
    @echo "🔍 Validating cache integrity..."
    @if [ -d ".cache" ]; then \
        echo "Checking API cache files..."; \
        find .cache -name '*.json' -exec sh -c 'jq . "$$1" >/dev/null 2>&1 || echo "❌ Invalid: $$1"' _ {} \; | head -10; \
        echo "✅ Validation complete"; \
    else \
        echo "No cache directory found"; \
    fi

