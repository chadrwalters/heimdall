# Heimdall Claude Commands & Agents

This directory contains custom Claude Desktop commands and agents for Heimdall development.

## Commands

### Git & Graphite

- `/gt:commit` - Smart GT commit workflow with validation, testing, and optional PR submission
  - `/gt:commit --submit` - Commit and submit PR to stack
  - `/gt:commit --submit --enhance` - Commit, submit, and AI-enhance PR title/description
- `/gt:restack` - Safe GT restack operations

### Pull Requests

- `/pr:request-review <number>` - Request comprehensive code review with AI analysis
  - Generates structured review request comments
  - Mentions @claude and @codex for multi-perspective review
  - Analyzes PR changes and provides context for reviewers

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
- `pr-generator-expert` - AI-powered PR title/description generation (model: haiku)
  - Uses huginn for consistent PR documentation
  - Smart model selection based on complexity
  - Integrates with GitHub CLI for automatic updates

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
