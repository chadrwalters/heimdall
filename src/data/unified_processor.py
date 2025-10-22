"""Unified data processing pipeline for merging PR and commit data with AI analysis."""

import logging
from typing import Any

from ..analysis.analysis_engine import AnalysisEngine
from ..config.state_manager import StateManager
from ..linear.linear_client import LinearClient
from .data_loader import DataLoader
from .data_validator import DataValidator
from .developer_metrics import DeveloperMetricsAggregator
from .processing_coordinator import ProcessingCoordinator

logger = logging.getLogger(__name__)


class UnifiedDataProcessor:
    """Process and unify PR and commit data with AI analysis."""

    def __init__(
        self,
        state_manager: StateManager | None = None,
        analysis_engine: AnalysisEngine | None = None,
        linear_client: LinearClient | None = None,
    ):
        """Initialize the processor with required components."""
        self.state_manager = state_manager or StateManager()
        self.data_loader = DataLoader(self.state_manager)
        self.processing_coordinator = ProcessingCoordinator(analysis_engine, linear_client)
        self.data_validator = DataValidator()
        self.developer_metrics_aggregator = DeveloperMetricsAggregator()

    def process_unified_data(
        self,
        pr_data_file: str = "org_prs.csv",
        commit_data_file: str = "org_commits.csv",
        output_file: str = "unified_pilot_data.csv",
        incremental: bool = True,
    ) -> int:
        """Process and unify all data sources."""
        logger.info("Starting unified data processing")

        # Load data
        prs_df = self.data_loader.load_csv_data(pr_data_file)
        commits_df = self.data_loader.load_csv_data(commit_data_file)

        if prs_df.empty and commits_df.empty:
            logger.warning("No data to process")
            return 0

        # Apply incremental filtering if enabled
        if incremental:
            prs_df = self.data_loader.filter_incremental_prs(prs_df)
            commits_df = self.data_loader.filter_incremental_commits(commits_df)

        logger.info(f"Processing {len(prs_df)} PRs and {len(commits_df)} commits")

        # Get PR commit SHAs for deduplication
        pr_commit_shas = self.data_loader.get_pr_commit_shas(prs_df)

        # Process PRs (high-context data)
        pr_records = []
        if not prs_df.empty:
            pr_records = self.processing_coordinator.process_pr_records(prs_df)

        # Process commits (low-context data)
        commit_records = []
        if not commits_df.empty:
            commit_records = self.processing_coordinator.process_commit_records(
                commits_df, pr_commit_shas
            )

        # Combine all records
        all_records = pr_records + commit_records

        # Sort by date
        all_records.sort(key=lambda r: r.date)

        # Save to output file
        records_written = self.data_validator.save_unified_data(
            all_records, output_file, incremental
        )

        # Update state
        if incremental:
            processed_prs = [r.source_url.split("/")[-1] for r in pr_records]
            processed_commits = [r.source_url.split("/")[-1] for r in commit_records]
            self.state_manager.update_after_batch_processing(
                processed_prs, processed_commits, len(all_records)
            )

        logger.info(f"Processing complete. {records_written} total records written.")

        # Generate developer metrics after unified data processing
        if records_written > 0 and all_records:
            try:
                metrics_written = self.developer_metrics_aggregator.aggregate_developer_metrics(
                    unified_data_file=output_file, incremental=incremental
                )
                logger.info(f"Generated {metrics_written} developer metrics records")
            except Exception as e:
                logger.error(f"Error generating developer metrics: {e}")

        return records_written

    def process_commits(self, commit_file: str, skip_processed: bool = True) -> list:
        """Process commits for compatibility with existing pipeline."""
        commits_df = self.data_loader.load_csv_data(commit_file)
        if commits_df.empty:
            return []

        if skip_processed:
            commits_df = self.data_loader.filter_incremental_commits(commits_df)

        return self.processing_coordinator.process_commit_records(commits_df, set())

    def validate_data_integrity(
        self, output_file: str = "unified_pilot_data.csv"
    ) -> dict[str, Any]:
        """Validate the integrity of processed data."""
        return self.data_validator.validate_data_integrity(output_file)

    def save_unified_data(self, records: list, output_file: str) -> None:
        """Save unified data to CSV."""
        self.data_validator.save_unified_data(records, output_file, incremental=False)

    def generate_developer_metrics(
        self,
        unified_data_file: str = "unified_pilot_data.csv",
        output_file: str = "developer_metrics.csv",
        incremental: bool = True,
    ) -> int:
        """Generate developer metrics from unified data."""
        return self.developer_metrics_aggregator.aggregate_developer_metrics(
            unified_data_file, output_file, incremental
        )

    def get_ai_usage_breakdown(
        self, unified_data_file: str = "unified_pilot_data.csv"
    ) -> dict[str, dict[str, Any]]:
        """Get AI usage breakdown by developer and tool type."""
        return self.developer_metrics_aggregator.get_ai_usage_breakdown(unified_data_file)

    def identify_developer_trends(
        self, developer_metrics_file: str = "developer_metrics.csv", weeks_to_analyze: int = 4
    ) -> dict[str, dict[str, Any]]:
        """Identify trends in developer metrics over time."""
        return self.developer_metrics_aggregator.identify_trends(
            developer_metrics_file, weeks_to_analyze
        )

    def validate_developer_metrics(
        self, developer_metrics_file: str = "developer_metrics.csv"
    ) -> dict[str, Any]:
        """Validate developer metrics data integrity."""
        return self.developer_metrics_aggregator.validate_developer_metrics(developer_metrics_file)
