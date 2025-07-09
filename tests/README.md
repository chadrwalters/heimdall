# AI Analysis Engine Test Suite

Comprehensive test suite for the AI Analysis Engine with 39+ tests covering all major functionality.

## Test Coverage

### ✅ PromptEngineer Tests (21 tests)
- Prompt creation with various PR/commit data
- Large diff truncation handling
- JSON response parsing (valid, invalid, partial)
- Impact score calculation
- Work type classification for 15 different scenarios

### ✅ AnalysisEngine Tests (7 tests)
- Successful PR analysis with mocked Claude API
- AI assistance detection in PRs
- Linear ticket extraction
- API error handling with graceful fallback
- Commit analysis
- Batch PR processing
- Usage statistics tracking

### ✅ Edge Cases Tests (3 tests)
- Empty PR body handling
- PRs with no file changes
- Massive PRs with 500+ files

### ✅ Performance Tests (2 tests)
- Concurrent PR analysis
- Cache performance validation

### ✅ AI Detection Tests (6 tests)
- Detection of various AI tools:
  - Claude Code
  - GitHub Copilot
  - Cursor
  - Generic AI assistants
  - Co-author formats

### 🔄 Integration Tests (1 test - skipped)
- Live API testing with real Claude API (requires ANTHROPIC_API_KEY)

## Running Tests

```bash
# Run all tests
pytest tests/test_analysis_integration.py -v

# Run without integration tests
pytest tests/test_analysis_integration.py -v -m "not integration"

# Run specific test class
pytest tests/test_analysis_integration.py::TestPromptEngineer -v

# Run with coverage
pytest tests/test_analysis_integration.py -v --cov=src.analysis --cov-report=html

# Run live API tests (requires ANTHROPIC_API_KEY)
ANTHROPIC_API_KEY=your-key pytest tests/test_analysis_integration.py -v -m integration
```

## Test Fixtures

Test fixtures are organized in `tests/fixtures/`:
- Sample PR and commit data for various scenarios
- Sample diffs (small, medium, large, truncated)
- Mock API responses
- Work type classification test cases
- AI-assisted PR bodies
- Edge case PR data

## CI/CD Integration

GitHub Actions workflow is configured in `.github/workflows/test-analysis.yml`:
- Runs on push/PR for analysis code changes
- Tests against Python 3.9, 3.10, and 3.11
- Includes coverage reporting
- Performance benchmarks on main branch
- Integration tests with test API key (if configured)

## Coverage

Current test coverage: **63%** overall
- `analysis_engine.py`: 68%
- `context_preparer.py`: 93%
- `prompt_engineer.py`: 64%
- `claude_client.py`: 18% (mostly mocked in tests)

## Known Issues

- One intermittent test failure in batch_analyze_prs (race condition in test setup)
- ClaudeClient has low coverage as it's mocked in most tests