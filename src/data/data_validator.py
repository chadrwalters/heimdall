"""Data validation utilities for unified data processing."""

import logging
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class DataValidator:
    """Validate data integrity and quality."""

    def validate_data_integrity(self, output_file: str = "unified_pilot_data.csv") -> dict[str, Any]:
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

    def save_unified_data(
        self, records: list, output_file: str, incremental: bool
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
