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
2. Request reviews with `just pr request-review` (via huginn)
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
just git status          # Check working directory
just git branch          # Show current branch
just pr request-review   # Request PR review (huginn)
```

## Resources

- [Graphite Docs](https://graphite.dev/docs)
- [GT CLI Reference](https://graphite.dev/docs/cli)
- [Stacked PRs Guide](https://graphite.dev/docs/stacked-prs)
