"""Unified data processing pipeline for merging PR and commit data with AI analysis."""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from ..analysis.analysis_engine import AnalysisEngine
from ..analysis.context_preparer import ContextPreparer
from ..config.state_manager import StateManager
from ..linear.linear_client import LinearClient
from ..linear.pr_matcher import PRTicketMatcher
from .developer_metrics import DeveloperMetricsAggregator

logger = logging.getLogger(__name__)


@dataclass
class UnifiedRecord:
    """Unified data model for analysis output."""

    repository: str
    date: str  # ISO format
    author: str
    source_type: str  # 'PR' or 'Commit'
    source_url: str
    context_level: str  # 'High' or 'Low'
    work_type: str  # AI-classified work type
    complexity_score: float
    risk_score: float
    clarity_score: float
    analysis_summary: str
    lines_added: int
    lines_deleted: int
    files_changed: int
    impact_score: float  # Calculated metric
    ai_assisted: bool
    ai_tool_type: str | None
    linear_ticket_id: str | None
    has_linear_ticket: bool
    process_compliant: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for CSV output."""
        return asdict(self)


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
        self.analysis_engine = analysis_engine
        self.linear_client = linear_client
        self.pr_matcher = PRTicketMatcher(linear_client) if linear_client else None
        self.context_preparer = ContextPreparer()
        self.developer_metrics_aggregator = DeveloperMetricsAggregator()

        # Load AI developer overrides
        self.ai_overrides = self._load_ai_overrides()

    def _load_ai_overrides(self) -> dict[str, dict[str, Any]]:
        """Load AI developer override configuration."""
        try:
            ai_config_path = Path("config/ai_developers.json")
            if ai_config_path.exists():
                with open(ai_config_path) as f:
                    config = json.load(f)
                    # Create lookup dict by email and username
                    overrides = {}
                    for dev in config.get("always_ai_developers", []):
                        email = dev.get("email", "").lower()
                        username = dev.get("username", "").lower()
                        if email:
                            overrides[email] = dev
                        if username:
                            overrides[username] = dev
                    return overrides
            return {}
        except Exception as e:
            logger.warning(f"Could not load AI developer overrides: {e}")
            return {}

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
        prs_df = self._load_csv_data(pr_data_file)
        commits_df = self._load_csv_data(commit_data_file)

        if prs_df.empty and commits_df.empty:
            logger.warning("No data to process")
            return 0

        # Apply incremental filtering if enabled
        if incremental:
            prs_df = self._filter_incremental_prs(prs_df)
            commits_df = self._filter_incremental_commits(commits_df)

        logger.info(f"Processing {len(prs_df)} PRs and {len(commits_df)} commits")

        # Process PRs (high-context data)
        pr_records = []
        if not prs_df.empty:
            pr_records = self._process_prs(prs_df)

        # Process commits (low-context data)
        commit_records = []
        if not commits_df.empty:
            commit_records = self._process_commits(commits_df, prs_df)

        # Combine all records
        all_records = pr_records + commit_records

        # Sort by date
        all_records.sort(key=lambda r: r.date)

        # Save to output file
        records_written = self._save_unified_data(all_records, output_file, incremental)

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

    def _load_csv_data(self, filename: str) -> pd.DataFrame:
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

    def _filter_incremental_prs(self, prs_df: pd.DataFrame) -> pd.DataFrame:
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

    def _filter_incremental_commits(self, commits_df: pd.DataFrame) -> pd.DataFrame:
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

    def _process_prs(self, prs_df: pd.DataFrame) -> list[UnifiedRecord]:
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
                record = self._create_unified_record(
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

    def _process_commits(
        self, commits_df: pd.DataFrame, prs_df: pd.DataFrame
    ) -> list[UnifiedRecord]:
        """Process commit data, removing duplicates that are part of PRs."""
        logger.info("Processing commit data with deduplication")

        # Get commit SHAs that are part of PRs for deduplication
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

        records = []
        deduplicated_count = 0

        for _, row in commits_df.iterrows():
            try:
                commit_data = row.to_dict()
                commit_sha = commit_data.get("sha", "")

                # Skip commits that are part of PRs
                if commit_sha in pr_commits:
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
                record = self._create_unified_record(
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
        author_lower = author.lower()
        if author_lower in self.ai_overrides:
            override_config = self.ai_overrides[author_lower]
            return True, override_config.get("ai_tool", "Unknown AI Tool")

        # Fall back to pattern detection
        return self.context_preparer.detect_ai_assistance(data)

    def _create_unified_record(
        self,
        data: dict[str, Any],
        context,
        analysis,
        ticket_match,
        ai_assisted: bool,
        ai_tool: str | None,
        source_type: str,
        context_level: str,
        linear_ticket_id: str | None = None,
    ) -> UnifiedRecord:
        """Create a unified record from processed data."""

        # Extract repository name
        repository = self._extract_repository_name(data)

        # Extract date
        date = self._extract_date(data, source_type)

        # Extract author
        author = self._extract_author(data, context)

        # Get source URL
        source_url = data.get("html_url", data.get("url", ""))

        # Get analysis scores or defaults
        work_type = "Unknown"
        complexity_score = 1.0
        risk_score = 1.0
        clarity_score = 5.0
        analysis_summary = "No analysis available"

        if analysis:
            work_type = analysis.get("work_type", work_type)
            complexity_score = float(analysis.get("complexity_score", complexity_score))
            risk_score = float(analysis.get("risk_score", risk_score))
            clarity_score = float(analysis.get("clarity_score", clarity_score))
            analysis_summary = analysis.get("analysis_summary", analysis_summary)

        # Calculate impact score: 40% complexity + 50% risk + 10% clarity
        impact_score = (0.4 * complexity_score) + (0.5 * risk_score) + (0.1 * clarity_score)

        # Extract file change metrics
        lines_added = context.metadata.get("additions", 0)
        lines_deleted = context.metadata.get("deletions", 0)
        files_changed = context.metadata.get("changed_files", len(context.file_changes))

        # Handle Linear ticket information
        ticket_id = linear_ticket_id
        has_ticket = False
        process_compliant = False

        if ticket_match:
            ticket_id = (
                ticket_match.primary_ticket.identifier if ticket_match.primary_ticket else None
            )
            has_ticket = len(ticket_match.ticket_ids) > 0
            process_compliant = ticket_match.primary_ticket is not None
        elif linear_ticket_id:
            has_ticket = True
            process_compliant = True  # Assume compliance if ticket ID found

        return UnifiedRecord(
            repository=repository,
            date=date,
            author=author,
            source_type=source_type,
            source_url=source_url,
            context_level=context_level,
            work_type=work_type,
            complexity_score=complexity_score,
            risk_score=risk_score,
            clarity_score=clarity_score,
            analysis_summary=analysis_summary,
            lines_added=int(lines_added),
            lines_deleted=int(lines_deleted),
            files_changed=int(files_changed),
            impact_score=round(impact_score, 2),
            ai_assisted=ai_assisted,
            ai_tool_type=ai_tool,
            linear_ticket_id=ticket_id,
            has_linear_ticket=has_ticket,
            process_compliant=process_compliant,
        )

    def _extract_repository_name(self, data: dict[str, Any]) -> str:
        """Extract repository name from data."""
        # Try various fields where repo name might be stored
        repo_url = data.get("repository_url", data.get("repo_url", ""))
        if repo_url:
            return repo_url.split("/")[-1]

        url = data.get("html_url", data.get("url", ""))
        if url and "github.com" in url:
            parts = url.split("/")
            if len(parts) >= 5:
                return parts[4]  # owner/repo format

        return data.get("repository", "unknown")

    def _extract_date(self, data: dict[str, Any], source_type: str) -> str:
        """Extract date in ISO format."""
        if source_type == "PR":
            date_str = data.get("merged_at") or data.get("created_at")
        else:  # Commit
            date_str = data.get("committed_at") or data.get("created_at")

        if date_str:
            try:
                # Parse and convert to ISO format
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                return dt.isoformat()
            except ValueError:
                pass

        # Fallback to current time
        return datetime.now(UTC).isoformat()

    def _extract_author(self, data: dict[str, Any], context) -> str:
        """Extract author email or username."""
        author = context.metadata.get("author", "")
        if not author:
            # Fallback extraction for different data formats
            if "commit" in data:
                author = data["commit"].get("author", {}).get("email", "unknown")
            elif "author_email" in data:  # Flattened CSV format
                author = data["author_email"]
            elif "user" in data:
                author = data.get("user", {}).get("login", "unknown")
            elif "user_login" in data:  # Flattened CSV format
                author = data["user_login"]
            else:
                author = "unknown"

        return author

    def _save_unified_data(
        self, records: list[UnifiedRecord], output_file: str, incremental: bool
    ) -> int:
        """Save unified records to CSV file."""
        if not records:
            logger.warning("No records to save")
            return 0

        # Convert to DataFrame
        df = pd.DataFrame([record.to_dict() for record in records])

        # Ensure proper column order
        column_order = [
            "repository",
            "date",
            "author",
            "source_type",
            "source_url",
            "context_level",
            "work_type",
            "complexity_score",
            "risk_score",
            "clarity_score",
            "analysis_summary",
            "lines_added",
            "lines_deleted",
            "files_changed",
            "impact_score",
            "ai_assisted",
            "ai_tool_type",
            "linear_ticket_id",
            "has_linear_ticket",
            "process_compliant",
        ]

        df = df.reindex(columns=column_order)

        # Save to file
        output_path = Path(output_file)

        if incremental and output_path.exists():
            # Append to existing file
            df.to_csv(output_path, mode="a", header=False, index=False)
            logger.info(f"Appended {len(records)} records to {output_file}")
        else:
            # Create new file
            df.to_csv(output_path, index=False)
            logger.info(f"Created {output_file} with {len(records)} records")

        return len(records)

    def validate_data_integrity(
        self, output_file: str = "unified_pilot_data.csv"
    ) -> dict[str, Any]:
        """Validate the integrity of processed data."""
        try:
            df = pd.read_csv(output_file)

            validation_results = {
                "total_records": len(df),
                "missing_data": {},
                "data_quality": {},
                "summary_stats": {},
            }

            # Check for missing data
            for col in df.columns:
                missing_count = df[col].isnull().sum()
                if missing_count > 0:
                    validation_results["missing_data"][col] = missing_count

            # Data quality checks
            validation_results["data_quality"] = {
                "invalid_scores": {
                    "complexity": len(
                        df[(df["complexity_score"] < 1) | (df["complexity_score"] > 10)]
                    ),
                    "risk": len(df[(df["risk_score"] < 1) | (df["risk_score"] > 10)]),
                    "clarity": len(df[(df["clarity_score"] < 1) | (df["clarity_score"] > 10)]),
                },
                "negative_metrics": {
                    "lines_added": len(df[df["lines_added"] < 0]),
                    "lines_deleted": len(df[df["lines_deleted"] < 0]),
                    "files_changed": len(df[df["files_changed"] < 0]),
                },
            }

            # Summary statistics
            validation_results["summary_stats"] = {
                "source_types": df["source_type"].value_counts().to_dict(),
                "work_types": df["work_type"].value_counts().to_dict(),
                "ai_assisted_rate": df["ai_assisted"].mean(),
                "process_compliance_rate": df["process_compliant"].mean(),
                "avg_impact_score": df["impact_score"].mean(),
            }

            logger.info(f"Data validation complete for {len(df)} records")
            return validation_results

        except Exception as e:
            logger.error(f"Error validating data: {e}")
            return {"error": str(e)}

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
