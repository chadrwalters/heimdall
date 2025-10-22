"""Monitoring, alerting, and resilience configuration schemas."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


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
                failure_threshold=5, recovery_timeout_seconds=60.0, timeout_seconds=30.0
            ),
            "github_api": CircuitBreakerConfig(
                failure_threshold=3, recovery_timeout_seconds=45.0, timeout_seconds=20.0
            ),
            "linear_api": CircuitBreakerConfig(
                failure_threshold=3, recovery_timeout_seconds=45.0, timeout_seconds=20.0
            ),
            "database": CircuitBreakerConfig(
                failure_threshold=2,
                success_threshold=2,
                recovery_timeout_seconds=30.0,
                timeout_seconds=10.0,
            ),
        }
    )

    # Alert configurations
    email_alerts: EmailAlertsConfig = Field(default_factory=EmailAlertsConfig)
    slack_alerts: SlackAlertsConfig = Field(default_factory=SlackAlertsConfig)
    webhook_alerts: WebhookAlertsConfig = Field(default_factory=WebhookAlertsConfig)
