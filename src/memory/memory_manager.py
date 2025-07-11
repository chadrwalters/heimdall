"""Enhanced memory management for large-scale processing."""

import gc
import logging
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional

import psutil

from ..config.constants import processing_limits

logger = logging.getLogger(__name__)


@dataclass
class MemoryStats:
    """Memory usage statistics."""

    total_mb: float
    used_mb: float
    available_mb: float
    percent_used: float
    process_memory_mb: float
    process_percent: float


class MemoryManager:
    """Enhanced memory manager with automatic cleanup and monitoring."""

    def __init__(
        self,
        max_memory_mb: Optional[int] = None,
        warning_threshold: Optional[float] = None,
        critical_threshold: float = 0.95,
        cleanup_interval: float = 30.0,
    ):
        """
        Initialize memory manager.

        Args:
            max_memory_mb: Maximum memory usage in MB
            warning_threshold: Warning threshold as fraction (0.0-1.0)
            critical_threshold: Critical threshold as fraction (0.0-1.0)
            cleanup_interval: Interval between cleanup checks (seconds)
        """
        self.max_memory_mb = max_memory_mb or processing_limits.MAX_MEMORY_MB
        self.warning_threshold = warning_threshold or processing_limits.MEMORY_WARNING_THRESHOLD
        self.critical_threshold = critical_threshold
        self.cleanup_interval = cleanup_interval

        self._cleanup_callbacks: list[Callable[[], None]] = []
        self._monitoring_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()
        self._lock = threading.Lock()

        # Process reference for monitoring
        self.process = psutil.Process()

    def start_monitoring(self) -> None:
        """Start background memory monitoring."""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            logger.warning("Memory monitoring already running")
            return

        self._stop_monitoring.clear()
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop, name="MemoryMonitor", daemon=True
        )
        self._monitoring_thread.start()
        logger.info("Memory monitoring started")

    def stop_monitoring(self) -> None:
        """Stop background memory monitoring."""
        if self._monitoring_thread:
            self._stop_monitoring.set()
            self._monitoring_thread.join(timeout=5.0)
            logger.info("Memory monitoring stopped")

    def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        while not self._stop_monitoring.wait(self.cleanup_interval):
            try:
                stats = self.get_memory_stats()
                self._check_memory_pressure(stats)
            except Exception as e:
                logger.warning(f"Memory monitoring error: {e}")

    def get_memory_stats(self) -> MemoryStats:
        """Get current memory statistics."""
        try:
            # System memory
            system_memory = psutil.virtual_memory()

            # Process memory
            process_memory = self.process.memory_info()
            process_memory_mb = process_memory.rss / (1024 * 1024)

            return MemoryStats(
                total_mb=system_memory.total / (1024 * 1024),
                used_mb=system_memory.used / (1024 * 1024),
                available_mb=system_memory.available / (1024 * 1024),
                percent_used=system_memory.percent / 100.0,
                process_memory_mb=process_memory_mb,
                process_percent=process_memory_mb / (system_memory.total / (1024 * 1024)),
            )
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            # Return safe defaults
            return MemoryStats(
                total_mb=0.0,
                used_mb=0.0,
                available_mb=0.0,
                percent_used=0.0,
                process_memory_mb=0.0,
                process_percent=0.0,
            )

    def _check_memory_pressure(self, stats: MemoryStats) -> None:
        """Check for memory pressure and take action."""
        # Check process memory against our limit
        if stats.process_memory_mb > self.max_memory_mb:
            logger.critical(
                f"Process memory ({stats.process_memory_mb:.1f}MB) "
                f"exceeds limit ({self.max_memory_mb}MB)"
            )
            self._trigger_aggressive_cleanup()
            return

        # Check system memory pressure
        if stats.percent_used >= self.critical_threshold:
            logger.critical(
                f"System memory critically high ({stats.percent_used:.1%}) - "
                "triggering aggressive cleanup"
            )
            self._trigger_aggressive_cleanup()
        elif stats.percent_used >= self.warning_threshold:
            logger.warning(
                f"System memory high ({stats.percent_used:.1%}) - "
                f"process using {stats.process_memory_mb:.1f}MB"
            )
            self._trigger_cleanup()

    def _trigger_cleanup(self) -> None:
        """Trigger normal cleanup procedures."""
        with self._lock:
            logger.info("Triggering memory cleanup")

            # Run registered cleanup callbacks
            for callback in self._cleanup_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.warning(f"Cleanup callback failed: {e}")

            # Force garbage collection
            collected = gc.collect()
            logger.debug(f"Garbage collection freed {collected} objects")

    def _trigger_aggressive_cleanup(self) -> None:
        """Trigger aggressive cleanup procedures."""
        with self._lock:
            logger.warning("Triggering aggressive memory cleanup")

            # Multiple GC passes for better cleanup
            total_collected = 0
            for i in range(3):
                collected = gc.collect()
                total_collected += collected
                if collected == 0:
                    break
                time.sleep(0.1)  # Small delay between passes

            logger.info(f"Aggressive GC freed {total_collected} objects")

            # Run cleanup callbacks
            for callback in self._cleanup_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.warning(f"Aggressive cleanup callback failed: {e}")

    def register_cleanup_callback(self, callback: Callable[[], None]) -> None:
        """Register a callback to run during memory cleanup."""
        with self._lock:
            self._cleanup_callbacks.append(callback)
            logger.debug(f"Registered cleanup callback: {callback.__name__}")

    def unregister_cleanup_callback(self, callback: Callable[[], None]) -> None:
        """Unregister a cleanup callback."""
        with self._lock:
            try:
                self._cleanup_callbacks.remove(callback)
                logger.debug(f"Unregistered cleanup callback: {callback.__name__}")
            except ValueError:
                logger.warning(f"Cleanup callback not found: {callback.__name__}")

    def check_memory_available(self, required_mb: float) -> bool:
        """Check if enough memory is available for an operation."""
        stats = self.get_memory_stats()

        # Check if we have enough system memory
        if stats.available_mb < required_mb:
            logger.warning(
                f"Insufficient system memory: need {required_mb}MB, "
                f"available {stats.available_mb:.1f}MB"
            )
            return False

        # Check if this would exceed our process limit
        projected_usage = stats.process_memory_mb + required_mb
        if projected_usage > self.max_memory_mb:
            logger.warning(
                f"Operation would exceed process memory limit: "
                f"current {stats.process_memory_mb:.1f}MB + "
                f"required {required_mb}MB = {projected_usage:.1f}MB > "
                f"limit {self.max_memory_mb}MB"
            )
            return False

        return True

    def force_cleanup(self) -> None:
        """Force immediate memory cleanup."""
        logger.info("Forcing immediate memory cleanup")
        self._trigger_cleanup()

    def get_memory_pressure_level(self) -> str:
        """Get current memory pressure level."""
        stats = self.get_memory_stats()

        if stats.percent_used >= self.critical_threshold:
            return "critical"
        elif stats.percent_used >= self.warning_threshold:
            return "warning"
        else:
            return "normal"

    def __enter__(self):
        """Context manager entry."""
        self.start_monitoring()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_monitoring()


# Global memory manager instance
_memory_manager: Optional[MemoryManager] = None
_manager_lock = threading.Lock()


def get_memory_manager() -> MemoryManager:
    """Get the global memory manager instance."""
    global _memory_manager

    if _memory_manager is None:
        with _manager_lock:
            if _memory_manager is None:
                _memory_manager = MemoryManager()

    return _memory_manager


def memory_efficient_operation(required_mb: float = 100.0):
    """Decorator for memory-efficient operations."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            manager = get_memory_manager()

            if not manager.check_memory_available(required_mb):
                logger.warning(f"Triggering cleanup before {func.__name__}")
                manager.force_cleanup()

                # Check again after cleanup
                if not manager.check_memory_available(required_mb):
                    raise MemoryError(
                        f"Insufficient memory for {func.__name__}: requires {required_mb}MB"
                    )

            try:
                return func(*args, **kwargs)
            finally:
                # Optional cleanup after large operations
                if required_mb > 500:  # Only for operations > 500MB
                    manager.force_cleanup()

        return wrapper

    return decorator
