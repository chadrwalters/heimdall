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

- [ ] Huginn installed: `huginn --help`
- [ ] PR namespace added: `just pr --help`
- [ ] Git utilities added: `just git status`
- [ ] GitHub utilities added: `just gh actions-latest`
- [ ] Documentation validation: `just docs validate-justfile`
- [ ] Linear integration: `just linear test`
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

**Verify**: `just docs list` shows all documentation files

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
just gh actions-watch

# Expected: CI runs via justfile commands
```

### Linear Integration

```bash
# Test Linear connection
just linear test

# Expected: Connection succeeds or shows clear error
```

## Verification Complete

All phases verified and functional! 🎉

**Next Steps:**
1. Team onboarding with Graphite workflow
2. Share .claude commands documentation
3. Monitor adoption and gather feedback
