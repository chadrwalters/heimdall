"""Production alerting system for North Star Metrics."""

import json
import logging
import smtplib
import time
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import requests

from ..config.schemas import load_settings

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Available alert channels."""

    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    LOG = "log"


class Alert:
    """Represents an alert."""

    def __init__(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.level = level
        self.title = title
        self.message = message
        self.source = source
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
        self.id = f"{source}_{int(time.time())}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "id": self.id,
            "level": self.level.value,
            "title": self.title,
            "message": self.message,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class AlertManager:
    """Manages alerting for production monitoring."""

    def __init__(self):
        self.settings = load_settings()
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.suppressed_alerts: Set[str] = set()
        self.last_alert_check = datetime.now()

        # Rate limiting for alerts
        self.alert_counts: Dict[str, int] = {}
        self.alert_windows: Dict[str, datetime] = {}
        self.max_alerts_per_hour = 10

    def send_alert(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
        channels: Optional[List[AlertChannel]] = None,
    ) -> bool:
        """Send an alert through specified channels."""
        alert = Alert(level, title, message, source, metadata)

        # Check if alert should be suppressed
        if self._should_suppress_alert(alert):
            logger.debug(f"Alert suppressed: {alert.id}")
            return False

        # Rate limiting
        if self._is_rate_limited(alert):
            logger.warning(f"Alert rate limited: {alert.id}")
            return False

        # Default channels based on alert level
        if channels is None:
            channels = self._get_default_channels(level)

        # Send through each channel
        success = True
        for channel in channels:
            try:
                if channel == AlertChannel.EMAIL:
                    self._send_email_alert(alert)
                elif channel == AlertChannel.SLACK:
                    self._send_slack_alert(alert)
                elif channel == AlertChannel.WEBHOOK:
                    self._send_webhook_alert(alert)
                elif channel == AlertChannel.LOG:
                    self._send_log_alert(alert)
            except Exception as e:
                logger.error(f"Failed to send alert via {channel.value}: {str(e)}")
                success = False

        # Store alert
        self.active_alerts[alert.id] = alert
        self.alert_history.append(alert)

        # Update rate limiting counters
        self._update_rate_limiting(alert)

        # Clean up old alerts
        self._cleanup_old_alerts()

        return success

    def _should_suppress_alert(self, alert: Alert) -> bool:
        """Check if alert should be suppressed."""
        # Check if alert type is suppressed
        alert_key = f"{alert.source}_{alert.level.value}"
        if alert_key in self.suppressed_alerts:
            return True

        # Check for duplicate alerts (within 5 minutes)
        cutoff_time = datetime.now() - timedelta(minutes=5)
        for existing_alert in self.alert_history:
            if (
                existing_alert.timestamp > cutoff_time
                and existing_alert.source == alert.source
                and existing_alert.title == alert.title
                and existing_alert.level == alert.level
            ):
                return True

        return False

    def _is_rate_limited(self, alert: Alert) -> bool:
        """Check if alert is rate limited."""
        alert_key = f"{alert.source}_{alert.level.value}"
        current_time = datetime.now()

        # Reset counter if window expired
        if alert_key in self.alert_windows:
            if current_time - self.alert_windows[alert_key] > timedelta(hours=1):
                self.alert_counts[alert_key] = 0
                self.alert_windows[alert_key] = current_time
        else:
            self.alert_counts[alert_key] = 0
            self.alert_windows[alert_key] = current_time

        # Check if limit exceeded
        return self.alert_counts.get(alert_key, 0) >= self.max_alerts_per_hour

    def _update_rate_limiting(self, alert: Alert) -> None:
        """Update rate limiting counters."""
        alert_key = f"{alert.source}_{alert.level.value}"
        self.alert_counts[alert_key] = self.alert_counts.get(alert_key, 0) + 1

    def _get_default_channels(self, level: AlertLevel) -> List[AlertChannel]:
        """Get default channels for alert level."""
        if level == AlertLevel.CRITICAL:
            return [AlertChannel.EMAIL, AlertChannel.SLACK, AlertChannel.LOG]
        elif level == AlertLevel.ERROR:
            return [AlertChannel.SLACK, AlertChannel.LOG]
        elif level == AlertLevel.WARNING:
            return [AlertChannel.LOG]
        else:
            return [AlertChannel.LOG]

    def _send_email_alert(self, alert: Alert) -> None:
        """Send alert via email."""
        email_config = getattr(self.settings, "email_alerts", None)
        if not email_config or not email_config.get("enabled", False):
            return

        smtp_server = email_config.get("smtp_server")
        smtp_port = email_config.get("smtp_port", 587)
        username = email_config.get("username")
        password = email_config.get("password")
        recipients = email_config.get("recipients", [])

        if not all([smtp_server, username, password, recipients]):
            logger.warning("Email configuration incomplete")
            return

        # Create message
        msg = MIMEMultipart()
        msg["From"] = username
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = f"[{alert.level.value.upper()}] {alert.title}"

        # Email body
        body = f"""
