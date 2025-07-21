# Python Import Conflicts Resolution Guide

## Purpose
Documentation for resolving Python import conflicts in the GitHub Linear Metrics project, particularly conflicts between local modules and built-in Python modules.

## When to Use This
- Python modules fail to import correctly
- `ModuleNotFoundError` despite modules existing
- Built-in Python modules not working as expected
- Import resolution debugging

**Keywords:** import conflicts, module resolution, python imports, debugging, troubleshooting

---

## Overview

Python import conflicts occur when local module names clash with built-in Python modules or third-party packages. This can cause Python to import the wrong module, leading to unexpected behavior or import errors.

---

## Common Import Conflict Types

### 1. Local Module vs Built-in Module
**Problem**: Local directory name matches a built-in Python module
```python
# Local directory: src/logging/
# Conflicts with: import logging (built-in)
```

**Symptoms**:
- `AttributeError` when accessing built-in module functions
- Module behaves unexpectedly
- Import statements work but module functionality fails

### 2. Local Module vs Third-party Package
**Problem**: Local module name matches installed package
```python
# Local file: requests.py
# Conflicts with: import requests (third-party)
```

**Symptoms**:
- Package functionality not available
- `ImportError` or `AttributeError` exceptions
- Version conflicts

### 3. Circular Import Dependencies
**Problem**: Modules import each other creating a loop
```python
# module_a.py imports module_b
# module_b.py imports module_a
```

**Symptoms**:
- `ImportError: cannot import name 'X'`
- Module appears to be partially initialized
- Runtime errors during import

---

## Historical Example: src/logging/ Conflict

### The Problem
The GitHub Linear Metrics project had a `src/logging/` directory that conflicted with Python's built-in `logging` module.

**File Structure**:
```
src/
├── logging/           # ❌ Conflicts with built-in 'logging'
│   ├── __init__.py
│   └── structured_logger.py
└── analysis/
    └── claude_client.py  # Imports 'logging'
```

**Error Manifestation**:
```python
# In claude_client.py
import logging  # Imported local src/logging/ instead of built-in

# When trying to use built-in logging functions:
logging.getLogger()  # AttributeError: module has no attribute 'getLogger'
```

### The Solution
1. **Renamed the conflicting directory**:
   ```bash
   mv src/logging/ src/structured_logging/
   ```

2. **Updated all import statements**:
   ```python
   # Before (conflicting)
   from ..logging import structured_logger
   from src.logging.structured_logger import get_structured_logger
   
   # After (resolved)
   from ..structured_logging import structured_logger
   from src.structured_logging.structured_logger import get_structured_logger
   ```

3. **Validated resolution**:
   ```bash
   uv run python -c "import logging; print('✅ Built-in logging module imports correctly')"
   ```

---

## Diagnosis Techniques

### 1. Check Module Path
```python
import sys
import module_name
print(f"Module path: {module_name.__file__}")
print(f"Sys path: {sys.path}")
```

### 2. Inspect Module Contents
```python
import module_name
print(f"Module attributes: {dir(module_name)}")
print(f"Module type: {type(module_name)}")
```

### 3. Use importlib for Detailed Info
```python
import importlib.util
spec = importlib.util.find_spec('module_name')
print(f"Module spec: {spec}")
print(f"Module origin: {spec.origin if spec else 'Not found'}")
```

### 4. Check Python Path Resolution
```bash
# Shows where Python would find a module
python -c "import sys; import module_name; print(module_name.__file__)"

# List all locations Python searches
python -c "import sys; print('\n'.join(sys.path))"
```

---

## Resolution Strategies

### Strategy 1: Rename Conflicting Modules
**Best for**: Local modules conflicting with built-ins

1. **Identify conflicts**:
   ```bash
   # Check if local name conflicts with built-in
   python -c "import module_name; print(module_name.__file__)"
   ```

2. **Choose a descriptive new name**:
   - `logging` → `structured_logging`
   - `json` → `custom_json`
   - `utils` → `project_utils`

3. **Rename systematically**:
   ```bash
   # Rename directory/file
   mv src/logging/ src/structured_logging/
   
   # Update imports across codebase
   find . -name "*.py" -exec sed -i 's/from \.\.logging/from ..structured_logging/g' {} \;
   ```

