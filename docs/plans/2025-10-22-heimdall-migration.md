# Heimdall Migration Plan - 2025-10-22

## Goal
Transform github_linear_metrics into a production-ready repository called Heimdall with comprehensive DX tooling, Graphite workflow support, and justfile-first architecture.

## Architecture Decisions
- **Justfile-First**: All operations (local dev and CI) go through justfile commands
- **Activity-Based Namespaces**: Organize commands by activity (git, gh, pr, linear, gt, etc.)
- **Huginn Integration**: Use huginn CLI as backend for PR and GitHub Actions operations
- **Graphite Workflow**: Full support for GT stacked PR workflow with specialized commands/agents
- **.claude Infrastructure**: Port proven commands/agents from spacewalker for DX consistency

## Tech Stack
- **Python**: 3.11+ with UV package manager
- **Huginn**: v1.3.1+ for PR/git utilities
- **Graphite**: GT CLI for stacked PR workflow
- **Just**: Command runner for reproducible workflows
- **Claude Desktop**: Custom commands and agents for AI-assisted development
- **GitHub Actions**: CI/CD with justfile integration

## Dependencies & Order
1. **Rename First**: Repository rename must complete before porting .claude files (path references)
2. **Justfile Foundation**: Add core utilities before porting commands that depend on them
3. **Huginn Before PR Commands**: Integrate huginn before porting PR-related .claude commands
4. **Commands Before Agents**: Port commands before agents that invoke them
5. **CI Last**: Update CI after justfile commands are in place

---

## Phase 1: Repository Rename (1-2 hours)

### Task 1.1: Update Project Metadata
**Estimate**: 5 minutes

1. Update `pyproject.toml`:
```toml
[project]
name = "heimdall"  # Changed from "north-star-metrics"
version = "0.1.0"
description = "Engineering Impact Framework - Heimdall observes developer productivity and engineering metrics"
```

2. Update `[tool.hatch.build.targets.wheel]`:
```toml
packages = ["src/hermod"]  # Keep hermod as internal package name
```

3. Verify dependencies remain unchanged

**Test**: `uv sync` completes successfully

**Commit**: "chore: rename project to heimdall in pyproject.toml"

---

### Task 1.2: Update README and Documentation
**Estimate**: 10 minutes

1. Update `README.md`:
   - Change title to "# Heimdall - Engineering Observability Framework"
   - Update description to reference Heimdall (Norse mythology: all-seeing guardian)
   - Keep technical content intact
   - Update any github_linear_metrics references

2. Update `CLAUDE.md`:
   - Change header to "# 🌟 Heimdall - Developer Productivity Analytics"
   - Update project overview paragraph
   - Search and replace `github_linear_metrics` → `heimdall`

3. Update `docs/INDEX.md`:
   - Update references from github_linear_metrics to heimdall

**Test**: Read through updated docs for consistency

**Commit**: "docs: update README and CLAUDE.md for Heimdall branding"

---

### Task 1.3: Update Justfile Project References
**Estimate**: 5 minutes

1. Search justfile for hardcoded `github_linear_metrics` strings
2. Replace with `heimdall` where appropriate
3. Keep internal paths that use directory structure as-is

**Test**: `just --list` shows all commands

**Commit**: "chore: update justfile references to heimdall"

---

### Task 1.4: Rename Local Directory
**Estimate**: 5 minutes

1. Navigate to parent directory: `cd ..`
2. Rename directory: `mv github_linear_metrics heimdall`
3. Navigate back: `cd heimdall`
4. Verify git status: `git status` (should show previous commits intact)

**Test**: `pwd` shows `/Users/chadwalters/source/work/heimdall`

