"""Cache warming utilities for predictable workloads."""

import asyncio
import logging
from typing import Any
from datetime import datetime, timedelta

from src.analysis.analysis_engine import AnalysisEngine
from src.data.streaming_processor import StreamingDataProcessor
from src.logging.structured_logger import get_logger, log_performance

logger = get_logger(__name__)


class CacheWarmer:
    """Warm cache for predictable analysis workloads."""
    
    def __init__(self, analysis_engine: AnalysisEngine):
        """Initialize cache warmer with analysis engine."""
        self.analysis_engine = analysis_engine
        self.processor = StreamingDataProcessor()
    
    async def warm_recent_prs(self, organization: str, days: int = 1, max_prs: int = 50) -> dict[str, Any]:
        """Warm cache with recent PRs."""
        with log_performance(logger, "cache_warm_recent_prs") as perf:
            warmed_count = 0
            already_cached = 0
            
            try:
                # Calculate date range
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                logger.info(f"Warming cache for {organization} PRs from last {days} days")
                
                # Process PRs from CSV files
                pr_files = self.processor._find_pr_files()
                
                for pr_file in pr_files[:max_prs]:  # Limit to max_prs
                    try:
                        # Read PR data
                        pr_data = self.processor._read_csv_file(pr_file)
                        
                        # Check if PR is within date range
                        pr_date = datetime.fromisoformat(pr_data.get('created_at', '').replace('Z', '+00:00'))
                        if start_date <= pr_date <= end_date:
                            # Prepare context to generate cache key
                            context = self.analysis_engine.context_preparer.prepare_pr_context(pr_data)
                            
                            # Check if already in cache
                            if context.cache_key in self.analysis_engine.results_cache:
                                already_cached += 1
                            else:
                                # Analyze to warm cache
                                self.analysis_engine.analyze_pr(pr_data, use_cache=True)
                                warmed_count += 1
                                
                    except Exception as e:
                        logger.warning(f"Failed to warm cache for PR: {e}")
                        continue
                
                perf.add_context(
                    organization=organization,
                    days=days,
                    warmed_count=warmed_count,
                    already_cached=already_cached
                )
                
                return {
                    "warmed_count": warmed_count,
                    "already_cached": already_cached,
                    "total_processed": warmed_count + already_cached,
                    "cache_size": len(self.analysis_engine.results_cache)
                }
                
            except Exception as e:
                logger.error(f"Cache warming failed: {e}")
                return {
                    "warmed_count": warmed_count,
                    "already_cached": already_cached,
                    "error": str(e)
                }
    
    async def warm_scheduled_analysis(self, organization: str, lookback_days: int = 7) -> dict[str, Any]:
        """Warm cache for scheduled analysis patterns."""
        with log_performance(logger, "cache_warm_scheduled") as perf:
            # For scheduled analyses, warm cache with:
            # 1. Most recent PRs (likely to be re-analyzed)
            # 2. High-impact PRs (frequently referenced)
            # 3. PRs without Linear tickets (process compliance checks)
            
            results = {
                "recent_prs": await self.warm_recent_prs(organization, days=lookback_days, max_prs=100),
                "timestamp": datetime.now().isoformat()
            }
            
            perf.add_context(
                organization=organization,
                lookback_days=lookback_days,
                total_warmed=results["recent_prs"]["warmed_count"]
            )
            
            return results
    
    def get_warming_stats(self) -> dict[str, Any]:
        """Get cache warming statistics."""
        return {
            "cache_size": len(self.analysis_engine.results_cache),
            "cache_hits": self.analysis_engine.cache_hits,
            "cache_misses": self.analysis_engine.cache_misses,
            "cache_hit_rate": self.analysis_engine.cache_hits / (self.analysis_engine.cache_hits + self.analysis_engine.cache_misses) 
                             if (self.analysis_engine.cache_hits + self.analysis_engine.cache_misses) > 0 else 0
        }