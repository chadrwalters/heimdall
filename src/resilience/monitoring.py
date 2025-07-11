"""Circuit breaker monitoring and health dashboard."""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from .alerting import AlertLevel, send_alert
from .circuit_breaker import get_all_circuit_breaker_stats

logger = logging.getLogger(__name__)


class CircuitBreakerMonitor:
    """Monitor circuit breaker health and performance."""

    def __init__(self):
        self.health_history = []
        self.alerts = []
        self.last_check = None

    def check_health(self) -> Dict[str, Any]:
        """Check overall circuit breaker health."""
        stats = get_all_circuit_breaker_stats()
        current_time = datetime.now()

        health_report = {
            "timestamp": current_time.isoformat(),
            "overall_health": "healthy",
            "total_breakers": len(stats),
            "breaker_states": {"closed": 0, "open": 0, "half_open": 0},
            "alerts": [],
            "summary": {},
            "details": stats,
        }

        # Analyze each circuit breaker
        for name, breaker_stats in stats.items():
            state = breaker_stats["state"]
            health_report["breaker_states"][state] += 1

            # Check for concerning patterns
            if state == "open":
                health_report["overall_health"] = "degraded"
                alert_data = {
                    "level": "warning",
                    "breaker": name,
                    "message": f"Circuit breaker '{name}' is open",
                    "timestamp": current_time.isoformat(),
                }
                health_report["alerts"].append(alert_data)

                # Send production alert
                send_alert(
                    AlertLevel.WARNING,
                    f"Circuit Breaker Open: {name}",
                    f"Circuit breaker '{name}' is open and blocking requests",
                    "circuit_breaker_monitor",
                    {"breaker_name": name, "state": state, "stats": breaker_stats},
                )

            # Check failure rates
            failure_rate = breaker_stats.get("failure_rate", 0)
            if failure_rate > 0.5:
                alert_data = {
                    "level": "warning",
                    "breaker": name,
                    "message": f"High failure rate: {failure_rate:.2%}",
                    "timestamp": current_time.isoformat(),
                }
                health_report["alerts"].append(alert_data)

                # Send production alert for high failure rate
                if failure_rate > 0.8:
                    send_alert(
                        AlertLevel.ERROR,
                        f"High Failure Rate: {name}",
                        f"Circuit breaker '{name}' has failure rate of {failure_rate:.2%}",
                        "circuit_breaker_monitor",
                        {
                            "breaker_name": name,
                            "failure_rate": failure_rate,
                            "stats": breaker_stats,
                        },
                    )

            # Check consecutive failures
            consecutive_failures = breaker_stats.get("consecutive_failures", 0)
            if consecutive_failures >= 3:
                alert_data = {
                    "level": "error",
                    "breaker": name,
                    "message": f"High consecutive failures: {consecutive_failures}",
                    "timestamp": current_time.isoformat(),
                }
                health_report["alerts"].append(alert_data)

                # Send production alert for consecutive failures
                if consecutive_failures >= 5:
                    send_alert(
                        AlertLevel.CRITICAL,
                        f"Critical Failures: {name}",
                        f"Circuit breaker '{name}' has {consecutive_failures} consecutive failures",
                        "circuit_breaker_monitor",
                        {
                            "breaker_name": name,
                            "consecutive_failures": consecutive_failures,
                            "stats": breaker_stats,
                        },
                    )

        # Overall health determination
        if health_report["breaker_states"]["open"] > 0:
            health_report["overall_health"] = "degraded"
        if len([a for a in health_report["alerts"] if a["level"] == "error"]) > 0:
            health_report["overall_health"] = "unhealthy"

        # Generate summary
        health_report["summary"] = {
            "total_calls": sum(s.get("total_calls", 0) for s in stats.values()),
            "successful_calls": sum(s.get("successful_calls", 0) for s in stats.values()),
            "failed_calls": sum(s.get("failed_calls", 0) for s in stats.values()),
            "average_success_rate": self._calculate_average_success_rate(stats),
            "open_breakers": [name for name, s in stats.items() if s["state"] == "open"],
            "degraded_breakers": [
                name for name, s in stats.items() if s.get("failure_rate", 0) > 0.3
            ],
        }

        # Store in history
        self.health_history.append(health_report)
        if len(self.health_history) > 100:  # Keep last 100 checks
            self.health_history.pop(0)

        self.last_check = current_time
        return health_report

    def _calculate_average_success_rate(self, stats: Dict[str, Any]) -> float:
        """Calculate average success rate across all breakers."""
        if not stats:
            return 1.0

        total_calls = sum(s.get("total_calls", 0) for s in stats.values())
        if total_calls == 0:
            return 1.0

        successful_calls = sum(s.get("successful_calls", 0) for s in stats.values())
        return successful_calls / total_calls

    def get_health_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get health trends over specified time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # Filter history to time period
        recent_history = [
            h for h in self.health_history if datetime.fromisoformat(h["timestamp"]) >= cutoff_time
        ]

        if not recent_history:
            return {"message": "No data available for the specified time period"}

        # Calculate trends
        trends = {
            "time_period_hours": hours,
            "total_checks": len(recent_history),
            "health_distribution": {"healthy": 0, "degraded": 0, "unhealthy": 0},
            "average_success_rate": 0,
            "total_failures": 0,
            "most_problematic_breakers": {},
            "recovery_times": [],
        }

        # Analyze trends
        for report in recent_history:
            health = report["overall_health"]
            trends["health_distribution"][health] += 1

            # Track problematic breakers
            for alert in report.get("alerts", []):
                breaker = alert["breaker"]
                if breaker not in trends["most_problematic_breakers"]:
                    trends["most_problematic_breakers"][breaker] = 0
                trends["most_problematic_breakers"][breaker] += 1

        # Calculate averages
        if recent_history:
            trends["average_success_rate"] = sum(
                h["summary"]["average_success_rate"] for h in recent_history
            ) / len(recent_history)
            trends["total_failures"] = sum(h["summary"]["failed_calls"] for h in recent_history)

        # Sort most problematic breakers
        trends["most_problematic_breakers"] = dict(
            sorted(trends["most_problematic_breakers"].items(), key=lambda x: x[1], reverse=True)
        )

        return trends

    def get_breaker_details(self, breaker_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific circuit breaker."""
        stats = get_all_circuit_breaker_stats()

        if breaker_name not in stats:
            return {"error": f"Circuit breaker '{breaker_name}' not found"}

        breaker_stats = stats[breaker_name]

        # Add historical data from health history
        historical_data = []
        for report in self.health_history:
            if breaker_name in report.get("details", {}):
                historical_data.append(
                    {
                        "timestamp": report["timestamp"],
                        "state": report["details"][breaker_name]["state"],
                        "success_rate": report["details"][breaker_name].get("success_rate", 0),
                        "total_calls": report["details"][breaker_name].get("total_calls", 0),
                    }
                )

        return {
            "name": breaker_name,
            "current_stats": breaker_stats,
            "historical_data": historical_data[-50:],  # Last 50 data points
            "recommendations": self._generate_recommendations(breaker_stats),
        }

    def _generate_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on circuit breaker stats."""
        recommendations = []

        state = stats.get("state", "unknown")
        failure_rate = stats.get("failure_rate", 0)
        consecutive_failures = stats.get("consecutive_failures", 0)

        if state == "open":
            recommendations.append("Circuit breaker is open. Check downstream service health.")
            recommendations.append("Consider implementing retry logic with exponential backoff.")

        if failure_rate > 0.5:
            recommendations.append(
                f"High failure rate ({failure_rate:.2%}). Investigate root cause."
            )
            recommendations.append("Consider adjusting failure threshold or recovery timeout.")

        if consecutive_failures >= 5:
            recommendations.append("High consecutive failures detected. Service may be down.")
            recommendations.append("Implement health checks for downstream service.")

        if stats.get("total_calls", 0) > 1000 and stats.get("successful_calls", 0) == 0:
            recommendations.append("No successful calls detected. Service may be misconfigured.")

        if not recommendations:
            recommendations.append("Circuit breaker is operating normally.")

        return recommendations

    def export_health_report(self, format: str = "json") -> str:
        """Export current health report in specified format."""
        health_report = self.check_health()

        if format.lower() == "json":
            return json.dumps(health_report, indent=2)
        elif format.lower() == "summary":
            return self._format_summary_report(health_report)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _format_summary_report(self, health_report: Dict[str, Any]) -> str:
        """Format health report as human-readable summary."""
        lines = []
        lines.append("=" * 50)
        lines.append("CIRCUIT BREAKER HEALTH REPORT")
        lines.append("=" * 50)
        lines.append(f"Timestamp: {health_report['timestamp']}")
        lines.append(f"Overall Health: {health_report['overall_health'].upper()}")
        lines.append(f"Total Breakers: {health_report['total_breakers']}")
        lines.append("")

        # Breaker states
        lines.append("Breaker States:")
        for state, count in health_report["breaker_states"].items():
            lines.append(f"  {state.upper()}: {count}")
        lines.append("")

        # Summary statistics
        summary = health_report["summary"]
        lines.append("Summary Statistics:")
        lines.append(f"  Total Calls: {summary['total_calls']:,}")
        lines.append(f"  Successful Calls: {summary['successful_calls']:,}")
        lines.append(f"  Failed Calls: {summary['failed_calls']:,}")
        lines.append(f"  Average Success Rate: {summary['average_success_rate']:.2%}")
        lines.append("")

        # Alerts
        if health_report["alerts"]:
            lines.append("Active Alerts:")
            for alert in health_report["alerts"]:
                lines.append(f"  [{alert['level'].upper()}] {alert['breaker']}: {alert['message']}")
        else:
            lines.append("No active alerts.")

        lines.append("")
        lines.append("=" * 50)

        return "\n".join(lines)


# Global monitor instance
_monitor = CircuitBreakerMonitor()


def get_circuit_breaker_health() -> Dict[str, Any]:
    """Get current circuit breaker health status."""
    return _monitor.check_health()


def get_circuit_breaker_trends(hours: int = 24) -> Dict[str, Any]:
    """Get circuit breaker health trends."""
    return _monitor.get_health_trends(hours)


def get_circuit_breaker_details(breaker_name: str) -> Dict[str, Any]:
    """Get detailed information about a specific circuit breaker."""
    return _monitor.get_breaker_details(breaker_name)


def export_circuit_breaker_report(format: str = "json") -> str:
    """Export circuit breaker health report."""
    return _monitor.export_health_report(format)
