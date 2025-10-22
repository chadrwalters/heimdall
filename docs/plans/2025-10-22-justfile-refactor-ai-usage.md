# Justfile Refactor + AI Usage Tracking Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor justfile to activity-based dispatcher pattern and add AI usage tracking for Claude Code + Codex with daily/weekly cost/token charts.

**Architecture:**
1. Simplify justfile to 6 activity namespaces (extract, chart, test, quality, cache, env)
2. Remove unused analysis/monitoring/benchmark commands
3. Add AI usage tracking: collection script → ingestion with deduplication → chart generation

**Tech Stack:** Just (justfile), Python 3.11+, ccusage/ccusage-codex (npm), matplotlib/pandas for charts

---

## Task 1: Remove Unused Scripts and Code

**Files:**
- Delete: `scripts/run_load_tests.py`
- Delete: `scripts/github_action_analyzer.py`
- Delete: `scripts/rollout_manager.py`
- Delete: `scripts/circuit_breaker_monitor.py`
- Delete: `scripts/log_analyzer.py`
- Delete: `scripts/schedule_analysis.sh`

**Step 1: Verify which scripts are referenced in justfile**

Run: `grep -E "(run_load_tests|github_action_analyzer|rollout_manager|circuit_breaker|log_analyzer|schedule_analysis)" justfile`
Expected: Shows lines referencing these scripts

**Step 2: Remove unused scripts**

```bash
rm scripts/run_load_tests.py
rm scripts/github_action_analyzer.py
rm scripts/rollout_manager.py
rm scripts/circuit_breaker_monitor.py
rm scripts/log_analyzer.py
rm scripts/schedule_analysis.sh
```

**Step 3: Verify scripts are deleted**

Run: `ls scripts/`
Expected: Deleted files should not appear

**Step 4: Commit cleanup**

```bash
git add -A
git commit -m "chore: remove unused benchmark and monitoring scripts"
```

---

## Task 2: Backup Current Justfile

**Files:**
- Copy: `justfile` → `justfile.backup`

**Step 1: Create backup**

```bash
cp justfile justfile.backup
```

**Step 2: Verify backup created**

Run: `ls -la justfile*`
Expected: Shows both `justfile` and `justfile.backup`

**Step 3: Commit backup**

```bash
git add justfile.backup
git commit -m "chore: backup original justfile before refactor"
```

---

## Task 3: Create New Simplified Justfile Header

**Files:**
- Modify: `justfile:1-40`

**Step 1: Replace header section**

Replace lines 1-40 in `justfile` with:

```justfile
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

# Colors for output
RED := "\\033[0;31m"
GREEN := "\\033[0;32m"
YELLOW := "\\033[1;33m"
BLUE := "\\033[0;34m"
NC := "\\033[0m" # No Color

# Default - show help
_default:
    @just help
```

**Step 2: Verify syntax**

