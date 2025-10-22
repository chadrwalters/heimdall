"""Rate limiting and backoff for GitHub API calls."""

import logging
import random
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class RateLimitInfo:
    """Rate limit information from GitHub API."""

    limit: int
    remaining: int
    reset_at: datetime
    used: int


class GitHubRateLimiter:
    """Rate limiter for GitHub API with exponential backoff."""

    def __init__(
        self,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
        rate_limit_buffer: int = 100,
    ):
        """Initialize rate limiter.

        Args:
            initial_delay: Initial delay in seconds for backoff
            max_delay: Maximum delay in seconds
            backoff_factor: Factor to multiply delay by on each retry
            jitter: Whether to add random jitter to delays
            rate_limit_buffer: Buffer to maintain before hitting rate limit
        """
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.rate_limit_buffer = rate_limit_buffer

        # Track rate limit status
        self._rate_limit_info: Optional[RateLimitInfo] = None
        self._last_request_time: Optional[datetime] = None
        self._consecutive_failures = 0

        # Statistics
        self.total_requests = 0
        self.rate_limited_requests = 0
        self.backoff_requests = 0

    def _parse_rate_limit_headers(self, response: requests.Response) -> RateLimitInfo:
        """Parse rate limit headers from GitHub API response.

        Args:
            response: HTTP response from GitHub API

        Returns:
            Rate limit information
        """
        headers = response.headers

        limit = int(headers.get("X-RateLimit-Limit", 5000))
        remaining = int(headers.get("X-RateLimit-Remaining", 0))
        used = int(headers.get("X-RateLimit-Used", 0))

        # Parse reset time
        reset_timestamp = int(headers.get("X-RateLimit-Reset", 0))
        reset_at = datetime.fromtimestamp(reset_timestamp) if reset_timestamp else datetime.now()

        return RateLimitInfo(limit=limit, remaining=remaining, reset_at=reset_at, used=used)

    def _calculate_delay(self, attempt: int = 0) -> float:
        """Calculate delay for next attempt.

        Args:
            attempt: Current attempt number (0-based)

        Returns:
            Delay in seconds
        """
        delay = self.initial_delay * (self.backoff_factor**attempt)
        delay = min(delay, self.max_delay)

        if self.jitter:
            # Add random jitter (±25% of delay)
            jitter_amount = delay * 0.25
            delay += random.uniform(-jitter_amount, jitter_amount)
            delay = max(0.1, delay)  # Minimum 0.1 second delay

        return delay

    def _should_wait_for_rate_limit(self) -> bool:
        """Check if we should wait due to rate limit constraints.

        Returns:
            True if we should wait
        """
        if not self._rate_limit_info:
            return False

        # Wait if we're close to the rate limit
        if self._rate_limit_info.remaining <= self.rate_limit_buffer:
            return True

        # Wait if rate limit has reset in the future
        now = datetime.now()
        if self._rate_limit_info.reset_at > now:
            time_until_reset = (self._rate_limit_info.reset_at - now).total_seconds()
            # Only wait if reset is soon (within 5 minutes)
            if time_until_reset <= 300:
                return True

        return False

    def _wait_for_rate_limit_reset(self) -> None:
        """Wait for rate limit to reset."""
        if not self._rate_limit_info:
            return

        now = datetime.now()
        if self._rate_limit_info.reset_at <= now:
            return

        wait_time = (self._rate_limit_info.reset_at - now).total_seconds()
        wait_time = min(wait_time, 3600)  # Max 1 hour wait

        logger.info(f"Rate limit hit, waiting {wait_time:.1f} seconds for reset")
        time.sleep(wait_time)

        # Clear rate limit info after reset
        self._rate_limit_info = None

    def execute_request(
        self, request_func: Callable[[], requests.Response], max_retries: int = 3
    ) -> requests.Response:
        """Execute a GitHub API request with rate limiting and retry logic.

        Args:
            request_func: Function that makes the HTTP request
            max_retries: Maximum number of retry attempts

        Returns:
            HTTP response

        Raises:
            requests.exceptions.RequestException: If all retries fail
        """
        self.total_requests += 1

        for attempt in range(max_retries + 1):
            try:
                # Check if we should wait for rate limit
                if self._should_wait_for_rate_limit():
                    self._wait_for_rate_limit_reset()
                    self.rate_limited_requests += 1

                # Add small delay between requests to be respectful
                if self._last_request_time:
                    time_since_last = (datetime.now() - self._last_request_time).total_seconds()
                    if time_since_last < 0.1:  # Minimum 100ms between requests
                        time.sleep(0.1 - time_since_last)

                # Execute the request
                response = request_func()
                self._last_request_time = datetime.now()

                # Update rate limit info
                self._rate_limit_info = self._parse_rate_limit_headers(response)

                # Handle specific status codes
                if response.status_code == 403:
                    # Rate limit exceeded
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        wait_time = int(retry_after)
                        logger.warning(f"Rate limit exceeded, waiting {wait_time} seconds")
                        time.sleep(wait_time)
                        continue

                    # Check if it's a rate limit response
                    if "rate limit exceeded" in response.text.lower():
                        self._wait_for_rate_limit_reset()
                        continue

                elif response.status_code == 429:
                    # Too Many Requests
                    retry_after = response.headers.get("Retry-After", "60")
                    wait_time = int(retry_after)
                    logger.warning(f"Too many requests, waiting {wait_time} seconds")
                    time.sleep(wait_time)
                    continue

                elif response.status_code >= 500:
                    # Server error - use exponential backoff
                    if attempt < max_retries:
                        delay = self._calculate_delay(attempt)
                        logger.warning(
                            f"Server error {response.status_code}, retrying in {delay:.1f}s"
                        )
                        time.sleep(delay)
                        self.backoff_requests += 1
                        continue

                # Reset failure count on success
                self._consecutive_failures = 0
                return response

            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException,
            ) as e:
                self._consecutive_failures += 1

                if attempt < max_retries:
                    delay = self._calculate_delay(attempt)
                    logger.warning(f"Request failed ({e}), retrying in {delay:.1f}s")
                    time.sleep(delay)
                    self.backoff_requests += 1
                    continue
                else:
                    logger.error(f"Request failed after {max_retries} retries: {e}")
                    raise

        # This should never be reached
        raise requests.exceptions.RequestException("Maximum retries exceeded")

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status.

        Returns:
            Dictionary with rate limit information
        """
        status = {
            "total_requests": self.total_requests,
            "rate_limited_requests": self.rate_limited_requests,
            "backoff_requests": self.backoff_requests,
            "rate_limit_info": None,
        }

        if self._rate_limit_info:
            status["rate_limit_info"] = {
                "limit": self._rate_limit_info.limit,
                "remaining": self._rate_limit_info.remaining,
                "used": self._rate_limit_info.used,
                "reset_at": self._rate_limit_info.reset_at.isoformat(),
                "reset_in_seconds": max(
                    0, (self._rate_limit_info.reset_at - datetime.now()).total_seconds()
                ),
            }

        return status


class RateLimitedSession(requests.Session):
    """Requests session with built-in rate limiting."""

    def __init__(self, rate_limiter: Optional[GitHubRateLimiter] = None):
        """Initialize rate limited session.

        Args:
            rate_limiter: Rate limiter instance (creates default if None)
        """
        super().__init__()
        self.rate_limiter = rate_limiter or GitHubRateLimiter()

    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make a rate-limited request.

        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request arguments

        Returns:
            HTTP response
        """

        def make_request():
            return super(RateLimitedSession, self).request(method, url, **kwargs)

        return self.rate_limiter.execute_request(make_request)

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get rate limit status."""
        return self.rate_limiter.get_rate_limit_status()
