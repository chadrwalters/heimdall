"""Adaptive rate limiter with exponential backoff for API calls."""

import logging
import random
import time
from dataclasses import dataclass
from typing import Optional

from ..config.constants import processing_limits

logger = logging.getLogger(__name__)


@dataclass
class RateLimitState:
    """State tracking for adaptive rate limiting."""

    last_request_time: float = 0.0
    consecutive_failures: int = 0
    current_delay: float = 1.0
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    jitter_factor: float = 0.1


class AdaptiveRateLimiter:
    """Adaptive rate limiter with exponential backoff and jitter."""

    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter_factor: float = 0.1,
        reset_threshold: int = 5,
    ):
        """
        Initialize adaptive rate limiter.

        Args:
            base_delay: Base delay between requests (seconds)
            max_delay: Maximum delay between requests (seconds)
            backoff_factor: Exponential backoff multiplier
            jitter_factor: Random jitter as fraction of delay
            reset_threshold: Consecutive successes to reset delay
        """
        self.state = RateLimitState(
            base_delay=base_delay,
            max_delay=max_delay,
            backoff_factor=backoff_factor,
            current_delay=base_delay,
        )
        self.jitter_factor = jitter_factor
        self.reset_threshold = reset_threshold
        self.consecutive_successes = 0

    def wait_if_needed(self) -> None:
        """Wait if rate limiting is needed."""
        current_time = time.time()
        elapsed = current_time - self.state.last_request_time

        if elapsed < self.state.current_delay:
            sleep_time = self.state.current_delay - elapsed

            # Add jitter to avoid thundering herd
            jitter = random.uniform(
                -self.jitter_factor * sleep_time, self.jitter_factor * sleep_time
            )
            sleep_time = max(0, sleep_time + jitter)

            logger.debug(
                f"Rate limiting: sleeping for {sleep_time:.2f}s "
                f"(base delay: {self.state.current_delay:.2f}s)"
            )
            time.sleep(sleep_time)

        self.state.last_request_time = time.time()

    def record_success(self) -> None:
        """Record a successful API call."""
        self.consecutive_successes += 1
        self.state.consecutive_failures = 0

        # Gradually reduce delay after consecutive successes
        if self.consecutive_successes >= self.reset_threshold:
            old_delay = self.state.current_delay
            self.state.current_delay = max(
                self.state.base_delay, self.state.current_delay / self.state.backoff_factor
            )

            if self.state.current_delay < old_delay:
                logger.debug(
                    f"Rate limiter: reduced delay from {old_delay:.2f}s "
                    f"to {self.state.current_delay:.2f}s after {self.consecutive_successes} successes"
                )

            self.consecutive_successes = 0

    def record_failure(self, is_rate_limit_error: bool = False) -> None:
        """
        Record a failed API call.

        Args:
            is_rate_limit_error: Whether this was specifically a rate limit error
        """
        self.consecutive_successes = 0
        self.state.consecutive_failures += 1

        # Increase delay on failures, especially rate limit errors
        if is_rate_limit_error:
            # More aggressive backoff for rate limit errors
            multiplier = self.state.backoff_factor * 1.5
        else:
            multiplier = self.state.backoff_factor

        old_delay = self.state.current_delay
        self.state.current_delay = min(self.state.max_delay, self.state.current_delay * multiplier)

        logger.warning(
            f"Rate limiter: increased delay from {old_delay:.2f}s "
            f"to {self.state.current_delay:.2f}s after failure "
            f"(consecutive failures: {self.state.consecutive_failures}, "
            f"rate_limit_error: {is_rate_limit_error})"
        )

    def get_current_delay(self) -> float:
        """Get current delay between requests."""
        return self.state.current_delay

    def reset(self) -> None:
        """Reset rate limiter to initial state."""
        logger.info("Rate limiter: resetting to initial state")
        self.state.current_delay = self.state.base_delay
        self.state.consecutive_failures = 0
        self.consecutive_successes = 0


class APIRateLimiterFactory:
    """Factory for creating API-specific rate limiters."""

    @staticmethod
    def create_anthropic_limiter() -> AdaptiveRateLimiter:
        """Create rate limiter for Anthropic API."""
        return AdaptiveRateLimiter(
            base_delay=0.5,  # Anthropic allows higher rates
            max_delay=30.0,
            backoff_factor=2.0,
            jitter_factor=0.1,
            reset_threshold=3,
        )

    @staticmethod
    def create_github_limiter() -> AdaptiveRateLimiter:
        """Create rate limiter for GitHub API."""
        return AdaptiveRateLimiter(
            base_delay=1.0,  # GitHub has stricter limits
            max_delay=60.0,
            backoff_factor=2.0,
            jitter_factor=0.15,
            reset_threshold=5,
        )

    @staticmethod
    def create_linear_limiter() -> AdaptiveRateLimiter:
        """Create rate limiter for Linear API."""
        return AdaptiveRateLimiter(
            base_delay=1.0,  # Linear GraphQL API
            max_delay=45.0,
            backoff_factor=1.8,
            jitter_factor=0.1,
            reset_threshold=4,
        )

    @staticmethod
    def create_generic_limiter(requests_per_minute: Optional[int] = None) -> AdaptiveRateLimiter:
        """Create generic rate limiter based on requests per minute."""
        if requests_per_minute is None:
            requests_per_minute = processing_limits.API_RATE_LIMIT_REQUESTS_PER_MINUTE

        # Calculate base delay from requests per minute
        base_delay = 60.0 / requests_per_minute if requests_per_minute > 0 else 1.0

        return AdaptiveRateLimiter(
            base_delay=base_delay,
            max_delay=min(60.0, base_delay * 30),
            backoff_factor=2.0,
            jitter_factor=0.1,
            reset_threshold=5,
        )
