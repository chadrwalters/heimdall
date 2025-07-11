"""Analysis coordination and orchestration for the analysis engine."""

import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Any

from ..config.constants import get_settings
from ..exceptions import AnalysisError, APIError
from ..memory import memory_efficient_operation
from ..structured_logging import (
    LogContext,
    get_structured_logger,
    log_business_event,
    log_error,
    log_performance,
    set_correlation_id,
)
from .cache_manager import CacheManager
from .claude_client import ClaudeClient
from .context_preparer import ContextPreparer, PreparedContext
from .memory_monitor import MemoryMonitor
from .prompt_engineer import PromptEngineer

logger = get_structured_logger(__name__, LogContext(component="analysis_coordinator"))


class AnalysisCoordinator:
    """Coordinates analysis workflow with resource management and monitoring."""

    def __init__(
        self, 
        claude_client: ClaudeClient,
        prompt_engineer: PromptEngineer,
        context_preparer: ContextPreparer,
        cache_manager: CacheManager,
        memory_monitor: MemoryMonitor,
        max_workers: int = None
    ):
        """Initialize analysis coordinator with injected dependencies."""
        self.claude_client = claude_client
        self.prompt_engineer = prompt_engineer
        self.context_preparer = context_preparer
        self.cache_manager = cache_manager
        self.memory_monitor = memory_monitor
        
        # Load settings and configure workers
        settings = get_settings()
        self.max_workers = min(
            max_workers or settings.processing_limits.max_workers_default,
            settings.processing_limits.max_workers_max,
        )
        
        # Register cache cleanup with memory monitor
        self.memory_monitor.register_cleanup_callback(self.cache_manager.clear)
        
        logger.info(
            "Analysis coordinator initialized",
            extra={"max_workers": self.max_workers},
        )

    def analyze_pr(
        self, pr_data: dict[str, Any], diff: str | None = None, use_cache: bool = True
    ) -> dict[str, Any]:
        """Analyze a single PR with comprehensive error handling."""
        correlation_id = set_correlation_id()
        pr_id = pr_data.get("id", "unknown")

        with log_performance(logger, "analyze_pr") as perf:
            # Prepare context
            context = self.context_preparer.prepare_pr_context(pr_data, diff)

            perf.add_context(
                pr_id=pr_id,
                repository=pr_data.get("base", {}).get("repo", {}).get("name", "unknown"),
                author=pr_data.get("user", {}).get("login", "unknown"),
                correlation_id=correlation_id,
            )

            log_business_event(
                logger,
                event_type="pr_analysis_started",
                entity_type="pull_request",
                entity_id=pr_id,
                repository=pr_data.get("base", {}).get("repo", {}).get("name", "unknown"),
            )

        # Check cache
        if use_cache:
            cached_result = self.cache_manager.get(context.cache_key)
            if cached_result is not None:
                logger.debug(f"Using cached result for PR {context.metadata.get('pr_id')}")
                return cached_result

        # Perform analysis
        try:
            result = self._perform_analysis(context, pr_data, use_cache)
            
            log_business_event(
                logger,
                event_type="pr_analysis_completed",
                entity_type="pull_request",
                entity_id=pr_id,
                work_type=result.get("work_type"),
                complexity_score=result.get("complexity_score"),
                risk_score=result.get("risk_score"),
                impact_score=result.get("impact_score"),
                api_tokens_used=result.get("api_tokens_used", 0),
            )

            return result

        except (APIError, AnalysisError, Exception) as e:
            log_error(
                logger,
                e,
                "pr_analysis",
                pr_id=pr_id,
                repository=pr_data.get("base", {}).get("repo", {}).get("name", "unknown"),
            )

            return self._create_error_result(context, pr_data, str(e), "PR")

    def analyze_commit(
        self, commit_data: dict[str, Any], diff: str | None = None, use_cache: bool = True
    ) -> dict[str, Any]:
        """Analyze a single commit with comprehensive error handling."""
        # Prepare context
        context = self.context_preparer.prepare_commit_context(commit_data, diff)

        # Check cache
        if use_cache:
            cached_result = self.cache_manager.get(context.cache_key)
            if cached_result is not None:
                logger.debug(f"Using cached result for commit {context.metadata.get('commit_sha')}")
                return cached_result

        # Perform analysis
        try:
            result = self._perform_analysis(context, commit_data, use_cache)
            return result

        except (APIError, AnalysisError) as e:
            logger.error(f"Error analyzing commit {context.metadata.get('commit_sha')}: {str(e)}")
            raise AnalysisError(f"Commit analysis failed: {str(e)}") from e
        except Exception as e:
            logger.error(
                f"Unexpected error analyzing commit {context.metadata.get('commit_sha')}: {str(e)}"
            )
            raise AnalysisError(f"Unexpected commit analysis error: {str(e)}") from e

    def _perform_analysis(
        self, context: PreparedContext, source_data: dict[str, Any], use_cache: bool
    ) -> dict[str, Any]:
        """Perform the core analysis logic."""
        # Create prompt
        prompt = self.prompt_engineer.create_analysis_prompt(
            title=context.title,
            description=context.description,
            diff=context.diff,
            file_changes=context.file_changes,
        )

        # Get AI analysis
        response = self.claude_client.analyze_code_change(
            prompt=prompt,
            system_prompt=self.prompt_engineer.SYSTEM_PROMPT,
            cache_key=context.cache_key if use_cache else None,
        )

        # Parse response
        analysis = self.prompt_engineer.parse_response(response["content"])

        # Calculate impact score
        impact_score = self.prompt_engineer.calculate_impact_score(
            analysis.complexity_score,
            analysis.risk_score,
            analysis.clarity_score,
            lines_changed=context.metadata.get("additions", 0)
            + context.metadata.get("deletions", 0),
            files_changed=context.metadata.get("changed_files", 0),
        )

        # Detect AI assistance and Linear ticket
        ai_assisted, ai_tool = self.context_preparer.detect_ai_assistance(source_data)
        linear_ticket = self.context_preparer.extract_linear_ticket_id(source_data)

        # Build result
        result = {
            "source_type": context.metadata.get("source_type", "Unknown"),
            "source_id": context.metadata.get("pr_id") or context.metadata.get("commit_sha"),
            "source_url": context.metadata.get("url"),
            "repository": source_data.get("base", {}).get("repo", {}).get("name") or 
                         source_data.get("repository", {}).get("name", "unknown"),
            "date": context.metadata.get("created_at") or context.metadata.get("committed_at"),
            "author": context.metadata.get("author"),
            "context_level": "High" if "pr_id" in context.metadata else "Low",
            "work_type": analysis.work_type,
            "complexity_score": analysis.complexity_score,
            "risk_score": analysis.risk_score,
            "clarity_score": analysis.clarity_score,
            "impact_score": impact_score,
            "analysis_summary": analysis.analysis_summary,
            "lines_added": context.metadata.get("additions", 0),
            "lines_deleted": context.metadata.get("deletions", 0),
            "files_changed": context.metadata.get("changed_files", 0),
            "ai_assisted": ai_assisted,
            "ai_tool_type": ai_tool,
            "linear_ticket_id": linear_ticket,
            "has_linear_ticket": linear_ticket is not None,
            "process_compliant": linear_ticket is not None,
            "api_tokens_used": response["usage"]["input_tokens"] + response["usage"]["output_tokens"],
            "analysis_time": response["response_time"],
        }

        # Cache result
        if use_cache:
            self.cache_manager.set(context.cache_key, result)

        return result

    def _create_error_result(
        self, context: PreparedContext, source_data: dict[str, Any], error_msg: str, source_type: str
    ) -> dict[str, Any]:
        """Create a standardized error result."""
        # Try to extract Linear ticket even on error
        try:
            linear_ticket = self.context_preparer.extract_linear_ticket_id(source_data)
        except Exception:
            linear_ticket = None

        return {
            "source_type": source_type,
            "source_id": context.metadata.get("pr_id") or context.metadata.get("commit_sha"),
            "source_url": context.metadata.get("url"),
            "repository": source_data.get("base", {}).get("repo", {}).get("name") or 
                         source_data.get("repository", {}).get("name", "unknown"),
            "date": context.metadata.get("created_at") or context.metadata.get("committed_at"),
            "author": context.metadata.get("author"),
            "context_level": "High" if source_type == "PR" else "Low",
            "work_type": "Unknown",
            "complexity_score": 5,
            "risk_score": 5,
            "clarity_score": 5,
            "impact_score": 5.0,
            "analysis_summary": f"Error during analysis: {error_msg}",
            "lines_added": context.metadata.get("additions", 0),
            "lines_deleted": context.metadata.get("deletions", 0),
            "files_changed": len(context.file_changes),
            "ai_assisted": False,
            "ai_tool_type": None,
            "linear_ticket_id": linear_ticket,
            "has_linear_ticket": linear_ticket is not None,
            "process_compliant": linear_ticket is not None,
            "api_tokens_used": 0,
            "analysis_time": 0,
        }

    @memory_efficient_operation(required_mb=500.0)
    def batch_analyze_prs(
        self,
        pr_list: list[dict[str, Any]],
        progress_callback: Callable[[int, int], None] | None = None,
        use_cache: bool = True,
    ) -> list[dict[str, Any]]:
        """Analyze multiple PRs with parallel processing and resource monitoring."""
        results = []
        total = len(pr_list)
        completed = 0

        # Check memory before starting
        self.memory_monitor.check_memory_usage()

        # Limit batch size to prevent memory issues
        settings = get_settings()
        max_batch = min(len(pr_list), settings.processing_limits.max_files_per_batch)
        if len(pr_list) > max_batch:
            logger.warning(
                f"Limiting batch size from {len(pr_list)} to {max_batch} to prevent memory issues"
            )
            pr_list = pr_list[:max_batch]
            total = max_batch

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks and store futures in order
            futures = []
            for pr in pr_list:
                future = executor.submit(self.analyze_pr, pr, use_cache=use_cache)
                futures.append((future, pr))

            # Process futures in original order to maintain result order
            for future, pr in futures:
                try:
                    settings = get_settings()
                    result = future.result(
                        timeout=settings.processing_limits.thread_timeout_seconds
                    )
                    results.append(result)
                except TimeoutError as e:
                    log_error(logger, e, "pr_batch_timeout", pr_id=pr.get("id", "unknown"))
                    results.append(self._create_batch_error_result(pr, "Processing timeout"))
                except (APIError, AnalysisError) as e:
                    log_error(logger, e, "pr_batch_analysis_error", pr_id=pr.get("id", "unknown"))
                    results.append(self._create_batch_error_result(pr, f"Analysis error: {str(e)}"))
                except Exception as e:
                    log_error(logger, e, "pr_batch_unexpected_error", pr_id=pr.get("id", "unknown"))
                    results.append(self._create_batch_error_result(pr, f"Unexpected error: {str(e)}"))

                completed += 1
                if progress_callback:
                    progress_callback(completed, total)

                # Check memory periodically
                if completed % 10 == 0:
                    self.memory_monitor.check_memory_usage()

                # Small delay to avoid rate limiting
                time.sleep(0.1)

        return results

    def _create_batch_error_result(self, item: dict[str, Any], error_msg: str) -> dict[str, Any]:
        """Create a standardized error result for batch operations."""
        return {
            "source_type": item.get("type", "Unknown"),
            "source_id": item.get("id", item.get("sha", "unknown")),
            "error": error_msg,
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
        }
