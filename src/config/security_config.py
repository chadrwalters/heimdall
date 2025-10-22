"""Security and logging configuration schemas."""

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings

from .enums import LogLevel


class SecurityConfig(BaseSettings):
    """Security configuration."""

    model_config = {"env_prefix": "NS_SECURITY_"}

    # API key validation
    api_key_min_length: int = Field(default=10, ge=5, le=50, env="NS_API_KEY_MIN_LENGTH")
    api_key_max_length: int = Field(default=500, ge=50, le=1000, env="NS_API_KEY_MAX_LENGTH")
    key_rotation_days: int = Field(default=90, ge=30, le=365, env="NS_KEY_ROTATION_DAYS")

    # Encryption settings
    encryption_key_length: int = Field(default=32, ge=16, le=64, env="NS_ENCRYPTION_KEY_LENGTH")
    pbkdf2_iterations: int = Field(default=100000, ge=10000, le=1000000, env="NS_PBKDF2_ITERATIONS")
    encryption_salt: str = Field(default="north_star_salt_2024", env="NS_ENCRYPTION_SALT")

    # Session management
    session_timeout_minutes: int = Field(default=60, ge=5, le=480, env="NS_SESSION_TIMEOUT_MINUTES")
    max_failed_attempts: int = Field(default=5, ge=1, le=20, env="NS_MAX_FAILED_ATTEMPTS")

    # File system security
    allowed_directories: List[str] = Field(
        default_factory=lambda: [
            "/tmp/north_star",
            "./data",
            "./logs",
            "./config",
            "./analysis_results",
        ],
        env="NS_ALLOWED_DIRECTORIES",
    )


class LoggingConfig(BaseSettings):
    """Logging configuration."""

    model_config = {"env_prefix": "NS_LOGGING_"}

    # Log levels
    default_log_level: LogLevel = Field(default=LogLevel.INFO, env="NS_DEFAULT_LOG_LEVEL")
    debug_log_level: LogLevel = Field(default=LogLevel.DEBUG, env="NS_DEBUG_LOG_LEVEL")

    # Log file settings
    max_log_file_size_mb: int = Field(default=100, ge=1, le=1000, env="NS_MAX_LOG_FILE_SIZE_MB")
    max_log_files: int = Field(default=10, ge=1, le=100, env="NS_MAX_LOG_FILES")
    enable_structured_logging: bool = Field(default=True, env="NS_ENABLE_STRUCTURED_LOGGING")

    # Sensitive data patterns for masking
    sensitive_patterns: List[str] = Field(
        default_factory=lambda: [
            r"sk-ant-[\w-]+",  # Anthropic keys
            r"ghp_[\w]+",  # GitHub tokens
            r"lin_api_[\w]+",  # Linear API keys
            r"Bearer\s+[\w.-]+",  # Bearer tokens
            r"password[\"':\s=]*[\w.-]+",  # Passwords
            r"secret[\"':\s=]*[\w.-]+",  # Secrets
        ],
        env="NS_SENSITIVE_PATTERNS",
    )
