---
name: test:debug
description: Interactive test debugging with systematic failure analysis
---

# Test Debug Command

Systematically debug test failures with guided troubleshooting.

## What This Does

Helps you debug failing tests through:
1. Failure analysis
2. Hypothesis formation
3. Targeted fixes
4. Verification

## Workflow

### Step 1: Identify Failing Test

```bash
# Run tests to see failures
just test unit
# Or specific test
just test unit tests/test_specific.py::test_function
```

Capture:
- Test name
- Error message
- Stack trace
- Failed assertion

### Step 2: Analyze Failure

Read the test code:
```python
# What is the test trying to verify?
# What are the test inputs?
# What is the expected behavior?
# What actually happened?
```

### Step 3: Form Hypothesis

Common failure patterns:
- **Incorrect assertion**: Test expects wrong value
- **Missing setup**: Fixture or mock not configured
- **Environment issue**: Missing env var or file
- **Timing issue**: Async or race condition
- **Data issue**: Test data doesn't match reality
- **Regression**: Code changed, test didn't update

### Step 4: Investigate Code

Based on hypothesis, read:
- Implementation code being tested
- Related fixtures in `conftest.py`
- Mock setups
- Test data files

### Step 5: Apply Fix

Options:
- Fix the code (if bug in implementation)
- Fix the test (if test is wrong)
- Fix the setup (if fixture issue)
- Add missing data (if data issue)

### Step 6: Verify Fix

```bash
# Run the specific test
just test unit tests/test_file.py::test_function
# Run related tests
just test unit tests/test_file.py
# Run all tests
just test all
```

Confirm:
- Failing test now passes
- No new test failures
- All related tests still pass

## Common Test Issues

### Assertion Errors

```python
# Expected: 5, Got: 6
assert result == 5
# Fix options:
# 1. Code is wrong, fix implementation
# 2. Test is wrong, update assertion
# 3. Setup is wrong, fix fixture
```

### Missing Fixtures

```python
# Error: fixture 'api_client' not found
# Fix: Add to conftest.py or import
@pytest.fixture
def api_client():
    return APIClient()
```

### Mock Issues

```python
# Error: mock not being called
# Fix: Ensure mock is patched correctly
@patch('module.function')
def test_something(mock_func):
    mock_func.return_value = expected
```

### Environment Variables

```python
# Error: None (missing env var)
# Fix: Add to test or use fixture
@pytest.fixture
def env_vars(monkeypatch):
    monkeypatch.setenv('API_KEY', 'test-key')
```

## Debugging Techniques

### Add Print Statements

```python
def test_something():
    result = function_under_test()
    print(f"DEBUG: result = {result}")  # Add this
    assert result == expected
```

### Use Debugger

```bash
# Run with debugger
just test unit tests/test_file.py::test_function --pdb
# Or add breakpoint in code
breakpoint()
```

### Isolate the Issue

```bash
# Run just one test
pytest tests/test_file.py::test_specific -v
# Run with verbose output
pytest tests/ -vv
# Show print statements
pytest tests/ -s
```

## Usage

```
/test:debug [test-name]
```

Provide test name or I'll help identify the failure.

## Requires

- pytest
- justfile test commands
- Access to test files and code
