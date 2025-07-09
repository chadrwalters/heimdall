# North Star Metrics Justfile
# https://github.com/casey/just

# Default recipe to display help
default:
    @echo "🌟 North Star Metrics - Command Runner"
    @echo ""
    @echo "📋 Quick Start:"
    @echo "  just setup         - Initial project setup"
    @echo "  just env-check     - Check environment status"
    @echo "  just verify-apis   - Verify API connections"
    @echo "  just pilot <org>   - Run 7-day pilot analysis"
    @echo ""
    @echo "📚 All Commands:"
    @just --list

# Setup and Environment Management
# ================================

# Initial project setup
setup:
    @echo "🚀 Setting up North Star Metrics project..."
    uv venv
    uv pip sync pyproject.toml
    @echo "✅ Setup complete. Run 'source .venv/bin/activate' to activate environment"

# Install development dependencies
dev-setup:
    uv pip install -e '.[dev]'
    @echo "✅ Development dependencies installed"

# Verify all API connections
verify-apis:
    @echo "🔍 Verifying API connections..."
    python scripts/verify_apis.py

# Show environment variables status
env-check:
    @echo "📋 Environment Variables Status:"
    @test -n "${GITHUB_TOKEN:-}" && echo "GitHub Token: ✅ Set" || echo "GitHub Token: ❌ Not set"
    @test -n "${LINEAR_API_KEY:-}${LINEAR_TOKEN:-}" && echo "Linear API Key: ✅ Set" || echo "Linear API Key: ❌ Not set"
    @test -n "${ANTHROPIC_API_KEY:-}" && echo "Anthropic API Key: ✅ Set" || echo "Anthropic API Key: ❌ Not set"

# Data Extraction
# ===============

# Run full data extraction for an organization
extract org days="7":
    @echo "📊 Extracting data for {{org}} (last {{days}} days)..."
    ./scripts/extraction/run_extraction.sh --org {{org}} --days {{days}}

# Run incremental extraction (only new data)
extract-incremental org:
    @echo "📊 Running incremental extraction for {{org}}..."
    ./scripts/extraction/run_extraction.sh --org {{org}} --incremental

# List all repositories for an organization
list-repos org:
    @echo "📋 Listing repositories for {{org}}..."
    ./scripts/extraction/list_repos.sh {{org}}

# Testing
# =======

# Run all tests
test:
    @echo "🧪 Running all tests..."
    uv run python -m pytest tests/ -v

# Run unit tests only
test-unit:
    @echo "🧪 Running unit tests..."
    uv run python -m pytest tests/ -v -k "not integration"

# Run integration tests only
test-integration:
    @echo "🧪 Running integration tests..."
    uv run python -m pytest tests/ -v -k "integration"

# Test Linear integration
test-linear:
    @echo "🔗 Testing Linear integration..."
    python scripts/test_linear_integration.py

# Test GitHub Actions analyzer
test-gh-analyzer:
    @echo "🤖 Testing GitHub Actions analyzer..."
    python scripts/test_github_action_analyzer.py

# Test analysis integration
test-analysis:
    @echo "🧠 Testing analysis integration..."
    python scripts/test_analysis_integration.py

# Analysis
# ========

# Run analysis on extracted data
analyze input="org_prs.csv":
    @echo "🧠 Running AI analysis on {{input}}..."
    python -m src.analysis.run_analysis {{input}}

# Run pilot analysis (7 days)
pilot org:
    @echo "🚀 Running pilot analysis for {{org}}..."
    just extract {{org}} 7
    just analyze

# TaskMaster Commands
# ===================

# Show next task
task-next:
    @echo "📋 Getting next task..."
    task-master next

# Show task details
task-show id:
    @echo "📋 Showing task {{id}}..."
    task-master show {{id}}

# Mark task as in-progress
task-start id:
    @echo "▶️ Starting task {{id}}..."
    task-master set-status --id={{id}} --status=in-progress

# Mark task as done
task-done id:
    @echo "✅ Completing task {{id}}..."
    task-master set-status --id={{id}} --status=done

# List tasks by status
task-list status="pending":
    @echo "📋 Listing {{status}} tasks..."
    task-master list --status={{status}}

# Show task progress
task-progress:
    @echo "📊 Task Progress..."
    task-master list

# GitHub Actions
# ==============

# Test PR analysis bot locally
test-pr-bot pr_number:
    @echo "🤖 Testing PR analysis bot on PR #{{pr_number}}..."
    cd .github/workflows && \
    gh pr view {{pr_number}} --json number,title,body,additions,deletions,changedFiles > pr_data.json && \
    gh pr diff {{pr_number}} > pr_diff.txt && \
    python ../../scripts/github_action_analyzer.py

