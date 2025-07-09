"""Application constants and configuration values.

This module provides access to configuration values that can be overridden
by environment variables through the Pydantic settings system.
"""

import threading
from typing import Final

from .schemas import load_settings

# Thread-safe singleton for settings
_settings_lock = threading.Lock()
_settings = None


def get_settings():
    """Get cached settings instance (thread-safe)."""
    global _settings
    if _settings is None:
        with _settings_lock:
            # Double-checked locking pattern
            if _settings is None:
                _settings = load_settings()
    return _settings


class ProcessingLimits:
    """Processing limits and constraints (environment-configurable)."""

    @property
    def DIFF_LENGTH_LIMIT(self) -> int:
        return get_settings().processing_limits.diff_length_limit

    @property
    def DIFF_TRUNCATION_BUFFER(self) -> int:
        return get_settings().processing_limits.diff_truncation_buffer

    @property
    def CACHE_SIZE_DEFAULT(self) -> int:
        return get_settings().processing_limits.cache_size_default

    @property
    def CACHE_SIZE_MAX(self) -> int:
        return get_settings().processing_limits.cache_size_max

    @property
    def CACHE_TTL_SECONDS(self) -> int:
        return get_settings().processing_limits.cache_ttl_seconds

    @property
    def MAX_WORKERS_DEFAULT(self) -> int:
        return get_settings().processing_limits.max_workers_default

    @property
    def MAX_WORKERS_MAX(self) -> int:
        return get_settings().processing_limits.max_workers_max

    @property
    def THREAD_TIMEOUT_SECONDS(self) -> int:
        return get_settings().processing_limits.thread_timeout_seconds

    @property
    def MAX_FILE_SIZE_MB(self) -> int:
        return get_settings().processing_limits.max_file_size_mb

    @property
    def CSV_CHUNK_SIZE(self) -> int:
        return get_settings().processing_limits.csv_chunk_size

    @property
    def MAX_FILES_PER_BATCH(self) -> int:
        return get_settings().processing_limits.max_files_per_batch

    @property
    def MAX_MEMORY_MB(self) -> int:
        return get_settings().processing_limits.max_memory_mb

    @property
    def MEMORY_WARNING_THRESHOLD(self) -> float:
        return get_settings().processing_limits.memory_warning_threshold

    @property
    def API_RATE_LIMIT_REQUESTS_PER_MINUTE(self) -> int:
        return get_settings().processing_limits.api_rate_limit_requests_per_minute

    @property
    def API_TIMEOUT_SECONDS(self) -> int:
        return get_settings().processing_limits.api_timeout_seconds

    @property
    def API_RETRY_ATTEMPTS(self) -> int:
        return get_settings().processing_limits.api_retry_attempts

    @property
    def API_RETRY_DELAY_SECONDS(self) -> float:
        return get_settings().processing_limits.api_retry_delay_seconds


class ValidationLimits:
    """Input validation limits (environment-configurable)."""

    @property
    def PROMPT_INPUT_MAX_LENGTH(self) -> int:
        return get_settings().validation_limits.prompt_input_max_length

    @property
    def TITLE_MAX_LENGTH(self) -> int:
        return get_settings().validation_limits.title_max_length

    @property
    def DESCRIPTION_MAX_LENGTH(self) -> int:
        return get_settings().validation_limits.description_max_length

    @property
    def FILENAME_MAX_LENGTH(self) -> int:
        return get_settings().validation_limits.filename_max_length

    @property
    def EMAIL_MAX_LENGTH(self) -> int:
        return get_settings().validation_limits.email_max_length

    @property
    def SCORE_MIN(self) -> int:
        return get_settings().validation_limits.score_min

    @property
    def SCORE_MAX(self) -> int:
        return get_settings().validation_limits.score_max

    @property
    def PERCENTAGE_MIN(self) -> float:
        return get_settings().validation_limits.percentage_min

    @property
    def PERCENTAGE_MAX(self) -> float:
        return get_settings().validation_limits.percentage_max

    @property
    def GRAPHQL_QUERY_MAX_LENGTH(self) -> int:
        return get_settings().validation_limits.graphql_query_max_length

    @property
    def GRAPHQL_MAX_COMPLEXITY(self) -> int:
        return get_settings().validation_limits.graphql_max_complexity

    @property
    def GRAPHQL_MAX_DEPTH(self) -> int:
        return get_settings().validation_limits.graphql_max_depth

    @property
    def GRAPHQL_VARIABLE_MAX_LENGTH(self) -> int:
        return get_settings().validation_limits.graphql_variable_max_length


