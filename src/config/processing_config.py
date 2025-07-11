"""Processing limits and validation configuration schemas."""


from pydantic import Field
from pydantic_settings import BaseSettings


class ProcessingLimitsConfig(BaseSettings):
    """Processing limits and constraints."""

    model_config = {"env_prefix": "NS_PROCESSING_"}

    # Diff processing limits
    diff_length_limit: int = Field(default=50000, ge=1000, le=1000000, env="NS_DIFF_LENGTH_LIMIT")
    diff_truncation_buffer: int = Field(default=1000, ge=100, le=10000, env="NS_DIFF_TRUNCATION_BUFFER")

    # Cache configuration
    cache_size_default: int = Field(default=1000, ge=100, le=10000, env="NS_CACHE_SIZE_DEFAULT")
    cache_size_max: int = Field(default=5000, ge=500, le=50000, env="NS_CACHE_SIZE_MAX")
    cache_ttl_seconds: int = Field(default=3600, ge=300, le=86400, env="NS_CACHE_TTL_SECONDS")

    # Threading and workers
    max_workers_default: int = Field(default=5, ge=1, le=20, env="NS_MAX_WORKERS_DEFAULT")
    max_workers_max: int = Field(default=20, ge=5, le=100, env="NS_MAX_WORKERS_MAX")
    thread_timeout_seconds: int = Field(default=300, ge=30, le=3600, env="NS_THREAD_TIMEOUT_SECONDS")

    # File processing
    max_file_size_mb: int = Field(default=100, ge=1, le=1000, env="NS_MAX_FILE_SIZE_MB")
    csv_chunk_size: int = Field(default=10000, ge=1000, le=100000, env="NS_CSV_CHUNK_SIZE")
    max_files_per_batch: int = Field(default=1000, ge=10, le=10000, env="NS_MAX_FILES_PER_BATCH")

    # Memory management
    max_memory_mb: int = Field(default=4096, ge=512, le=32768, env="NS_MAX_MEMORY_MB")
    memory_warning_threshold: float = Field(default=0.8, ge=0.5, le=0.95, env="NS_MEMORY_WARNING_THRESHOLD")

    # API limits
    api_rate_limit_requests_per_minute: int = Field(default=100, ge=10, le=1000, env="NS_API_RATE_LIMIT_RPM")
    api_timeout_seconds: int = Field(default=30, ge=5, le=300, env="NS_API_TIMEOUT_SECONDS")
    api_retry_attempts: int = Field(default=3, ge=1, le=10, env="NS_API_RETRY_ATTEMPTS")
    api_retry_delay_seconds: float = Field(default=1.0, ge=0.1, le=60.0, env="NS_API_RETRY_DELAY_SECONDS")


class ValidationLimitsConfig(BaseSettings):
    """Input validation limits."""

    model_config = {"env_prefix": "NS_VALIDATION_"}

    # Input length limits
    prompt_input_max_length: int = Field(default=100000, ge=1000, le=1000000, env="NS_PROMPT_INPUT_MAX_LENGTH")
    title_max_length: int = Field(default=500, ge=10, le=1000, env="NS_TITLE_MAX_LENGTH")
    description_max_length: int = Field(default=10000, ge=100, le=50000, env="NS_DESCRIPTION_MAX_LENGTH")
    filename_max_length: int = Field(default=255, ge=10, le=1000, env="NS_FILENAME_MAX_LENGTH")
    email_max_length: int = Field(default=320, ge=5, le=500, env="NS_EMAIL_MAX_LENGTH")

    # Score validation
    score_min: int = Field(default=1, ge=0, le=5, env="NS_SCORE_MIN")
    score_max: int = Field(default=10, ge=5, le=20, env="NS_SCORE_MAX")
    percentage_min: float = Field(default=0.0, ge=0.0, le=0.5, env="NS_PERCENTAGE_MIN")
    percentage_max: float = Field(default=100.0, ge=50.0, le=100.0, env="NS_PERCENTAGE_MAX")

    # GraphQL validation
    graphql_query_max_length: int = Field(default=10000, ge=100, le=100000, env="NS_GRAPHQL_QUERY_MAX_LENGTH")
    graphql_max_complexity: int = Field(default=1000, ge=10, le=10000, env="NS_GRAPHQL_MAX_COMPLEXITY")
    graphql_max_depth: int = Field(default=15, ge=3, le=50, env="NS_GRAPHQL_MAX_DEPTH")
    graphql_variable_max_length: int = Field(default=1000, ge=10, le=10000, env="NS_GRAPHQL_VARIABLE_MAX_LENGTH")


class PricingConfig(BaseSettings):
    """API pricing configuration."""

    model_config = {"env_prefix": "NS_PRICING_"}

    # Claude API pricing (per 1K tokens)
    claude_input_price_per_1k: float = Field(default=0.003, ge=0.0, le=1.0, env="NS_CLAUDE_INPUT_PRICE_PER_1K")
    claude_output_price_per_1k: float = Field(default=0.015, ge=0.0, le=1.0, env="NS_CLAUDE_OUTPUT_PRICE_PER_1K")

    # Cost monitoring
    daily_cost_warning_threshold: float = Field(default=50.0, ge=1.0, le=1000.0, env="NS_DAILY_COST_WARNING_THRESHOLD")
    monthly_cost_limit: float = Field(default=1000.0, ge=10.0, le=10000.0, env="NS_MONTHLY_COST_LIMIT")
