---
name: ground-truth
description: Verify documentation matches implementation reality - find drift between docs and code
---

# Ground Truth Command

Find and fix drift between documentation and implementation.

## What This Checks

### 1. Justfile Commands vs Documentation

- Commands mentioned in docs but missing from justfile
- Justfile commands not documented
- Outdated command signatures

### 2. Code Examples vs Reality

- Code examples in docs that don't work
- API calls that have changed
- Outdated import statements

### 3. Configuration vs Documentation

- Environment variables mentioned but not used
- Config options in docs but not in code
- Defaults that don't match

### 4. Dependencies vs Documentation

- Requirements mentioned but not in pyproject.toml
- Unused dependencies still documented
- Version mismatches

## Workflow

### Step 1: Scan Documentation

```bash
just docs list
```

Read all .md files and extract:
- Justfile command references
- Code examples
- Configuration references
- Dependency mentions

### Step 2: Verify Against Reality

- Check each justfile command exists: `just --list`
- Test code examples run: `uv run python -c "..."`
- Verify env vars used: `grep -r "os.getenv" src/`
- Check dependencies: `cat pyproject.toml`

### Step 3: Report Findings

Create report:

```
❌ DRIFT FOUND:

Documentation Issues:
- CLAUDE.md line 45: references `just analyze-all` but command doesn't exist
- docs/setup-guide.md: example uses old LinearClient API

Code Issues:
- src/config/settings.py uses ANTHROPIC_MODEL but not documented
- pyproject.toml has `bleach` but never imported

Justfile Issues:
- `test-visual` command exists but not in any docs
```

### Step 4: Propose Fixes

For each issue, offer:
- Update documentation OR
- Update implementation OR
- Remove deprecated references

## Usage

```
/ground-truth
```

I'll systematically check docs against reality and report drift.

## Requires

- Access to all documentation files
- Ability to run justfile commands
- Access to source code for verification
