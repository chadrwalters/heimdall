"""Claude API client for AI-powered code analysis."""

import logging
import time
from typing import Any

import backoff
from anthropic import Anthropic

from ..security.key_manager import EnvironmentKeyManager, KeySecurityError, SecureKeyManager

logger = logging.getLogger(__name__)


class ClaudeClient:
    """Client for interacting with Anthropic's Claude API."""

    MODEL_ID = "claude-sonnet-4-20250514"
    MAX_RETRIES = 3
    DEFAULT_MAX_TOKENS = 4096
    DEFAULT_TEMPERATURE = 0.3

    def __init__(self, api_key: str | None = None):
        """Initialize the Claude client with API key."""
        self.secure_manager = SecureKeyManager()
        self.env_manager = EnvironmentKeyManager(self.secure_manager)

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
            raise ValueError(f"Failed to initialize Claude client: {e}")

        self.client = Anthropic(api_key=self.api_key)
        self.total_tokens_used = 0
        self.total_api_calls = 0
        self.cache = {}

    @backoff.on_exception(
        backoff.expo, Exception, max_tries=MAX_RETRIES, jitter=backoff.full_jitter
    )
    def analyze_code_change(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        cache_key: str | None = None,
    ) -> dict[str, Any]:
        """Send a prompt to Claude for code analysis."""
        # Check cache if key provided
        if cache_key and cache_key in self.cache:
            logger.debug(f"Cache hit for key: {cache_key}")
            return self.cache[cache_key]

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

            start_time = time.time()
            response = self.client.messages.create(**kwargs)
            elapsed_time = time.time() - start_time

            self.total_api_calls += 1

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

            logger.info(
                f"API call completed in {elapsed_time:.2f}s, tokens used: {result['usage']}"
            )

            return result

        except Exception as e:
            logger.error(f"Error calling Claude API: {str(e)}")
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
        return {
            "total_api_calls": self.total_api_calls,
            "total_tokens_used": self.total_tokens_used,
            "cache_size": len(self.cache),
            "model": self.MODEL_ID,
        }

    def clear_cache(self):
        """Clear the response cache."""
        self.cache.clear()
        logger.info("Cache cleared")

    def estimate_cost(self, input_tokens: int = None, output_tokens: int = None) -> float:
        """Estimate cost based on token usage."""
        # Claude Sonnet 4 pricing (as of 2025)
        # These are example prices - update with actual pricing
        INPUT_PRICE_PER_1K = 0.003
        OUTPUT_PRICE_PER_1K = 0.015

        if input_tokens is None:
            input_tokens = self.total_tokens_used // 2  # Rough estimate
        if output_tokens is None:
            output_tokens = self.total_tokens_used // 2

        input_cost = (input_tokens / 1000) * INPUT_PRICE_PER_1K
        output_cost = (output_tokens / 1000) * OUTPUT_PRICE_PER_1K

        return input_cost + output_cost
