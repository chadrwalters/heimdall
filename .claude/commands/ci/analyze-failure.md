---
name: ci:analyze-failure
description: Debug CI failures with executor-validator loops for systematic troubleshooting
---

# CI Analyze Failure Command

Systematically debug CI failures using executor-validator pattern.

## What This Does

Uses a two-agent approach:
1. **Executor**: Makes hypotheses and attempts fixes
2. **Validator**: Verifies fixes and provides feedback

This prevents:
- Guessing at solutions
- Incomplete fixes
- Missing edge cases

## Workflow

### Step 1: Gather CI Context

```bash
# Get latest CI run
just gh actions-latest
# Or specific run
gh run view <run-id>
```

Extract:
- Failed job name
- Error messages
- Full logs
- Environment details

### Step 2: Executor Analysis

**Executor** (me) will:
1. Analyze error messages
2. Form hypothesis about root cause
3. Identify relevant code/config
4. Propose specific fix

### Step 3: Validator Review

**Validator** (code review agent) will:
1. Review proposed fix
2. Check for edge cases
3. Verify completeness
4. Suggest improvements

### Step 4: Implement Fix

After validation:
1. Apply the fix
2. Test locally: `just test`
3. Commit: `git add . && git commit -m "fix(ci): ..."`
4. Push and monitor

### Step 5: Verify CI Success

```bash
just gh actions-watch
```

Confirm:
- CI job passes
- No new failures introduced
- Related tests still pass

## Common CI Failures

### Test Failures

- Missing dependencies in CI
- Environment variable not set
- Test order dependency
- Flaky tests

### Lint/Format Failures

- Pre-commit hook differences
- Ruff version mismatch
- Import order issues

### Type Check Failures

- Mypy version differences
- Missing type stubs
- New untyped dependencies

### Security Scan Failures

- New vulnerable dependency
- False positive needing skip
- Security issue in code

## Usage

```
/ci:analyze-failure [run-id]
```

Provide run ID or I'll fetch the latest failure.

## Executor-Validator Pattern

```
┌─────────────┐         ┌──────────────┐
│  Executor   │────────>│  Validator   │
│  (Analyze   │ Propose │  (Verify     │
│   & Fix)    │<────────│   & Guide)   │
└─────────────┘  Refine └──────────────┘
```

Benefits:
- Systematic approach
- Catches edge cases
- Complete solutions
- Learning loop

## Requires

- GitHub CLI (`gh`)
- Access to CI logs
- justfile gh commands
