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
