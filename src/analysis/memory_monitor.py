"""Memory monitoring for analysis engine."""

from typing import Any, Callable

from ..config.constants import get_settings
from ..memory import get_memory_manager
from ..structured_logging import LogContext, get_structured_logger

logger = get_structured_logger(__name__, LogContext(component="memory_monitor"))


class MemoryMonitor:
    """Monitors memory usage and triggers cleanup when needed."""

    def __init__(self):
        """Initialize memory monitor."""
        self.memory_manager = get_memory_manager()
        self.cleanup_callbacks = []
        self.settings = get_settings()
        
        # Start memory monitoring
        self.memory_manager.start_monitoring()
        
        logger.info("Memory monitor initialized")

    def register_cleanup_callback(self, callback: Callable[[], None]) -> None:
        """Register a callback to be called when memory cleanup is needed."""
        self.cleanup_callbacks.append(callback)
        logger.debug(f"Registered cleanup callback: {callback.__name__}")

    def check_memory_usage(self) -> dict[str, Any]:
        """Check memory usage and trigger cleanup if needed."""
        try:
            stats = self.memory_manager.get_memory_stats()
            pressure = self.memory_manager.get_memory_pressure_level()
            
            memory_info = {
                "total_mb": stats.total_mb,
                "used_mb": stats.used_mb,
                "available_mb": stats.available_mb,
                "percent_used": stats.percent_used * 100,
                "process_memory_mb": stats.process_memory_mb,
                "process_percent": stats.process_percent * 100,
                "pressure_level": pressure,
            }
            
            if pressure == "warning":
                logger.warning(
                    f"Memory pressure warning: {stats.percent_used:.1%} "
                    f"({stats.used_mb:.1f}MB used, {stats.available_mb:.1f}MB available)"
                )
            elif pressure == "critical":
                logger.critical(
                    f"Critical memory pressure: {stats.percent_used:.1%} "
                    f"({stats.used_mb:.1f}MB used, {stats.available_mb:.1f}MB available)"
                )
                self._trigger_cleanup("critical_memory_pressure")
                
            return memory_info
            
        except Exception as e:
            logger.warning(f"Enhanced memory monitoring failed: {e}")
            return self._fallback_memory_check()

    def _fallback_memory_check(self) -> dict[str, Any]:
        """Fallback memory monitoring using psutil."""
        try:
            import psutil
            
            memory_info = psutil.virtual_memory()
            memory_percent = memory_info.percent / 100
            
            memory_data = {
                "total_mb": memory_info.total / (1024 * 1024),
                "used_mb": memory_info.used / (1024 * 1024),
                "available_mb": memory_info.available / (1024 * 1024),
                "percent_used": memory_percent * 100,
                "pressure_level": self._get_pressure_level(memory_percent),
                "fallback_monitoring": True,
            }
            
            if memory_percent > self.settings.processing_limits.memory_warning_threshold:
                logger.warning(
                    f"High memory usage (fallback): {memory_percent:.1%}. "
                    f"Consider reducing batch size or cache size."
                )
                
                # Trigger cleanup if critically high
                critical_threshold = min(
                    self.settings.processing_limits.memory_warning_threshold + 0.1, 
                    0.95
                )
                if memory_percent > critical_threshold:
                    logger.warning(
                        f"Memory critically high ({memory_percent:.1%}) - triggering cleanup"
                    )
                    self._trigger_cleanup("critical_memory_fallback")
                    
            return memory_data
            
        except Exception as fallback_e:
            logger.error(f"Fallback memory monitoring also failed: {fallback_e}")
            return {
                "error": "Unable to monitor memory usage",
                "pressure_level": "unknown",
                "fallback_monitoring": True,
            }

    def _get_pressure_level(self, memory_percent: float) -> str:
        """Determine memory pressure level from percentage."""
        warning_threshold = self.settings.processing_limits.memory_warning_threshold
        critical_threshold = min(warning_threshold + 0.1, 0.95)
        
        if memory_percent > critical_threshold:
            return "critical"
        elif memory_percent > warning_threshold:
            return "warning"
        else:
            return "normal"

    def _trigger_cleanup(self, reason: str) -> None:
        """Trigger all registered cleanup callbacks."""
        logger.info(f"Triggering memory cleanup due to: {reason}")
        
        cleanup_count = 0
        for callback in self.cleanup_callbacks:
            try:
                callback()
                cleanup_count += 1
                logger.debug(f"Executed cleanup callback: {callback.__name__}")
            except Exception as e:
                logger.error(f"Cleanup callback {callback.__name__} failed: {e}")
        
        logger.info(f"Completed {cleanup_count}/{len(self.cleanup_callbacks)} cleanup callbacks")

    def get_memory_stats(self) -> dict[str, Any]:
        """Get comprehensive memory statistics."""
        try:
            enhanced_stats = self.memory_manager.get_memory_stats()
            return {
                "total_mb": enhanced_stats.total_mb,
                "used_mb": enhanced_stats.used_mb,
                "available_mb": enhanced_stats.available_mb,
                "percent_used": enhanced_stats.percent_used * 100,
                "process_memory_mb": enhanced_stats.process_memory_mb,
                "process_percent": enhanced_stats.process_percent * 100,
                "pressure_level": self.memory_manager.get_memory_pressure_level(),
                "monitoring_type": "enhanced",
            }
        except Exception:
            return self._fallback_memory_check()

    def force_cleanup(self, reason: str = "manual") -> None:
        """Manually trigger cleanup callbacks."""
        self._trigger_cleanup(reason)
