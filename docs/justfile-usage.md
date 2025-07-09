# Justfile Usage Guide

This project uses [Just](https://github.com/casey/just) as a command runner to simplify common tasks.

## Installation

If you don't have Just installed:

```bash
# macOS
brew install just

# Linux
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to /usr/local/bin

# Or with cargo
cargo install just
```

## Quick Start

```bash
# Show all available commands
just

# Initial setup
just setup
just verify-apis

# Run a pilot analysis
just pilot your-org-name

# Work on tasks
just task-next
just task-start 6
just task-done 6
```

## Common Workflows

### 1. Initial Project Setup

```bash
just setup          # Create venv and install dependencies
just dev-setup      # Install dev dependencies
just env-check      # Check if environment variables are set
just verify-apis    # Test API connections
```

### 2. Data Extraction

```bash
# Extract last 7 days of data
just extract your-org

# Extract custom time period
just extract your-org 30

# Run incremental update
just extract-incremental your-org

# List repositories
just list-repos your-org
```

### 3. Running Analysis

```bash
# Analyze extracted data
just analyze

# Run full pilot (extract + analyze)
just pilot your-org

# Full pipeline with custom days
just pipeline your-org 30
```

### 4. Task Management

```bash
just task-next              # Show next task
just task-show 6            # Show details for task 6
just task-start 6           # Mark task 6 as in-progress
just task-done 6            # Mark task 6 as done
just task-list              # List pending tasks
just task-list done         # List completed tasks
just task-progress          # Show overall progress
```

### 5. Testing

```bash
just test                   # Run all tests
just test-unit              # Unit tests only
just test-integration       # Integration tests only
just test-linear            # Test Linear integration
just test-gh-analyzer       # Test GitHub analyzer
just test-analysis          # Test analysis engine
```

### 6. Development

```bash
just format                 # Format code with black
just lint                   # Run linting
just typecheck              # Run type checking
just quality                # Run all quality checks
just watch                  # Watch and run tests on changes
just clean                  # Clean generated files
```

### 7. GitHub Actions

```bash
# Test PR analysis bot locally
just test-pr-bot 123
```

## Key Commands Reference

| Command | Description |
|---------|-------------|
| `just` | Show all available commands |
| `just setup` | Initial project setup |
| `just env-check` | Check environment variables |
| `just verify-apis` | Test all API connections |
| `just pilot <org>` | Run 7-day pilot analysis |
| `just pipeline <org> <days>` | Run full pipeline |
| `just task-next` | Show next task to work on |
| `just test` | Run all tests |
| `just quality` | Run code quality checks |
| `just stats` | Show project statistics |
| `just help-workflows` | Show common workflows |

## Environment Variables

Required environment variables:
- `GITHUB_TOKEN` - GitHub personal access token
- `LINEAR_API_KEY` or `LINEAR_TOKEN` - Linear API key
- `ANTHROPIC_API_KEY` - Anthropic API key

Check status with:
```bash
just env-check
```

## Tips

1. **Shortcuts**: The most common command `just task-next` has a shortcut `just next`

2. **Parameters**: Commands accept parameters:
   ```bash
   just extract my-org 30    # Extract 30 days
   just task-show 6          # Show task 6
   ```

3. **Chaining**: Chain commands for workflows:
   ```bash
   just verify-apis && just pilot my-org
   ```

4. **Help**: Get help on specific topics:
   ```bash
   just help-env        # Environment variables help
   just help-workflows  # Common workflows
   ```

## Extending the Justfile

To add new commands, edit the `justfile` and add recipes like:

```just
# Description of your command
my-command param1 param2="default":
    @echo "Running with {{param1}} and {{param2}}"
    python scripts/my_script.py {{param1}} {{param2}}
```