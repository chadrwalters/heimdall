"""Claude API client for AI-powered code analysis."""

import time
from typing import Any

import backoff
from anthropic import Anthropic

from ..api.rate_limiter import APIRateLimiterFactory
from ..config.constants import get_settings
from ..logging import (
    LogContext,
    get_structured_logger,
    log_api_call,
    log_error,
    log_performance,
    set_correlation_id,
)
from ..resilience.circuit_breaker import CircuitBreakerConfig, get_circuit_breaker
from ..security.key_manager import EnvironmentKeyManager, KeySecurityError, SecureKeyManager

logger = get_structured_logger(__name__, LogContext(component="claude_client"))


class ClaudeClient:
    """Client for interacting with Anthropic's Claude API."""

    MODEL_ID = "claude-sonnet-4-20250514"
    MAX_RETRIES = 3
    DEFAULT_MAX_TOKENS = 4096
    DEFAULT_TEMPERATURE = 0.3

    def __init__(self, api_key: str | None = None):
        """Initialize the Claude client with API key."""
        correlation_id = set_correlation_id()

        with log_performance(logger, "claude_client_init"):
            self.secure_manager = SecureKeyManager()
            self.env_manager = EnvironmentKeyManager(self.secure_manager)
            self.rate_limiter = APIRateLimiterFactory.create_anthropic_limiter()

            # Initialize circuit breaker
            circuit_config = CircuitBreakerConfig(
                failure_threshold=5,
                recovery_timeout=60.0,
                success_threshold=3,
                timeout=30.0,
                expected_exceptions=(Exception,),
                ignored_exceptions=(KeyboardInterrupt, SystemExit),
            )
            self.circuit_breaker = get_circuit_breaker("claude-api", circuit_config)

            logger.info(
                "Claude client initialized",
                extra={
                    "correlation_id": correlation_id,
                    "circuit_breaker": "claude-api",
                    "model": self.MODEL_ID,
                },
            )

            try:
                if api_key:
                    # Validate provided key
                    if not self.secure_manager.validate_api_key(api_key, "anthropic"):
                        logger.warning("Provided API key failed validation checks")
                    self.api_key = api_key
                else:
                    # Get key from environment with validation
                    self.api_key = self.env_manager.get_api_key(
                        "ANTHROPIC_API_KEY", "anthropic", required=True
                    )
            except KeySecurityError as e:
                log_error(logger, e, "api_key_initialization")
                raise ValueError(f"Failed to initialize Claude client: {e}")

            self.client = Anthropic(api_key=self.api_key)
            self.total_tokens_used = 0
            self.total_api_calls = 0
            self.cache = {}

    def analyze_code_change(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        cache_key: str | None = None,
    ) -> dict[str, Any]:
        """Send a prompt to Claude for code analysis with circuit breaker protection."""
        correlation_id = set_correlation_id()

        with log_performance(logger, "analyze_code_change") as perf:
            # Check cache if key provided
            if cache_key and cache_key in self.cache:
                logger.debug(
                    "Cache hit for analysis request",
                    extra={"cache_key": cache_key, "correlation_id": correlation_id},
                )
                return self.cache[cache_key]

            perf.add_context(
                model=self.MODEL_ID,
                max_tokens=max_tokens,
                temperature=temperature,
                has_cache_key=cache_key is not None,
                prompt_length=len(prompt),
            )

            # Use circuit breaker to protect API call
            return self.circuit_breaker.call(
                self._make_api_call,
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                cache_key=cache_key,
            )

    @backoff.on_exception(
        backoff.expo, Exception, max_tries=MAX_RETRIES, jitter=backoff.full_jitter
    )
    def _make_api_call(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        cache_key: str | None = None,
    ) -> dict[str, Any]:
        """Make the actual API call with retry logic."""
        try:
            messages = [{"role": "user", "content": prompt}]

            kwargs = {
                "model": self.MODEL_ID,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            if system_prompt:
                kwargs["system"] = system_prompt

            # Apply adaptive rate limiting
            self.rate_limiter.wait_if_needed()

            start_time = time.time()

            log_api_call(
                logger,
                method="POST",
                url="https://api.anthropic.com/v1/messages",
                model=self.MODEL_ID,
                max_tokens=max_tokens,
                temperature=temperature,
                prompt_length=len(prompt),
                has_system_prompt=system_prompt is not None,
            )

            response = self.client.messages.create(**kwargs)
            elapsed_time = time.time() - start_time

            self.total_api_calls += 1

            # Record successful API call for rate limiting
            self.rate_limiter.record_success()

            # Extract the response content
            if hasattr(response, "content") and response.content:
                content = response.content[0].text if response.content else ""
            else:
                content = ""

            result = {
                "content": content,
                "model": self.MODEL_ID,
                "usage": {
                    "input_tokens": response.usage.input_tokens
                    if hasattr(response, "usage")
                    else 0,
                    "output_tokens": response.usage.output_tokens
                    if hasattr(response, "usage")
                    else 0,
                },
                "response_time": elapsed_time,
            }

            # Update token usage
            if hasattr(response, "usage"):
                self.total_tokens_used += response.usage.input_tokens + response.usage.output_tokens

            # Cache the result if key provided
            if cache_key:
                self.cache[cache_key] = result

            log_api_call(
                logger,
                method="POST",
                url="https://api.anthropic.com/v1/messages",
                status_code=200,
                duration_ms=elapsed_time * 1000,
                input_tokens=result["usage"]["input_tokens"],
                output_tokens=result["usage"]["output_tokens"],
                total_tokens=result["usage"]["input_tokens"] + result["usage"]["output_tokens"],
            )

            return result

        except Exception as e:
            # Record failed API call for rate limiting
            is_rate_limit = "rate limit" in str(e).lower() or "429" in str(e)
            self.rate_limiter.record_failure(is_rate_limit_error=is_rate_limit)

            log_error(
                logger,
                e,
                "claude_api_call",
                model=self.MODEL_ID,
                prompt_length=len(prompt),
                max_tokens=max_tokens,
            )
            raise

    def batch_analyze(
        self,
        prompts: list[dict[str, Any]],
        system_prompt: str | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        progress_callback: callable = None,
    ) -> list[dict[str, Any]]:
        """Analyze multiple prompts in batch with progress tracking."""
        results = []
        total = len(prompts)

        for idx, prompt_data in enumerate(prompts):
            # Extract prompt and cache key
            if isinstance(prompt_data, dict):
                prompt = prompt_data.get("prompt", "")
                cache_key = prompt_data.get("cache_key", None)
                metadata = prompt_data.get("metadata", {})
            else:
                prompt = str(prompt_data)
                cache_key = None
                metadata = {}

            try:
                result = self.analyze_code_change(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    cache_key=cache_key,
                )
                result["metadata"] = metadata
                results.append(result)

            except Exception as e:
                logger.error(f"Error analyzing item {idx + 1}/{total}: {str(e)}")
                results.append({"error": str(e), "metadata": metadata})

            # Call progress callback if provided
            if progress_callback:
                progress_callback(idx + 1, total)

            # Small delay to avoid rate limiting
            if idx < total - 1:
                time.sleep(0.1)

        return results

    def get_usage_stats(self) -> dict[str, Any]:
        """Get usage statistics for this client session."""
        stats = {
            "total_api_calls": self.total_api_calls,
            "total_tokens_used": self.total_tokens_used,
            "cache_size": len(self.cache),
            "model": self.MODEL_ID,
        }

        # Add circuit breaker stats
        circuit_stats = self.circuit_breaker.get_stats()
        stats["circuit_breaker"] = circuit_stats

        return stats

    def clear_cache(self):
        """Clear the response cache."""
        cache_size = len(self.cache)
        self.cache.clear()
        logger.info(
            "Cache cleared",
            extra={
                "event": "cache_cleared",
                "previous_size": cache_size,
                "component": "claude_client",
            },
        )

    def get_circuit_breaker_stats(self) -> dict[str, Any]:
        """Get circuit breaker statistics."""
        return self.circuit_breaker.get_stats()

    def reset_circuit_breaker(self):
        """Manually reset the circuit breaker."""
        self.circuit_breaker.reset()
        logger.info("Circuit breaker reset")

    def estimate_cost(self, input_tokens: int = None, output_tokens: int = None) -> float:
        """Estimate cost based on token usage."""
        settings = get_settings()

        if input_tokens is None:
            input_tokens = self.total_tokens_used // 2  # Rough estimate
        if output_tokens is None:
            output_tokens = self.total_tokens_used // 2

        input_cost = (input_tokens / 1000) * settings.pricing.claude_input_price_per_1k
        output_cost = (output_tokens / 1000) * settings.pricing.claude_output_price_per_1k

        return input_cost + output_cost
