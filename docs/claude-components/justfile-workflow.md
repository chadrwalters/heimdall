# 🎯 JUSTFILE FIRST, ALWAYS

**Workflow**: Need command? → `just help` → Find it → Use it

**Anti-pattern**: Running `python`, `uv`, `pytest` directly when justfile equivalents exist

## Core Philosophy
- Justfiles provide standardized, project-specific command interfaces
- They encapsulate complex multi-step operations with proper environment setup
- They ensure consistent parameters and error handling
- Always check justfile before reaching for underlying tools

## Command Discovery Examples

### ✅ CORRECT Pattern
```bash
just help                    # Discover available commands first
just env-check               # Check environment setup
just verify-apis            # Test API connections
just pilot degree-analytics  # Run standardized pilot analysis
just pipeline org 30        # Full 30-day analysis pipeline
```

### ❌ ANTI-PATTERNS to Avoid
```bash
python main.py              # Don't use Python directly
uv run python scripts/...   # Use `just test-*` instead
pytest tests/               # Use `just test` or `just test-unit`
./scripts/extraction/...    # Use `just extract` instead
```

## Common Command Categories

### Environment & Setup
- **Setup**: `just setup`, `just dev-setup`, `just env-check`
- **Validation**: `just verify-apis`, `just validate-config`

### Data Operations
- **Extraction**: `just extract <org> [days]`, `just extract-incremental <org>`
- **Analysis**: `just analyze [input]`, `just pilot <org>`
- **Pipeline**: `just pipeline <org> <days>` (full end-to-end)

### Testing & Quality
- **Testing**: `just test`, `just test-unit`, `just test-integration`
- **Specific**: `just test-linear`, `just test-gh-analyzer`
- **Quality**: `just lint`, `just format`, `just coverage`

### Utilities
- **Monitoring**: `just status`, `just logs`, `just health`
- **Cleanup**: `just clean`, `just reset-state`

## Workflow Examples

### Daily Development
```bash
just setup                   # Initial setup
just env-check              # Verify environment
just verify-apis            # Test connections
just test                   # Run tests
# Work on features...
just test-unit              # Quick validation
```

### Analysis Pipeline
```bash
just env-check              # Pre-flight check
just pilot org-name         # Quick 7-day pilot
just extract org-name 30    # Full month extraction
just analyze data.csv       # Run AI analysis
```

### Testing Workflow
```bash
just test-unit              # Fast unit tests
just test-integration       # Integration tests
just test-linear           # Linear API tests
just test-gh-analyzer      # GitHub Actions tests
```

## When Direct Commands Are Acceptable

**Limited cases for direct usage:**
- Git operations: `git status`, `git diff` (read-only)
- File operations: `ls`, `cat`, `grep` (simple inspection)
- Environment debugging: `env | grep TOKEN` (troubleshooting)

**Always use justfile for:**
- Multi-step operations
- API-dependent commands
- Complex parameter combinations
- Frequently repeated tasks
- Operations requiring environment setup