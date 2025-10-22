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
