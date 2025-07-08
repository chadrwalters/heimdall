"""State management for tracking processed records and incremental updates."""

import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class StateManager:
    """Manages the analysis state for incremental processing."""

    def __init__(self, state_file: str = "config/analysis_state.json"):
        """Initialize the StateManager with a state file path."""
        self.state_file = Path(state_file)
        self._ensure_state_file_exists()

    def _ensure_state_file_exists(self) -> None:
        """Ensure the state file exists with default values."""
        if not self.state_file.exists():
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            default_state = {
                "last_run_date": None,
                "processed_pr_ids": [],
                "processed_commit_shas": [],
                "total_records_processed": 0,
            }
            self._save_state(default_state)

    def _load_state(self) -> dict[str, Any]:
        """Load the current state from file."""
        try:
            with open(self.state_file) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading state file: {e}")
            raise

    def _save_state(self, state: dict[str, Any]) -> None:
        """Save the state to file."""
        try:
            with open(self.state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving state file: {e}")
            raise

    def get_last_run_date(self) -> datetime | None:
        """Get the last run date as a datetime object."""
        state = self._load_state()
        if state["last_run_date"]:
            return datetime.fromisoformat(state["last_run_date"].replace("Z", "+00:00"))
        return None

    def get_date_range_for_incremental_update(
        self, default_days: int = 7
    ) -> tuple[datetime, datetime]:
        """Get the date range for incremental update."""
        last_run = self.get_last_run_date()
        end_date = datetime.now(UTC)

        if last_run:
            # Start from last run date minus 1 day for overlap
            start_date = last_run - timedelta(days=1)
        else:
            # First run, get default days of history
            start_date = end_date - timedelta(days=default_days)

        return start_date, end_date

    def get_processed_pr_ids(self) -> set[str]:
        """Get the set of processed PR IDs."""
        state = self._load_state()
        return set(state["processed_pr_ids"])

    def get_processed_commit_shas(self) -> set[str]:
        """Get the set of processed commit SHAs."""
        state = self._load_state()
        return set(state["processed_commit_shas"])

    def is_pr_processed(self, pr_id: str) -> bool:
        """Check if a PR has been processed."""
        return pr_id in self.get_processed_pr_ids()

    def is_commit_processed(self, commit_sha: str) -> bool:
        """Check if a commit has been processed."""
        return commit_sha in self.get_processed_commit_shas()

    def mark_pr_processed(self, pr_id: str) -> None:
        """Mark a single PR as processed."""
        state = self._load_state()
        if pr_id not in state["processed_pr_ids"]:
            state["processed_pr_ids"].append(pr_id)
            self._save_state(state)

    def mark_commit_processed(self, commit_sha: str) -> None:
        """Mark a single commit as processed."""
        state = self._load_state()
        if commit_sha not in state["processed_commit_shas"]:
            state["processed_commit_shas"].append(commit_sha)
            self._save_state(state)

    def update_after_batch_processing(
        self, pr_ids: list[str], commit_shas: list[str], records_processed: int
    ) -> None:
        """Update state after processing a batch of records."""
        state = self._load_state()

        # Update last run date
        state["last_run_date"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")

        # Add new IDs, avoiding duplicates
        existing_prs = set(state["processed_pr_ids"])
        existing_commits = set(state["processed_commit_shas"])

        new_prs = [pr_id for pr_id in pr_ids if pr_id not in existing_prs]
        new_commits = [sha for sha in commit_shas if sha not in existing_commits]

        state["processed_pr_ids"].extend(new_prs)
        state["processed_commit_shas"].extend(new_commits)

        # Update total records
        state["total_records_processed"] += records_processed

        self._save_state(state)

        logger.info(
            f"State updated: {len(new_prs)} new PRs, {len(new_commits)} new commits, "
            f"total processed: {state['total_records_processed']}"
        )

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about the current state."""
        state = self._load_state()
        last_run = self.get_last_run_date()

        return {
            "last_run_date": last_run.isoformat() if last_run else None,
            "total_prs_processed": len(state["processed_pr_ids"]),
            "total_commits_processed": len(state["processed_commit_shas"]),
            "total_records_processed": state["total_records_processed"],
            "days_since_last_run": (datetime.now(UTC) - last_run).days if last_run else None,
        }

    def reset_state(self) -> None:
        """Reset the state to initial values (use with caution)."""
        logger.warning("Resetting analysis state - all processing history will be lost!")
        default_state = {
            "last_run_date": None,
            "processed_pr_ids": [],
            "processed_commit_shas": [],
            "total_records_processed": 0,
        }
        self._save_state(default_state)

    def cleanup_old_records(self, days_to_keep: int = 90) -> None:
        """Remove processed IDs older than specified days (not implemented yet)."""
        # This would require storing timestamps with each ID
        # For now, just log a warning
        logger.warning(
            "cleanup_old_records not implemented - would need timestamps for each record"
        )
