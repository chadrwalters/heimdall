"""Data loading and filtering for unified processing."""

import json
import logging
from pathlib import Path

import pandas as pd

from ..config.state_manager import StateManager

logger = logging.getLogger(__name__)


class DataLoader:
    """Handle data loading and incremental filtering."""

    def __init__(self, state_manager: StateManager | None = None):
        self.state_manager = state_manager or StateManager()

    def load_csv_data(self, filename: str) -> pd.DataFrame:
        """Load CSV data with error handling."""
        try:
            file_path = Path(filename)
            if not file_path.exists():
                logger.warning(f"File {filename} does not exist")
                return pd.DataFrame()

            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} records from {filename}")
            return df
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            return pd.DataFrame()

    def filter_incremental_prs(self, prs_df: pd.DataFrame) -> pd.DataFrame:
        """Filter PRs for incremental processing."""
        if prs_df.empty:
            return prs_df

        processed_ids = self.state_manager.get_processed_pr_ids()

        # Filter based on PR ID or number
        if "id" in prs_df.columns:
            mask = ~prs_df["id"].astype(str).isin(processed_ids)
        elif "number" in prs_df.columns:
            mask = ~prs_df["number"].astype(str).isin(processed_ids)
        else:
            logger.warning("Cannot filter PRs incrementally - no ID column found")
            return prs_df

        filtered_df = prs_df[mask]
        logger.info(f"Incremental filter: {len(filtered_df)} new PRs (was {len(prs_df)})")
        return filtered_df

    def filter_incremental_commits(self, commits_df: pd.DataFrame) -> pd.DataFrame:
        """Filter commits for incremental processing."""
        if commits_df.empty:
            return commits_df

        processed_shas = self.state_manager.get_processed_commit_shas()

        if "sha" in commits_df.columns:
            mask = ~commits_df["sha"].isin(processed_shas)
        else:
            logger.warning("Cannot filter commits incrementally - no SHA column found")
            return commits_df

        filtered_df = commits_df[mask]
        logger.info(f"Incremental filter: {len(filtered_df)} new commits (was {len(commits_df)})")
        return filtered_df

    def get_pr_commit_shas(self, prs_df: pd.DataFrame) -> set[str]:
        """Extract commit SHAs that are part of PRs for deduplication."""
        pr_commits = set()
        if not prs_df.empty and "commits" in prs_df.columns:
            for commits_data in prs_df["commits"].dropna():
                if isinstance(commits_data, str):
                    try:
                        commit_list = json.loads(commits_data)
                        pr_commits.update(
                            commit["sha"] for commit in commit_list if "sha" in commit
                        )
                    except json.JSONDecodeError:
                        continue
        return pr_commits
