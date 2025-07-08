"""Application constants and configuration values."""

from typing import Final


class ProcessingLimits:
    """Processing limits and constraints."""

    # Diff processing limits
    DIFF_LENGTH_LIMIT: Final[int] = 4000
    DIFF_TRUNCATION_BUFFER: Final[int] = 100

    # Cache settings
    CACHE_SIZE_DEFAULT: Final[int] = 1000
    CACHE_SIZE_MAX: Final[int] = 10000
    CACHE_TTL_SECONDS: Final[int] = 3600  # 1 hour

    # Threading and concurrency
    MAX_WORKERS_DEFAULT: Final[int] = 5
    MAX_WORKERS_MAX: Final[int] = 20
    THREAD_TIMEOUT_SECONDS: Final[int] = 300  # 5 minutes

    # File processing
    MAX_FILE_SIZE_MB: Final[int] = 100
    CSV_CHUNK_SIZE: Final[int] = 10000
    MAX_FILES_PER_BATCH: Final[int] = 1000

    # Memory limits
    MAX_MEMORY_MB: Final[int] = 2048  # 2GB
    MEMORY_WARNING_THRESHOLD: Final[float] = 0.8  # 80%

    # API rate limiting
    API_RATE_LIMIT_REQUESTS_PER_MINUTE: Final[int] = 60
    API_TIMEOUT_SECONDS: Final[int] = 30
    API_RETRY_ATTEMPTS: Final[int] = 3
    API_RETRY_DELAY_SECONDS: Final[float] = 1.0


class ValidationLimits:
    """Input validation limits."""

    # String length limits
    PROMPT_INPUT_MAX_LENGTH: Final[int] = 10000
    TITLE_MAX_LENGTH: Final[int] = 500
    DESCRIPTION_MAX_LENGTH: Final[int] = 2000
    FILENAME_MAX_LENGTH: Final[int] = 200
    EMAIL_MAX_LENGTH: Final[int] = 254

    # Numeric ranges
    SCORE_MIN: Final[int] = 1
    SCORE_MAX: Final[int] = 10
    PERCENTAGE_MIN: Final[float] = 0.0
    PERCENTAGE_MAX: Final[float] = 100.0

    # GraphQL limits
    GRAPHQL_QUERY_MAX_LENGTH: Final[int] = 10000
    GRAPHQL_MAX_COMPLEXITY: Final[int] = 100
    GRAPHQL_MAX_DEPTH: Final[int] = 10
    GRAPHQL_VARIABLE_MAX_LENGTH: Final[int] = 1000


class Pricing:
    """API pricing information (update regularly)."""

    # Claude Sonnet 4 pricing per 1K tokens (as of 2025)
    CLAUDE_INPUT_PRICE_PER_1K: Final[float] = 0.003
    CLAUDE_OUTPUT_PRICE_PER_1K: Final[float] = 0.015

    # Cost thresholds for monitoring
    DAILY_COST_WARNING_THRESHOLD: Final[float] = 100.0  # $100/day
    MONTHLY_COST_LIMIT: Final[float] = 1000.0  # $1000/month


class SecuritySettings:
    """Security configuration."""

    # Key management
    API_KEY_MIN_LENGTH: Final[int] = 10
    API_KEY_MAX_LENGTH: Final[int] = 500
    KEY_ROTATION_DAYS: Final[int] = 90

    # Encryption
    ENCRYPTION_KEY_LENGTH: Final[int] = 32
    PBKDF2_ITERATIONS: Final[int] = 100000

    # Session management
    SESSION_TIMEOUT_MINUTES: Final[int] = 60
    MAX_FAILED_ATTEMPTS: Final[int] = 5


class LoggingConfig:
    """Logging configuration."""

    # Log levels
    DEFAULT_LOG_LEVEL: Final[str] = "INFO"
    DEBUG_LOG_LEVEL: Final[str] = "DEBUG"

    # Log file settings
    MAX_LOG_FILE_SIZE_MB: Final[int] = 100
    MAX_LOG_FILES: Final[int] = 5

    # Sensitive data patterns to mask
    SENSITIVE_PATTERNS: Final[list[str]] = [
        r"sk-ant-[\w-]+",  # Anthropic keys
        r"ghp_[\w]+",  # GitHub tokens
        r"lin_api_[\w]+",  # Linear API keys
        r"Bearer\s+[\w.-]+",  # Bearer tokens
    ]


class FileExtensions:
    """Supported file extensions."""

    # Data files
    CSV_EXTENSION: Final[str] = ".csv"
    JSON_EXTENSION: Final[str] = ".json"

    # Log files
    LOG_EXTENSION: Final[str] = ".log"

    # Config files
    CONFIG_EXTENSIONS: Final[list[str]] = [".json", ".yaml", ".yml", ".toml"]


class MetricsConfig:
    """Metrics and analysis configuration."""

    # Impact score weights (must sum to 1.0)
    COMPLEXITY_WEIGHT: Final[float] = 0.4
    RISK_WEIGHT: Final[float] = 0.5
    CLARITY_WEIGHT: Final[float] = 0.1

    # Time periods
    PILOT_DAYS: Final[int] = 7
    DEFAULT_ANALYSIS_DAYS: Final[int] = 30
    MAX_ANALYSIS_DAYS: Final[int] = 365

    # Thresholds
    HIGH_IMPACT_THRESHOLD: Final[float] = 7.0
    HIGH_COMPLEXITY_THRESHOLD: Final[int] = 8
    HIGH_RISK_THRESHOLD: Final[int] = 8

    # Developer metrics
    DEVELOPER_METRICS_WINDOW_WEEKS: Final[int] = 4
    MIN_COMMITS_FOR_ANALYSIS: Final[int] = 5
