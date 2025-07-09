"""Developer metrics aggregation functionality for weekly developer performance tracking."""

import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class DeveloperMetrics:
    """Developer metrics model as specified in the PRD."""

    author: str
    period: str  # e.g., "2025-W01" for week 1
    commit_frequency: float  # commits per day average
    pr_frequency: float  # PRs per week
    ai_usage_rate: float  # percentage of AI-assisted work
    avg_pr_size: float  # average files changed per PR
    avg_complexity: float  # average complexity score
    avg_impact_score: float  # average impact score

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for CSV output."""
        return asdict(self)


class DeveloperMetricsAggregator:
    """Aggregate weekly developer metrics from unified data."""

    def __init__(self):
        """Initialize the aggregator."""
        self.logger = logging.getLogger(__name__)

    def aggregate_developer_metrics(
        self,
        unified_data_file: str = "unified_pilot_data.csv",
        output_file: str = "developer_metrics.csv",
        incremental: bool = True,
    ) -> int:
        """Aggregate developer metrics from unified data."""
        self.logger.info("Starting developer metrics aggregation")

        # Load unified data
        df = self._load_unified_data(unified_data_file)
        if df.empty:
            self.logger.warning("No unified data to process for developer metrics")
            return 0

        # Group data by author and week
        grouped_data = self._group_by_author_and_week(df)

        # Calculate metrics for each group
        developer_metrics = []
        for (author, week_period), group_df in grouped_data:
            try:
                metrics = self._calculate_developer_metrics(author, week_period, group_df)
                developer_metrics.append(metrics)
            except Exception as e:
                self.logger.error(f"Error calculating metrics for {author} in {week_period}: {e}")
                continue

        # Save metrics to output file
        records_written = self._save_developer_metrics(developer_metrics, output_file, incremental)

        self.logger.info(
            f"Developer metrics aggregation complete. {records_written} records written."
        )
        return records_written

    def _load_unified_data(self, filename: str) -> pd.DataFrame:
        """Load unified data with error handling."""
        try:
            file_path = Path(filename)
            if not file_path.exists():
                self.logger.warning(f"File {filename} does not exist")
                return pd.DataFrame()

            df = pd.read_csv(file_path)
            self.logger.info(f"Loaded {len(df)} records from {filename}")

            # Ensure date column is datetime
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])

            return df
        except Exception as e:
            self.logger.error(f"Error loading {filename}: {e}")
            return pd.DataFrame()

    def _group_by_author_and_week(self, df: pd.DataFrame) -> pd.core.groupby.DataFrameGroupBy:
        """Group unified data by author and week."""
        # Add week period column in YYYY-Wnn format
        df["week_period"] = df["date"].dt.strftime("%Y-W%U")

        # Group by author and week period
        grouped = df.groupby(["author", "week_period"])

        self.logger.info(f"Grouped data into {len(grouped)} author-week combinations")
        return grouped

    def _calculate_developer_metrics(
        self, author: str, week_period: str, group_df: pd.DataFrame
    ) -> DeveloperMetrics:
        """Calculate metrics for a single author-week combination."""

        # Calculate commit frequency (commits per day average)
        # Assuming 7 days per week, count unique commit source types
        commit_count = len(group_df[group_df["source_type"] == "Commit"])
        commit_frequency = commit_count / 7.0  # commits per day

        # Calculate PR frequency (PRs per week)
        pr_count = len(group_df[group_df["source_type"] == "PR"])
        pr_frequency = float(pr_count)  # already per week

        # Calculate AI usage rate (percentage of AI-assisted work)
        total_work = len(group_df)
        ai_assisted_work = len(group_df[group_df["ai_assisted"] == True])
        ai_usage_rate = (ai_assisted_work / total_work * 100) if total_work > 0 else 0.0

        # Calculate average PR size (average files changed per PR)
        pr_data = group_df[group_df["source_type"] == "PR"]
        avg_pr_size = pr_data["files_changed"].mean() if not pr_data.empty else 0.0

        # Calculate average complexity score
        avg_complexity = group_df["complexity_score"].mean()

        # Calculate average impact score
        avg_impact_score = group_df["impact_score"].mean()

        return DeveloperMetrics(
            author=author,
            period=week_period,
            commit_frequency=round(commit_frequency, 3),
            pr_frequency=round(pr_frequency, 1),
            ai_usage_rate=round(ai_usage_rate, 1),
            avg_pr_size=round(avg_pr_size, 1),
            avg_complexity=round(avg_complexity, 2),
            avg_impact_score=round(avg_impact_score, 2),
        )

    def _save_developer_metrics(
        self, metrics: list[DeveloperMetrics], output_file: str, incremental: bool
    ) -> int:
        """Save developer metrics to CSV file."""
        if not metrics:
            self.logger.warning("No developer metrics to save")
            return 0

        # Convert to DataFrame
        df = pd.DataFrame([metric.to_dict() for metric in metrics])

        # Ensure proper column order
        column_order = [
            "author",
            "period",
            "commit_frequency",
            "pr_frequency",
            "ai_usage_rate",
            "avg_pr_size",
            "avg_complexity",
            "avg_impact_score",
        ]

        df = df.reindex(columns=column_order)

        # Save to file
        output_path = Path(output_file)

        if incremental and output_path.exists():
            # Load existing data to check for duplicates
            existing_df = pd.read_csv(output_path)
            # Remove duplicates based on author and period
            existing_keys = set(zip(existing_df["author"], existing_df["period"], strict=False))
            new_metrics = [m for m in metrics if (m.author, m.period) not in existing_keys]

            if new_metrics:
                new_df = pd.DataFrame([metric.to_dict() for metric in new_metrics])
                new_df = new_df.reindex(columns=column_order)
                new_df.to_csv(output_path, mode="a", header=False, index=False)
                self.logger.info(
                    f"Appended {len(new_metrics)} new developer metrics to {output_file}"
                )
                return len(new_metrics)
            else:
                self.logger.info("No new developer metrics to append")
                return 0
        else:
            # Create new file
            df.to_csv(output_path, index=False)
            self.logger.info(f"Created {output_file} with {len(metrics)} developer metrics")
            return len(metrics)

    def get_ai_usage_breakdown(
        self, unified_data_file: str = "unified_pilot_data.csv"
    ) -> dict[str, dict[str, float]]:
        """Get breakdown of AI usage by tool type for each developer."""
        df = self._load_unified_data(unified_data_file)
        if df.empty:
            return {}

        # Filter AI-assisted work
        ai_work = df[df["ai_assisted"] == True]

        breakdown = {}
        for author in df["author"].unique():
            author_work = df[df["author"] == author]
            author_ai_work = ai_work[ai_work["author"] == author]

            if len(author_work) == 0:
                continue

            breakdown[author] = {
                "total_work": len(author_work),
                "ai_assisted": len(author_ai_work),
                "ai_percentage": round(len(author_ai_work) / len(author_work) * 100, 1),
                "tools": {},
            }

            # Breakdown by tool type
            if not author_ai_work.empty:
                tool_counts = author_ai_work["ai_tool_type"].value_counts().to_dict()
                total_ai = len(author_ai_work)
                for tool, count in tool_counts.items():
                    if pd.notna(tool):  # Skip NaN values
                        breakdown[author]["tools"][tool] = {
                            "count": count,
                            "percentage": round(count / total_ai * 100, 1),
                        }

        return breakdown

    def identify_trends(
        self, developer_metrics_file: str = "developer_metrics.csv", weeks_to_analyze: int = 4
    ) -> dict[str, dict[str, Any]]:
        """Identify trends over time for each developer."""
        try:
            df = pd.read_csv(developer_metrics_file)
            if df.empty:
                return {}

            # Convert period to datetime for sorting
            df["period_date"] = pd.to_datetime(df["period"] + "-1", format="%Y-W%U-%w")
            df = df.sort_values(["author", "period_date"])

            trends = {}
            for author in df["author"].unique():
                author_data = df[df["author"] == author].tail(weeks_to_analyze)

                if len(author_data) < 2:
                    continue  # Need at least 2 data points for trend

                trends[author] = {"weeks_analyzed": len(author_data), "metrics_trends": {}}

                # Calculate trends for key metrics
                metrics_to_analyze = [
                    "commit_frequency",
                    "pr_frequency",
                    "ai_usage_rate",
                    "avg_pr_size",
                    "avg_complexity",
                    "avg_impact_score",
                ]

                for metric in metrics_to_analyze:
                    values = author_data[metric].values
                    if len(values) >= 2:
                        # Simple linear trend calculation
                        x = np.arange(len(values))
                        slope, _ = np.polyfit(x, values, 1)

                        trends[author]["metrics_trends"][metric] = {
                            "slope": round(slope, 4),
                            "direction": "increasing"
                            if slope > 0.01
                            else "decreasing"
                            if slope < -0.01
                            else "stable",
                            "current_value": round(values[-1], 2),
                            "previous_value": round(values[-2], 2),
                            "change": round(values[-1] - values[-2], 2),
                        }

            return trends

        except Exception as e:
            self.logger.error(f"Error identifying trends: {e}")
            return {}

    def validate_developer_metrics(
        self, developer_metrics_file: str = "developer_metrics.csv"
    ) -> dict[str, Any]:
        """Validate the integrity of developer metrics data."""
        try:
            df = pd.read_csv(developer_metrics_file)

            validation_results = {
                "total_records": len(df),
                "unique_developers": len(df["author"].unique()),
                "date_range": {},
                "data_quality": {},
                "summary_stats": {},
            }

            # Date range analysis
            if not df.empty:
                validation_results["date_range"] = {
                    "earliest_period": df["period"].min(),
                    "latest_period": df["period"].max(),
                    "total_periods": len(df["period"].unique()),
                }

            # Data quality checks
            validation_results["data_quality"] = {
                "negative_values": {
                    "commit_frequency": len(df[df["commit_frequency"] < 0]),
                    "pr_frequency": len(df[df["pr_frequency"] < 0]),
                    "ai_usage_rate": len(df[df["ai_usage_rate"] < 0]),
                    "avg_pr_size": len(df[df["avg_pr_size"] < 0]),
                },
                "invalid_percentages": len(df[df["ai_usage_rate"] > 100]),
                "missing_data": df.isnull().sum().to_dict(),
            }

            # Summary statistics
            numeric_columns = [
                "commit_frequency",
                "pr_frequency",
                "ai_usage_rate",
                "avg_pr_size",
                "avg_complexity",
                "avg_impact_score",
            ]
            validation_results["summary_stats"] = {
                col: {
                    "mean": round(df[col].mean(), 2),
                    "median": round(df[col].median(), 2),
                    "std": round(df[col].std(), 2),
                    "min": round(df[col].min(), 2),
                    "max": round(df[col].max(), 2),
                }
                for col in numeric_columns
                if col in df.columns
            }

            self.logger.info(f"Developer metrics validation complete for {len(df)} records")
            return validation_results

        except Exception as e:
            self.logger.error(f"Error validating developer metrics: {e}")
            return {"error": str(e)}
