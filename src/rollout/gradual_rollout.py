"""Gradual rollout capabilities for large organizations."""

import json
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..config.environment_loader import get_current_environment
from ..logging.structured_logger import get_structured_logger


class RolloutPhase(Enum):
    """Rollout phases for gradual deployment."""

    PLANNING = "planning"
    PILOT = "pilot"
    CANARY = "canary"
    GRADUAL = "gradual"
    FULL = "full"
    COMPLETE = "complete"
    PAUSED = "paused"
    ROLLED_BACK = "rolled_back"


class RolloutStrategy(Enum):
    """Rollout strategies."""

    PERCENTAGE_BASED = "percentage"
    REPOSITORY_BASED = "repository"
    TEAM_BASED = "team"
    TIME_BASED = "time"
    HYBRID = "hybrid"


@dataclass
class RolloutConfig:
    """Configuration for gradual rollout."""

    organization: str
    strategy: RolloutStrategy
    total_repositories: int
    pilot_repositories: List[str] = field(default_factory=list)
    canary_percentage: float = 0.1  # 10% for canary
    gradual_percentage_steps: List[float] = field(default_factory=lambda: [0.25, 0.5, 0.75, 1.0])
    phase_duration_hours: int = 24  # 24 hours per phase
    success_threshold: float = 0.95  # 95% success rate to proceed
    rollback_threshold: float = 0.80  # 80% success rate triggers rollback
    max_concurrent_repositories: int = 50
    excluded_repositories: List[str] = field(default_factory=list)
    priority_repositories: List[str] = field(default_factory=list)


@dataclass
class RolloutMetrics:
    """Metrics for rollout monitoring."""

    phase: RolloutPhase
    repositories_processed: int
    repositories_successful: int
    repositories_failed: int
    total_processing_time_minutes: float
    average_response_time_ms: float
    error_rate: float
    phase_start_time: datetime
    phase_end_time: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.repositories_processed == 0:
            return 1.0
        return self.repositories_successful / self.repositories_processed

    @property
    def phase_duration_hours(self) -> float:
        """Calculate phase duration in hours."""
        end_time = self.phase_end_time or datetime.now()
        duration = end_time - self.phase_start_time
        return duration.total_seconds() / 3600