### Strategy 2: Use Absolute Imports
**Best for**: Disambiguation between relative and absolute imports

```python
# Instead of ambiguous relative import
from .logging import something

# Use explicit absolute import
from src.structured_logging import something
```

### Strategy 3: Import Aliasing
**Best for**: Temporary workarounds

```python
# Import with alias to avoid conflicts
import logging as python_logging
from .custom_logging import logger as custom_logger
```

### Strategy 4: Module Path Manipulation
**Best for**: Advanced cases (use sparingly)

```python
import sys
import importlib

# Temporarily modify path for specific import
original_path = sys.path[:]
sys.path.insert(0, '/path/to/specific/module')
try:
    import specific_module
finally:
    sys.path[:] = original_path
```

---

## Prevention Best Practices

### 1. Naming Conventions
- **Avoid built-in module names**: `logging`, `json`, `os`, `sys`, `datetime`, etc.
- **Use descriptive prefixes**: `project_logging`, `custom_utils`
- **Check before naming**: `python -c "import proposed_name"` (should fail for safe names)

### 2. Directory Structure
- **Group related modules**: `src/authentication/`, `src/data_processing/`
- **Use domain-specific names**: `github_client/`, `linear_integration/`
- **Avoid generic names**: `utils/`, `helpers/`, `common/`

### 3. Import Style Guidelines
- **Prefer absolute imports** over relative when possible
- **Be explicit about sources**:
  ```python
  # Good - clear where module comes from
  from src.structured_logging.structured_logger import get_logger
  
  # Avoid - ambiguous source
  from logging import get_logger
  ```

### 4. Development Workflow
- **Test imports early**: Validate imports work in clean environment
- **Use virtual environments**: Isolate project dependencies
- **Regular conflict checks**: Include in CI/CD pipeline

---

## Testing and Validation

### 1. Import Validation Script
```python
#!/usr/bin/env python3
"""Validate that all imports work correctly."""

import sys
import importlib

def test_built_in_modules():
    """Test that built-in modules import correctly."""
    built_ins = ['logging', 'json', 'os', 'sys', 'datetime', 'collections']
    
    for module_name in built_ins:
        try:
            module = importlib.import_module(module_name)
            print(f"✅ {module_name}: {module.__file__ or 'built-in'}")
        except ImportError as e:
            print(f"❌ {module_name}: {e}")
            return False
    return True

def test_project_modules():
    """Test that project modules import correctly."""
    project_modules = [
        'src.structured_logging.structured_logger',
        'src.analysis.claude_client',
        'src.git_extraction.cli'
    ]
    
    for module_name in project_modules:
        try:
            module = importlib.import_module(module_name)
            print(f"✅ {module_name}: {module.__file__}")
        except ImportError as e:
            print(f"❌ {module_name}: {e}")
            return False
    return True

if __name__ == "__main__":
    print("🔍 Testing Built-in Modules:")
    built_in_ok = test_built_in_modules()
    
    print("\n🔍 Testing Project Modules:")
    project_ok = test_project_modules()
    
    if built_in_ok and project_ok:
        print("\n✅ All imports working correctly")
        sys.exit(0)
    else:
        print("\n❌ Import conflicts detected")
        sys.exit(1)
```

### 2. Automated Conflict Detection
```bash
#!/bin/bash
# check_import_conflicts.sh

echo "🔍 Checking for import conflicts..."

# List of built-in modules that commonly conflict
BUILTIN_MODULES=("logging" "json" "os" "sys" "datetime" "collections" "email" "http" "urllib" "csv")

# Check for local modules that might conflict
for module in "${BUILTIN_MODULES[@]}"; do
    if [ -d "src/$module" ] || [ -f "src/$module.py" ]; then
        echo "⚠️  Potential conflict: src/$module conflicts with built-in module"
    fi
done

# Test actual imports
echo "Testing built-in module imports..."
for module in "${BUILTIN_MODULES[@]}"; do
    python -c "import $module; print(f'✅ $module: {$module.__file__ or \"built-in\"}')" 2>/dev/null || \
    echo "❌ $module: import failed"
done

echo "Import conflict check complete"
```

