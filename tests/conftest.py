"""Pytest configuration and shared fixtures."""

import os

import pytest


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires API key)"
    )
    config.addinivalue_line("markers", "slow: mark test as slow running")


@pytest.fixture(scope="session")
def api_key():
    """Get API key from environment or skip test."""
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        pytest.skip("ANTHROPIC_API_KEY not set")
    return key


@pytest.fixture
def mock_anthropic_response():
    """Provide a mock Anthropic API response."""
    return {
        "response": '{"work_type": "New Feature", "complexity_score": 7, "risk_score": 5, "clarity_score": 8, "analysis_summary": "Test analysis"}',
        "usage": {"total_tokens": 1000, "prompt_tokens": 800, "completion_tokens": 200},
    }


@pytest.fixture(autouse=True)
def reset_caches():
    """Reset any caches between tests."""
    # This would reset any module-level caches if needed
    yield


@pytest.fixture
def mock_cache_directory():
    """Provide a temporary cache directory for testing."""
    import shutil
    import tempfile
    
    temp_dir = tempfile.mkdtemp()
    cache_dir = os.path.join(temp_dir, ".cache")
    os.makedirs(cache_dir, exist_ok=True)
    
    # Create cache subdirectories
    for subdir in ["repos", "prs", "commits"]:
        os.makedirs(os.path.join(cache_dir, subdir), exist_ok=True)
    
    yield cache_dir
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_cache_entry():
    """Provide a mock cache entry for testing."""
    return {
        "cached_at": "2025-07-09T19:05:53Z",
        "ttl_seconds": 3600,
        "etag": "test-etag-123",
        "data": {
            "test": "data",
            "number": 123,
            "array": [1, 2, 3]
        }
    }


@pytest.fixture
def mock_extraction_data():
    """Provide mock extraction data for testing."""
    return {
        "repos": [
            {
                "name": "test-repo-1",
                "full_name": "org/test-repo-1",
                "archived": False,
                "language": "Python"
            }
        ],
        "prs": [
            {
                "number": 123,
                "title": "Test PR",
                "state": "open",
                "author": {"login": "testuser"}
            }
        ],
        "commits": [
            {
                "sha": "abc123def456",
                "commit": {
                    "message": "Test commit",
                    "author": {"name": "Test User"}
                }
            }
        ]
    }
