"""Coordinates PR and commit processing with analysis and ticket matching."""

import logging
from typing import Any

from ..analysis.analysis_engine import AnalysisEngine
from ..analysis.context_preparer import ContextPreparer
from ..linear.linear_client import LinearClient
from ..linear.pr_matcher import PRTicketMatcher
from .ai_override_manager import AIOverrideManager
from .record_factory import RecordFactory
from .unified_record import UnifiedRecord

logger = logging.getLogger(__name__)


class ProcessingCoordinator:
    """Coordinate processing of PRs and commits with analysis and ticket matching."""

    def __init__(
        self,
        analysis_engine: AnalysisEngine | None = None,
        linear_client: LinearClient | None = None,
    ):
        self.analysis_engine = analysis_engine
        self.linear_client = linear_client
        self.pr_matcher = PRTicketMatcher(linear_client) if linear_client else None
        self.context_preparer = ContextPreparer()
        self.record_factory = RecordFactory()
        self.ai_override_manager = AIOverrideManager()

    def process_pr_records(self, prs_df) -> list[UnifiedRecord]:
        """Process PR data into unified records."""
        logger.info("Processing PR data")
        records = []

        for _, row in prs_df.iterrows():
            try:
                # Convert row to dict for processing
                pr_data = row.to_dict()

                # Prepare context for analysis
                context = self.context_preparer.prepare_pr_context(pr_data)

                # Get AI analysis if engine is available
                analysis_result = None
                if self.analysis_engine:
                    analysis_result = self.analysis_engine.analyze(context)

                # Match with Linear tickets
                ticket_match = None
                if self.pr_matcher:
                    ticket_match = self.pr_matcher.match_pr(pr_data)

                # Detect AI assistance
                ai_assisted, ai_tool = self._detect_ai_assistance(
                    pr_data, context.metadata.get("author", "")
                )

                # Create unified record
                record = self.record_factory.create_unified_record(
                    data=pr_data,
                    context=context,
                    analysis=analysis_result,
                    ticket_match=ticket_match,
                    ai_assisted=ai_assisted,
                    ai_tool=ai_tool,
                    source_type="PR",
                    context_level="High",
                )

                records.append(record)

            except Exception as e:
                logger.error(f"Error processing PR {row.get('id', 'unknown')}: {e}")
                continue

        logger.info(f"Processed {len(records)} PR records")
        return records

    def process_commit_records(self, commits_df, pr_commit_shas: set[str]) -> list[UnifiedRecord]:
        """Process commit data, removing duplicates that are part of PRs."""
        logger.info("Processing commit data with deduplication")

        records = []
        deduplicated_count = 0

        for _, row in commits_df.iterrows():
            try:
                commit_data = row.to_dict()
                commit_sha = commit_data.get("sha", "")

                # Skip commits that are part of PRs
                if commit_sha in pr_commit_shas:
                    deduplicated_count += 1
                    continue

                # Prepare context for analysis
                context = self.context_preparer.prepare_commit_context(commit_data)

                # Get AI analysis if engine is available
                analysis_result = None
                if self.analysis_engine:
                    analysis_result = self.analysis_engine.analyze(context)

                # Detect AI assistance
                ai_assisted, ai_tool = self._detect_ai_assistance(
                    commit_data, context.metadata.get("author", "")
                )

                # Extract Linear ticket ID if present
                linear_ticket_id = self.context_preparer.extract_linear_ticket_id(commit_data)

                # Create unified record
                record = self.record_factory.create_unified_record(
                    data=commit_data,
                    context=context,
                    analysis=analysis_result,
                    ticket_match=None,
                    ai_assisted=ai_assisted,
                    ai_tool=ai_tool,
                    source_type="Commit",
                    context_level="Low",
                    linear_ticket_id=linear_ticket_id,
                )

                records.append(record)

            except Exception as e:
                logger.error(f"Error processing commit {row.get('sha', 'unknown')}: {e}")
                continue

        logger.info(
            f"Processed {len(records)} commit records, deduplicated {deduplicated_count} PR commits"
        )
        return records

    def _detect_ai_assistance(self, data: dict[str, Any], author: str) -> tuple[bool, str | None]:
        """Detect AI assistance using both pattern detection and overrides."""
        # Check override configuration first
        ai_assisted, ai_tool = self.ai_override_manager.check_ai_override(author)
        if ai_assisted:
            return ai_assisted, ai_tool

        # Fall back to pattern detection
        return self.context_preparer.detect_ai_assistance(data)