### 3. CI/CD Integration
```yaml
# .github/workflows/import-check.yml
name: Import Conflict Check

on: [push, pull_request]

jobs:
  import-check:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        pip install uv
        uv sync
    - name: Check import conflicts
      run: |
        uv run python scripts/test_imports.py
```

---

## Troubleshooting Specific Scenarios

### Scenario 1: "AttributeError: module has no attribute"
**Cause**: Local module shadowing built-in module

**Steps**:
1. Check module source: `python -c "import module; print(module.__file__)"`
2. If path shows local file instead of built-in, rename local module
3. Update all imports to new name
4. Validate: `python -c "import module; print(dir(module))"`

### Scenario 2: "ModuleNotFoundError" for existing module
**Cause**: Python path issues or circular imports

**Steps**:
1. Check sys.path: `python -c "import sys; print(sys.path)"`
2. Verify module location relative to Python path
3. Check for circular imports with import tracing
4. Use absolute imports to clarify module sources

### Scenario 3: "Import works but functionality missing"
**Cause**: Partial module shadowing

**Steps**:
1. Compare module attributes: `python -c "import module; print(sorted(dir(module)))"`
2. Check against expected built-in attributes
3. Identify source of shadowing module
4. Resolve conflict through renaming or path adjustment

---

## UV-Specific Considerations

### Virtual Environment Isolation
UV automatically manages virtual environments, which helps prevent some system-wide conflicts:

```bash
# UV creates isolated environment
uv sync

# Run in isolated environment
uv run python -c "import logging; print(logging.__file__)"
```

### Project-Specific Module Resolution
UV's project structure supports clean module organization:

```toml
# pyproject.toml
[project]
name = "github-linear-metrics"

[tool.uv]
# UV handles dependency isolation automatically
```

### Dependency Conflict Detection
UV detects dependency conflicts during installation:

```bash
# UV will warn about conflicts
uv add package-that-conflicts

# Check for conflicts
uv tree
```

---

## Quick Reference Commands

### Diagnosis Commands
```bash
# Check where Python finds a module
python -c "import MODULE; print(MODULE.__file__)"

# List module attributes
python -c "import MODULE; print(dir(MODULE))"

# Show Python path
python -c "import sys; print('\n'.join(sys.path))"

# Find module spec
python -c "import importlib.util; print(importlib.util.find_spec('MODULE'))"
```

### Resolution Commands
```bash
# Rename conflicting directory
mv src/logging/ src/structured_logging/

# Update imports in all Python files
find . -name "*.py" -exec sed -i 's/old_import/new_import/g' {} \;

# Test import resolution
uv run python -c "import logging; print('✅ Built-in logging works')"

# Run full import validation
uv run python scripts/test_imports.py
```

### Validation Commands
```bash
# Validate all built-in modules
python -c "import logging, json, os, sys, datetime; print('✅ All built-ins working')"

# Check project modules
uv run python -c "from src.structured_logging import structured_logger; print('✅ Project modules working')"

# Run with UV environment
uv run python -m pytest tests/test_imports.py -v
```

---

## Emergency Recovery

If imports are completely broken:

1. **Reset Python path**:
   ```bash
   unset PYTHONPATH
   uv sync
   ```

2. **Clean environment**:
   ```bash
   rm -rf .venv/
   uv sync
   ```

3. **Validate minimal import**:
   ```bash
   uv run python -c "import sys; print(sys.version)"
   ```

4. **Restore from backup** (if available):
   ```bash
   git checkout HEAD -- src/
   ```

5. **Systematic conflict resolution**:
   - Identify conflicts with diagnosis commands
   - Apply appropriate resolution strategy
   - Validate each fix before proceeding

---

## Related Documentation

- [UV Migration Guide](../setup/uv-migration.md) - For UV-specific setup
- [Setup Guide](../setup-guide.md) - For environment configuration
- [Troubleshooting Index](../troubleshooting/) - For other common issues

---

## Summary

Import conflicts are common in Python projects but can be systematically resolved:

1. **Identify**: Use diagnosis commands to locate conflicts
2. **Rename**: Choose non-conflicting module names
3. **Update**: Systematically update all import references
4. **Validate**: Test that both built-in and project modules work
5. **Prevent**: Follow naming conventions and testing practices

The key is early detection and systematic resolution to maintain clean, predictable import behavior.