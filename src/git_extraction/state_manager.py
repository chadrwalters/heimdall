"""Repository state management for tracking analysis progress."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class RepoStateManager:
    """Manage repository analysis state."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir

    def get_state_file(self, org: str, repo: str) -> Path:
        """Get the state file path for a repository."""
        return self.cache_dir / "state" / f"{org}_{repo}.json"

    def get_last_analyzed_commit(self, org: str, repo: str) -> Optional[str]:
        """Get the last analyzed commit SHA for a repository.

        Args:
            org: Organization name
            repo: Repository name

        Returns:
            Last analyzed commit SHA or None
        """
        state_file = self.get_state_file(org, repo)

        if not state_file.exists():
            return None

        try:
            with open(state_file, "r") as f:
                state = json.load(f)
            return state.get("last_analyzed_commit")
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Invalid state file format for {org}/{repo}: {e}")
            return None
        except (IOError, OSError) as e:
            logger.warning(f"Failed to read state file for {org}/{repo}: {e}")
            return None

    def update_last_analyzed_commit(self, org: str, repo: str, commit_sha: str) -> None:
        """Update the last analyzed commit SHA for a repository.

        Args:
            org: Organization name
            repo: Repository name
            commit_sha: Commit SHA to store
        """
        state_file = self.get_state_file(org, repo)
        state_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing state or create new
        state = {}
        if state_file.exists():
            try:
                with open(state_file, "r") as f:
                    state = json.load(f)
            except (json.JSONDecodeError, IOError, OSError) as e:
                logger.warning(f"Failed to read existing state for {org}/{repo}: {e}")

        # Update state
        state.update(
            {
                "last_analyzed_commit": commit_sha,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
        )

        # Save state
        try:
            with open(state_file, "w") as f:
                json.dump(state, f, indent=2)
        except (IOError, OSError) as e:
            logger.error(f"Failed to save state for {org}/{repo}: {e}")
            raise