# Development Helpers
# ===================

# Format Python code
format:
    @echo "🎨 Formatting Python code..."
    uv run ruff format src/ scripts/ tests/
    uv run ruff check --fix src/ scripts/ tests/

# Lint Python code
lint:
    @echo "🔍 Linting Python code..."
    ruff check src/ scripts/ tests/
    @echo "✅ Linting completed successfully!"

# Type check Python code (optional - requires mypy to be added)
typecheck:
    @echo "🔍 Type checking would require mypy..."
    @echo "💡 Consider adding 'mypy>=1.0.0' to dev-dependencies for type checking"

# Run all code quality checks
quality: format lint typecheck
    @echo "✅ All code quality checks passed!"

# Documentation
# =============

# Generate documentation
docs:
    @echo "📚 Generating documentation..."
    @echo "Documentation is in docs/ directory"
    @ls -la docs/

# Serve documentation locally
docs-serve:
    @echo "📚 Serving documentation at http://localhost:8000"
    cd docs && python -m http.server 8000

# List all documentation files
docs-list:
    @echo "📚 Documentation Files:"
    @find docs -name "*.md" -type f | sort

# Create a new documentation file
docs-new name:
    @echo "📝 Creating new documentation: docs/{{name}}.md"
    @touch docs/{{name}}.md
    @echo "# {{name}}" > docs/{{name}}.md
    @echo "" >> docs/{{name}}.md
    @echo "## Overview" >> docs/{{name}}.md
    @echo "" >> docs/{{name}}.md
    @echo "TODO: Add documentation content" >> docs/{{name}}.md
    @echo "✅ Created docs/{{name}}.md"

# Utility Commands
# ================

# Clean up generated files
clean:
    @echo "🧹 Cleaning up..."
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    rm -f .coverage
    rm -rf .pytest_cache
    rm -rf .mypy_cache
    @echo "✅ Cleanup complete"

# Show repository statistics
stats:
    @echo "📊 Repository Statistics:"
    @echo "Total Python files: $(find src scripts -name '*.py' | wc -l)"
    @echo "Total lines of code: $(find src scripts -name '*.py' -exec cat {} + | wc -l)"
    @echo "Total tests: $(find tests -name 'test_*.py' | wc -l)"

# Watch for file changes and run tests
watch:
    @echo "👁️ Watching for changes..."
    watchmedo shell-command \
        --patterns="*.py" \
        --recursive \
        --command='clear && just test' \
        src tests

# Docker Commands (if needed later)
# ==================================

# Build Docker image
docker-build:
    @echo "🐳 Building Docker image..."
    docker build -t north-star-metrics .

# Run in Docker
docker-run:
    @echo "🐳 Running in Docker..."
    docker run -it --rm \
        -v $(pwd):/app \
        -e GITHUB_TOKEN \
        -e LINEAR_API_KEY \
        -e ANTHROPIC_API_KEY \
        north-star-metrics

# Deployment
# ==========

# Deploy GitHub Actions workflow
deploy-gh-actions:
    @echo "🚀 Deploying GitHub Actions workflow..."
    @echo "Workflow already in .github/workflows/"
    @echo "Commit and push to deploy"

# Quick Commands
# ==============

# Run the next task from TaskMaster
next:
    @just task-next

# Start working on the next task
start-next:
    @task_id=$(task-master next --json | jq -r '.id' 2>/dev/null || echo ""); \
    if [ -n "$task_id" ]; then \
        echo "▶️ Starting task $task_id..."; \
        task-master set-status --id=$task_id --status=in-progress; \
    else \
        echo "❌ Could not determine next task ID"; \
    fi

# Quick pilot run
quick-pilot org="my-org":
    @just pilot {{org}}

# Scheduling Commands
# ===================

# Run main pipeline with all options
pipeline-run org mode="incremental" days="7" output="." force="false":
    @echo "🚀 Running pipeline for {{org}} in {{mode}} mode..."
    python main.py --org {{org}} --mode {{mode}} --days {{days}} --output-dir {{output}} {{ if force == "true" { "--force" } else { "" } }}

# Set up scheduled analysis (copy configuration template)
schedule-setup:
    @echo "⚙️ Setting up scheduled analysis..."
    @if [ ! -f config/schedule.conf ]; then \
        cp config/schedule.conf.example config/schedule.conf; \
        echo "✅ Created config/schedule.conf - please customize it"; \
    else \
        echo "⚠️ config/schedule.conf already exists"; \
    fi
    @echo "📝 Edit config/schedule.conf to set your organization and preferences"

