"""Cache management for analysis engine."""

import time
from typing import Any

from cachetools import TTLCache

from ..config.constants import get_settings
from ..structured_logging import LogContext, get_structured_logger

logger = get_structured_logger(__name__, LogContext(component="cache_manager"))


class CacheManager:
    """Manages caching for analysis results with statistics tracking."""

    def __init__(self, cache_size: int = None):
        """Initialize cache manager with configurable size."""
        settings = get_settings()
        
        # Use TTL cache with size limit
        cache_size = min(
            cache_size or settings.processing_limits.cache_size_default,
            settings.processing_limits.cache_size_max,
        )
        
        self.cache = TTLCache(
            maxsize=cache_size, 
            ttl=settings.processing_limits.cache_ttl_seconds
        )
        
        # Cache metrics
        self.cache_hits = 0
        self.cache_misses = 0
        self._start_time = time.time()
        
        logger.info(
            "Cache manager initialized",
            extra={
                "cache_size": cache_size,
                "ttl_seconds": settings.processing_limits.cache_ttl_seconds,
            },
        )

    def get(self, key: str) -> Any | None:
        """Get item from cache, tracking hit/miss statistics."""
        if key in self.cache:
            self.cache_hits += 1
            logger.debug(f"Cache hit for key: {key}")
            return self.cache[key]
        
        self.cache_misses += 1
        logger.debug(f"Cache miss for key: {key}")
        return None

    def set(self, key: str, value: Any) -> None:
        """Set item in cache."""
        self.cache[key] = value
        logger.debug(f"Cached item with key: {key}")

    def clear(self) -> int:
        """Clear all cache entries and return count of cleared items."""
        cache_size = len(self.cache)
        self.cache.clear()
        
        logger.info(
            "Cache cleared",
            extra={
                "items_cleared": cache_size,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
            },
        )
        
        return cache_size

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total_requests if total_requests > 0 else 0
        uptime_seconds = time.time() - self._start_time
        
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": hit_rate,
            "cache_size": len(self.cache),
            "cache_maxsize": self.cache.maxsize,
            "cache_ttl": self.cache.ttl,
            "uptime_seconds": uptime_seconds,
            "requests_per_second": total_requests / uptime_seconds if uptime_seconds > 0 else 0,
        }

    def get_memory_usage(self) -> dict[str, Any]:
        """Get approximate memory usage of cache."""
        try:
            import sys
            
            total_size = sys.getsizeof(self.cache)
            
            # Estimate size of cached items
            for key, value in self.cache.items():
                total_size += sys.getsizeof(key) + sys.getsizeof(value)
                
            return {
                "cache_memory_bytes": total_size,
                "cache_memory_mb": total_size / (1024 * 1024),
                "items_count": len(self.cache),
                "avg_item_size_bytes": total_size / len(self.cache) if len(self.cache) > 0 else 0,
            }
        except Exception as e:
            logger.warning(f"Failed to calculate cache memory usage: {e}")
            return {"error": "Unable to calculate memory usage"}

    def cleanup_expired(self) -> int:
        """Manually trigger cleanup of expired items and return count."""
        # TTLCache automatically cleans up expired items, but we can force it
        original_size = len(self.cache)
        
        # Access cache info to trigger cleanup
        _ = self.cache.currsize
        
        cleaned_count = original_size - len(self.cache)
        
        if cleaned_count > 0:
            logger.debug(f"Cleaned up {cleaned_count} expired cache items")
            
        return cleaned_count

    def get_cache_info(self) -> dict[str, Any]:
        """Get detailed cache information including internal state."""
        return {
            "maxsize": self.cache.maxsize,
            "currsize": len(self.cache),
            "ttl": self.cache.ttl,
            "timer": getattr(self.cache, 'timer', time.time)(),
            "hits": self.cache_hits,
            "misses": self.cache_misses,
        }