class GradualRolloutManager:
    """Manages gradual rollout of analysis across large organizations."""

    def __init__(self, config: RolloutConfig):
        self.config = config
        self.current_phase = RolloutPhase.PLANNING
        self.logger = get_structured_logger(f"rollout.{config.organization}")
        self.metrics_history: List[RolloutMetrics] = []
        self.processed_repositories: Set[str] = set()
        self.failed_repositories: Set[str] = set()
        self.rollout_state_file = Path(f"rollout_state_{config.organization}.json")

        # Load existing state if available
        self._load_state()

    def start_rollout(self) -> Dict[str, Any]:
        """Start the gradual rollout process."""
        self.logger.info(
            "Starting gradual rollout",
            extra={
                "organization": self.config.organization,
                "strategy": self.config.strategy.value,
                "total_repositories": self.config.total_repositories,
            },
        )

        self.current_phase = RolloutPhase.PILOT
        self._save_state()

        return self._execute_pilot_phase()

    def _execute_pilot_phase(self) -> Dict[str, Any]:
        """Execute pilot phase with selected repositories."""
        self.logger.info("Executing pilot phase")

        # Select pilot repositories
        pilot_repos = self._select_pilot_repositories()

        start_time = datetime.now()
        metrics = RolloutMetrics(
            phase=RolloutPhase.PILOT,
            repositories_processed=0,
            repositories_successful=0,
            repositories_failed=0,
            total_processing_time_minutes=0.0,
            average_response_time_ms=0.0,
            error_rate=0.0,
            phase_start_time=start_time,
        )

        # Process pilot repositories
        for repo in pilot_repos:
            success, processing_time_ms = self._process_repository(repo)
            metrics.repositories_processed += 1

            if success:
                metrics.repositories_successful += 1
                self.processed_repositories.add(repo)
            else:
                metrics.repositories_failed += 1
                self.failed_repositories.add(repo)
                metrics.errors.append(f"Failed to process repository: {repo}")

        metrics.phase_end_time = datetime.now()
        metrics.total_processing_time_minutes = metrics.phase_duration_hours * 60
        metrics.error_rate = 1.0 - metrics.success_rate

        self.metrics_history.append(metrics)

        # Evaluate pilot results
        if metrics.success_rate >= self.config.success_threshold:
            self.logger.info(
                "Pilot phase successful, proceeding to canary",
                extra={
                    "success_rate": metrics.success_rate,
                    "repositories_processed": metrics.repositories_processed,
                },
            )
            self.current_phase = RolloutPhase.CANARY
            return {"status": "pilot_complete", "next_phase": "canary", "metrics": metrics}
        else:
            self.logger.error(
                "Pilot phase failed",
                extra={
                    "success_rate": metrics.success_rate,
                    "threshold": self.config.success_threshold,
                },
            )
            self.current_phase = RolloutPhase.ROLLED_BACK
            return {"status": "pilot_failed", "rollback": True, "metrics": metrics}

    def continue_rollout(self) -> Dict[str, Any]:
        """Continue to the next rollout phase."""
        if self.current_phase == RolloutPhase.CANARY:
            return self._execute_canary_phase()
        elif self.current_phase == RolloutPhase.GRADUAL:
            return self._execute_gradual_phase()
        elif self.current_phase == RolloutPhase.FULL:
            return self._execute_full_phase()
        else:
            return {"status": "invalid_phase", "current_phase": self.current_phase.value}

    def _execute_canary_phase(self) -> Dict[str, Any]:
        """Execute canary phase with small percentage of repositories."""
        self.logger.info("Executing canary phase")

        canary_repos = self._select_canary_repositories()
        return self._process_repository_batch(canary_repos, RolloutPhase.CANARY)

    def _execute_gradual_phase(self) -> Dict[str, Any]:
        """Execute gradual phase with increasing percentages."""
        self.logger.info("Executing gradual phase")

        for percentage in self.config.gradual_percentage_steps:
            if percentage <= self._get_current_coverage():
                continue  # Skip already processed percentages

            batch_repos = self._select_gradual_repositories(percentage)
            result = self._process_repository_batch(batch_repos, RolloutPhase.GRADUAL)

            if result["status"] != "phase_complete":
                return result

            # Check if we should continue to next percentage
            if not self._should_continue_gradual():
                return {"status": "gradual_paused", "current_percentage": percentage}

        self.current_phase = RolloutPhase.FULL
        return {"status": "gradual_complete", "next_phase": "full"}

    def _execute_full_phase(self) -> Dict[str, Any]:
        """Execute full rollout to all remaining repositories."""
        self.logger.info("Executing full phase")

        remaining_repos = self._get_remaining_repositories()
        result = self._process_repository_batch(remaining_repos, RolloutPhase.FULL)

        if result["status"] == "phase_complete":
            self.current_phase = RolloutPhase.COMPLETE
            return {
                "status": "rollout_complete",
                "total_repositories": len(self.processed_repositories),
            }

        return result

    def _select_pilot_repositories(self) -> List[str]:
        """Select repositories for pilot phase."""
        if self.config.pilot_repositories:
            return self.config.pilot_repositories

        # Auto-select pilot repositories based on criteria
        all_repos = self._get_all_repositories()

        # Prioritize smaller, less critical repositories for pilot
        # In production, this would analyze repository metadata
        pilot_count = min(5, len(all_repos) // 10)  # 10% or max 5 repos
        return random.sample(all_repos, pilot_count)

    def _select_canary_repositories(self) -> List[str]:
        """Select repositories for canary phase."""
        all_repos = self._get_all_repositories()
        canary_count = max(1, int(len(all_repos) * self.config.canary_percentage))

        available_repos = [r for r in all_repos if r not in self.processed_repositories]
        return random.sample(available_repos, min(canary_count, len(available_repos)))

    def _select_gradual_repositories(self, target_percentage: float) -> List[str]:
        """Select repositories for gradual phase up to target percentage."""
        all_repos = self._get_all_repositories()
        target_count = int(len(all_repos) * target_percentage)
        current_count = len(self.processed_repositories)

        if target_count <= current_count:
            return []

        batch_count = min(target_count - current_count, self.config.max_concurrent_repositories)

        available_repos = [r for r in all_repos if r not in self.processed_repositories]
        return available_repos[:batch_count]

    def _process_repository_batch(
        self, repositories: List[str], phase: RolloutPhase
    ) -> Dict[str, Any]:
        """Process a batch of repositories and track metrics."""
        start_time = datetime.now()

        metrics = RolloutMetrics(
            phase=phase,
            repositories_processed=0,
            repositories_successful=0,
            repositories_failed=0,
            total_processing_time_minutes=0.0,
            average_response_time_ms=0.0,
            error_rate=0.0,
            phase_start_time=start_time,
        )

        total_processing_time = 0.0

        for repo in repositories:
            success, processing_time_ms = self._process_repository(repo)
            metrics.repositories_processed += 1
            total_processing_time += processing_time_ms

            if success:
                metrics.repositories_successful += 1
                self.processed_repositories.add(repo)
            else:
                metrics.repositories_failed += 1
                self.failed_repositories.add(repo)
                metrics.errors.append(f"Failed to process repository: {repo}")

            # Check for early rollback conditions
            if metrics.repositories_processed >= 10:  # Check after processing 10 repos
                current_success_rate = metrics.success_rate
                if current_success_rate < self.config.rollback_threshold:
                    self.logger.error(
                        "Early rollback triggered",
                        extra={
                            "success_rate": current_success_rate,
                            "threshold": self.config.rollback_threshold,
                        },
                    )
                    self.current_phase = RolloutPhase.ROLLED_BACK
                    return {
                        "status": "rolled_back",
                        "reason": "low_success_rate",
                        "metrics": metrics,
                    }

        metrics.phase_end_time = datetime.now()
        metrics.average_response_time_ms = (
            total_processing_time / len(repositories) if repositories else 0
        )
        metrics.error_rate = 1.0 - metrics.success_rate

        self.metrics_history.append(metrics)
        self._save_state()

        # Evaluate phase results
        if metrics.success_rate >= self.config.success_threshold:
            return {"status": "phase_complete", "metrics": metrics}
        else:
            self.current_phase = RolloutPhase.PAUSED
            return {"status": "phase_paused", "reason": "below_threshold", "metrics": metrics}

    def _process_repository(self, repository: str) -> tuple[bool, float]:
        """Process a single repository (mock implementation)."""
        # In production, this would call the actual analysis pipeline
        processing_time_ms = random.uniform(100, 5000)  # Simulate processing time

        # Simulate success/failure (90% success rate)
        success = random.random() > 0.1

        if not success:
            self.logger.warning(f"Repository processing failed: {repository}")

        # Simulate actual processing time
        time.sleep(processing_time_ms / 10000)  # Convert to seconds and scale down

        return success, processing_time_ms

    def _get_all_repositories(self) -> List[str]:
        """Get list of all repositories for the organization."""
        # In production, this would fetch from GitHub API
        return [f"repo-{i:03d}" for i in range(1, self.config.total_repositories + 1)]

    def _get_remaining_repositories(self) -> List[str]:
        """Get list of repositories not yet processed."""
        all_repos = self._get_all_repositories()
        return [r for r in all_repos if r not in self.processed_repositories]

    def _get_current_coverage(self) -> float:
        """Get current rollout coverage percentage."""
        total_repos = self.config.total_repositories
        if total_repos == 0:
            return 1.0
        return len(self.processed_repositories) / total_repos

    def _should_continue_gradual(self) -> bool:
        """Determine if gradual rollout should continue."""
        if not self.metrics_history:
            return True

        latest_metrics = self.metrics_history[-1]
        return latest_metrics.success_rate >= self.config.success_threshold

    def pause_rollout(self) -> Dict[str, Any]:
        """Pause the current rollout."""
        self.logger.info("Pausing rollout")
        self.current_phase = RolloutPhase.PAUSED
        self._save_state()

        return {
            "status": "paused",
            "current_coverage": self._get_current_coverage(),
            "repositories_processed": len(self.processed_repositories),
        }

    def resume_rollout(self) -> Dict[str, Any]:
        """Resume a paused rollout."""
        if self.current_phase != RolloutPhase.PAUSED:
            return {"status": "error", "message": "Rollout is not paused"}

        self.logger.info("Resuming rollout")

        # Determine next phase based on current progress
        coverage = self._get_current_coverage()
        if coverage < self.config.canary_percentage:
            self.current_phase = RolloutPhase.CANARY
        elif coverage < max(self.config.gradual_percentage_steps):
            self.current_phase = RolloutPhase.GRADUAL
        else:
            self.current_phase = RolloutPhase.FULL

        return self.continue_rollout()

    def rollback_rollout(self) -> Dict[str, Any]:
        """Rollback the current rollout."""
        self.logger.error("Rolling back rollout")
        self.current_phase = RolloutPhase.ROLLED_BACK
        self._save_state()

        return {
            "status": "rolled_back",
            "repositories_to_revert": list(self.processed_repositories),
            "total_reverted": len(self.processed_repositories),
        }

    def get_rollout_status(self) -> Dict[str, Any]:
        """Get current rollout status and metrics."""
        return {
            "organization": self.config.organization,
            "current_phase": self.current_phase.value,
            "coverage_percentage": self._get_current_coverage() * 100,
            "repositories_processed": len(self.processed_repositories),
            "repositories_failed": len(self.failed_repositories),
            "total_repositories": self.config.total_repositories,
            "latest_metrics": self.metrics_history[-1].__dict__ if self.metrics_history else None,
            "environment": get_current_environment(),
        }

    def generate_rollout_report(self) -> Dict[str, Any]:
        """Generate comprehensive rollout report."""
        total_time = sum(m.phase_duration_hours for m in self.metrics_history)
        total_processed = len(self.processed_repositories)
        total_failed = len(self.failed_repositories)

        return {
            "rollout_summary": {
                "organization": self.config.organization,
                "strategy": self.config.strategy.value,
                "final_phase": self.current_phase.value,
                "total_duration_hours": total_time,
                "total_repositories_processed": total_processed,
                "total_repositories_failed": total_failed,
                "overall_success_rate": total_processed / (total_processed + total_failed)
                if (total_processed + total_failed) > 0
                else 0,
            },
            "phase_metrics": [m.__dict__ for m in self.metrics_history],
            "failed_repositories": list(self.failed_repositories),
            "recommendations": self._generate_recommendations(),
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on rollout results."""
        recommendations = []

        if not self.metrics_history:
            return ["No rollout data available for recommendations"]

        overall_success_rate = len(self.processed_repositories) / max(
            1, len(self.processed_repositories) + len(self.failed_repositories)
        )

        if overall_success_rate < 0.9:
            recommendations.append(
                "Consider investigating common failure patterns before next rollout"
            )

        avg_phase_duration = sum(m.phase_duration_hours for m in self.metrics_history) / len(
            self.metrics_history
        )
        if avg_phase_duration > self.config.phase_duration_hours * 1.5:
            recommendations.append(
                "Phase durations exceeded expected time - consider optimizing processing"
            )

        if len(self.failed_repositories) > 0:
            recommendations.append("Retry failed repositories with updated configuration")

        if self.current_phase == RolloutPhase.COMPLETE:
            recommendations.append(
                "Rollout completed successfully - monitor for any delayed issues"
            )

        return recommendations

    def _save_state(self) -> None:
        """Save current rollout state to file."""
        state = {
            "organization": self.config.organization,
            "current_phase": self.current_phase.value,
            "processed_repositories": list(self.processed_repositories),
            "failed_repositories": list(self.failed_repositories),
            "metrics_history": [m.__dict__ for m in self.metrics_history],
            "last_updated": datetime.now().isoformat(),
        }

        with open(self.rollout_state_file, "w") as f:
            json.dump(state, f, indent=2, default=str)

    def _load_state(self) -> None:
        """Load rollout state from file if it exists."""
        if not self.rollout_state_file.exists():
            return

        try:
            with open(self.rollout_state_file, "r") as f:
                state = json.load(f)

            self.current_phase = RolloutPhase(state.get("current_phase", "planning"))
            self.processed_repositories = set(state.get("processed_repositories", []))
            self.failed_repositories = set(state.get("failed_repositories", []))

            # Restore metrics history
            for metrics_data in state.get("metrics_history", []):
                metrics = RolloutMetrics(
                    phase=RolloutPhase(metrics_data["phase"]),
                    repositories_processed=metrics_data["repositories_processed"],
                    repositories_successful=metrics_data["repositories_successful"],
                    repositories_failed=metrics_data["repositories_failed"],
                    total_processing_time_minutes=metrics_data["total_processing_time_minutes"],
                    average_response_time_ms=metrics_data["average_response_time_ms"],
                    error_rate=metrics_data["error_rate"],
                    phase_start_time=datetime.fromisoformat(metrics_data["phase_start_time"]),
                    phase_end_time=datetime.fromisoformat(metrics_data["phase_end_time"])
                    if metrics_data.get("phase_end_time")
                    else None,
                    errors=metrics_data.get("errors", []),
                )
                self.metrics_history.append(metrics)

            self.logger.info(
                "Rollout state loaded from file",
                extra={
                    "phase": self.current_phase.value,
                    "processed_count": len(self.processed_repositories),
                },
            )

        except Exception as e:
            self.logger.error(f"Failed to load rollout state: {str(e)}")


def create_default_rollout_config(organization: str, total_repositories: int) -> RolloutConfig:
    """Create a default rollout configuration."""
    return RolloutConfig(
        organization=organization,
        strategy=RolloutStrategy.PERCENTAGE_BASED,
        total_repositories=total_repositories,
        canary_percentage=0.05,  # 5% for canary
        gradual_percentage_steps=[0.15, 0.35, 0.65, 1.0],  # 15%, 35%, 65%, 100%
        phase_duration_hours=12,  # 12 hours per phase
        success_threshold=0.95,
        rollback_threshold=0.85,
        max_concurrent_repositories=25,
    )
