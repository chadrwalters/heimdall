"""Environment-specific configuration loader."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class EnvironmentConfigLoader:
    """Loads environment-specific configuration."""

    def __init__(self):
        self.config_dir = Path(__file__).parent.parent.parent / "config"
        self.environments_dir = self.config_dir / "environments"
        self.current_env = self._detect_environment()
        self._cache: Dict[str, Any] = {}

    def _detect_environment(self) -> str:
        """Detect current environment from various sources."""
        # Check environment variable first
        env = os.getenv("NORTH_STAR_ENV", "").lower()
        if env in ["development", "staging", "production"]:
            return env

        # Check common CI/deployment environment variables
        if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
            return "staging"  # CI environments default to staging

        # Check for production indicators
        if os.getenv("PRODUCTION") or os.getenv("PROD") or os.getenv("NODE_ENV") == "production":
            return "production"

        # Check for explicit staging
        if os.getenv("STAGING") or os.getenv("NODE_ENV") == "staging":
            return "staging"

        # Default to development for local environments
        return "development"

    def get_environment(self) -> str:
        """Get current environment name."""
        return self.current_env

    def load_environment_config(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration for specified environment."""
        env = environment or self.current_env

        if env in self._cache:
            return self._cache[env]

        config_file = self.environments_dir / f"{env}.yaml"

        if not config_file.exists():
            raise FileNotFoundError(f"Environment config not found: {config_file}")

        with open(config_file, "r") as f:
            config = yaml.safe_load(f)

        # Apply environment variable overrides
        config = self._apply_env_overrides(config)

        self._cache[env] = config
        return config

    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to config."""
        # Define environment variable mappings
        env_mappings = {
            # Processing limits
            "NS_DIFF_LENGTH_LIMIT": ("processing_limits", "diff_length_limit"),
            "NS_MAX_WORKERS": ("processing_limits", "max_workers_default"),
            "NS_API_TIMEOUT": ("processing_limits", "api_timeout_seconds"),
            "NS_MEMORY_LIMIT_MB": ("processing_limits", "max_memory_mb"),
            # Security settings
            "NS_SESSION_TIMEOUT": ("security", "session_timeout_minutes"),
            "NS_MAX_FAILED_ATTEMPTS": ("security", "max_failed_attempts"),
            # Logging
            "NS_LOG_LEVEL": ("logging", "default_log_level"),
            "NS_DEBUG_LOG_LEVEL": ("logging", "debug_log_level"),
            # Metrics
            "NS_PILOT_DAYS": ("metrics", "pilot_days"),
            "NS_DEFAULT_ANALYSIS_DAYS": ("metrics", "default_analysis_days"),
            "NS_HIGH_IMPACT_THRESHOLD": ("metrics", "high_impact_threshold"),
            # Pricing
            "NS_DAILY_COST_WARNING": ("pricing", "daily_cost_warning_threshold"),
            "NS_MONTHLY_COST_LIMIT": ("pricing", "monthly_cost_limit"),
            # Monitoring
            "NS_MONITORING_ENABLED": ("monitoring", "enabled"),
            "NS_CHECK_INTERVAL_MINUTES": ("monitoring", "check_interval_minutes"),
            "NS_MAX_ALERTS_PER_HOUR": ("monitoring", "max_alerts_per_hour"),
            # Email alerts
            "NS_EMAIL_ALERTS_ENABLED": ("email_alerts", "enabled"),
            "NS_SMTP_SERVER": ("email_alerts", "smtp_server"),
            "NS_SMTP_PORT": ("email_alerts", "smtp_port"),
            "NS_SMTP_USERNAME": ("email_alerts", "username"),
            "NS_SMTP_PASSWORD": ("email_alerts", "password"),
            # Slack alerts
            "NS_SLACK_ALERTS_ENABLED": ("slack_alerts", "enabled"),
            "NS_SLACK_WEBHOOK_URL": ("slack_alerts", "webhook_url"),
            # Webhook alerts
            "NS_WEBHOOK_ALERTS_ENABLED": ("webhook_alerts", "enabled"),
            "NS_WEBHOOK_URL": ("webhook_alerts", "url"),
            "NS_WEBHOOK_AUTH_TOKEN": ("webhook_alerts", "auth_token"),
        }

        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert value to appropriate type
                converted_value = self._convert_env_value(value)

                # Ensure section exists
                if section not in config:
                    config[section] = {}

                config[section][key] = converted_value

        return config

    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type."""
        # Boolean conversion
        if value.lower() in ("true", "false"):
            return value.lower() == "true"

        # Integer conversion
        try:
            if "." not in value:
                return int(value)
        except ValueError:
            pass

        # Float conversion
        try:
            return float(value)
        except ValueError:
            pass

        # String (default)
        return value

    def get_config_value(self, section: str, key: str, default: Any = None) -> Any:
        """Get a specific configuration value."""
        config = self.load_environment_config()
        return config.get(section, {}).get(key, default)

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.current_env == "development"

    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.current_env == "staging"

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.current_env == "production"

    def get_feature_flags(self) -> Dict[str, bool]:
        """Get environment-specific feature flags."""
        config = self.load_environment_config()
        env_section = config.get(self.current_env, {})

        return {
            "debug_mode": env_section.get("enable_debug_mode", False),
            "monitoring": env_section.get("enable_monitoring", True),
            "alerting": env_section.get("enable_alerting", True),
            "circuit_breakers": env_section.get("enable_circuit_breakers", True),
            "rate_limiting": env_section.get("enable_rate_limiting", True),
            "caching": env_section.get("enable_caching", True),
            "hot_reload": env_section.get("enable_hot_reload", False),
            "profiling": env_section.get("enable_profiling", False),
            "performance_testing": env_section.get("enable_performance_testing", False),
            "verbose_errors": env_section.get("verbose_error_messages", False),
        }

    def validate_environment_config(self) -> Dict[str, Any]:
        """Validate current environment configuration."""
        config = self.load_environment_config()

        validation_results = {
            "environment": self.current_env,
            "config_file_exists": True,
            "warnings": [],
            "errors": [],
            "recommendations": [],
        }

        # Check required sections
        required_sections = [
            "processing_limits",
            "validation_limits",
            "security",
            "logging",
            "metrics",
            "pricing",
        ]

        for section in required_sections:
            if section not in config:
                validation_results["errors"].append(f"Missing required section: {section}")

        # Environment-specific validations
        if self.is_production():
            # Production should have strict security settings
            security = config.get("security", {})
            if security.get("session_timeout_minutes", 0) > 60:
                validation_results["warnings"].append(
                    "Production session timeout should be <= 60 minutes"
                )

            # Production should have monitoring enabled
            monitoring = config.get("monitoring", {})
            if not monitoring.get("enabled", False):
                validation_results["errors"].append("Monitoring must be enabled in production")

            # Production shouldn't have debug mode enabled
            prod_config = config.get("production", {})
            if prod_config.get("enable_debug_mode", False):
                validation_results["warnings"].append(
                    "Debug mode should not be enabled in production"
                )

        elif self.is_development():
            # Development recommendations
            dev_config = config.get("development", {})
            if not dev_config.get("enable_debug_mode", False):
                validation_results["recommendations"].append(
                    "Consider enabling debug mode for development"
                )

        # Check for required environment variables in production
        if self.is_production():
            required_env_vars = ["ANTHROPIC_API_KEY", "GITHUB_TOKEN", "LINEAR_API_KEY"]

            for env_var in required_env_vars:
                if not os.getenv(env_var):
                    validation_results["errors"].append(
                        f"Missing required environment variable: {env_var}"
                    )

        return validation_results

    def switch_environment(self, environment: str) -> None:
        """Switch to a different environment (for testing)."""
        if environment not in ["development", "staging", "production"]:
            raise ValueError(f"Invalid environment: {environment}")

        self.current_env = environment
        # Clear cache to force reload
        self._cache.clear()


# Global instance
_env_loader = EnvironmentConfigLoader()


def get_environment_loader() -> EnvironmentConfigLoader:
    """Get the global environment loader instance."""
    return _env_loader


def get_current_environment() -> str:
    """Get current environment name."""
    return _env_loader.get_environment()


def is_development() -> bool:
    """Check if running in development."""
    return _env_loader.is_development()


def is_staging() -> bool:
    """Check if running in staging."""
    return _env_loader.is_staging()


def is_production() -> bool:
    """Check if running in production."""
    return _env_loader.is_production()


def get_feature_flags() -> Dict[str, bool]:
    """Get environment-specific feature flags."""
    return _env_loader.get_feature_flags()


def validate_environment() -> Dict[str, Any]:
    """Validate current environment configuration."""
    return _env_loader.validate_environment_config()
