# UV Migration Guide

## Purpose
Comprehensive guide for migrating from traditional Python venv/pip workflows to UV package manager for the GitHub Linear Metrics project.

## When to Use This
- Setting up development environment with UV
- Migrating existing venv-based setups to UV
- Understanding UV-based workflows
- Troubleshooting UV installation and usage

**Keywords:** uv, package manager, migration, setup, virtual environment, dependencies

---

## What is UV?

UV is a fast Python package manager that replaces pip and venv with a single, much faster tool. It provides:

- **10-100x faster** than pip for dependency resolution and installation
- **Automatic virtual environment management** - no need for manual venv creation
- **Lock file generation** for reproducible builds
- **Built-in project management** with pyproject.toml integration

---

## Installation

### Prerequisites

- **Python 3.11+** (UV manages Python versions but requires Python to be available)
- **Git** for repository operations
- **GitHub CLI** (optional but recommended): `gh` command for API operations

### Install UV

```bash
# macOS/Linux (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Alternative: via Homebrew (macOS)
brew install uv

# Alternative: via pip (not recommended)
pip install uv
```

### Verify Installation

```bash
uv --version
# Should show version 0.1.0 or higher
```

---

## Migration from Venv/Pip

### Old Workflow (venv/pip)
```bash
# Old way
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
pip install -e .
python main.py
```

### New Workflow (UV)
```bash
# New way
uv sync                    # Automatically creates venv and installs deps
uv run python main.py      # Runs in managed environment
```

### Key Differences

| Operation | Venv/Pip | UV |
|-----------|----------|-----|
| Create environment | `python -m venv .venv` | Automatic with `uv sync` |
| Activate environment | `source .venv/bin/activate` | Not needed |
| Install dependencies | `pip install -r requirements.txt` | `uv sync` |
| Run Python | `python script.py` | `uv run python script.py` |
| Add dependency | `pip install package` | `uv add package` |
| Remove dependency | `pip uninstall package` | `uv remove package` |

---

## Project Setup with UV

### 1. Initial Setup
```bash
# Clone repository
git clone <repository-url>
cd github_linear_metrics

# Setup project with UV
just setup
# OR manually:
uv sync
```

### 2. Development Dependencies
```bash
# Install development dependencies
just dev-setup
# OR manually:
uv sync --group dev
```

### 3. Verify Installation
```bash
# Check environment status
just env-check

# Verify API connections
just verify-apis

# Check UV status
just uv-status  # (new command)
```

---

## Common UV Commands

### Project Management
```bash
# Sync dependencies with lock file
uv sync

# Install new dependency
uv add requests

# Install development dependency
uv add --group dev pytest

# Remove dependency
uv remove requests

# Update all dependencies
uv sync --upgrade

# Show project info
uv show
```

### Execution
```bash
# Run Python script
uv run python script.py

# Run module
uv run python -m module_name

# Run with environment variables
uv run --env GITHUB_TOKEN=xyz python script.py

# Run shell in UV environment
uv run bash
```

### Dependency Management
```bash
# Show dependency tree
uv tree

# Check for security vulnerabilities
uv audit

# Generate requirements.txt (if needed)
uv export --format requirements-txt > requirements.txt
```

---

## GitHub Linear Metrics Specific Workflows

### 1. Development Workflow
```bash
# Start development session
just setup              # Initial setup with UV
just env-check          # Verify environment
just test               # Run tests with UV

# Daily development
uv run python -m pytest tests/    # Run tests
uv run python -m ruff check src/  # Lint code
uv run python main.py --org myorg # Run analysis
```

### 2. Data Extraction
```bash
# Extract data (uses UV internally)
just extract myorg 7    # 7-day extraction
just pilot myorg        # Quick pilot analysis
```

### 3. Adding Dependencies
```bash
# Add runtime dependency
uv add pandas

# Add development dependency  
uv add --group dev black

# Add optional dependency
uv add --optional plotting matplotlib
```

---

## Environment Variables

UV respects environment variables the same as traditional Python:

```bash
# Load from .env file (automatic with python-dotenv)
GITHUB_TOKEN=your_token_here
LINEAR_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Or export manually
export GITHUB_TOKEN=your_token_here
uv run python main.py
```

