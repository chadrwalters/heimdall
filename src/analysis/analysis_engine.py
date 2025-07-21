"""Main AI Analysis Engine combining all components with clean architecture."""

from typing import Any

from ..structured_logging import (
    LogContext,
    get_structured_logger,
    log_performance,
    set_correlation_id,
)
from .analysis_coordinator import AnalysisCoordinator
from .cache_manager import CacheManager
from .claude_client import ClaudeClient
from .context_preparer import ContextPreparer, PreparedContext
from .memory_monitor import MemoryMonitor
from .prompt_engineer import PromptEngineer

logger = get_structured_logger(__name__, LogContext(component="analysis_engine"))


class AnalysisEngine:
    """Main engine for AI-powered code analysis with clean separation of concerns."""

    def __init__(self, api_key: str | None = None, max_workers: int = None, cache_size: int = None):
        """Initialize the analysis engine with dependency injection."""
        correlation_id = set_correlation_id()

        with log_performance(logger, "analysis_engine_init") as perf:
            # Initialize core components
            self.claude_client = ClaudeClient(api_key=api_key)
            self.prompt_engineer = PromptEngineer()
            self.context_preparer = ContextPreparer()
            
            # Initialize resource management components
            self.cache_manager = CacheManager(cache_size=cache_size)
            self.memory_monitor = MemoryMonitor()
            
            # Initialize coordination component
            self.coordinator = AnalysisCoordinator(
                claude_client=self.claude_client,
                prompt_engineer=self.prompt_engineer,
                context_preparer=self.context_preparer,
                cache_manager=self.cache_manager,
                memory_monitor=self.memory_monitor,
                max_workers=max_workers
            )

            perf.add_context(
                max_workers=self.coordinator.max_workers,
                cache_size=self.cache_manager.cache.maxsize,
                correlation_id=correlation_id,
            )

            logger.info(
                "Analysis engine initialized",
                extra={
                    "max_workers": self.coordinator.max_workers,
                    "cache_size": self.cache_manager.cache.maxsize,
                    "correlation_id": correlation_id,
                },
            )

    # Public API methods - delegate to coordinator
    def analyze_pr(
        self, pr_data: dict[str, Any], diff: str | None = None, use_cache: bool = True
    ) -> dict[str, Any]:
        """Analyze a single PR."""
        return self.coordinator.analyze_pr(pr_data, diff, use_cache)

    def analyze_commit(
        self, commit_data: dict[str, Any], diff: str | None = None, use_cache: bool = True
    ) -> dict[str, Any]:
        """Analyze a single commit."""
        return self.coordinator.analyze_commit(commit_data, diff, use_cache)

    def batch_analyze_prs(
        self,
        pr_list: list[dict[str, Any]],
        progress_callback: callable = None,
        use_cache: bool = True,
    ) -> list[dict[str, Any]]:
        """Analyze multiple PRs with parallel processing."""
        return self.coordinator.batch_analyze_prs(pr_list, progress_callback, use_cache)

    def batch_analyze_commits(
        self,
        commit_list: list[dict[str, Any]],
        progress_callback: callable = None,
        use_cache: bool = True,
    ) -> list[dict[str, Any]]:
        """Analyze multiple commits with parallel processing."""
        # Delegate to coordinator for consistency
        results = []
        total = len(commit_list)
        completed = 0

        for commit in commit_list:
            try:
                result = self.coordinator.analyze_commit(commit, use_cache=use_cache)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing commit: {str(e)}")
                results.append({
                    "source_type": "Commit",
                    "source_id": commit.get("sha", "unknown"),
                    "error": f"Processing error: {str(e)}",
                    "work_type": "Unknown",
                    "complexity_score": 0,
                    "risk_score": 0,
                    "clarity_score": 0,
                    "impact_score": 0,
                    "ai_assisted": False,
                    "ai_tool_type": None,
                    "linear_ticket_id": None,
                    "has_linear_ticket": False,
                    "process_compliant": False,
                    "api_tokens_used": 0,
                    "analysis_time": 0,
                })

            completed += 1
            if progress_callback:
                progress_callback(completed, total)

        return results

    def analyze(self, context: PreparedContext, use_cache: bool = True) -> dict[str, Any]:
        """Analyze prepared context (works for both PRs and commits)."""
        # Check cache
        if use_cache:
            cached_result = self.cache_manager.get(context.cache_key)
            if cached_result is not None:
                logger.debug(f"Using cached result for context {context.cache_key}")
                return cached_result

        # Create prompt
        prompt = self.prompt_engineer.create_analysis_prompt(
            title=context.title,
            description=context.description,
            diff=context.diff,
            file_changes=context.file_changes,
        )

        # Get analysis
        try:
            response = self.claude_client.analyze_code_change(prompt)
            result = self.prompt_engineer.parse_response(response["content"])

            # Cache result
            if use_cache:
                self.cache_manager.set(context.cache_key, result)

            logger.debug(f"Analysis complete for context {context.cache_key}")
            return result

        except Exception as e:
            logger.error(f"Analysis failed for context {context.cache_key}: {e}")
            return {
                "work_type": "Unknown",
                "complexity_score": 1,
                "risk_score": 1,
                "clarity_score": 5,
                "analysis_summary": f"Analysis failed: {str(e)}",
            }

    # Resource management methods
    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive analysis statistics."""
        claude_stats = self.claude_client.get_usage_stats()
        cache_stats = self.cache_manager.get_stats()
        memory_stats = self.memory_monitor.get_memory_stats()
        
        return {
            **claude_stats,
            **cache_stats,
            "memory_stats": memory_stats,
            "max_workers": self.coordinator.max_workers,
            "estimated_cost": self.claude_client.estimate_cost(),
        }

    def clear_cache(self) -> None:
        """Clear all caches."""
        claude_cache_size = len(self.claude_client.cache)
        results_cache_size = self.cache_manager.clear()

        self.claude_client.clear_cache()

        logger.info(
            "All caches cleared",
            extra={
                "event": "caches_cleared",
                "claude_cache_size": claude_cache_size,
                "results_cache_size": results_cache_size,
                "component": "analysis_engine",
            },
        )

    def check_memory_usage(self) -> dict[str, Any]:
        """Check current memory usage."""
        return self.memory_monitor.check_memory_usage()

    def force_cleanup(self, reason: str = "manual") -> None:
        """Force cleanup of resources."""
        self.memory_monitor.force_cleanup(reason)
