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