---

## Troubleshooting

### UV Not Found
```bash
# Check if UV is in PATH
which uv

# If not found, reinstall
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or restart terminal
```

### Permission Errors
```bash
# On macOS/Linux, ensure UV has proper permissions
chmod +x ~/.local/bin/uv

# On Windows, run as administrator or check PATH
```

### Slow Performance
```bash
# Clear UV cache if needed
uv cache clean

# Use specific Python version
uv python install 3.11
uv sync --python 3.11
```

### Virtual Environment Issues
```bash
# UV creates environments in project/.venv by default
# To see where environment is:
uv run python -c "import sys; print(sys.prefix)"

# To reset environment completely:
rm -rf .venv
uv sync
```

### Dependency Conflicts
```bash
# Show conflict details
uv sync --verbose

# Update lock file
uv lock --upgrade

# Check specific package version
uv show package_name
```

---

## Integration with IDEs

### VS Code
1. Install Python extension
2. Open project folder
3. VS Code should auto-detect UV environment in `.venv/`
4. If not detected: `Ctrl+Shift+P` → "Python: Select Interpreter" → Select `.venv/bin/python`

### PyCharm
1. Open project
2. File → Settings → Project → Python Interpreter
3. Add → Existing environment
4. Point to `.venv/bin/python`

### Vim/Neovim
UV environments work with LSP servers automatically when using `.venv/bin/python`.

---

## Performance Benefits

### Speed Comparison (typical project)
| Operation | Pip | UV | Improvement |
|-----------|-----|-----|------------|
| Install dependencies | 45s | 3s | **15x faster** |
| Resolve conflicts | 2m | 8s | **15x faster** |
| Cold install | 1m 20s | 12s | **7x faster** |
| Update all packages | 35s | 5s | **7x faster** |

### Memory Usage
- **UV**: ~50MB RAM during operations
- **Pip**: ~200MB RAM during operations

---

## Best Practices

### 1. Always Use uv run
```bash
# Good
uv run python script.py
uv run pytest

# Avoid (bypasses UV environment)
python script.py
pytest
```

### 2. Use Lock Files
- Commit `uv.lock` to repository
- Ensures reproducible builds across environments
- Run `uv sync` to install exact locked versions

### 3. Group Dependencies
```toml
# pyproject.toml
[tool.uv]
dev-dependencies = [
    "pytest>=8.0.0",
    "ruff>=0.8.0",
]
```

### 4. Environment-Specific Requirements
```bash
# Production: install only runtime deps
uv sync --no-group dev

# Development: install all groups
uv sync --group dev
```

---

## Migration Checklist

- [ ] **Install UV**: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- [ ] **Verify installation**: `uv --version`
- [ ] **Setup project**: `just setup` or `uv sync`
- [ ] **Test environment**: `just env-check`
- [ ] **Update IDE**: Configure to use `.venv/bin/python`
- [ ] **Update scripts**: Use `uv run` prefix for Python commands
- [ ] **Remove old venv**: `rm -rf .venv` (if using old setup)
- [ ] **Test workflows**: Run `just test` and `just extract`

---

## Getting Help

### UV Documentation
- **Official docs**: https://docs.astral.sh/uv/
- **GitHub**: https://github.com/astral-sh/uv

### Project-Specific Help
```bash
# Check project status
just uv-status

# Test imports
just fix-imports

# Get help
just help
```

### Common Issues
- See [Import Conflicts Guide](../troubleshooting/import-conflicts.md)
- See [Setup Guide](../setup-guide.md) for environment setup
- See [Troubleshooting](../troubleshooting/) for specific issues

---

## Summary

UV provides a significantly faster and simpler Python development experience:

1. **Single command setup**: `uv sync` replaces venv creation + pip install
2. **Faster operations**: 10-100x speed improvements over pip
3. **Automatic environment management**: No need to activate/deactivate
4. **Better dependency resolution**: Faster conflict detection and resolution
5. **Integrated tooling**: Built-in project management and lock files

The GitHub Linear Metrics project is now fully migrated to UV for optimal development experience.