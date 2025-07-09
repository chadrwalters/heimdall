"""Main AI Analysis Engine combining all components."""

import logging
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
from typing import Any

import psutil
from cachetools import TTLCache

from ..config.schemas import load_settings
from ..exceptions import (
    AnalysisError,
    APIError,
)
from .claude_client import ClaudeClient
from .context_preparer import ContextPreparer, PreparedContext
from .prompt_engineer import PromptEngineer

logger = logging.getLogger(__name__)


class AnalysisEngine:
    """Main engine for AI-powered code analysis."""

    def __init__(self, api_key: str | None = None, max_workers: int = None, cache_size: int = None):
        """Initialize the analysis engine."""
        self.claude_client = ClaudeClient(api_key=api_key)
        self.prompt_engineer = PromptEngineer()
        self.context_preparer = ContextPreparer()
        
        # Load settings
        settings = load_settings()
        
        # Set safe defaults with limits
        self.max_workers = min(
            max_workers or settings.processing_limits.max_workers_default, 
            settings.processing_limits.max_workers_max
        )

        # Use TTL cache with size limit
        cache_size = min(
            cache_size or settings.processing_limits.cache_size_default, 
            settings.processing_limits.cache_size_max
        )
        self.results_cache = TTLCache(maxsize=cache_size, ttl=settings.processing_limits.cache_ttl_seconds)

        # Memory monitoring
        self._memory_warning_logged = False

    def _check_memory_usage(self) -> None:
        """Monitor memory usage and warn if approaching limits."""
        try:
            memory_info = psutil.virtual_memory()
            memory_usage_mb = memory_info.used / (1024 * 1024)
            memory_percent = memory_info.percent / 100

            settings = load_settings()
            if (
                memory_usage_mb
                > settings.processing_limits.max_memory_mb * settings.processing_limits.memory_warning_threshold
                and not self._memory_warning_logged
            ):
                logger.warning(
                    f"High memory usage: {memory_usage_mb:.1f}MB ({memory_percent:.1%}). "
                    f"Consider reducing batch size or cache size."
                )
                self._memory_warning_logged = True

                # Clear cache if memory is very high
                if memory_percent > 0.9:
                    logger.warning("Memory critically high - clearing cache")
                    self.clear_cache()

        except (OSError, psutil.Error) as e:
            logger.debug(f"Memory monitoring failed: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error in memory monitoring: {e}")

    def _get_memory_stats(self) -> dict[str, Any]:
        """Get current memory statistics."""
        try:
            memory_info = psutil.virtual_memory()
            return {
                "total_mb": memory_info.total / (1024 * 1024),
                "used_mb": memory_info.used / (1024 * 1024),
                "available_mb": memory_info.available / (1024 * 1024),
                "percent_used": memory_info.percent,
                "cache_size": len(self.results_cache),
            }
        except (OSError, psutil.Error) as e:
            logger.debug(f"Failed to get memory stats: {e}")
            return {"error": "Unable to get memory stats"}
        except Exception as e:
            logger.warning(f"Unexpected error getting memory stats: {e}")
            return {"error": "Unable to get memory stats"}

    def analyze_pr(
        self, pr_data: dict[str, Any], diff: str | None = None, use_cache: bool = True
    ) -> dict[str, Any]:
        """Analyze a single PR."""
        # Prepare context
        context = self.context_preparer.prepare_pr_context(pr_data, diff)

        # Check cache
        if use_cache and context.cache_key in self.results_cache:
            logger.debug(f"Using cached result for PR {context.metadata.get('pr_id')}")
            return self.results_cache[context.cache_key]

        # Create prompt
        prompt = self.prompt_engineer.create_analysis_prompt(
            title=context.title,
            description=context.description,
            diff=context.diff,
            file_changes=context.file_changes,
        )

        # Get AI analysis
        try:
            response = self.claude_client.analyze_code_change(
                prompt=prompt,
                system_prompt=self.prompt_engineer.SYSTEM_PROMPT,
                cache_key=context.cache_key if use_cache else None,
            )

            # Parse response
            analysis = self.prompt_engineer.parse_response(response["content"])

            # Calculate impact score
            impact_score = self.prompt_engineer.calculate_impact_score(
                analysis.complexity_score, analysis.risk_score, analysis.clarity_score,
                lines_changed=context.metadata.get('additions', 0) + context.metadata.get('deletions', 0),
                files_changed=context.metadata.get('changed_files', 0)
            )

            # Detect AI assistance
            ai_assisted, ai_tool = self.context_preparer.detect_ai_assistance(pr_data)

            # Extract Linear ticket
            linear_ticket = self.context_preparer.extract_linear_ticket_id(pr_data)

            # Build result
            result = {
                "source_type": "PR",
                "source_id": context.metadata.get("pr_id"),
                "source_url": context.metadata.get("url"),
                "repository": pr_data.get("base", {}).get("repo", {}).get("name", "unknown"),
                "date": context.metadata.get("created_at"),
                "author": context.metadata.get("author"),
                "context_level": "High",
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
                "api_tokens_used": response["usage"]["input_tokens"]
                + response["usage"]["output_tokens"],
                "analysis_time": response["response_time"],
            }

            # Cache result
            if use_cache:
                self.results_cache[context.cache_key] = result

            return result

        except (APIError, AnalysisError, Exception) as e:
            logger.error(f"Error analyzing PR {context.metadata.get('pr_id')}: {str(e)}")
            # Try to extract Linear ticket even on error
            try:
                linear_ticket = self.context_preparer.extract_linear_ticket_id(pr_data)
            except Exception:
                linear_ticket = None

            return {
                "source_type": "PR",
                "source_id": context.metadata.get("pr_id"),
                "source_url": context.metadata.get("url"),
                "repository": pr_data.get("base", {}).get("repo", {}).get("name", "unknown"),
                "date": context.metadata.get("created_at"),
                "author": context.metadata.get("author"),
                "context_level": "High",
                "work_type": "Unknown",
                "complexity_score": 5,
                "risk_score": 5,
                "clarity_score": 5,
                "impact_score": 5.0,
                "analysis_summary": f"Error during analysis: {str(e)}",
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

    def analyze_commit(
        self, commit_data: dict[str, Any], diff: str | None = None, use_cache: bool = True
    ) -> dict[str, Any]:
        """Analyze a single commit."""
        # Prepare context
        context = self.context_preparer.prepare_commit_context(commit_data, diff)

        # Check cache
        if use_cache and context.cache_key in self.results_cache:
            logger.debug(f"Using cached result for commit {context.metadata.get('commit_sha')}")
            return self.results_cache[context.cache_key]

        # Create prompt
        prompt = self.prompt_engineer.create_analysis_prompt(
            title=context.title,
            description=context.description,
            diff=context.diff,
            file_changes=context.file_changes,
        )

        # Get AI analysis
        try:
            response = self.claude_client.analyze_code_change(
                prompt=prompt,
                system_prompt=self.prompt_engineer.SYSTEM_PROMPT,
                cache_key=context.cache_key if use_cache else None,
            )

            # Parse response
            analysis = self.prompt_engineer.parse_response(response["content"])

            # Calculate impact score
            impact_score = self.prompt_engineer.calculate_impact_score(
                analysis.complexity_score, analysis.risk_score, analysis.clarity_score,
                lines_changed=context.metadata.get('additions', 0) + context.metadata.get('deletions', 0),
                files_changed=len(context.file_changes)
            )

            # Detect AI assistance
            ai_assisted, ai_tool = self.context_preparer.detect_ai_assistance(commit_data)

            # Extract Linear ticket
            linear_ticket = self.context_preparer.extract_linear_ticket_id(commit_data)

            # Build result
            result = {
                "source_type": "Commit",
                "source_id": context.metadata.get("commit_sha"),
                "source_url": context.metadata.get("url"),
                "repository": commit_data.get("repository", {}).get("name", "unknown"),
                "date": context.metadata.get("committed_at"),
                "author": context.metadata.get("author"),
                "context_level": "Low",
                "work_type": analysis.work_type,
                "complexity_score": analysis.complexity_score,
                "risk_score": analysis.risk_score,
                "clarity_score": analysis.clarity_score,
                "impact_score": impact_score,
                "analysis_summary": analysis.analysis_summary,
                "lines_added": context.metadata.get("additions", 0),
                "lines_deleted": context.metadata.get("deletions", 0),
                "files_changed": len(context.file_changes),
                "ai_assisted": ai_assisted,
                "ai_tool_type": ai_tool,
                "linear_ticket_id": linear_ticket,
                "has_linear_ticket": linear_ticket is not None,
                "process_compliant": False,  # Commits are not process compliant
                "api_tokens_used": response["usage"]["input_tokens"]
                + response["usage"]["output_tokens"],
                "analysis_time": response["response_time"],
            }

            # Cache result
            if use_cache:
                self.results_cache[context.cache_key] = result

            return result

        except (APIError, AnalysisError) as e:
            logger.error(f"Error analyzing commit {context.metadata.get('commit_sha')}: {str(e)}")
            raise AnalysisError(f"Commit analysis failed: {str(e)}") from e
        except Exception as e:
            logger.error(
                f"Unexpected error analyzing commit {context.metadata.get('commit_sha')}: {str(e)}"
            )
            raise AnalysisError(f"Unexpected commit analysis error: {str(e)}") from e

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
        self._check_memory_usage()

        # Limit batch size to prevent memory issues
        settings = load_settings()
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
                    settings = load_settings()
                    result = future.result(timeout=settings.processing_limits.thread_timeout_seconds)
                    results.append(result)
                except TimeoutError:
                    logger.error(f"Timeout processing PR {pr.get('id', 'unknown')}")
                    results.append(self._create_error_result(pr, "Processing timeout"))
                except (APIError, AnalysisError) as e:
                    logger.error(
                        f"Analysis error processing PR {pr.get('id', 'unknown')}: {str(e)}"
                    )
                    results.append(self._create_error_result(pr, f"Analysis error: {str(e)}"))
                except Exception as e:
                    logger.error(
                        f"Unexpected error processing PR {pr.get('id', 'unknown')}: {str(e)}"
                    )
                    results.append(self._create_error_result(pr, f"Unexpected error: {str(e)}"))

                completed += 1
                if progress_callback:
                    progress_callback(completed, total)

                # Check memory periodically
                if completed % 10 == 0:
                    self._check_memory_usage()

                # Small delay to avoid rate limiting
                time.sleep(0.1)

        return results

    def _create_error_result(self, item: dict[str, Any], error_msg: str) -> dict[str, Any]:
        """Create a standardized error result."""
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

    def batch_analyze_commits(
        self,
        commit_list: list[dict[str, Any]],
        progress_callback: Callable[[int, int], None] | None = None,
        use_cache: bool = True,
    ) -> list[dict[str, Any]]:
        """Analyze multiple commits with parallel processing."""
        results = []
        total = len(commit_list)
        completed = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_commit = {
                executor.submit(self.analyze_commit, commit, use_cache=use_cache): commit
                for commit in commit_list
            }

            # Process completed tasks
            for future in as_completed(future_to_commit):
                commit = future_to_commit[future]
                try:
                    result = future.result()
                    results.append(result)
                except (APIError, AnalysisError) as e:
                    logger.error(f"Analysis error processing commit: {str(e)}")
                    results.append(self._create_error_result(commit, f"Analysis error: {str(e)}"))
                except Exception as e:
                    logger.error(f"Unexpected error processing commit: {str(e)}")
                    results.append(self._create_error_result(commit, f"Unexpected error: {str(e)}"))

                completed += 1
                if progress_callback:
                    progress_callback(completed, total)

                # Small delay to avoid rate limiting
                time.sleep(0.1)

        return results

    def get_stats(self) -> dict[str, Any]:
        """Get analysis statistics including memory usage."""
        stats = self.claude_client.get_usage_stats()
        stats["cache_hits"] = len(self.results_cache)
        stats["cache_maxsize"] = self.results_cache.maxsize
        stats["estimated_cost"] = self.claude_client.estimate_cost()
        stats["memory_stats"] = self._get_memory_stats()
        stats["max_workers"] = self.max_workers
        return stats

    def analyze(self, context: PreparedContext, use_cache: bool = True) -> dict[str, Any]:
        """Analyze prepared context (works for both PRs and commits)."""
        # Check cache
        if use_cache and context.cache_key in self.results_cache:
            logger.debug(f"Using cached result for context {context.cache_key}")
            return self.results_cache[context.cache_key]

        # Create prompt
        prompt = self.prompt_engineer.create_analysis_prompt(
            title=context.title,
            description=context.description,
            diff=context.diff,
            file_changes=context.file_changes,
        )

        # Get analysis
        try:
            response = self.claude_client.analyze(prompt)
            result = self.prompt_engineer.parse_response(response["response"])

            # Cache result
            if use_cache:
                self.results_cache[context.cache_key] = result

            logger.debug(f"Analysis complete for context {context.cache_key}")
            return result

        except (APIError, AnalysisError) as e:
            logger.error(f"Analysis failed for context {context.cache_key}: {e}")
            return {
                "work_type": "Unknown",
                "complexity_score": 1,
                "risk_score": 1,
                "clarity_score": 5,
                "analysis_summary": f"Analysis failed: {str(e)}",
            }
        except Exception as e:
            logger.error(f"Unexpected analysis error for context {context.cache_key}: {e}")
            return {
                "work_type": "Unknown",
                "complexity_score": 1,
                "risk_score": 1,
                "clarity_score": 5,
                "analysis_summary": f"Unexpected analysis error: {str(e)}",
            }

    def clear_cache(self):
        """Clear all caches."""
        self.claude_client.clear_cache()
        self.results_cache.clear()
        logger.info("All caches cleared")
