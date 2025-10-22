"""Main configuration settings combining all domain-specific configs."""

from pydantic_settings import BaseSettings

from .analysis_config import AIDevsConfig, MetricsConfig
from .monitoring_config import MonitoringConfig
from .processing_config import PricingConfig, ProcessingLimitsConfig, ValidationLimitsConfig
from .security_config import LoggingConfig, SecurityConfig


class NorthStarSettings(BaseSettings):
    """Main application settings combining all configuration domains."""

    model_config = {"env_prefix": "NS_"}

    # Core settings
    debug: bool = False
    environment: str = "production"

    # Domain-specific configurations
    processing_limits: ProcessingLimitsConfig = ProcessingLimitsConfig()
    validation_limits: ValidationLimitsConfig = ValidationLimitsConfig()
    pricing: PricingConfig = PricingConfig()
    security: SecurityConfig = SecurityConfig()
    logging: LoggingConfig = LoggingConfig()
    metrics: MetricsConfig = MetricsConfig()
    monitoring: MonitoringConfig = MonitoringConfig()


def load_settings() -> NorthStarSettings:
    """Load and return application settings."""
    return NorthStarSettings()


def load_ai_developers_config() -> AIDevsConfig:
    """Load AI developers configuration from file."""
    import json
    from pathlib import Path

    config_file = Path("config/ai_developers.json")
    if config_file.exists():
        with open(config_file) as f:
            data = json.load(f)
        return AIDevsConfig(**data)

    return AIDevsConfig()
