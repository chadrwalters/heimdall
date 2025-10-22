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
- List all documentation files: `just docs list`
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

- Run `just docs validate-justfile`
- Test all justfile commands
- Verify all doc links work

## Usage

```
/cleanup-docs-justfile
```

I'll systematically go through justfile and docs, proposing cleanups.