Alert Details:
- Level: {alert.level.value.upper()}
- Source: {alert.source}
- Time: {alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")}
- Message: {alert.message}

Metadata:
{json.dumps(alert.metadata, indent=2)}

--
North Star Metrics Monitoring System
"""

        msg.attach(MIMEText(body, "plain"))

        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(msg)

        logger.info(f"Email alert sent: {alert.id}")

    def _send_slack_alert(self, alert: Alert) -> None:
        """Send alert via Slack webhook."""
        slack_config = getattr(self.settings, "slack_alerts", None)
        if not slack_config or not slack_config.get("enabled", False):
            return

        webhook_url = slack_config.get("webhook_url")
        if not webhook_url:
            logger.warning("Slack webhook URL not configured")
            return

        # Color coding for alert levels
        colors = {
            AlertLevel.INFO: "#36a64f",
            AlertLevel.WARNING: "#ff9500",
            AlertLevel.ERROR: "#ff0000",
            AlertLevel.CRITICAL: "#ff0000",
        }

        # Create Slack message
        payload = {
            "attachments": [
                {
                    "color": colors.get(alert.level, "#000000"),
                    "title": f"{alert.level.value.upper()}: {alert.title}",
                    "text": alert.message,
                    "fields": [
                        {"title": "Source", "value": alert.source, "short": True},
                        {
                            "title": "Time",
                            "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
                            "short": True,
                        },
                    ],
                    "footer": "North Star Metrics",
                    "ts": int(alert.timestamp.timestamp()),
                }
            ]
        }

        # Add metadata fields
        if alert.metadata:
            for key, value in alert.metadata.items():
                payload["attachments"][0]["fields"].append(
                    {"title": key, "value": str(value), "short": True}
                )

        # Send to Slack
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()

        logger.info(f"Slack alert sent: {alert.id}")

    def _send_webhook_alert(self, alert: Alert) -> None:
        """Send alert via webhook."""
        webhook_config = getattr(self.settings, "webhook_alerts", None)
        if not webhook_config or not webhook_config.get("enabled", False):
            return

        webhook_url = webhook_config.get("url")
        if not webhook_url:
            logger.warning("Webhook URL not configured")
            return

        # Send alert data
        payload = alert.to_dict()
        headers = {"Content-Type": "application/json"}

        # Add authentication if configured
        auth_token = webhook_config.get("auth_token")
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        response = requests.post(webhook_url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()

        logger.info(f"Webhook alert sent: {alert.id}")

    def _send_log_alert(self, alert: Alert) -> None:
        """Send alert to logs."""
        log_level = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL,
        }.get(alert.level, logging.INFO)

        logger.log(log_level, f"ALERT [{alert.level.value.upper()}] {alert.title}: {alert.message}")

    def _cleanup_old_alerts(self) -> None:
        """Clean up old alerts from memory."""
        cutoff_time = datetime.now() - timedelta(hours=24)

        # Remove old active alerts
        self.active_alerts = {
            alert_id: alert
            for alert_id, alert in self.active_alerts.items()
            if alert.timestamp > cutoff_time
        }

        # Keep only recent history (last 1000 alerts)
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]

    def suppress_alerts(
        self, source: str, level: Optional[AlertLevel] = None, duration_minutes: int = 60
    ) -> None:
        """Suppress alerts for a specific source and level."""
        if level:
            alert_key = f"{source}_{level.value}"
        else:
            # Suppress all levels for this source
            for alert_level in AlertLevel:
                alert_key = f"{source}_{alert_level.value}"
                self.suppressed_alerts.add(alert_key)
            return

        self.suppressed_alerts.add(alert_key)

        # Schedule removal of suppression (simplified - in production use a task scheduler)
        logger.info(f"Alerts suppressed for {source}:{level.value} for {duration_minutes} minutes")

    def unsuppress_alerts(self, source: str, level: Optional[AlertLevel] = None) -> None:
        """Remove alert suppression."""
        if level:
            alert_key = f"{source}_{level.value}"
            self.suppressed_alerts.discard(alert_key)
        else:
            # Remove suppression for all levels
            for alert_level in AlertLevel:
                alert_key = f"{source}_{alert_level.value}"
                self.suppressed_alerts.discard(alert_key)

        logger.info(f"Alert suppression removed for {source}:{level.value if level else 'all'}")

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get list of active alerts."""
        return [alert.to_dict() for alert in self.active_alerts.values()]

    def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get alert history for specified time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [alert.to_dict() for alert in self.alert_history if alert.timestamp > cutoff_time]

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of alert activity."""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        last_hour = now - timedelta(hours=1)

        recent_alerts = [a for a in self.alert_history if a.timestamp > last_24h]
        hourly_alerts = [a for a in self.alert_history if a.timestamp > last_hour]

        # Count by level
        level_counts = {level.value: 0 for level in AlertLevel}
        for alert in recent_alerts:
            level_counts[alert.level.value] += 1

        # Count by source
        source_counts = {}
        for alert in recent_alerts:
            source_counts[alert.source] = source_counts.get(alert.source, 0) + 1

        return {
            "active_alerts": len(self.active_alerts),
            "alerts_last_24h": len(recent_alerts),
            "alerts_last_hour": len(hourly_alerts),
            "suppressed_alert_types": len(self.suppressed_alerts),
            "alert_levels_24h": level_counts,
            "alert_sources_24h": dict(
                sorted(source_counts.items(), key=lambda x: x[1], reverse=True)
            ),
            "most_active_sources": list(
                dict(sorted(source_counts.items(), key=lambda x: x[1], reverse=True)).keys()
            )[:5],
        }


# Global alert manager instance
_alert_manager = AlertManager()


def send_alert(
    level: AlertLevel,
    title: str,
    message: str,
    source: str,
    metadata: Optional[Dict[str, Any]] = None,
    channels: Optional[List[AlertChannel]] = None,
) -> bool:
    """Send an alert."""
    return _alert_manager.send_alert(level, title, message, source, metadata, channels)


def get_active_alerts() -> List[Dict[str, Any]]:
    """Get active alerts."""
    return _alert_manager.get_active_alerts()


def get_alert_history(hours: int = 24) -> List[Dict[str, Any]]:
    """Get alert history."""
    return _alert_manager.get_alert_history(hours)


def get_alert_summary() -> Dict[str, Any]:
    """Get alert summary."""
    return _alert_manager.get_alert_summary()


def suppress_alerts(
    source: str, level: Optional[AlertLevel] = None, duration_minutes: int = 60
) -> None:
    """Suppress alerts."""
    _alert_manager.suppress_alerts(source, level, duration_minutes)


def unsuppress_alerts(source: str, level: Optional[AlertLevel] = None) -> None:
    """Remove alert suppression."""
    _alert_manager.unsuppress_alerts(source, level)
