"""Circuit breaker pattern implementation for external API resilience."""

import asyncio
import enum
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

# from ..config.schemas import load_settings  # Removed to avoid import issues

logger = logging.getLogger(__name__)


class CircuitBreakerState(enum.Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, blocking calls
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker monitoring."""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    consecutive_failures: int = 0
    last_failure_time: Optional[float] = None
    state_changes: List[str] = field(default_factory=list)
    current_state: CircuitBreakerState = CircuitBreakerState.CLOSED

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_calls == 0:
            return 1.0
        return self.successful_calls / self.total_calls

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate."""
        return 1.0 - self.success_rate


class CircuitBreakerError(Exception):
    """Base exception for circuit breaker errors."""

    pass


class CircuitBreakerOpenError(CircuitBreakerError):
    """Exception raised when circuit breaker is open."""

    def __init__(self, service_name: str, retry_after: float):
        self.service_name = service_name
        self.retry_after = retry_after
        super().__init__(
            f"Circuit breaker is open for {service_name}. Retry after {retry_after:.1f}s"
        )


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5  # Number of failures to open circuit
    recovery_timeout: float = 60.0  # Seconds to wait before trying half-open
    success_threshold: int = 3  # Successful calls needed to close circuit
    timeout: float = 30.0  # Call timeout in seconds

    # Sliding window for failure tracking
    window_size: int = 100  # Number of recent calls to track
    minimum_calls: int = 10  # Minimum calls before evaluating failures

    # Exponential backoff for recovery
    max_recovery_timeout: float = 300.0  # Maximum recovery timeout (5 minutes)
    backoff_multiplier: float = 2.0  # Multiplier for exponential backoff

    # Exception handling
    expected_exceptions: tuple = (Exception,)  # Exceptions that count as failures
    ignored_exceptions: tuple = ()  # Exceptions that don't count as failures


class CircuitBreaker:
    """Circuit breaker implementation for external API calls."""

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        """Initialize circuit breaker."""
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.stats = CircuitBreakerStats()
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._recovery_timeout = self.config.recovery_timeout
        self._call_history = deque(maxlen=self.config.window_size)
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitBreakerState:
        """Get current circuit breaker state."""
        return self._state

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit breaker."""
        if self._state != CircuitBreakerState.OPEN:
            return False

        if self._last_failure_time is None:
            return True

        time_since_failure = time.time() - self._last_failure_time
        return time_since_failure >= self._recovery_timeout

    def _record_success(self):
        """Record a successful call."""
        self._call_history.append(True)
        self.stats.successful_calls += 1
        self.stats.total_calls += 1
        self._failure_count = 0

        if self._state == CircuitBreakerState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.config.success_threshold:
                self._reset_circuit()

    def _record_failure(self, exception: Exception):
        """Record a failed call."""
        self._call_history.append(False)
        self.stats.failed_calls += 1
        self.stats.total_calls += 1
        self.stats.consecutive_failures += 1
        self._failure_count += 1
        self._last_failure_time = time.time()
        self.stats.last_failure_time = self._last_failure_time

        # Check if we should open the circuit
        if self._should_open_circuit():
            self._open_circuit()
        elif self._state == CircuitBreakerState.HALF_OPEN:
            # Failed during half-open, go back to open
            self._open_circuit()

    def _should_open_circuit(self) -> bool:
        """Check if circuit should be opened."""
        if self._state == CircuitBreakerState.OPEN:
            return False

        # Check failure threshold first (consecutive failures)
        if self._failure_count >= self.config.failure_threshold:
            return True

        # Need minimum calls before evaluating failure rate
        if len(self._call_history) < self.config.minimum_calls:
            return False

        # Check failure rate in sliding window
        recent_failures = sum(1 for success in self._call_history if not success)
        failure_rate = recent_failures / len(self._call_history)

        return failure_rate >= 0.5  # 50% failure rate

    def _open_circuit(self):
        """Open the circuit breaker."""
        if self._state != CircuitBreakerState.OPEN:
            logger.warning(f"Circuit breaker '{self.name}' opened due to failures")
            self._state = CircuitBreakerState.OPEN
            self.stats.current_state = CircuitBreakerState.OPEN
            self.stats.state_changes.append(f"OPENED at {time.time()}")

            # Exponential backoff for recovery timeout
            self._recovery_timeout = min(
                self._recovery_timeout * self.config.backoff_multiplier,
                self.config.max_recovery_timeout,
            )

    def _reset_circuit(self):
        """Reset the circuit breaker to closed state."""
        logger.info(f"Circuit breaker '{self.name}' reset to closed state")
        self._state = CircuitBreakerState.CLOSED
        self.stats.current_state = CircuitBreakerState.CLOSED
        self.stats.state_changes.append(f"CLOSED at {time.time()}")
        self._failure_count = 0
        self._success_count = 0
        self.stats.consecutive_failures = 0
        self._recovery_timeout = self.config.recovery_timeout

    def _enter_half_open(self):
        """Enter half-open state to test if service recovered."""
        logger.info(f"Circuit breaker '{self.name}' entering half-open state")
        self._state = CircuitBreakerState.HALF_OPEN
        self.stats.current_state = CircuitBreakerState.HALF_OPEN
        self.stats.state_changes.append(f"HALF_OPEN at {time.time()}")
        self._success_count = 0

    def _check_state(self):
        """Check and update circuit breaker state."""
        if self._state == CircuitBreakerState.OPEN and self._should_attempt_reset():
            self._enter_half_open()

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function with circuit breaker protection."""
        self._check_state()

        # Block calls if circuit is open
        if self._state == CircuitBreakerState.OPEN:
            raise CircuitBreakerOpenError(self.name, self._recovery_timeout)

        # Limit concurrent calls in half-open state
        if self._state == CircuitBreakerState.HALF_OPEN:
            # Only allow one call at a time in half-open
            if self._success_count == 0:
                pass  # Allow first test call
            else:
                # Wait for current test to complete
                time.sleep(0.1)
                if self._state == CircuitBreakerState.OPEN:
                    raise CircuitBreakerOpenError(self.name, self._recovery_timeout)

        try:
            start_time = time.time()
            result = func(*args, **kwargs)

            # Check for timeout
            if time.time() - start_time > self.config.timeout:
                raise TimeoutError(f"Call to {self.name} timed out")

            self._record_success()
            return result

        except Exception as e:
            # Check if this exception should be ignored
            if isinstance(e, self.config.ignored_exceptions):
                logger.debug(f"Ignoring exception in circuit breaker '{self.name}': {e}")
                return None

            # Check if this is an expected failure
            if isinstance(e, self.config.expected_exceptions):
                self._record_failure(e)
                logger.warning(f"Circuit breaker '{self.name}' recorded failure: {e}")

            raise

    async def async_call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute an async function with circuit breaker protection."""
        async with self._lock:
            self._check_state()

            # Block calls if circuit is open
            if self._state == CircuitBreakerState.OPEN:
                raise CircuitBreakerOpenError(self.name, self._recovery_timeout)

        try:
            # Apply timeout
            result = await asyncio.wait_for(func(*args, **kwargs), timeout=self.config.timeout)

            async with self._lock:
                self._record_success()

            return result

        except Exception as e:
            async with self._lock:
                # Check if this exception should be ignored
                if isinstance(e, self.config.ignored_exceptions):
                    logger.debug(f"Ignoring exception in circuit breaker '{self.name}': {e}")
                    return None

                # Check if this is an expected failure
                if isinstance(e, self.config.expected_exceptions):
                    self._record_failure(e)
                    logger.warning(f"Circuit breaker '{self.name}' recorded failure: {e}")

            raise

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self._state.value,
            "total_calls": self.stats.total_calls,
            "successful_calls": self.stats.successful_calls,
            "failed_calls": self.stats.failed_calls,
            "consecutive_failures": self.stats.consecutive_failures,
            "success_rate": self.stats.success_rate,
            "failure_rate": self.stats.failure_rate,
            "last_failure_time": self.stats.last_failure_time,
            "recovery_timeout": self._recovery_timeout,
            "state_changes": self.stats.state_changes[-10:],  # Last 10 state changes
        }

    def reset(self):
        """Manually reset the circuit breaker."""
        logger.info(f"Manually resetting circuit breaker '{self.name}'")
        self._reset_circuit()


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""

    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._configs: Dict[str, CircuitBreakerConfig] = {}

    def register(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Register a new circuit breaker."""
        if name in self._breakers:
            return self._breakers[name]

        breaker = CircuitBreaker(name, config)
        self._breakers[name] = breaker
        self._configs[name] = config or CircuitBreakerConfig()

        logger.info(f"Registered circuit breaker: {name}")
        return breaker

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get a circuit breaker by name."""
        return self._breakers.get(name)

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get stats for all circuit breakers."""
        return {name: breaker.get_stats() for name, breaker in self._breakers.items()}

    def reset_all(self):
        """Reset all circuit breakers."""
        for breaker in self._breakers.values():
            breaker.reset()

    def list_breakers(self) -> List[str]:
        """List all registered circuit breaker names."""
        return list(self._breakers.keys())


# Global registry instance
_registry = CircuitBreakerRegistry()


def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """Get or create a circuit breaker."""
    return _registry.register(name, config)


def circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None):
    """Decorator to apply circuit breaker to a function."""

    def decorator(func):
        breaker = get_circuit_breaker(name, config)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)

        return wrapper

    return decorator


def async_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None):
    """Decorator to apply circuit breaker to an async function."""

    def decorator(func):
        breaker = get_circuit_breaker(name, config)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await breaker.async_call(func, *args, **kwargs)

        return wrapper

    return decorator


def get_all_circuit_breaker_stats() -> Dict[str, Dict[str, Any]]:
    """Get stats for all circuit breakers."""
    return _registry.get_all_stats()


def reset_all_circuit_breakers():
    """Reset all circuit breakers."""
    _registry.reset_all()
