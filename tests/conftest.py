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