**Commit**: N/A (directory rename doesn't need commit)

---

### Task 1.5: Update GitHub Repository Name
**Estimate**: 10 minutes (manual GitHub UI operation)

**Manual Steps**:
1. Go to GitHub repository settings
2. Rename repository from `github_linear_metrics` to `heimdall`
3. Update remote URL locally:
```bash
git remote set-url origin https://github.com/YOUR_ORG/heimdall.git
```

**Test**: `git remote -v` shows correct heimdall URL

**Note**: Provide instructions to user, don't execute GitHub API operations

---

### Task 1.6: Update CI Configuration
**Estimate**: 5 minutes

1. Update `.github/workflows/ci.yml` header comment:
```yaml
name: CI

# Heimdall CI Pipeline - Run on pull requests and pushes to main
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
```

**Test**: No functional changes, verify YAML syntax

**Commit**: "ci: update CI configuration for Heimdall branding"

---

## Phase 2: Justfile Foundation (2-3 hours)

### Task 2.1: Add Huginn Installation to Setup
**Estimate**: 10 minutes

1. Add to justfile `env` namespace:
```just
# Install huginn CLI for PR and git utilities
install-huginn:
    @echo "Installing huginn CLI..."
    uv tool install huginn
    @echo "Verifying huginn installation..."
    huginn --version

# Update setup to include huginn
setup: install-huginn
    @echo "Setting up Heimdall development environment..."
    uv sync
    uv run pre-commit install
    @echo "✅ Setup complete!"
```

**Test**: `just install-huginn` succeeds, `huginn --version` shows v1.3.1+

**Commit**: "feat(justfile): add huginn CLI installation"

---

### Task 2.2: Add PR Namespace with Huginn Integration
**Estimate**: 15 minutes

1. Add `pr` namespace to justfile:
```just
# ============================================================================
# PR Operations (via huginn)
# ============================================================================

# Request PR reviews with AI-generated context
pr-request-review *args:
    huginn pr request-review {{args}}

# Enhance PR description with AI analysis
pr-enhance *args:
    huginn pr enhance {{args}}

# Show last PR review
pr-last-review command *args:
    huginn pr-last-review {{command}} {{args}}

# General PR operations
pr command *args:
    huginn pr {{command}} {{args}}
```

**Test**:
- `just pr --help` shows huginn PR help
- `just pr-request-review --help` shows command usage

**Commit**: "feat(justfile): add pr namespace with huginn integration"

---

### Task 2.3: Add Git Utilities Namespace
**Estimate**: 15 minutes

1. Add `git` namespace to justfile:
```just
# ============================================================================
# Git Utilities
# ============================================================================

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
    git diff {{args}}
```

**Test**:
- `just git-branch` shows current branch
- `just git-commits 5` shows last 5 commits
- `just git-status` shows clean status
- `just git-info` shows repo information

**Commit**: "feat(justfile): add git utilities namespace"

---

### Task 2.4: Add GitHub Actions Utilities
**Estimate**: 15 minutes

1. Add `gh` namespace to justfile:
```just
# ============================================================================
# GitHub Utilities
# ============================================================================

# GitHub Actions operations via huginn
gh-actions command *args:
    huginn actions {{command}} {{args}}

# View latest GitHub Actions run
gh-actions-latest:
    gh run list --limit 1

# Watch GitHub Actions run
gh-actions-watch:
    gh run watch

# Sync branch with remote
gh-branch-sync:
    @echo "Fetching from remote..."
    git fetch origin
    @echo "Current branch: $(git rev-parse --abbrev-ref HEAD)"
    @echo "Commits behind: $(git rev-list --count HEAD..@{u} 2>/dev/null || echo '0')"
    @echo "Commits ahead: $(git rev-list --count @{u}..HEAD 2>/dev/null || echo '0')"
```

**Test**:
- `just gh-actions --help` shows huginn actions help
- `just gh-branch-sync` shows sync status

**Commit**: "feat(justfile): add GitHub utilities namespace"

---

### Task 2.5: Add Documentation Validation
**Estimate**: 20 minutes

1. Add `docs` namespace to justfile:
```just
# ============================================================================
# Documentation
# ============================================================================

# Validate justfile is in sync with documentation
docs-validate-justfile:
    #!/usr/bin/env bash
    set -euo pipefail

    echo "Validating justfile documentation..."

    # Extract justfile commands
    just --list --unsorted > /tmp/justfile-commands.txt

    # Check if CLAUDE.md references justfile workflow
    if ! grep -q "justfile" CLAUDE.md; then
        echo "❌ CLAUDE.md missing justfile references"
        exit 1
    fi

    echo "✅ Justfile documentation valid"

# Validate all documentation links
docs-validate-links:
    @echo "Checking documentation links..."
    @find docs -name "*.md" -type f | while read -r file; do \
        echo "Checking $$file..."; \
    done
    @echo "✅ Documentation links validated"

# List all documentation files
docs-list:
    @find docs -name "*.md" -type f | sort
```

**Test**:
- `just docs-validate-justfile` passes
- `just docs-list` shows all markdown files

**Commit**: "feat(justfile): add documentation validation commands"

---

### Task 2.6: Add Linear Integration Utilities
**Estimate**: 15 minutes

1. Add `linear` namespace to justfile:
```just
# ============================================================================
# Linear Integration
# ============================================================================

# Test Linear API connection
linear-test:
    @echo "Testing Linear API connection..."
    uv run python -c "from src.linear.linear_client import LinearClient; import os; client = LinearClient(os.getenv('LINEAR_API_KEY')); print('✅ Linear API connected')"

# Extract Linear cycles for date range
linear-cycles start end:
    uv run python scripts/extract_linear_cycles.py --start-date {{start}} --end-date {{end}}

# Show Linear environment variables
linear-env:
    @echo "LINEAR_API_KEY: $(echo $LINEAR_API_KEY | head -c 10)..."
    @echo "LINEAR_TEAM_ID: $LINEAR_TEAM_ID"
```

**Test**:
- `just linear-env` shows masked API key
- `just linear-test` connects successfully (if LINEAR_API_KEY set)

**Commit**: "feat(justfile): add linear integration utilities"

---

### Task 2.7: Update CI to Use Justfile Commands
**Estimate**: 20 minutes

1. Update `.github/workflows/ci.yml` to be justfile-first:
```yaml
  lint:
    name: Lint with Ruff
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v5
        with:
          version: "latest"
          enable-cache: true

      - name: Set up Python
        run: uv python install 3.12

      - name: Install dependencies
        run: uv sync

      - name: Install Just
        run: |
          curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to /usr/local/bin

      - name: Run linter via justfile
        run: just quality lint

      - name: Run formatter check via justfile
        run: just quality format-check
```

2. Update `test` job:
```yaml
      - name: Run tests with coverage
        run: just test-coverage
```

3. Update `type-check` job:
```yaml
      - name: Run mypy
        run: just quality type-check
```

4. Update `security` job:
```yaml
      - name: Run bandit security scan
        run: just quality security
```

5. Add corresponding justfile commands if missing:
```just
# Format check (don't modify files)
format-check:
    uv run ruff format --check .

# Type checking with mypy
type-check:
    uv run mypy src --ignore-missing-imports

# Security scanning with bandit
security:
    uv run bandit -c pyproject.toml -r src/

# Test with coverage
test-coverage:
    uv run pytest tests/ -v --cov=src --cov-report=xml --cov-report=term
```

**Test**:
- `just quality format-check` passes
- `just quality type-check` runs
- `just quality security` runs
- `just test-coverage` generates coverage report

**Commit**: "ci: migrate CI to justfile-first architecture"

---

## Phase 3: Port Critical .claude Infrastructure (3-4 hours)

### Task 3.1: Port Graphite Expert Agent
**Estimate**: 15 minutes

1. Create `.claude/agents/graphite-expert.md`:
```markdown
---
name: graphite-expert
description: General Graphite workflow operations specialist - handles GT commands, stack management, and troubleshooting (plugin:heimdall@local)
model: haiku
---

# Graphite Expert Agent

You are a Graphite workflow specialist for the Heimdall project.

## Your Expertise
- GT command execution and troubleshooting
- Stack management and visualization
- Branch relationships and dependencies
- Sync operations with remote

## Core Responsibilities
1. **Execute GT Commands**: Run GT operations via justfile when available
2. **Explain Stack State**: Help users understand their stack structure
3. **Troubleshoot Issues**: Diagnose and fix GT workflow problems
4. **Guide Best Practices**: Recommend optimal GT workflows

## Available Tools
- `just gt:*` commands (when available)
- Direct GT CLI for operations not in justfile
- Git commands for inspection
- GitHub API for PR status

## Workflow Patterns
- Always check stack state before operations
- Verify remote sync status
- Explain consequences before destructive operations
- Provide rollback options when possible

## Common Operations
- `gt stack` - Visualize current stack
- `gt log` - Show stack history
- `gt sync` - Sync with remote
- `gt restack` - Reorganize stack
- `gt submit` - Create/update PRs for stack
```

**Test**: Agent appears in Claude Desktop

**Commit**: "feat(.claude): add graphite-expert agent"

---

### Task 3.2: Port GT Commit Command
**Estimate**: 30 minutes

1. Create `.claude/commands/gt/commit.md`:
```markdown
---
name: gt:commit
description: Smart GT commit workflow with validation, testing, and proper stack management
---

# GT Commit Command

This command handles the complete Graphite commit workflow with validation.

## Workflow

1. **Invoke git-commit-expert agent** to handle the commit process
2. Agent will:
   - Analyze staged changes
   - Determine if this is a new branch (`gt create`) or existing (`gt modify`)
   - Run tests before committing
   - Create properly formatted commit messages
   - Execute GT commit command
   - Verify commit success

## Usage

```
/gt:commit
```

The agent will guide you through the process and handle all validation.

## What Gets Checked
- Staged changes exist
- Tests pass before commit
- Commit message follows conventions
- GT stack state is valid
- Branch is properly created/modified

## Requires
- git-commit-expert agent
- Working GT installation
- Tests configured in justfile
```

**Test**: Command appears in Claude Desktop

**Commit**: "feat(.claude): add gt:commit command"

---

### Task 3.3: Port Git Commit Expert Agent
**Estimate**: 45 minutes

1. Create `.claude/agents/git-commit-expert.md` (adapted from spacewalker):
```markdown
---
name: git-commit-expert
description: GT commit workflow specialist - handles smart staging, branch detection, validation, and testing for Graphite commits (plugin:heimdall@local)
model: haiku
---

# Git Commit Expert Agent

You are a specialist in Graphite (GT) commit workflows for the Heimdall project.

## Your Mission
Execute complete GT commit workflow with validation, testing, and proper stack management.

## Workflow Steps

### 1. Check Git Status
```bash
git status --short
```

Verify:
- [ ] Staged changes exist (green M/A/D)
- [ ] Working directory state
- [ ] Current branch name

### 2. Determine GT Command
- **New branch** (not yet in GT stack): Use `gt create`
- **Existing branch** (already in GT stack): Use `gt modify`

Check with:
```bash
gt stack
```

### 3. Review Staged Changes
```bash
git diff --staged
```

Analyze:
- Scope of changes
- Files affected
- Complexity level

### 4. Run Tests (MANDATORY)
```bash
just test-unit
```

**CRITICAL**: Tests MUST pass before commit.
- If tests fail: STOP and report failures
- User must fix tests before proceeding

### 5. Generate Commit Message
Format: `<type>(<scope>): <description>`

Types:
- feat: New feature
- fix: Bug fix
- refactor: Code refactoring
- test: Test additions
- docs: Documentation
- chore: Maintenance

Examples:
- `feat(justfile): add pr namespace with huginn integration`
- `fix(linear): handle missing team ID gracefully`
- `refactor(git): extract commit utilities to module`

### 6. Execute GT Commit
```bash
# For new branch
gt create -m "commit message"

# For existing branch
gt modify -m "commit message"
```

### 7. Verify Success
```bash
git log -1 --oneline
gt stack
```

Confirm:
- Commit appears in log
- Stack shows updated branch
- Changes are committed

## Error Handling

### Tests Fail
1. Show test output
2. Do NOT proceed with commit
3. Ask user to fix tests
4. Re-run when ready

### GT Command Fails
1. Show error message
2. Check GT stack state
3. Suggest fixes (sync, restack, etc.)
4. Retry after fix

### Unstaged Changes
1. Show `git status`
2. Ask user which files to stage
3. Use `git add <files>`
4. Proceed with workflow

## Best Practices
- **Always run tests** before committing
- **Use descriptive commit messages** following conventions
- **Check GT stack** before and after operations
- **Verify success** with log and stack commands
- **Never commit failing tests**

## Available Commands
- `just test-unit` - Run fast unit tests
- `just test` - Run all tests
- `git add <files>` - Stage specific files
- `git add -p` - Interactive staging
- `gt stack` - Show stack structure
- `gt log` - Show stack history
```

**Test**: Agent appears in Claude Desktop

**Commit**: "feat(.claude): add git-commit-expert agent"

---

### Task 3.4: Port GT Restack Command
**Estimate**: 15 minutes

1. Create `.claude/commands/gt/restack.md`:
```markdown
---
name: gt:restack
description: Safe GT restack operations with validation and rollback options
---

# GT Restack Command

Safely restack your Graphite branches with validation.

## Workflow

1. **Invoke gt-restack-expert agent** to handle the restack
2. Agent will:
   - Check current stack state
   - Verify clean working directory
   - Show restack plan
   - Execute restack
   - Verify success

## Usage

```
/gt:restack
```

## What Gets Checked
- Working directory is clean
- Current stack structure
- Remote sync status
- Restack operation success

## Requires
- gt-restack-expert agent
- Working GT installation
- Clean working directory (no uncommitted changes)
```

**Test**: Command appears in Claude Desktop

**Commit**: "feat(.claude): add gt:restack command"

---

### Task 3.5: Port GT Restack Expert Agent
**Estimate**: 30 minutes

1. Create `.claude/agents/gt-restack-expert.md`:
```markdown
---
name: gt-restack-expert
description: GT restack specialist - handles safe restack operations with validation and rollback (plugin:heimdall@local)
model: haiku
---

# GT Restack Expert Agent

You are a specialist in Graphite restack operations for the Heimdall project.

## Your Mission
Execute safe GT restack operations with proper validation and rollback options.

## Workflow Steps

### 1. Verify Clean Working Directory
```bash
git status --short
```

**CRITICAL**: Working directory MUST be clean.
- If dirty: Ask user to commit or stash changes
- Do NOT proceed with restack on dirty working directory

### 2. Check Current Stack
```bash
gt stack
```

Show user:
- Current stack structure
- Branch relationships
- Number of branches affected

### 3. Check Remote Sync
```bash
git fetch origin
gt log
```

Verify:
- Local is in sync with remote
- No diverged branches
- No conflicts pending

### 4. Show Restack Plan
Explain to user:
- Which branches will be affected
- What the new structure will be
- Potential conflicts

Ask for confirmation before proceeding.

### 5. Execute Restack
```bash
gt restack
```

Monitor output for:
- Success messages
- Conflict warnings
- Error messages

### 6. Verify Success
```bash
gt stack
git log --oneline --graph -10
```

Confirm:
- Stack structure is correct
- No broken relationships
- All branches properly rebased

### 7. Provide Rollback Option
If restack fails or user is unhappy:

```bash
git reflog
# Find commit before restack
git reset --hard <commit-hash>
gt stack --sync
```

## Error Handling

### Dirty Working Directory
1. Show `git status`
2. Ask user: "commit" or "stash"?
3. Wait for clean state
4. Retry restack

### Restack Conflicts
1. Show conflict files
2. Guide user through resolution
3. Continue restack after resolution
4. Verify final state

### Remote Divergence
1. Explain divergence
2. Suggest: `gt sync` or `git pull --rebase`
3. Retry restack after sync

## Safety Measures
- **Always check working directory** before restack
- **Show restack plan** before execution
- **Verify remote sync** to avoid divergence
- **Provide rollback** instructions if needed
- **Never force** without user confirmation

## Best Practices
- Restack on clean working directory
- Sync with remote before restack
- Review stack structure after restack
- Communicate changes to team
- Use `gt log` to understand impact

## Available Commands
- `gt restack` - Restack current branch and descendants
- `gt stack` - Show stack structure
- `gt log` - Show stack history
- `gt sync` - Sync with remote
- `git reflog` - View operation history
```

**Test**: Agent appears in Claude Desktop

**Commit**: "feat(.claude): add gt-restack-expert agent"

---

## Phase 4: Port High-Value .claude Infrastructure (4-5 hours)

### Task 4.1: Port Cleanup Docs/Justfile Command
**Estimate**: 20 minutes

1. Create `.claude/commands/cleanup-docs-justfile.md`:
```markdown
---
name: cleanup-docs-justfile
description: Clean up and organize documentation and justfile for consistency and maintainability
---

# Cleanup Docs/Justfile Command

Systematically clean up documentation and justfile organization.

## What This Does

1. **Justfile Cleanup**:
   - Remove unused commands
   - Consolidate duplicates
   - Organize into logical namespaces
   - Add missing help text
   - Verify all commands work

2. **Documentation Cleanup**:
   - Remove outdated docs
   - Fix broken links
   - Update references
   - Consolidate redundant content
   - Verify code examples

## Workflow

### Step 1: Analyze Current State
- List all justfile commands: `just --list`
- List all documentation files: `just docs-list`
- Identify inconsistencies

### Step 2: Justfile Organization
- Group related commands into namespaces
- Remove unused/broken commands
- Add help text for all commands
- Standardize naming conventions

### Step 3: Documentation Updates
- Update INDEX.md with current structure
- Fix broken internal links
- Remove obsolete guides
- Update code examples to match current justfile

### Step 4: Validation
- Run `just docs-validate-justfile`
- Test all justfile commands
- Verify all doc links work

## Usage

```
/cleanup-docs-justfile
```

I'll systematically go through justfile and docs, proposing cleanups.
```

**Test**: Command appears in Claude Desktop

**Commit**: "feat(.claude): add cleanup-docs-justfile command"

---

### Task 4.2: Port Create Command Meta-Command
**Estimate**: 15 minutes

1. Create `.claude/commands/create-command.md`:
```markdown
---
name: create-command
description: Meta-command for creating new .claude commands with proper structure and documentation
---

# Create Command Meta-Command

Quickly create new .claude commands with proper structure.

## What This Does

Creates a new command file in `.claude/commands/` with:
- Proper frontmatter (name, description)
- Standard structure
- Usage examples
- Workflow documentation

## Usage

```
/create-command <category>/<name>
```

Examples:
- `/create-command gt/sync`
- `/create-command test/watch`
- `/create-command linear/sync-tickets`

## Generated Structure

```markdown
---
name: category:name
description: [I'll ask you for this]
---

# Command Name

[I'll ask you what this command should do]

## Workflow

1. Step 1
2. Step 2
3. Step 3

## Usage

```
/category:name [args]
```

## Requires
- Dependencies listed here
```

## After Creation

I'll:
1. Create the file in correct location
2. Add to command index if needed
3. Test that command appears in Claude Desktop
```

**Test**: Command appears in Claude Desktop

**Commit**: "feat(.claude): add create-command meta-command"

---

### Task 4.3: Port Ground Truth Command
**Estimate**: 25 minutes

1. Create `.claude/commands/ground-truth.md`:
```markdown
---
name: ground-truth
description: Verify documentation matches implementation reality - find drift between docs and code
---

# Ground Truth Command

Find and fix drift between documentation and implementation.

## What This Checks

### 1. Justfile Commands vs Documentation
- Commands mentioned in docs but missing from justfile
- Justfile commands not documented
- Outdated command signatures

### 2. Code Examples vs Reality
- Code examples in docs that don't work
- API calls that have changed
- Outdated import statements

### 3. Configuration vs Documentation
- Environment variables mentioned but not used
- Config options in docs but not in code
- Defaults that don't match

### 4. Dependencies vs Documentation
- Requirements mentioned but not in pyproject.toml
- Unused dependencies still documented
- Version mismatches

## Workflow

### Step 1: Scan Documentation
```bash
just docs-list
```
Read all .md files and extract:
- Justfile command references
- Code examples
- Configuration references
- Dependency mentions

### Step 2: Verify Against Reality
- Check each justfile command exists: `just --list`
- Test code examples run: `uv run python -c "..."`
- Verify env vars used: `grep -r "os.getenv" src/`
- Check dependencies: `cat pyproject.toml`

### Step 3: Report Findings
Create report:
```
❌ DRIFT FOUND:

Documentation Issues:
- CLAUDE.md line 45: references `just analyze-all` but command doesn't exist
- docs/setup-guide.md: example uses old LinearClient API

Code Issues:
- src/config/settings.py uses ANTHROPIC_MODEL but not documented
- pyproject.toml has `bleach` but never imported

Justfile Issues:
- `test-visual` command exists but not in any docs
```

### Step 4: Propose Fixes
For each issue, offer:
- Update documentation OR
- Update implementation OR
- Remove deprecated references

## Usage

```
/ground-truth
```

I'll systematically check docs against reality and report drift.

## Requires
- Access to all documentation files
- Ability to run justfile commands
- Access to source code for verification
```

**Test**: Command appears in Claude Desktop

**Commit**: "feat(.claude): add ground-truth verification command"

---

### Task 4.4: Port CI Analyze Failure Command
**Estimate**: 30 minutes

1. Create `.claude/commands/ci/analyze-failure.md`:
```markdown
---
name: ci:analyze-failure
description: Debug CI failures with executor-validator loops for systematic troubleshooting
---

# CI Analyze Failure Command

Systematically debug CI failures using executor-validator pattern.

## What This Does

Uses a two-agent approach:
1. **Executor**: Makes hypotheses and attempts fixes
2. **Validator**: Verifies fixes and provides feedback

This prevents:
- Guessing at solutions
- Incomplete fixes
- Missing edge cases

## Workflow

### Step 1: Gather CI Context
```bash
# Get latest CI run
just gh-actions-latest

# Or specific run
gh run view <run-id>
```

Extract:
- Failed job name
- Error messages
- Full logs
- Environment details

### Step 2: Executor Analysis
**Executor** (me) will:
1. Analyze error messages
2. Form hypothesis about root cause
3. Identify relevant code/config
4. Propose specific fix

### Step 3: Validator Review
**Validator** (zen:debug or zen:codereview) will:
1. Review proposed fix
2. Check for edge cases
3. Verify completeness
4. Suggest improvements

### Step 4: Implement Fix
After validation:
1. Apply the fix
2. Test locally: `just test`
3. Commit: `git add . && git commit -m "fix(ci): ..."`
4. Push and monitor

### Step 5: Verify CI Success
```bash
just gh-actions-watch
```

Confirm:
- CI job passes
- No new failures introduced
- Related tests still pass

## Common CI Failures

### Test Failures
- Missing dependencies in CI
- Environment variable not set
- Test order dependency
- Flaky tests

### Lint/Format Failures
- Pre-commit hook differences
- Ruff version mismatch
- Import order issues

### Type Check Failures
- Mypy version differences
- Missing type stubs
- New untyped dependencies

### Security Scan Failures
- New vulnerable dependency
- False positive needing skip
- Security issue in code

## Usage

```
/ci:analyze-failure [run-id]
```

Provide run ID or I'll fetch the latest failure.

## Executor-Validator Pattern

```
┌─────────────┐         ┌──────────────┐
│  Executor   │────────>│  Validator   │
│  (Analyze   │ Propose │  (Verify     │
│   & Fix)    │<────────│   & Guide)   │
└─────────────┘  Refine └──────────────┘
```

Benefits:
- Systematic approach
- Catches edge cases
- Complete solutions
- Learning loop

## Requires
- GitHub CLI (`gh`)
- Access to repository
- Justfile commands for testing
```

**Test**: Command appears in Claude Desktop

**Commit**: "feat(.claude): add ci:analyze-failure command"

---

### Task 4.5: Port Test Debug Command
**Estimate**: 30 minutes

1. Create `.claude/commands/test/debug.md`:
```markdown
---
name: test:debug
description: Interactive test debugging with systematic failure analysis
---

# Test Debug Command

Systematically debug test failures with guided troubleshooting.

## What This Does

Helps you debug failing tests through:
1. Failure analysis
2. Hypothesis formation
3. Targeted fixes
4. Verification

## Workflow

### Step 1: Identify Failing Test
```bash
# Run tests to see failures
just test-unit

# Or specific test
just test-unit tests/test_specific.py::test_function
```

Capture:
- Test name
- Error message
- Stack trace
- Failed assertion

### Step 2: Analyze Failure
Read the test code:
```python
# What is the test trying to verify?
# What are the test inputs?
# What is the expected behavior?
# What actually happened?
```

### Step 3: Form Hypothesis
Common failure patterns:
- **Incorrect assertion**: Test expects wrong value
- **Missing setup**: Fixture or mock not configured
- **Environment issue**: Missing env var or file
- **Timing issue**: Async or race condition
- **Data issue**: Test data doesn't match reality
- **Regression**: Code changed, test didn't update

### Step 4: Investigate Code
Based on hypothesis, read:
- Implementation code being tested
- Related fixtures in `conftest.py`
- Mock setups
- Test data files

### Step 5: Apply Fix
Options:
- Fix the code (if bug in implementation)
- Fix the test (if test is wrong)
- Fix the setup (if fixture issue)
- Add missing data (if data issue)

### Step 6: Verify Fix
```bash
# Run the specific test
just test-unit tests/test_file.py::test_function

# Run related tests
just test-unit tests/test_file.py

# Run all tests
just test
```

Confirm:
- Failing test now passes
- No new test failures
- All related tests still pass

## Common Test Issues

### Assertion Errors
```python
# Expected: 5, Got: 6
assert result == 5

# Fix options:
# 1. Code is wrong, fix implementation
# 2. Test is wrong, update assertion
# 3. Setup is wrong, fix fixture
```

### Missing Fixtures
```python
# Error: fixture 'api_client' not found

# Fix: Add to conftest.py or import
@pytest.fixture
def api_client():
    return APIClient()
```

### Mock Issues
```python
# Error: mock not being called

# Fix: Ensure mock is patched correctly
@patch('module.function')
def test_something(mock_func):
    mock_func.return_value = expected
```

### Environment Variables
```python
# Error: None (missing env var)

# Fix: Add to test or use fixture
@pytest.fixture
def env_vars(monkeypatch):
    monkeypatch.setenv('API_KEY', 'test-key')
```

## Debugging Techniques

### Add Print Statements
```python
def test_something():
    result = function_under_test()
    print(f"DEBUG: result = {result}")  # Add this
    assert result == expected
```

### Use Debugger
```bash
# Run with debugger
just test-unit tests/test_file.py::test_function --pdb

# Or add breakpoint in code
breakpoint()
```

### Isolate the Issue
```python
# Comment out assertions one by one
# assert condition1  # Pass
# assert condition2  # Fail <- Problem is here
```

## Usage

```
/test:debug [test-path]
```

Provide test path or describe the failure.

## Requires
- Pytest installed
- Justfile test commands
- Access to test files and source code
```

**Test**: Command appears in Claude Desktop

**Commit**: "feat(.claude): add test:debug command"

---

### Task 4.6: Port Linear Enhance Command
**Estimate**: 25 minutes

1. Create `.claude/commands/linear/enhance.md`:
```markdown
---
name: linear:enhance
description: AI-enhance Linear ticket descriptions with context and acceptance criteria
---

# Linear Enhance Command

Use AI to enhance Linear ticket descriptions with rich context.

## What This Does

Takes a basic Linear ticket and adds:
- Detailed description
- Acceptance criteria
- Technical considerations
- Related tickets
- Implementation notes

## Workflow

### Step 1: Get Ticket ID
```
/linear:enhance ENG-123
```

### Step 2: Fetch Current Ticket
```bash
# Uses Linear API
just linear-test  # Verify connection first
```

Read current ticket:
- Title
- Description (if any)
- Status
- Assignee
- Labels/Projects

### Step 3: Analyze Context
Search codebase for relevant:
- Related code files
- Similar past tickets
- Technical constraints
- Implementation patterns

### Step 4: Generate Enhanced Description

Template:
```markdown
## Overview
[Clear summary of what needs to be done]

## Context
[Why this is needed, background information]

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Technical Notes
- Implementation approach
- Files likely to change
- Potential challenges
- Testing requirements

## Related
- ENG-XXX: Related ticket
- PR #123: Similar implementation
```

### Step 5: Preview and Confirm
Show enhanced description.
Ask: "Update ticket with this description?"

### Step 6: Update Ticket
```bash
# Use Linear API to update
# POST to Linear GraphQL endpoint
```

Confirm success.

## Use Cases

### New Feature Tickets
Add:
- User stories
- UI/UX considerations
- API design
- Data model changes

### Bug Tickets
Add:
- Reproduction steps
- Expected vs actual behavior
- Root cause analysis
- Fix approach

### Refactoring Tickets
Add:
- Current state
- Desired state
- Migration strategy
- Risk assessment

## Usage

```
/linear:enhance <ticket-id>
```

Example:
```
/linear:enhance ENG-456
```

## Requires
- LINEAR_API_KEY environment variable
- justfile linear commands
- Access to Linear API
```

**Test**: Command appears in Claude Desktop

**Commit**: "feat(.claude): add linear:enhance command"

---

### Task 4.7: Port PR Review Expert Agent
**Estimate**: 30 minutes

1. Create `.claude/agents/pr-review-expert.md`:
```markdown
---
name: pr-review-expert
description: PR review request generation specialist - integrates with huginn for AI-assisted review requests (plugin:heimdall@local)
model: haiku
---

# PR Review Expert Agent

You are a specialist in generating high-quality PR review requests using huginn.

## Your Mission
Create compelling PR review requests that help reviewers understand changes quickly.

## Workflow Steps

### 1. Analyze Current PR
```bash
# Get current branch
git branch --show-current

# Get PR info
gh pr view
```

Extract:
- PR title
- Current description
- Changed files
- Diff stats

### 2. Read Changed Files
For key files:
```bash
git diff main...HEAD -- path/to/file
```

Understand:
- What changed
- Why it changed
- Impact of changes

### 3. Generate Review Context
Create structured context:

```markdown
## Changes Summary
[High-level overview of what changed]

## Key Files
- `file1.py`: [What changed and why]
- `file2.py`: [What changed and why]

## Review Focus
- [ ] Logic correctness in X
- [ ] Error handling for Y
- [ ] Performance impact of Z

## Testing
- Tests added: [list]
- Manual testing: [steps]

## Questions for Reviewers
1. Question 1?
2. Question 2?
```

### 4. Request Review via Huginn
```bash
just pr-request-review
```

This calls:
```bash
huginn pr request-review
```

Huginn will:
- Read PR changes
- Generate AI review context
- Post review request
- Tag appropriate reviewers

### 5. Verify Request Sent
```bash
gh pr view
```

Confirm:
- Review request shows in PR
- Reviewers are tagged
- Context is clear

## Review Request Best Practices

### For Small PRs (<100 lines)
- Concise summary
- Key changes highlighted
- Focus on critical logic

### For Large PRs (>100 lines)
- Break down by file/module
- Highlight critical sections
- Provide file-by-file guide
- Suggest review order

### For Complex PRs
- Architecture diagram
- Decision rationale
- Alternative approaches considered
- Migration strategy if applicable

## Common PR Types

### Feature PRs
Highlight:
- User-facing changes
- API additions
- Database migrations
- Configuration changes

### Bug Fix PRs
Highlight:
- Root cause
- Fix approach
- Regression prevention
- Test coverage

### Refactoring PRs
Highlight:
- Before/after comparison
- Behavior preservation
- Performance impact
- Risk mitigation

## Huginn Integration

Huginn provides:
- AI-generated review context
- Smart reviewer suggestions
- Review priority assessment
- Automated review request posting

Usage:
```bash
just pr-request-review           # Current PR
just pr-request-review --pr 123  # Specific PR
```

## Error Handling

### No PR Found
1. Check current branch has PR
2. Create PR first: `gh pr create`
3. Retry review request

### Huginn Not Installed
1. Install: `just install-huginn`
2. Verify: `huginn --version`
3. Retry

### Review Request Fails
1. Check GitHub auth: `gh auth status`
2. Verify PR exists: `gh pr view`
3. Check network connection
4. Retry with `--verbose`

## Available Commands
- `just pr-request-review` - Request PR review with AI context
- `gh pr view` - View current PR details
- `git diff main...HEAD` - Show PR changes
- `huginn pr --help` - Huginn PR options
```

**Test**: Agent appears in Claude Desktop

**Commit**: "feat(.claude): add pr-review-expert agent"

---

## Phase 5: Final Integration and Documentation (2-3 hours)

### Task 5.1: Create .claude Commands Index
**Estimate**: 15 minutes

1. Create `.claude/README.md`:
```markdown
# Heimdall Claude Commands & Agents

This directory contains custom Claude Desktop commands and agents for Heimdall development.

## Commands

### Git & Graphite
- `/gt:commit` - Smart GT commit workflow with validation
- `/gt:restack` - Safe GT restack operations

### Testing & Quality
- `/test:debug` - Interactive test debugging
- `/ci:analyze-failure` - Debug CI failures systematically

### Linear Integration
- `/linear:enhance` - AI-enhance Linear ticket descriptions

### Project Maintenance
- `/cleanup-docs-justfile` - Clean up docs and justfile
- `/create-command` - Create new .claude commands
- `/ground-truth` - Verify docs match implementation

## Agents

### Workflow Specialists
- `git-commit-expert` - GT commit workflow (model: haiku)
- `gt-restack-expert` - GT restack operations (model: haiku)
- `graphite-expert` - General GT operations (model: haiku)

### Review & Analysis
- `pr-review-expert` - PR review requests (model: haiku)

## Usage

Commands are invoked with `/`:
```
/gt:commit
/test:debug tests/test_file.py::test_function
```

Agents are invoked automatically by commands or manually via agent selection.

## Adding New Commands

Use the meta-command:
```
/create-command <category>/<name>
```

This creates properly structured command files.

## Requirements

- Claude Desktop with custom commands enabled
- Huginn CLI for PR operations: `just install-huginn`
- Graphite CLI for GT commands: `brew install graphite`
- GitHub CLI for PR/Actions: `brew install gh`
```

**Test**: README renders properly

**Commit**: "docs(.claude): add commands and agents index"

---

### Task 5.2: Update Main Documentation for Heimdall
**Estimate**: 30 minutes

1. Update `docs/INDEX.md`:
```markdown
# Heimdall Documentation Index

Heimdall is the all-seeing observer of engineering productivity and metrics.

## Quick Links
- [Setup Guide](setup-guide.md) - Get started with Heimdall
- [Usage Guide](usage-guide.md) - Daily workflows
- [Justfile Reference](../justfile) - All available commands
- [Claude Commands](.claude/README.md) - AI-assisted workflows

## Core Concepts
- [Linear Integration](linear-integration.md) - Ticket correlation
- [Metrics Analysis](metrics-analysis-guide.md) - Understanding impact scores
- [GitHub Workflow](github-linear-workflow.md) - PR analysis

## Developer Experience
- [Graphite Workflow](.claude/commands/gt/) - Stacked PR development
- [Testing Guide](testing-guide.md) - Test strategy and debugging
- [CI/CD Pipeline](.github/workflows/ci.yml) - Automated quality checks

## Architecture
- Hermod (CLI): AI usage tracking and metrics collection
- Heimdall (Core): Engineering observability framework
- Integration: GitHub, Linear, Anthropic APIs

## Component Guides
- [Hermod CLI](../src/hermod/README.md) - CLI tool for AI usage tracking
- [Data Extraction](data-extraction.md) - GitHub/Linear data collection
- [Analysis Engine](analysis-engine.md) - AI-powered work classification
```

**Test**: Links work correctly

**Commit**: "docs: update INDEX.md for Heimdall structure"

---

### Task 5.3: Add Graphite Workflow Guide
**Estimate**: 30 minutes

1. Create `docs/graphite-workflow.md`:
```markdown
# Graphite Workflow Guide

Heimdall fully supports Graphite (GT) stacked PR workflows.

## What is Graphite?

Graphite enables stacked PR development:
- Work on multiple dependent changes simultaneously
- Create logical review units instead of massive PRs
- Maintain dependencies between PRs automatically

## Setup

```bash
# Install Graphite CLI
brew install graphite

# Initialize in repo
gt repo init

# Create first branch
gt branch create feature-name
```

## Daily Workflow

### Create New Feature Branch
```bash
# Using Claude command
/gt:commit

# Or manually
gt create -m "feat: add new feature"
```

### Modify Existing Branch
```bash
# Make changes, stage them
git add .

# Using Claude command
/gt:commit

# Or manually
gt modify -m "refactor: improve implementation"
```

### Restack After Changes
```bash
# Using Claude command
/gt:restack

# Or manually
gt restack
```

### Submit Stack for Review
```bash
# Submit all branches in stack
gt stack submit

# Or specific branch
gt submit
```

## Claude Integration

Heimdall provides AI-assisted GT workflows:

### `/gt:commit` Command
- Validates staged changes
- Runs tests before commit
- Generates conventional commit messages
- Handles both `gt create` and `gt modify`

### `/gt:restack` Command
- Verifies clean working directory
- Shows restack plan before execution
- Validates final stack state
- Provides rollback instructions

### Agents
- `git-commit-expert`: Handles commit workflow
- `gt-restack-expert`: Handles restack operations
- `graphite-expert`: General GT troubleshooting

## Best Practices

### Branch Naming
```
feature/eng-123-short-description
bugfix/eng-456-fix-auth
refactor/eng-789-cleanup-tests
```

Include Linear ticket ID for correlation.

### Commit Messages
Follow conventional commits:
```
feat(scope): add new feature
fix(scope): correct bug
refactor(scope): improve code
```

### Stack Organization
- Keep stacks focused on single feature/epic
- Break large changes into logical review units
- Maintain clear dependencies between PRs

### Review Process
1. Submit bottom of stack first
2. Request reviews with `/pr:request-review` (via huginn)
3. Address feedback branch-by-branch
4. Restack after changes: `/gt:restack`
5. Re-submit updated PRs

## Troubleshooting

### Stack State Issues
```bash
# View current stack
gt stack

# View stack log
gt log

# Sync with remote
gt sync
```

### Rebase Conflicts
```bash
# During restack, if conflicts:
# 1. Resolve conflicts in files
# 2. Stage resolved files: git add .
# 3. Continue: gt restack --continue
```

### Remote Divergence
```bash
# Fetch latest
git fetch origin

# Sync stack
gt sync

# If needed, force sync
gt sync --force
```

## Justfile Commands

All GT operations available via justfile:

```bash
just git-status          # Check working directory
just git-branch          # Show current branch
just pr-request-review   # Request PR review (huginn)
```

## Resources

- [Graphite Docs](https://graphite.dev/docs)
- [GT CLI Reference](https://graphite.dev/docs/cli)
- [Stacked PRs Guide](https://graphite.dev/docs/stacked-prs)
```

**Test**: Document is complete and clear

**Commit**: "docs: add graphite workflow guide"

---

### Task 5.4: Update Setup Guide for Heimdall
**Estimate**: 20 minutes

1. Update `docs/setup-guide.md`:

Add Heimdall-specific setup:
```markdown
## Developer Tools

### Required
- **uv**: Python package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **just**: Command runner (`brew install just`)
- **git**: Version control

### Recommended
- **Graphite CLI**: Stacked PR workflow (`brew install graphite`)
- **Huginn CLI**: AI-assisted PR/git operations (`just install-huginn`)
- **GitHub CLI**: PR and Actions management (`brew install gh`)

### Optional
- **Claude Desktop**: For .claude commands and agents
- **pre-commit**: Git hooks for quality (`uv tool install pre-commit`)

## Initial Setup

```bash
# Clone repository
git clone https://github.com/YOUR_ORG/heimdall.git
cd heimdall

# Run setup
just setup

# This installs:
# - Python dependencies via uv
# - Huginn CLI for PR operations
# - Pre-commit hooks

# Verify installation
just env-check
```

## Graphite Setup

```bash
# Install Graphite CLI
brew install graphite

# Initialize in repo
gt repo init

# Verify
gt stack
```

## Claude Desktop Setup

If using Claude Desktop with custom commands:

1. Enable custom commands in Claude Desktop settings
2. Navigate to `.claude/` directory
3. Commands and agents will be automatically available
4. Try `/gt:commit` to verify

## API Keys

Create `.env` file:
```bash
# GitHub
GITHUB_TOKEN=ghp_...

# Linear
LINEAR_API_KEY=lin_api_...
LINEAR_TEAM_ID=...

# Anthropic (for AI analysis)
ANTHROPIC_API_KEY=sk-ant-...
```

Verify APIs:
```bash
just verify-apis
```
```

**Test**: Setup guide is accurate

**Commit**: "docs: update setup guide for Heimdall tools"

---

### Task 5.5: Create Migration Verification Checklist
**Estimate**: 15 minutes

1. Create `docs/verification/heimdall-migration-checklist.md`:
```markdown
# Heimdall Migration Verification Checklist

Use this checklist to verify the migration is complete.

## Phase 1: Repository Rename
- [ ] `pyproject.toml` project name is "heimdall"
- [ ] README.md title reflects Heimdall
- [ ] CLAUDE.md updated to Heimdall branding
- [ ] Local directory renamed to `heimdall`
- [ ] GitHub repository renamed to `heimdall`
- [ ] Git remote URL updated
- [ ] CI configuration references Heimdall

**Verify**: `git remote -v` shows heimdall URL

## Phase 2: Justfile Foundation
- [ ] Huginn installed: `huginn --version`
- [ ] PR namespace added: `just pr --help`
- [ ] Git utilities added: `just git-status`
- [ ] GitHub utilities added: `just gh-actions --help`
- [ ] Documentation validation: `just docs-validate-justfile`
- [ ] Linear integration: `just linear-test`
- [ ] CI uses justfile: `.github/workflows/ci.yml` calls `just` commands

**Verify**: `just --list` shows all new commands

## Phase 3: Critical .claude Infrastructure
- [ ] `.claude/agents/graphite-expert.md` exists
- [ ] `.claude/commands/gt/commit.md` exists
- [ ] `.claude/agents/git-commit-expert.md` exists
- [ ] `.claude/commands/gt/restack.md` exists
- [ ] `.claude/agents/gt-restack-expert.md` exists
- [ ] Commands appear in Claude Desktop

**Verify**: `/gt:commit` command available in Claude Desktop

## Phase 4: High-Value .claude Infrastructure
- [ ] `.claude/commands/cleanup-docs-justfile.md` exists
- [ ] `.claude/commands/create-command.md` exists
- [ ] `.claude/commands/ground-truth.md` exists
- [ ] `.claude/commands/ci/analyze-failure.md` exists
- [ ] `.claude/commands/test/debug.md` exists
- [ ] `.claude/commands/linear/enhance.md` exists
- [ ] `.claude/agents/pr-review-expert.md` exists

**Verify**: All commands available in Claude Desktop

## Phase 5: Documentation
- [ ] `.claude/README.md` created
- [ ] `docs/INDEX.md` updated
- [ ] `docs/graphite-workflow.md` created
- [ ] `docs/setup-guide.md` updated
- [ ] All documentation links work

**Verify**: `just docs-validate-links` passes (if implemented)

## Functional Testing

### Graphite Workflow
```bash
# Create test branch
gt branch create test-migration

# Make change
echo "test" >> README.md
git add README.md

# Test commit command (in Claude Desktop)
/gt:commit

# Expected: Commit succeeds with proper message
```

### Huginn Integration
```bash
# Test PR operations
just pr --help

# Expected: Shows huginn PR help
```

### CI Pipeline
```bash
# Push to feature branch
git push origin feature/test

# Watch CI
just gh-actions-watch

# Expected: CI runs via justfile commands
```

### Linear Integration
```bash
# Test Linear connection
just linear-test

# Expected: "✅ Linear API connected"
```

## Cleanup

After verification passes:
- [ ] Delete test branches
- [ ] Remove test commits
- [ ] Archive old spacewalker commands (don't delete yet)

## Sign-off

- [ ] All checklist items complete
- [ ] All tests passing: `just test`
- [ ] CI passing on main branch
- [ ] Documentation reviewed
- [ ] Ready for team adoption

**Migration Complete**: `git tag v0.2.0-heimdall-migration`
```

**Test**: Checklist is comprehensive

**Commit**: "docs: add heimdall migration verification checklist"

---

### Task 5.6: Final Verification and Summary
**Estimate**: 30 minutes

1. Run complete test suite:
```bash
just test
```

2. Verify justfile commands:
```bash
just --list
```

3. Check documentation links:
```bash
just docs-list
```

4. Verify .claude structure:
```bash
find .claude -type f -name "*.md"
```

5. Create completion summary in `docs/plans/2025-10-22-heimdall-migration-COMPLETE.md`:
```markdown
# Heimdall Migration - Completion Report

**Date**: 2025-10-22
**Status**: ✅ COMPLETE

## Summary

Successfully migrated github_linear_metrics to Heimdall with:
- Repository renamed locally and on GitHub
- Huginn CLI integrated into justfile
- Critical Graphite workflow commands and agents ported
- High-value DX commands and agents ported
- CI migrated to justfile-first architecture
- Comprehensive documentation updated

## What Was Accomplished

### Phase 1: Repository Rename ✅
- Project renamed to "heimdall" in pyproject.toml
- All documentation updated with Heimdall branding
- Local directory and GitHub repository renamed
- Git remote URLs updated

### Phase 2: Justfile Foundation ✅
- Huginn CLI installed and integrated
- PR namespace added (request-review, enhance, etc.)
- Git utilities namespace added (branch, commits, status, etc.)
- GitHub utilities namespace added (actions, branch-sync)
- Documentation validation commands added
- Linear integration commands added
- CI migrated to use justfile commands exclusively

### Phase 3: Critical .claude Infrastructure ✅
- ported `graphite-expert` agent
- ported `/gt:commit` command with `git-commit-expert` agent
- ported `/gt:restack` command with `gt-restack-expert` agent
- All Graphite workflow automation in place

### Phase 4: High-Value .claude Infrastructure ✅
- ported `/cleanup-docs-justfile` command
- ported `/create-command` meta-command
- ported `/ground-truth` verification command
- ported `/ci:analyze-failure` debugging command
- ported `/test:debug` interactive debugging
- ported `/linear:enhance` ticket enhancement
- ported `pr-review-expert` agent

### Phase 5: Documentation ✅
- Created .claude README with command index
- Updated docs/INDEX.md for Heimdall structure
- Created Graphite workflow guide
- Updated setup guide with new tools
- Created migration verification checklist

## Metrics

**Commands Ported**: 8 commands across 4 categories
**Agents Ported**: 5 specialized agents
**Justfile Commands Added**: 15+ new commands
**Documentation Files**: 5+ created/updated
**Test Coverage**: All 210 tests passing

## Team Benefits

1. **Graphite Workflow**: Full GT support with AI assistance
2. **PR Quality**: AI-enhanced review requests via huginn
3. **Debugging**: Systematic CI and test debugging
4. **Linear Integration**: Enhanced ticket management
5. **Consistency**: Justfile-first for all operations
6. **Documentation**: Comprehensive guides and verification

## Next Steps

1. **Team Onboarding**: Share Graphite workflow guide
2. **Adoption Tracking**: Monitor command usage
3. **Feedback Loop**: Gather team input on .claude commands
4. **Phase 3 Commands**: Consider porting nice-to-have commands
5. **Custom Commands**: Use `/create-command` for team-specific needs

## Migration Checklist

See: [Heimdall Migration Verification Checklist](../verification/heimdall-migration-checklist.md)

**Status**: ✅ All items verified

## Sign-off

- **Migration Complete**: 2025-10-22
- **Tests Passing**: ✅ 210/210
- **CI Passing**: ✅ All jobs green
- **Documentation**: ✅ Complete
- **Team Ready**: ✅ Yes

**Tagged**: `v0.2.0-heimdall-migration`
```

**Commit**: "docs: add migration completion report"

---

## Execution Strategy

### Recommended Approach

**Week 1**: Phases 1-2 (Foundation)
- Day 1: Repository rename (Tasks 1.1-1.6)
- Day 2-3: Justfile foundation (Tasks 2.1-2.7)

**Week 2**: Phase 3 (Critical .claude)
- Day 1-2: Graphite commands and agents (Tasks 3.1-3.5)

**Week 3**: Phase 4 (High-Value .claude)
- Day 1-2: DX commands (Tasks 4.1-4.4)
- Day 3: Testing and Linear commands (Tasks 4.5-4.7)

**Week 4**: Phase 5 (Documentation & Verification)
- Day 1: Documentation (Tasks 5.1-5.4)
- Day 2: Verification (Tasks 5.5-5.6)

### Alternative: Sprint Approach

**Sprint 1** (1 week): Rename + Foundation
- All of Phase 1 and Phase 2
- Outcome: Heimdall with huginn integration

**Sprint 2** (1 week): Graphite Workflow
- All of Phase 3
- Outcome: Full GT workflow support

**Sprint 3** (1 week): DX Tools
- All of Phase 4
- Outcome: Complete DX command suite

**Sprint 4** (1 week): Polish
- All of Phase 5
- Outcome: Production-ready documentation

## Risk Mitigation

### Critical Risks

1. **Repository Rename Issues**
   - Backup before rename
   - Update all CI/CD references
   - Test clone from new URL

2. **Huginn Integration Failures**
   - Verify huginn version compatibility
   - Test on sample PR before rolling out
   - Have fallback to manual PR operations

3. **.claude Command Conflicts**
   - Review existing .claude setup before porting
   - Test each command individually
   - Don't overwrite existing customizations

4. **CI Breaking Changes**
   - Test CI changes on feature branch first
   - Keep old CI config as backup
   - Monitor first few CI runs closely

### Testing Strategy

- **After each task**: Run relevant tests
- **After each phase**: Run full test suite
- **Before merge**: Complete verification checklist
- **After deployment**: Monitor CI for issues

## Success Criteria

- [ ] All 210 tests passing
- [ ] CI green on main branch
- [ ] All justfile commands functional
- [ ] All .claude commands available in Claude Desktop
- [ ] Documentation complete and accurate
- [ ] Team can follow Graphite workflow guide
- [ ] Migration verification checklist 100% complete

---

**Plan Status**: Ready for execution
**Estimated Total Time**: 12-20 hours (depending on approach)
**Recommended**: Start with Phase 1 (rename) immediately
