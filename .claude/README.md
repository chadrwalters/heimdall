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
- Huginn CLI for PR operations: `just env install-huginn`
- Graphite CLI for GT commands: `brew install graphite`
- GitHub CLI for PR/Actions: `brew install gh`