Run: `just --list 2>&1 | head -5`
Expected: Shows command list or error (we'll fix errors in next tasks)

**Step 3: Commit header**

```bash
git add justfile
git commit -m "refactor(justfile): add simplified activity-based header"
```

---

## Task 4: Implement Help Command

**Files:**
- Modify: `justfile` (after header, around line 40)

**Step 1: Add help command**

Add after header variables:

```justfile
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
```

**Step 2: Test help command**

Run: `just help`
Expected: Shows formatted help with all activity categories

**Step 3: Commit help system**

```bash
git add justfile
git commit -m "feat(justfile): implement activity-based help system"
```

---

## Task 5: Implement ENV Commands

**Files:**
- Modify: `justfile` (add env section)

**Step 1: Add env command dispatcher and implementations**

```justfile
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                          ENV - Environment Management                        ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Initial project setup with UV
env command *args:
    @just env-{{command}} {{args}}

# Set up development environment from scratch
env-setup:
    @echo "🚀 Setting up GitHub Linear Metrics project..."
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @which uv > /dev/null || (echo "❌ uv not found. Install: curl -LsSf https://astral.sh/uv/install.sh | sh" && exit 1)
    @echo "✅ UV found: $(uv --version)"
    @echo ""
    @echo "📦 Installing dependencies..."
    @uv sync
    @echo "✅ Dependencies installed"
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
```

**Step 2: Test env commands**

Run: `just env check`
Expected: Shows environment variable status

Run: `just env --list` or `just --list | grep env`
Expected: Shows env subcommands

**Step 3: Commit env commands**

```bash
git add justfile
git commit -m "feat(justfile): implement env activity namespace"
```

---

## Task 6: Implement EXTRACT Commands

**Files:**
- Modify: `justfile` (add extract section)

**Step 1: Add extract command dispatcher and implementations**

```justfile
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
```

**Step 2: Test extract commands**

Run: `just extract github --help` (should show error with usage)
Run: `just extract list-repos degree-analytics | head -5`
Expected: Lists first 5 repos

**Step 3: Commit extract commands**

```bash
git add justfile
git commit -m "feat(justfile): implement extract activity namespace"
```

---

## Task 7: Implement CHART Commands

**Files:**
- Modify: `justfile` (add chart section)

**Step 1: Add chart command dispatcher and implementations**

```justfile
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
```

**Step 2: Test chart commands (if you have data)**

Run: `just chart metrics src/org_commits.csv src/org_prs.csv`
Expected: Generates charts (or error if no data files)

**Step 3: Commit chart commands**

```bash
git add justfile
git commit -m "feat(justfile): implement chart activity namespace"
```

---

## Task 8: Implement TEST Commands

**Files:**
- Modify: `justfile` (add test section)

**Step 1: Add test command dispatcher and implementations**

```justfile
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
```

**Step 2: Test test commands**

Run: `just test unit`
Expected: Runs unit tests (or shows pytest not configured if no tests exist)

**Step 3: Commit test commands**

```bash
git add justfile
git commit -m "feat(justfile): implement test activity namespace"
```

---

## Task 9: Implement QUALITY Commands

**Files:**
- Modify: `justfile` (add quality section)

**Step 1: Add quality command dispatcher and implementations**

```justfile
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
```

**Step 2: Test quality commands**

Run: `just quality lint`
Expected: Runs ruff linting

**Step 3: Commit quality commands**

```bash
git add justfile
git commit -m "feat(justfile): implement quality activity namespace"
```

---

## Task 10: Implement CACHE Commands (Unified Git + API)

**Files:**
- Modify: `justfile` (add cache section)

**Step 1: Add cache command dispatcher and implementations**

```justfile
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
```

**Step 2: Test cache commands**

Run: `just cache status`
Expected: Shows cache statistics

Run: `just cache clean`
Expected: Cleans API cache

**Step 3: Commit cache commands**

```bash
git add justfile
git commit -m "feat(justfile): implement unified cache activity namespace"
```

---

## Task 11: Remove Old Command Definitions

**Files:**
- Modify: `justfile` (remove old commands)

**Step 1: Remove old sections from justfile**

Delete these entire sections (search for headers and remove):
- All `benchmark*` commands
- All `monitor*`, `status`, `health`, `logs`, `debug-*` commands
- All `analyze*`, `reanalyze` commands
- `pilot`, `pipeline`, `pipeline-with-linear` commands
- Old `extract`, `list-repos` (non-namespaced versions)
- Old `test`, `lint`, `format` (non-namespaced versions)
- Old `cache-*`, `git-*` (non-namespaced versions)
- Old `setup`, `env-check` (non-namespaced versions)

**Step 2: Verify no duplicate commands**

Run: `just --list | sort | uniq -d`
Expected: No output (no duplicates)

**Step 3: Verify all commands work**

Run: `just --list`
Expected: Shows only new activity-based commands

**Step 4: Commit cleanup**

```bash
git add justfile
git commit -m "refactor(justfile): remove old non-namespaced commands"
```

---

## Task 12: Create AI Usage Collection Script

**Files:**
- Create: `scripts/collect_ai_usage.py`

**Step 1: Write collection script**

Create `scripts/collect_ai_usage.py`:

```python
#!/usr/bin/env python3
"""Collect AI usage data from ccusage and ccusage-codex.

Generates combined JSON file with Claude Code and Codex usage for specified time period.
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any


def run_command(cmd: list[str]) -> Dict[str, Any]:
    """Run command and return parsed JSON output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running {cmd[0]}: {e.stderr}", file=sys.stderr)
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from {cmd[0]}: {e}", file=sys.stderr)
        return {}


def collect_usage(developer: str, days: int = 7) -> Dict[str, Any]:
    """Collect usage data from both ccusage and ccusage-codex.

    Args:
        developer: Developer canonical name
        days: Number of days to collect (default: 7)

    Returns:
        Combined usage data with metadata
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    since_str = start_date.strftime("%Y%m%d")

    print(f"📊 Collecting AI usage for {developer} (last {days} days)")
    print(f"   Date range: {start_date.date()} to {end_date.date()}")

    # Collect Claude Code usage
    print("   Fetching Claude Code usage...")
    claude_data = run_command([
        "ccusage", "daily", "--json", "--since", since_str
    ])

    # Collect Codex usage
    print("   Fetching Codex usage...")
    codex_data = run_command([
        "ccusage-codex", "daily", "--json", "--since", since_str
    ])

    # Combine with metadata
    combined = {
        "metadata": {
            "developer": developer,
            "collected_at": datetime.now().isoformat(),
            "date_range": {
                "start": start_date.date().isoformat(),
                "end": end_date.date().isoformat(),
                "days": days
            },
            "version": "1.0"
        },
        "claude_code": claude_data,
        "codex": codex_data
    }

    return combined


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python collect_ai_usage.py <developer> [days=7]")
        print("Example: python collect_ai_usage.py Chad 7")
        sys.exit(1)

    developer = sys.argv[1]
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 7

    # Collect data
    data = collect_usage(developer, days)

    # Generate output filename
    output_dir = Path("data/ai_usage/submissions")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_str = datetime.now().strftime("%Y%m%d")
    output_file = output_dir / f"ai_usage_{developer}_{date_str}_{timestamp}.json"

    # Write output
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\n✅ Usage data collected: {output_file}")
    print(f"   Claude Code: {len(data['claude_code'].get('daily', []))} days")
    print(f"   Codex: {len(data['codex'].get('daily', []))} days")

    # Show totals
    claude_totals = data['claude_code'].get('totals', {})
    codex_totals = data['codex'].get('totals', {})

    if claude_totals:
        print(f"\n💰 Claude Code Total Cost: ${claude_totals.get('totalCost', 0):.2f}")
        print(f"   Total Tokens: {claude_totals.get('totalTokens', 0):,}")

    if codex_totals:
        print(f"\n💰 Codex Total Cost: ${codex_totals.get('totalCost', 0):.2f}")
        print(f"   Total Tokens: {codex_totals.get('totalTokens', 0):,}")


if __name__ == "__main__":
    main()
```

**Step 2: Make script executable**

```bash
chmod +x scripts/collect_ai_usage.py
```

**Step 3: Test script (if ccusage installed)**

Run: `python scripts/collect_ai_usage.py TestDev 1`
Expected: Creates JSON file in `data/ai_usage/submissions/`

**Step 4: Commit collection script**

```bash
git add scripts/collect_ai_usage.py
git commit -m "feat(ai-usage): add usage collection script for ccusage/codex"
```

---

## Task 13: Add AI Usage Commands to Justfile

**Files:**
- Modify: `justfile` (add ai-usage section)

**Step 1: Add ai-usage namespace after chart section**

```justfile
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                        AI-USAGE - AI Usage Tracking                         ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# AI usage command dispatcher
ai-usage command *args:
    @just ai-usage-{{command}} {{args}}

# Collect AI usage data (ccusage + ccusage-codex)
ai-usage-collect developer days="7":
    @echo "📊 Collecting AI usage for {{developer}} (last {{days}} days)..."
    @uv run python scripts/collect_ai_usage.py {{developer}} {{days}}
```

**Step 2: Update help command to include ai-usage**

Add to help command after CHART section:

```justfile
    @echo ""
    @echo "🤖 AI-USAGE - AI Usage Tracking:"
    @echo "  just ai-usage collect <developer> [days=7]  Collect ccusage + codex data"
```

**Step 3: Test ai-usage command**

Run: `just ai-usage collect Chad 1`
Expected: Collects usage data (or shows error if ccusage not installed)

**Step 4: Commit ai-usage commands**

```bash
git add justfile
git commit -m "feat(justfile): add ai-usage activity namespace"
```

---

## Task 14: Update Help Command with Final Categories

**Files:**
- Modify: `justfile` help command

**Step 1: Verify help shows all new commands**

Run: `just help`
Expected: Shows all 7 activity categories (extract, chart, ai-usage, test, quality, cache, env)

**Step 2: Update QUICK START section in help**

Ensure help command shows:
```justfile
    @echo "🚀 QUICK START:"
    @echo "  just env setup                    Set up environment"
    @echo "  just env verify-apis              Test API connections"
    @echo "  just extract github <org> 30      Extract GitHub data"
    @echo "  just chart metrics commits.csv prs.csv  Generate charts"
    @echo "  just ai-usage collect <dev> 7     Track AI usage"
```

**Step 3: Commit help updates**

```bash
git add justfile
git commit -m "docs(justfile): update help with all activity namespaces"
```

---

## Task 15: Test All Activity Namespaces

**Files:**
- None (testing only)

**Step 1: Test each namespace**

```bash
# Test dispatchers work
just env check
just extract list-repos degree-analytics | head -3
just cache status
just test --help  # Should show error with available commands

# Test help for each activity
just help | grep -A 10 "EXTRACT"
just help | grep -A 10 "CHART"
just help | grep -A 10 "AI-USAGE"
```

**Step 2: Verify no old commands remain**

Run: `just --list | grep -v "^  [a-z]*-" | grep "  "`
Expected: Only shows namespaced commands (no old standalone commands)

**Step 3: Document verification**

Create verification checklist:
- [ ] `just help` shows all categories
- [ ] `just env setup` works
- [ ] `just extract github` shows usage error (needs args)
- [ ] `just chart metrics` shows usage error (needs args)
- [ ] `just ai-usage collect` shows usage error (needs args)
- [ ] `just test all` runs (or shows pytest not configured)
- [ ] `just quality lint` runs
- [ ] `just cache status` works

**Step 4: Commit test results**

```bash
git add -A
git commit -m "test: verify all activity namespaces functional"
```

---

## Task 16: Clean Up Backup and Finalize

**Files:**
- Delete: `justfile.backup`
- Update: `docs/INDEX.md` or relevant docs

**Step 1: Remove backup file**

```bash
rm justfile.backup
```

**Step 2: Update documentation references**

Update any docs that reference old justfile commands:
- `docs/setup-guide.md`
- `docs/usage-guide.md`
- `CLAUDE.md` component files

Change old commands to new namespace format.

**Step 3: Commit finalization**

```bash
git add -A
git commit -m "refactor: complete justfile activity-based refactor

- Simplified to 7 activity namespaces: extract, chart, ai-usage, test, quality, cache, env
- Removed unused commands: benchmark, monitor, analyze, workflows
- Unified cache management (git + API)
- Added AI usage tracking foundation
- Clean dispatcher pattern for all activities"
```

**Step 4: Create summary**

Run: `just --list | wc -l`
Expected: ~40-50 commands (down from ~100+)

---

## Next Steps

**Plan complete!** The justfile refactoring establishes the foundation for AI usage tracking.

**Remaining work (separate plan needed):**
1. **AI Usage Ingestion** - Script to process submitted JSON files with deduplication
2. **AI Usage Charts** - Chart generation matching existing metrics chart style
3. **Testing** - Unit tests for new scripts
4. **Documentation** - Update all docs with new command structure

**Implementation approach?**
- **Subagent-Driven** (this session): I dispatch subagent per task + review between
- **Parallel Session**: Open new session with `superpowers:executing-plans` for batch execution