# Test scheduled analysis script
schedule-test org="my-org":
    @echo "🧪 Testing scheduled analysis for {{org}}..."
    ./scripts/schedule_analysis.sh --org {{org}} --mode pilot

# Show cron examples for scheduling
schedule-help:
    @echo "📅 Scheduling Examples:"
    @echo ""
    @echo "1. Add to crontab (crontab -e):"
    @echo "   # Daily at 6 AM"
    @echo "   0 6 * * * $(pwd)/scripts/schedule_analysis.sh >/dev/null 2>&1"
    @echo ""
    @echo "   # Monday-Friday at 8 AM"
    @echo "   0 8 * * 1-5 $(pwd)/scripts/schedule_analysis.sh >/dev/null 2>&1"
    @echo ""
    @echo "2. GitHub Actions workflow:"
    @echo "   Already configured in .github/workflows/scheduled-analysis.yml"
    @echo "   Set GITHUB_ORG variable in repository settings"
    @echo ""
    @echo "3. Manual testing:"
    @echo "   just schedule-test your-org-name"

# Show today's progress
today:
    @echo "📅 Today's Progress:"
    @echo ""
    @echo "Completed tasks:"
    @task-master list --status=done --json 2>/dev/null | jq -r '.[] | select(.updated_at | startswith("'$(date +%Y-%m-%d)'")) | "  ✅ #\(.id): \(.title)"' || echo "  None today"
    @echo ""
    @echo "In progress:"
    @task-master list --status=in-progress --json 2>/dev/null | jq -r '.[] | "  ▶️ #\(.id): \(.title)"' || echo "  None"

# Full pipeline run
pipeline org="my-org" days="30":
    @echo "🚀 Running full pipeline for {{org}}..."
    just verify-apis
    just extract {{org}} {{days}}
    just analyze
    @echo "✅ Pipeline complete!"

# Data Quality & Validation
# =========================

# Run comprehensive data quality checks
validate-data file="unified_pilot_data.csv":
    @echo "🔍 Running data quality validation on {{file}}..."
    python scripts/validation/check_data_quality.py {{file}}

# Detect anomalies and outliers in data
detect-anomalies file="unified_pilot_data.csv" method="iqr":
    @echo "🚨 Detecting anomalies in {{file}} using {{method}} method..."
    python scripts/validation/detect_anomalies.py {{file}} --method {{method}}

# Check data consistency across files
check-consistency dir=".":
    @echo "🔄 Checking data consistency in {{dir}}..."
    python scripts/validation/check_data_consistency.py {{dir}}

# Run methodology validation
validate-methodology file="unified_pilot_data.csv" sample="20":
    @echo "✅ Running methodology validation on {{file}}..."
    python scripts/validation/validate_methodology.py {{file}} --sample-size {{sample}}

# Run all validation checks
validate-all file="unified_pilot_data.csv":
    @echo "🏁 Running all validation checks on {{file}}..."
    just validate-data {{file}}
    just detect-anomalies {{file}}
    just check-consistency
    just validate-methodology {{file}}
    @echo "✅ All validation checks complete!"

# Generate validation report summary
validation-summary:
    @echo "📊 Validation Results Summary:"
    @echo ""
    @if [ -d "validation_results" ]; then \
        echo "Recent validation reports:"; \
        ls -lt validation_results/*.json | head -5; \
        echo ""; \
        echo "Run 'just validate-all' to generate fresh reports"; \
    else \
        echo "No validation results found. Run 'just validate-all' first."; \
    fi

# Help Commands
# =============

# Show all available environment variables
help-env:
    @echo "🔍 Required Environment Variables:"
    @echo ""
    @echo "GITHUB_TOKEN       - GitHub personal access token"
    @echo "LINEAR_API_KEY     - Linear API key (or LINEAR_TOKEN)"
    @echo "ANTHROPIC_API_KEY  - Anthropic API key for Claude"
    @echo ""
    @echo "Set these in your .env file or export them in your shell"

# Show project structure
help-structure:
    @echo "📁 Project Structure:"
    @tree -d -L 2 --filesfirst

# Show common workflows
help-workflows:
    @echo "📋 Common Workflows:"
    @echo ""
    @echo "1. Initial Setup:"
    @echo "   just setup"
    @echo "   just verify-apis"
    @echo ""
    @echo "2. Run Pilot Analysis:"
    @echo "   just pilot your-org-name"
    @echo ""
    @echo "3. Development:"
    @echo "   just task-next"
    @echo "   just test"
    @echo "   just quality"
    @echo ""
    @echo "4. Full Pipeline:"
    @echo "   just pipeline your-org-name 30"