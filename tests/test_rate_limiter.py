#!/usr/bin/env python3
"""Tests for adaptive rate limiter."""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.rate_limiter import AdaptiveRateLimiter, APIRateLimiterFactory


class TestAdaptiveRateLimiter:
    """Test the adaptive rate limiter functionality."""

    def test_initialization(self):
        """Test rate limiter initialization."""
        limiter = AdaptiveRateLimiter(
            base_delay=1.0,
            max_delay=30.0,
            backoff_factor=2.0,
            jitter_factor=0.1,
            reset_threshold=5,
        )

        assert limiter.state.base_delay == 1.0
        assert limiter.state.max_delay == 30.0
        assert limiter.state.current_delay == 1.0
        assert limiter.state.backoff_factor == 2.0

    def test_success_tracking(self):
        """Test that successes reduce delay over time."""
        limiter = AdaptiveRateLimiter(base_delay=2.0, reset_threshold=3)

        # Increase delay first
        limiter.record_failure(is_rate_limit_error=True)
        increased_delay = limiter.state.current_delay
        assert increased_delay > 2.0

        # Record successes
        for _ in range(5):
            limiter.record_success()

        # Delay should be reduced
        assert limiter.state.current_delay <= increased_delay

    def test_failure_tracking(self):
        """Test that failures increase delay."""
        limiter = AdaptiveRateLimiter(base_delay=1.0)
        initial_delay = limiter.state.current_delay

        # Record a failure
        limiter.record_failure(is_rate_limit_error=False)

        # Delay should increase
        assert limiter.state.current_delay > initial_delay

    def test_rate_limit_error_handling(self):
        """Test special handling for rate limit errors."""
        limiter = AdaptiveRateLimiter(base_delay=1.0, backoff_factor=2.0)

        # Rate limit error should increase delay more aggressively
        limiter.record_failure(is_rate_limit_error=True)
        rate_limit_delay = limiter.state.current_delay

        # Reset to test regular failure
        limiter.reset()
        limiter.record_failure(is_rate_limit_error=False)
        regular_delay = limiter.state.current_delay

        # Rate limit error should cause larger delay increase
        assert rate_limit_delay > regular_delay

    def test_max_delay_enforcement(self):
        """Test that delay never exceeds maximum."""
        limiter = AdaptiveRateLimiter(base_delay=1.0, max_delay=10.0, backoff_factor=2.0)

        # Record many failures
        for _ in range(20):
            limiter.record_failure(is_rate_limit_error=True)

        # Should not exceed max delay
        assert limiter.state.current_delay <= 10.0

    def test_reset_functionality(self):
        """Test that reset returns to initial state."""
        limiter = AdaptiveRateLimiter(base_delay=1.0)

        # Increase delay
        limiter.record_failure(is_rate_limit_error=True)
        assert limiter.state.current_delay > 1.0

        # Reset
        limiter.reset()

        # Should be back to base delay
        assert limiter.state.current_delay == 1.0
        assert limiter.state.consecutive_failures == 0

    def test_wait_functionality(self):
        """Test basic wait functionality."""
        limiter = AdaptiveRateLimiter(base_delay=0.1)  # Short delay for testing

        # First call won't wait since no previous request
        start_time = time.time()
        limiter.wait_if_needed()
        time.time() - start_time

        # Second call should wait
        start_time = time.time()
        limiter.wait_if_needed()
        elapsed2 = time.time() - start_time

        # Second call should take longer due to rate limiting
        assert elapsed2 >= 0.05  # Allow some tolerance

    def test_get_current_delay(self):
        """Test getting current delay value."""
        limiter = AdaptiveRateLimiter(base_delay=1.5)

        assert limiter.get_current_delay() == 1.5

        limiter.record_failure(is_rate_limit_error=False)

        assert limiter.get_current_delay() > 1.5


class TestAPIRateLimiterFactory:
    """Test the API rate limiter factory."""

    def test_anthropic_limiter_creation(self):
        """Test creation of Anthropic-specific rate limiter."""
        limiter = APIRateLimiterFactory.create_anthropic_limiter()

        assert isinstance(limiter, AdaptiveRateLimiter)
        assert limiter.state.base_delay == 0.5
        assert limiter.state.max_delay == 30.0
        assert limiter.reset_threshold == 3

    def test_github_limiter_creation(self):
        """Test creation of GitHub-specific rate limiter."""
        limiter = APIRateLimiterFactory.create_github_limiter()

        assert isinstance(limiter, AdaptiveRateLimiter)
        assert limiter.state.base_delay == 1.0
        assert limiter.state.max_delay == 60.0
        assert limiter.reset_threshold == 5

    def test_linear_limiter_creation(self):
        """Test creation of Linear-specific rate limiter."""
        limiter = APIRateLimiterFactory.create_linear_limiter()

        assert isinstance(limiter, AdaptiveRateLimiter)
        assert limiter.state.base_delay == 1.0
        assert limiter.state.max_delay == 45.0
        assert limiter.state.backoff_factor == 1.8

    def test_generic_limiter_creation(self):
        """Test creation of generic rate limiter."""
        limiter = APIRateLimiterFactory.create_generic_limiter(requests_per_minute=120)

        assert isinstance(limiter, AdaptiveRateLimiter)
        # 120 requests per minute = 0.5 seconds per request
        assert limiter.state.base_delay == 0.5

    def test_generic_limiter_with_defaults(self):
        """Test generic limiter with default configuration."""
        limiter = APIRateLimiterFactory.create_generic_limiter()

        assert isinstance(limiter, AdaptiveRateLimiter)
        # Should use default configuration from processing limits
        assert limiter.state.base_delay > 0


class TestRateLimiterEdgeCases:
    """Test edge cases and error conditions."""

    def test_zero_requests_per_minute(self):
        """Test handling of zero requests per minute."""
        limiter = APIRateLimiterFactory.create_generic_limiter(requests_per_minute=0)

        # Should default to 1 second delay
        assert limiter.state.base_delay == 1.0

    def test_negative_delays(self):
        """Test that negative delays are handled properly."""
        # This should not raise an error
        limiter = AdaptiveRateLimiter(base_delay=0.1, max_delay=0.05)

        # Even with max < base, should not crash
        limiter.record_failure(is_rate_limit_error=True)
        assert limiter.state.current_delay >= 0

    def test_concurrent_access(self):
        """Test that rate limiter works with concurrent access."""
        import threading

        limiter = AdaptiveRateLimiter(base_delay=0.01)  # Very short for testing
        results = []

        def worker():
            for _ in range(10):
                start = time.time()
                limiter.wait_if_needed()
                results.append(time.time() - start)
                limiter.record_success()

        # Start multiple threads
        threads = [threading.Thread(target=worker) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have recorded all results
        assert len(results) == 30