class Pricing:
    """API pricing information (environment-configurable)."""

    @property
    def CLAUDE_INPUT_PRICE_PER_1K(self) -> float:
        return get_settings().pricing.claude_input_price_per_1k

    @property
    def CLAUDE_OUTPUT_PRICE_PER_1K(self) -> float:
        return get_settings().pricing.claude_output_price_per_1k

    @property
    def DAILY_COST_WARNING_THRESHOLD(self) -> float:
        return get_settings().pricing.daily_cost_warning_threshold

    @property
    def MONTHLY_COST_LIMIT(self) -> float:
        return get_settings().pricing.monthly_cost_limit


class SecuritySettings:
    """Security configuration (environment-configurable)."""

    @property
    def API_KEY_MIN_LENGTH(self) -> int:
        return get_settings().security.api_key_min_length

    @property
    def API_KEY_MAX_LENGTH(self) -> int:
        return get_settings().security.api_key_max_length

    @property
    def KEY_ROTATION_DAYS(self) -> int:
        return get_settings().security.key_rotation_days

    @property
    def ENCRYPTION_KEY_LENGTH(self) -> int:
        return get_settings().security.encryption_key_length

    @property
    def PBKDF2_ITERATIONS(self) -> int:
        return get_settings().security.pbkdf2_iterations

    @property
    def SESSION_TIMEOUT_MINUTES(self) -> int:
        return get_settings().security.session_timeout_minutes

    @property
    def MAX_FAILED_ATTEMPTS(self) -> int:
        return get_settings().security.max_failed_attempts

    @property
    def ENCRYPTION_SALT(self) -> str:
        return get_settings().security.encryption_salt

    @property
    def ALLOWED_DIRECTORIES(self) -> list[str]:
        return get_settings().security.allowed_directories


class LoggingConfig:
    """Logging configuration (environment-configurable)."""

    @property
    def DEFAULT_LOG_LEVEL(self) -> str:
        level = get_settings().logging.default_log_level
        return level.value if hasattr(level, "value") else str(level)

    @property
    def DEBUG_LOG_LEVEL(self) -> str:
        level = get_settings().logging.debug_log_level
        return level.value if hasattr(level, "value") else str(level)

    @property
    def MAX_LOG_FILE_SIZE_MB(self) -> int:
        return get_settings().logging.max_log_file_size_mb

    @property
    def MAX_LOG_FILES(self) -> int:
        return get_settings().logging.max_log_files

    @property
    def SENSITIVE_PATTERNS(self) -> list[str]:
        return get_settings().logging.sensitive_patterns


class FileExtensions:
    """Supported file extensions (static constants)."""

    CSV_EXTENSION: Final[str] = ".csv"
    JSON_EXTENSION: Final[str] = ".json"
    LOG_EXTENSION: Final[str] = ".log"
    CONFIG_EXTENSIONS: Final[list[str]] = [".json", ".yaml", ".yml", ".toml"]


class MetricsConfig:
    """Metrics and analysis configuration (environment-configurable)."""

    @property
    def COMPLEXITY_WEIGHT(self) -> float:
        return get_settings().metrics.complexity_weight

    @property
    def RISK_WEIGHT(self) -> float:
        return get_settings().metrics.risk_weight

    @property
    def CLARITY_WEIGHT(self) -> float:
        return get_settings().metrics.clarity_weight

    @property
    def PILOT_DAYS(self) -> int:
        return get_settings().metrics.pilot_days

    @property
    def DEFAULT_ANALYSIS_DAYS(self) -> int:
        return get_settings().metrics.default_analysis_days

    @property
    def MAX_ANALYSIS_DAYS(self) -> int:
        return get_settings().metrics.max_analysis_days

    @property
    def HIGH_IMPACT_THRESHOLD(self) -> float:
        return get_settings().metrics.high_impact_threshold

    @property
    def HIGH_COMPLEXITY_THRESHOLD(self) -> int:
        return get_settings().metrics.high_complexity_threshold

    @property
    def HIGH_RISK_THRESHOLD(self) -> int:
        return get_settings().metrics.high_risk_threshold

    @property
    def DEVELOPER_METRICS_WINDOW_WEEKS(self) -> int:
        return get_settings().metrics.developer_metrics_window_weeks

    @property
    def MIN_COMMITS_FOR_ANALYSIS(self) -> int:
        return get_settings().metrics.min_commits_for_analysis


# Create singleton instances for backward compatibility
processing_limits = ProcessingLimits()
validation_limits = ValidationLimits()
pricing = Pricing()
security_settings = SecuritySettings()
logging_config = LoggingConfig()
metrics_config = MetricsConfig()
