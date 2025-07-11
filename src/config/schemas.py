"""Pydantic configuration schemas for North Star Metrics."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings


class LogLevel(str, Enum):
    """Valid log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class APIKeyType(str, Enum):
    """Valid API key types."""

    ANTHROPIC = "anthropic"
    GITHUB = "github"
    LINEAR = "linear"
    GENERIC = "generic"


class AITool(str, Enum):
    """Valid AI tools."""

    CLAUDE = "claude"
    COPILOT = "copilot"
    CURSOR = "cursor"
    CODEIUM = "codeium"
    OTHER = "other"


class WorkType(str, Enum):
    """Valid work types for analysis."""

    NEW_FEATURE = "New Feature"
    BUG_FIX = "Bug Fix"
    REFACTORING = "Refactoring"
    DOCUMENTATION = "Documentation"
    PERFORMANCE = "Performance"
    SECURITY = "Security"
    INFRASTRUCTURE = "Infrastructure"
    TESTING = "Testing"


class BlastRadius(str, Enum):
    """Valid blast radius levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AIDevConfig(BaseModel):
    """Configuration for an AI developer."""

    username: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    ai_tool: AITool
    percentage: float = Field(..., ge=0.0, le=100.0)

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class AIDevsConfig(BaseModel):
    """Configuration for AI developers."""

    always_ai_developers: List[AIDevConfig] = Field(default_factory=list)

    @field_validator("always_ai_developers")
    @classmethod
    def validate_unique_developers(cls, v):
        """Ensure developers are unique by username and email."""
        usernames = set()
        emails = set()

        for dev in v:
            if dev.username.lower() in usernames:
                raise ValueError(f"Duplicate username: {dev.username}")
            if dev.email.lower() in emails:
                raise ValueError(f"Duplicate email: {dev.email}")

            usernames.add(dev.username.lower())
            emails.add(dev.email.lower())

        return v


class EmailAlertsConfig(BaseModel):
    """Email alerting configuration."""

    enabled: bool = Field(default=False)
    smtp_server: Optional[str] = None
    smtp_port: int = Field(default=587, ge=1, le=65535)
    username: Optional[str] = None
    password: Optional[str] = None
    recipients: List[str] = Field(default_factory=list)

    @field_validator("recipients")
    @classmethod
    def validate_email_recipients(cls, v):
        """Validate email addresses."""
        import re

        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        for email in v:
            if not re.match(email_pattern, email):
                raise ValueError(f"Invalid email address: {email}")
        return v


class SlackAlertsConfig(BaseModel):
    """Slack alerting configuration."""

    enabled: bool = Field(default=False)
    webhook_url: Optional[str] = None
    channel: Optional[str] = None

    @field_validator("webhook_url")
    @classmethod
    def validate_webhook_url(cls, v):
        """Validate Slack webhook URL."""
        if v and not v.startswith("https://hooks.slack.com/"):
            raise ValueError("Invalid Slack webhook URL")
        return v


class WebhookAlertsConfig(BaseModel):
    """Webhook alerting configuration."""

    enabled: bool = Field(default=False)
    url: Optional[str] = None
    auth_token: Optional[str] = None
    headers: Dict[str, str] = Field(default_factory=dict)

    @field_validator("url")
    @classmethod
    def validate_webhook_url(cls, v):
        """Validate webhook URL."""
        if v and not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("Webhook URL must start with http:// or https://")
        return v


class CircuitBreakerConfig(BaseModel):
    """Circuit breaker configuration."""

    enabled: bool = Field(default=True)
    failure_threshold: int = Field(default=5, ge=1, le=100)
    recovery_timeout_seconds: float = Field(default=60.0, ge=10.0, le=3600.0)
    success_threshold: int = Field(default=3, ge=1, le=20)
    timeout_seconds: float = Field(default=30.0, ge=5.0, le=300.0)
    window_size: int = Field(default=100, ge=10, le=1000)
    minimum_calls: int = Field(default=10, ge=5, le=100)
    max_recovery_timeout_seconds: float = Field(default=300.0, ge=60.0, le=3600.0)
    backoff_multiplier: float = Field(default=2.0, ge=1.1, le=5.0)

    @model_validator(mode="after")
    def validate_thresholds(self):
        """Ensure thresholds are logical."""
        if self.success_threshold > self.failure_threshold:
            raise ValueError("success_threshold should not exceed failure_threshold")
        if self.max_recovery_timeout_seconds < self.recovery_timeout_seconds:
            raise ValueError("max_recovery_timeout_seconds must be >= recovery_timeout_seconds")
        return self


class MonitoringConfig(BaseModel):
    """Monitoring and alerting configuration."""

    enabled: bool = Field(default=True)
    check_interval_minutes: int = Field(default=5, ge=1, le=60)
    max_alerts_per_hour: int = Field(default=10, ge=1, le=100)

    # Circuit breaker configurations
    circuit_breakers: Dict[str, CircuitBreakerConfig] = Field(
        default_factory=lambda: {
            "anthropic_api": CircuitBreakerConfig(
                failure_threshold=5,
                recovery_timeout_seconds=60.0,
                timeout_seconds=30.0
            ),
            "github_api": CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout_seconds=45.0,
                timeout_seconds=20.0
            ),
            "linear_api": CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout_seconds=45.0,
                timeout_seconds=15.0
            ),
        }
    )

    # Alert configurations
    email_alerts: EmailAlertsConfig = Field(default_factory=EmailAlertsConfig)
    slack_alerts: SlackAlertsConfig = Field(default_factory=SlackAlertsConfig)
    webhook_alerts: WebhookAlertsConfig = Field(default_factory=WebhookAlertsConfig)


class AnalysisState(BaseModel):
    """Analysis state configuration."""

    last_run_date: Optional[datetime] = None
    processed_pr_ids: List[str] = Field(default_factory=list)
    processed_commit_shas: List[str] = Field(default_factory=list)
    total_records_processed: int = Field(default=0, ge=0)

    @field_validator("processed_pr_ids", "processed_commit_shas")
    @classmethod
    def validate_unique_ids(cls, v):
        """Ensure IDs are unique."""
        return list(set(v))


class ProcessingLimitsConfig(BaseSettings):
    """Processing limits configuration."""

    # Diff processing limits
    diff_length_limit: int = Field(default=4000, ge=1000, le=50000, env="DIFF_LENGTH_LIMIT")
    diff_truncation_buffer: int = Field(default=100, ge=50, le=1000, env="DIFF_TRUNCATION_BUFFER")

    # Cache settings
    cache_size_default: int = Field(default=1000, ge=100, le=100000, env="CACHE_SIZE_DEFAULT")
    cache_size_max: int = Field(default=10000, ge=1000, le=100000, env="CACHE_SIZE_MAX")
    cache_ttl_seconds: int = Field(
        default=3600, ge=300, le=86400, env="CACHE_TTL_SECONDS"
    )  # 5 min to 24 hours

    # Threading and concurrency
    max_workers_default: int = Field(default=5, ge=1, le=50, env="MAX_WORKERS_DEFAULT")
    max_workers_max: int = Field(default=20, ge=1, le=100, env="MAX_WORKERS_MAX")
    thread_timeout_seconds: int = Field(
        default=300, ge=30, le=3600, env="THREAD_TIMEOUT_SECONDS"
    )  # 30 sec to 1 hour

    # File processing
    max_file_size_mb: int = Field(default=100, ge=1, le=1000, env="MAX_FILE_SIZE_MB")
    csv_chunk_size: int = Field(default=10000, ge=1000, le=100000, env="CSV_CHUNK_SIZE")
    max_files_per_batch: int = Field(default=1000, ge=100, le=10000, env="MAX_FILES_PER_BATCH")

    # Memory limits
    max_memory_mb: int = Field(default=2048, ge=512, le=16384, env="MAX_MEMORY_MB")  # 512MB to 16GB
    memory_warning_threshold: float = Field(
        default=0.8, ge=0.5, le=0.95, env="MEMORY_WARNING_THRESHOLD"
    )

    # API rate limiting
    api_rate_limit_requests_per_minute: int = Field(
        default=60, ge=10, le=6000, env="API_RATE_LIMIT_REQUESTS_PER_MINUTE"
    )
    api_timeout_seconds: int = Field(default=30, ge=5, le=300, env="API_TIMEOUT_SECONDS")
    api_retry_attempts: int = Field(default=3, ge=1, le=10, env="API_RETRY_ATTEMPTS")
    api_retry_delay_seconds: float = Field(
        default=1.0, ge=0.1, le=60.0, env="API_RETRY_DELAY_SECONDS"
    )

    @model_validator(mode="after")
    def validate_cache_max_greater_than_default(self):
        """Ensure max cache size is greater than default."""
        if self.cache_size_max < self.cache_size_default:
            raise ValueError("cache_size_max must be greater than cache_size_default")
        return self

    @model_validator(mode="after")
    def validate_max_workers_greater_than_default(self):
        """Ensure max workers is greater than default."""
        if self.max_workers_max < self.max_workers_default:
            raise ValueError("max_workers_max must be greater than max_workers_default")
        return self

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


class ValidationLimitsConfig(BaseSettings):
    """Input validation limits configuration."""

    # String length limits
    prompt_input_max_length: int = Field(
        default=10000, ge=1000, le=100000, env="PROMPT_INPUT_MAX_LENGTH"
    )
    title_max_length: int = Field(default=500, ge=100, le=2000, env="TITLE_MAX_LENGTH")
    description_max_length: int = Field(
        default=2000, ge=500, le=10000, env="DESCRIPTION_MAX_LENGTH"
    )
    filename_max_length: int = Field(default=200, ge=50, le=500, env="FILENAME_MAX_LENGTH")
    email_max_length: int = Field(default=254, ge=50, le=500, env="EMAIL_MAX_LENGTH")

    # Numeric ranges
    score_min: int = Field(default=1, ge=1, le=10, env="SCORE_MIN")
    score_max: int = Field(default=10, ge=1, le=10, env="SCORE_MAX")
    percentage_min: float = Field(default=0.0, ge=0.0, le=100.0, env="PERCENTAGE_MIN")
    percentage_max: float = Field(default=100.0, ge=0.0, le=100.0, env="PERCENTAGE_MAX")

    # GraphQL limits
    graphql_query_max_length: int = Field(
        default=10000, ge=1000, le=100000, env="GRAPHQL_QUERY_MAX_LENGTH"
    )
    graphql_max_complexity: int = Field(default=100, ge=10, le=1000, env="GRAPHQL_MAX_COMPLEXITY")
    graphql_max_depth: int = Field(default=10, ge=3, le=50, env="GRAPHQL_MAX_DEPTH")
    graphql_variable_max_length: int = Field(
        default=1000, ge=100, le=10000, env="GRAPHQL_VARIABLE_MAX_LENGTH"
    )

    @model_validator(mode="after")
    def validate_score_max_greater_than_min(self):
        """Ensure score_max is greater than score_min."""
        if self.score_max < self.score_min:
            raise ValueError("score_max must be greater than score_min")
        return self

    @model_validator(mode="after")
    def validate_percentage_max_greater_than_min(self):
        """Ensure percentage_max is greater than percentage_min."""
        if self.percentage_max < self.percentage_min:
            raise ValueError("percentage_max must be greater than percentage_min")
        return self

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


class PricingConfig(BaseSettings):
    """API pricing configuration."""

    # Claude pricing per 1K tokens
    claude_input_price_per_1k: float = Field(
        default=0.003, ge=0.0, le=1.0, env="CLAUDE_INPUT_PRICE_PER_1K"
    )
    claude_output_price_per_1k: float = Field(
        default=0.015, ge=0.0, le=1.0, env="CLAUDE_OUTPUT_PRICE_PER_1K"
    )

    # Cost thresholds
    daily_cost_warning_threshold: float = Field(
        default=100.0, ge=1.0, le=10000.0, env="DAILY_COST_WARNING_THRESHOLD"
    )
    monthly_cost_limit: float = Field(
        default=1000.0, ge=10.0, le=100000.0, env="MONTHLY_COST_LIMIT"
    )

    @model_validator(mode="after")
    def validate_monthly_greater_than_daily(self):
        """Ensure monthly limit is greater than daily threshold."""
        if self.monthly_cost_limit < self.daily_cost_warning_threshold:
            raise ValueError(
                "monthly_cost_limit should be greater than daily_cost_warning_threshold"
            )
        return self

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


class SecurityConfig(BaseSettings):
    """Security configuration."""

    # Key management
    api_key_min_length: int = Field(default=10, ge=8, le=50, env="API_KEY_MIN_LENGTH")
    api_key_max_length: int = Field(default=500, ge=50, le=2000, env="API_KEY_MAX_LENGTH")
    key_rotation_days: int = Field(default=90, ge=30, le=365, env="KEY_ROTATION_DAYS")

    # Encryption
    encryption_key_length: int = Field(default=32, ge=16, le=64, env="ENCRYPTION_KEY_LENGTH")
    pbkdf2_iterations: int = Field(default=100000, ge=50000, le=1000000, env="PBKDF2_ITERATIONS")
    encryption_salt: str = Field(default="north_star_metrics_default_salt", env="ENCRYPTION_SALT")

    # Session management
    session_timeout_minutes: int = Field(
        default=60, ge=5, le=480, env="SESSION_TIMEOUT_MINUTES"
    )  # 5 min to 8 hours
    max_failed_attempts: int = Field(default=5, ge=3, le=20, env="MAX_FAILED_ATTEMPTS")

    # File system access
    allowed_directories: list[str] = Field(
        default=[
            "config",
            "logs",
            "data",
            "output",
            "temp",
            ".coverage",
            "scripts",
            "docs",
            "tests",
            "tmp",
            "var",
        ],
        env="ALLOWED_DIRECTORIES",
    )

    @model_validator(mode="after")
    def validate_key_max_greater_than_min(self):
        """Ensure api_key_max_length is greater than api_key_min_length."""
        if self.api_key_max_length < self.api_key_min_length:
            raise ValueError("api_key_max_length must be greater than api_key_min_length")
        return self

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


class LoggingConfig(BaseSettings):
    """Logging configuration."""

    # Log levels
    default_log_level: LogLevel = Field(default=LogLevel.INFO, env="DEFAULT_LOG_LEVEL")
    debug_log_level: LogLevel = Field(default=LogLevel.DEBUG, env="DEBUG_LOG_LEVEL")

    # Log file settings
    max_log_file_size_mb: int = Field(default=100, ge=10, le=1000, env="MAX_LOG_FILE_SIZE_MB")
    max_log_files: int = Field(default=5, ge=1, le=100, env="MAX_LOG_FILES")

    # Structured logging
    enable_structured_logging: bool = Field(default=True, env="ENABLE_STRUCTURED_LOGGING")
    enable_correlation_ids: bool = Field(default=True, env="ENABLE_CORRELATION_IDS")

    # Sensitive data patterns to mask
    sensitive_patterns: List[str] = Field(
        default_factory=lambda: [
            r"sk-ant-[\w-]+",  # Anthropic keys
            r"ghp_[\w]+",  # GitHub tokens
            r"lin_api_[\w]+",  # Linear API keys
            r"Bearer\s+[\w.-]+",  # Bearer tokens
        ]
    )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class MetricsConfig(BaseSettings):
    """Metrics and analysis configuration."""

    # Impact score weights (must sum to 1.0)
    complexity_weight: float = Field(default=0.4, ge=0.0, le=1.0, env="COMPLEXITY_WEIGHT")
    risk_weight: float = Field(default=0.5, ge=0.0, le=1.0, env="RISK_WEIGHT")
    clarity_weight: float = Field(default=0.1, ge=0.0, le=1.0, env="CLARITY_WEIGHT")

    # Time periods
    pilot_days: int = Field(default=7, ge=1, le=30, env="PILOT_DAYS")
    default_analysis_days: int = Field(default=30, ge=1, le=365, env="DEFAULT_ANALYSIS_DAYS")
    max_analysis_days: int = Field(default=365, ge=30, le=730, env="MAX_ANALYSIS_DAYS")

    # Thresholds
    high_impact_threshold: float = Field(default=7.0, ge=5.0, le=9.0, env="HIGH_IMPACT_THRESHOLD")
    high_complexity_threshold: int = Field(default=8, ge=5, le=10, env="HIGH_COMPLEXITY_THRESHOLD")
    high_risk_threshold: int = Field(default=8, ge=5, le=10, env="HIGH_RISK_THRESHOLD")
    impact_score_max: float = Field(default=9.5, ge=8.0, le=10.0, env="IMPACT_SCORE_MAX")

    # Developer metrics
    developer_metrics_window_weeks: int = Field(
        default=4, ge=1, le=52, env="DEVELOPER_METRICS_WINDOW_WEEKS"
    )
    min_commits_for_analysis: int = Field(default=5, ge=1, le=100, env="MIN_COMMITS_FOR_ANALYSIS")

    @model_validator(mode="after")
    def validate_weights_sum_to_one(self):
        """Ensure all weights sum to 1.0."""
        total = self.complexity_weight + self.risk_weight + self.clarity_weight

        if abs(total - 1.0) > 0.001:  # Allow small floating point errors
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        return self

    @model_validator(mode="after")
    def validate_max_greater_than_default(self):
        """Ensure max_analysis_days is greater than default_analysis_days."""
        if self.max_analysis_days < self.default_analysis_days:
            raise ValueError("max_analysis_days must be greater than default_analysis_days")
        return self

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


class NorthStarSettings(BaseSettings):
    """Main application settings with environment variable support."""

    # Environment
    environment: str = Field(default="development", env="NORTH_STAR_ENV")
    debug: bool = Field(default=False, env="NORTH_STAR_DEBUG")

    # API Keys
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    github_token: Optional[str] = Field(default=None, env="GITHUB_TOKEN")
    linear_api_key: Optional[str] = Field(default=None, env=["LINEAR_API_KEY", "LINEAR_TOKEN"])

    # Application settings
    organization_name: Optional[str] = Field(default=None, env="ORGANIZATION_NAME")
    default_analysis_days: int = Field(default=30, env="DEFAULT_ANALYSIS_DAYS")

    # Configuration overrides
    config_dir: str = Field(default="config", env="NORTH_STAR_CONFIG_DIR")
    data_dir: str = Field(default="analysis_results", env="NORTH_STAR_DATA_DIR")
    logs_dir: str = Field(default="logs", env="NORTH_STAR_LOGS_DIR")

    # Nested configurations
    processing_limits: ProcessingLimitsConfig = Field(
        default_factory=lambda: ProcessingLimitsConfig(_env_file=None)
    )
    validation_limits: ValidationLimitsConfig = Field(
        default_factory=lambda: ValidationLimitsConfig(_env_file=None)
    )
    pricing: PricingConfig = Field(default_factory=lambda: PricingConfig(_env_file=None))
    security: SecurityConfig = Field(default_factory=lambda: SecurityConfig(_env_file=None))
    logging: LoggingConfig = Field(default_factory=lambda: LoggingConfig(_env_file=None))
    metrics: MetricsConfig = Field(default_factory=lambda: MetricsConfig(_env_file=None))
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment value."""
        valid_envs = ["development", "staging", "production", "test"]
        if v not in valid_envs:
            raise ValueError(f"Environment must be one of {valid_envs}")
        return v

    @field_validator("anthropic_api_key")
    @classmethod
    def validate_anthropic_key(cls, v):
        """Validate Anthropic API key format."""
        if v is not None and not v.startswith("sk-ant-"):
            raise ValueError('Anthropic API key must start with "sk-ant-"')
        return v

    @field_validator("github_token")
    @classmethod
    def validate_github_token(cls, v):
        """Validate GitHub token format."""
        if v is not None and not (
            v.startswith("ghp_")
            or v.startswith("github_pat_")
            or v.startswith("gho_")
            or v.startswith("ghs_")
        ):
            raise ValueError(
                'GitHub token must start with "ghp_", "github_pat_", "gho_", or "ghs_"'
            )
        return v

    @field_validator("linear_api_key")
    @classmethod
    def validate_linear_key(cls, v):
        """Validate Linear API key format."""
        if v is not None and not v.startswith("lin_api_"):
            raise ValueError('Linear API key must start with "lin_api_"')
        return v

    @model_validator(mode="after")
    def validate_required_keys_for_production(self):
        """Ensure required API keys are present in production."""
        if self.environment == "production":
            required_keys = []
            if not self.anthropic_api_key:
                required_keys.append("anthropic_api_key")
            if not self.github_token:
                required_keys.append("github_token")

            if required_keys:
                raise ValueError(f"Production environment requires these API keys: {required_keys}")

        return self

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"
        validate_assignment = True
        use_enum_values = True
        extra = "ignore"  # Ignore extra fields from environment


def load_settings() -> NorthStarSettings:
    """Load and validate application settings."""
    return NorthStarSettings()


def validate_ai_developers_config(config_data: Dict[str, Any]) -> AIDevsConfig:
    """Validate AI developers configuration."""
    return AIDevsConfig(**config_data)


def validate_analysis_state(state_data: Dict[str, Any]) -> AnalysisState:
    """Validate analysis state."""
    return AnalysisState(**state_data)
