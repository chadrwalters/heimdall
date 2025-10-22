"""Pydantic configuration schemas for North Star Metrics.

This module maintains backward compatibility while delegating to domain-specific configuration modules.
"""

# Re-export all classes from domain-specific modules for backward compatibility
from .analysis_config import AIDevConfig, AIDevsConfig, AnalysisState, MetricsConfig
from .enums import AITool, APIKeyType, BlastRadius, LogLevel, WorkType
from .main_settings import NorthStarSettings, load_ai_developers_config, load_settings
from .monitoring_config import (
    CircuitBreakerConfig,
    EmailAlertsConfig,
    MonitoringConfig,
    SlackAlertsConfig,
    WebhookAlertsConfig,
)
from .processing_config import PricingConfig, ProcessingLimitsConfig, ValidationLimitsConfig
from .security_config import LoggingConfig, SecurityConfig

# Maintain the original load_settings function for compatibility
__all__ = [
    # Enums
    "LogLevel",
    "APIKeyType",
    "AITool",
    "WorkType",
    "BlastRadius",
    # Analysis configuration
    "AIDevConfig",
    "AIDevsConfig",
    "AnalysisState",
    "MetricsConfig",
    # Monitoring configuration
    "EmailAlertsConfig",
    "SlackAlertsConfig",
    "WebhookAlertsConfig",
    "CircuitBreakerConfig",
    "MonitoringConfig",
    # Processing configuration
    "ProcessingLimitsConfig",
    "ValidationLimitsConfig",
    "PricingConfig",
    # Security configuration
    "SecurityConfig",
    "LoggingConfig",
    # Main settings
    "NorthStarSettings",
    "load_settings",
    "load_ai_developers_config",
]
