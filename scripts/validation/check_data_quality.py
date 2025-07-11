#!/usr/bin/env python3
"""
North Star Metrics - Data Quality Verification Script

Comprehensive data quality checks for ensuring data integrity,
completeness, and consistency in the North Star Metrics framework.
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Set up logging for data quality checks."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger(__name__)


def load_data(file_path: str) -> pd.DataFrame:
    """Load data file for quality verification."""
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        raise ValueError(f"Failed to load data from {file_path}: {e}")


def check_completeness(df: pd.DataFrame) -> Dict[str, Any]:
    """Check data completeness (missing values)."""
    logger = logging.getLogger(__name__)
    logger.info("Checking data completeness...")

    completeness_results = {
        "total_records": len(df),
        "column_completeness": {},
        "critical_missing": [],
        "warnings": [],
        "overall_completeness": 0.0,
    }

    # Critical columns that must be complete
    critical_columns = [
        "repository",
        "source_id",
        "author",
        "date",
        "work_type",
        "complexity_score",
        "risk_score",
        "clarity_score",
        "impact_score",
    ]

    # Calculate completeness for each column
    total_completeness = 0
    for col in df.columns:
        non_null_count = df[col].notna().sum()
        completeness_pct = (non_null_count / len(df)) * 100
        completeness_results["column_completeness"][col] = {
            "non_null_count": int(non_null_count),
            "completeness_percentage": round(completeness_pct, 2),
        }
        total_completeness += completeness_pct

        # Check critical columns
        if col in critical_columns and completeness_pct < 95:
            completeness_results["critical_missing"].append(
                {
                    "column": col,
                    "completeness": completeness_pct,
                    "missing_count": len(df) - non_null_count,
                }
            )

        # Check for warnings
        elif completeness_pct < 90:
            completeness_results["warnings"].append(
                {
                    "column": col,
                    "completeness": completeness_pct,
                    "missing_count": len(df) - non_null_count,
                }
            )

    completeness_results["overall_completeness"] = round(total_completeness / len(df.columns), 2)

    return completeness_results


def check_uniqueness(df: pd.DataFrame) -> Dict[str, Any]:
    """Check for duplicate records."""
    logger = logging.getLogger(__name__)
    logger.info("Checking data uniqueness...")

    uniqueness_results = {
        "total_records": len(df),
        "duplicate_analysis": {},
        "duplicate_records": [],
        "uniqueness_score": 0.0,
    }

    # Check for duplicates based on key columns
    key_columns = ["repository", "source_id", "author", "date"]
    available_keys = [col for col in key_columns if col in df.columns]

    if available_keys:
        # Check for exact duplicates
        duplicates = df.duplicated(subset=available_keys, keep=False)
        duplicate_count = duplicates.sum()

        uniqueness_results["duplicate_analysis"] = {
            "key_columns": available_keys,
            "duplicate_count": int(duplicate_count),
            "unique_count": len(df) - duplicate_count,
            "uniqueness_percentage": round(((len(df) - duplicate_count) / len(df)) * 100, 2),
        }

        # Get duplicate record details
        if duplicate_count > 0:
            duplicate_records = df[duplicates]
            for idx, row in duplicate_records.iterrows():
                uniqueness_results["duplicate_records"].append(
                    {
                        "index": int(idx),
                        "source_id": row.get("source_id", "unknown"),
                        "repository": row.get("repository", "unknown"),
                        "author": row.get("author", "unknown"),
                        "date": row.get("date", "unknown"),
                    }
                )

        uniqueness_results["uniqueness_score"] = round(
            ((len(df) - duplicate_count) / len(df)) * 100, 2
        )

    return uniqueness_results


def check_validity(df: pd.DataFrame) -> Dict[str, Any]:
    """Check data validity (ranges, formats, business rules)."""
    logger = logging.getLogger(__name__)
    logger.info("Checking data validity...")

    validity_results = {
        "total_records": len(df),
        "score_validation": {},
        "date_validation": {},
        "email_validation": {},
        "invalid_records": [],
        "validity_score": 0.0,
    }

    invalid_count = 0

    # Score validation (should be 1-10)
    score_columns = ["complexity_score", "risk_score", "clarity_score", "impact_score"]
    for score_col in score_columns:
        if score_col in df.columns:
            invalid_scores = df[(df[score_col] < 1) | (df[score_col] > 10)]
            validity_results["score_validation"][score_col] = {
                "total_records": len(df),
                "valid_records": len(df) - len(invalid_scores),
                "invalid_records": len(invalid_scores),
                "validity_percentage": round(((len(df) - len(invalid_scores)) / len(df)) * 100, 2),
            }

            # Add invalid records to the list
            for idx, row in invalid_scores.iterrows():
                validity_results["invalid_records"].append(
                    {
                        "index": int(idx),
                        "source_id": row.get("source_id", "unknown"),
                        "validation_type": "invalid_score",
                        "column": score_col,
                        "value": row[score_col],
                        "expected_range": "1-10",
                    }
                )
                invalid_count += 1

    # Date validation
    if "date" in df.columns:
        try:
            df["date_parsed"] = pd.to_datetime(df["date"], errors="coerce")
            invalid_dates = df[df["date_parsed"].isna() & df["date"].notna()]
            future_dates = df[df["date_parsed"] > datetime.now()]

            validity_results["date_validation"] = {
                "total_records": len(df),
                "valid_dates": len(df) - len(invalid_dates) - len(future_dates),
                "invalid_dates": len(invalid_dates),
                "future_dates": len(future_dates),
                "validity_percentage": round(
                    ((len(df) - len(invalid_dates) - len(future_dates)) / len(df)) * 100, 2
                ),
            }

            # Add invalid dates
            for idx, row in invalid_dates.iterrows():
                validity_results["invalid_records"].append(
                    {
                        "index": int(idx),
                        "source_id": row.get("source_id", "unknown"),
                        "validation_type": "invalid_date",
                        "column": "date",
                        "value": row["date"],
                        "expected_format": "ISO datetime",
                    }
                )
                invalid_count += 1

            # Add future dates
            for idx, row in future_dates.iterrows():
                validity_results["invalid_records"].append(
                    {
                        "index": int(idx),
                        "source_id": row.get("source_id", "unknown"),
                        "validation_type": "future_date",
                        "column": "date",
                        "value": row["date"],
                        "issue": "Date is in the future",
                    }
                )
                invalid_count += 1

        except Exception as e:
            logger.warning(f"Date validation failed: {e}")

    # Email validation (basic check)
    if "author" in df.columns:
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        valid_emails = df["author"].str.match(email_pattern, na=False)
        invalid_emails = df[~valid_emails & df["author"].notna()]

        validity_results["email_validation"] = {
            "total_records": len(df),
            "valid_emails": valid_emails.sum(),
            "invalid_emails": len(invalid_emails),
            "validity_percentage": round((valid_emails.sum() / len(df)) * 100, 2),
        }

        # Add invalid emails (limit to first 10)
        for idx, row in invalid_emails.head(10).iterrows():
            validity_results["invalid_records"].append(
                {
                    "index": int(idx),
                    "source_id": row.get("source_id", "unknown"),
                    "validation_type": "invalid_email",
                    "column": "author",
                    "value": row["author"],
                    "expected_format": "valid email address",
                }
            )
            invalid_count += 1

    # Calculate overall validity score
    total_checks = len(df) * (len(score_columns) + 2)  # scores + date + email
    valid_checks = total_checks - invalid_count
    validity_results["validity_score"] = round((valid_checks / total_checks) * 100, 2)

    return validity_results


def check_consistency(df: pd.DataFrame) -> Dict[str, Any]:
    """Check data consistency (logical relationships)."""
    logger = logging.getLogger(__name__)
    logger.info("Checking data consistency...")

    consistency_results = {
        "total_records": len(df),
        "impact_score_consistency": {},
        "work_type_consistency": {},
        "ai_detection_consistency": {},
        "inconsistent_records": [],
        "consistency_score": 0.0,
    }

    inconsistency_count = 0

    # Impact score consistency (formula: 40% complexity + 50% risk + 10% clarity)
    if all(
        col in df.columns
        for col in ["complexity_score", "risk_score", "clarity_score", "impact_score"]
    ):
        df["calculated_impact"] = (
            df["complexity_score"] * 0.4 + df["risk_score"] * 0.5 + df["clarity_score"] * 0.1
        )

        # Allow small floating point differences (0.1)
        impact_inconsistent = abs(df["impact_score"] - df["calculated_impact"]) > 0.1
        inconsistent_impact = df[impact_inconsistent]

        consistency_results["impact_score_consistency"] = {
            "total_records": len(df),
            "consistent_records": len(df) - len(inconsistent_impact),
            "inconsistent_records": len(inconsistent_impact),
            "consistency_percentage": round(
                ((len(df) - len(inconsistent_impact)) / len(df)) * 100, 2
            ),
        }

        # Add inconsistent records
        for idx, row in inconsistent_impact.head(10).iterrows():
            consistency_results["inconsistent_records"].append(
                {
                    "index": int(idx),
                    "source_id": row.get("source_id", "unknown"),
                    "consistency_type": "impact_score_calculation",
                    "actual_impact": round(row["impact_score"], 2),
                    "calculated_impact": round(row["calculated_impact"], 2),
                    "difference": round(abs(row["impact_score"] - row["calculated_impact"]), 2),
                }
            )
            inconsistency_count += 1

    # Work type vs complexity consistency
    if all(col in df.columns for col in ["work_type", "complexity_score"]):
        # Check for suspicious patterns
        suspicious_patterns = [
            ("Chore", "high_complexity", df["work_type"] == "Chore", df["complexity_score"] > 8),
            (
                "New Feature",
                "low_complexity",
                df["work_type"] == "New Feature",
                df["complexity_score"] < 3,
            ),
            (
                "Bug Fix",
                "very_high_complexity",
                df["work_type"] == "Bug Fix",
                df["complexity_score"] > 9,
            ),
        ]

        consistency_results["work_type_consistency"] = {
            "total_records": len(df),
            "suspicious_patterns": {},
        }

        for work_type, pattern_name, type_filter, complexity_filter in suspicious_patterns:
            suspicious = df[type_filter & complexity_filter]
            consistency_results["work_type_consistency"]["suspicious_patterns"][pattern_name] = {
                "count": len(suspicious),
                "percentage": round((len(suspicious) / len(df[type_filter])) * 100, 2)
                if len(df[type_filter]) > 0
                else 0,
            }

            # Add to inconsistent records
            for idx, row in suspicious.head(5).iterrows():
                consistency_results["inconsistent_records"].append(
                    {
                        "index": int(idx),
                        "source_id": row.get("source_id", "unknown"),
                        "consistency_type": "work_type_complexity",
                        "work_type": row["work_type"],
                        "complexity_score": row["complexity_score"],
                        "pattern": pattern_name,
                    }
                )
                inconsistency_count += 1

    # AI detection consistency
    if all(col in df.columns for col in ["ai_assisted", "ai_tool_type"]):
        ai_assisted_with_no_tool = df[
            (df["ai_assisted"] == True) & (df["ai_tool_type"].isna() | (df["ai_tool_type"] == ""))
        ]
        no_ai_with_tool = df[
            (df["ai_assisted"] == False) & (df["ai_tool_type"].notna() & (df["ai_tool_type"] != ""))
        ]

        consistency_results["ai_detection_consistency"] = {
            "total_records": len(df),
            "ai_assisted_no_tool": len(ai_assisted_with_no_tool),
            "no_ai_with_tool": len(no_ai_with_tool),
            "consistency_percentage": round(
                ((len(df) - len(ai_assisted_with_no_tool) - len(no_ai_with_tool)) / len(df)) * 100,
                2,
            ),
        }

        # Add inconsistent AI records
        for idx, row in ai_assisted_with_no_tool.head(5).iterrows():
            consistency_results["inconsistent_records"].append(
                {
                    "index": int(idx),
                    "source_id": row.get("source_id", "unknown"),
                    "consistency_type": "ai_detection",
                    "issue": "AI assisted but no tool specified",
                    "ai_assisted": row["ai_assisted"],
                    "ai_tool_type": row.get("ai_tool_type", "None"),
                }
            )
            inconsistency_count += 1

    # Calculate overall consistency score
    total_records = len(df)
    consistent_records = total_records - min(inconsistency_count, total_records)
    consistency_results["consistency_score"] = (
        round((consistent_records / total_records) * 100, 2) if total_records > 0 else 100
    )

    return consistency_results


def check_timeliness(df: pd.DataFrame) -> Dict[str, Any]:
    """Check data timeliness (recency and appropriate date ranges)."""
    logger = logging.getLogger(__name__)
    logger.info("Checking data timeliness...")

    timeliness_results = {
        "total_records": len(df),
        "date_range_analysis": {},
        "recency_analysis": {},
        "timeliness_score": 0.0,
    }

    if "date" in df.columns:
        try:
            df["date_parsed"] = pd.to_datetime(df["date"], errors="coerce")
            valid_dates = df[df["date_parsed"].notna()]

            if len(valid_dates) > 0:
                min_date = valid_dates["date_parsed"].min()
                max_date = valid_dates["date_parsed"].max()
                now = datetime.now()

                timeliness_results["date_range_analysis"] = {
                    "earliest_record": min_date.isoformat(),
                    "latest_record": max_date.isoformat(),
                    "time_span_days": (max_date - min_date).days,
                    "days_since_latest": (now - max_date).days,
                    "total_valid_dates": len(valid_dates),
                }

                # Recency analysis
                days_since_latest = (now - max_date).days

                # Recent data (within last 7 days)
                recent_cutoff = now - timedelta(days=7)
                recent_records = valid_dates[valid_dates["date_parsed"] >= recent_cutoff]

                # Old data (older than 1 year)
                old_cutoff = now - timedelta(days=365)
                old_records = valid_dates[valid_dates["date_parsed"] < old_cutoff]

                timeliness_results["recency_analysis"] = {
                    "recent_records_7d": len(recent_records),
                    "recent_percentage_7d": round(
                        (len(recent_records) / len(valid_dates)) * 100, 2
                    ),
                    "old_records_1y": len(old_records),
                    "old_percentage_1y": round((len(old_records) / len(valid_dates)) * 100, 2),
                    "days_since_latest_record": days_since_latest,
                }

                # Calculate timeliness score
                # Score based on how recent the latest data is
                if days_since_latest <= 1:
                    timeliness_score = 100
                elif days_since_latest <= 7:
                    timeliness_score = 90
                elif days_since_latest <= 30:
                    timeliness_score = 70
                elif days_since_latest <= 90:
                    timeliness_score = 50
                else:
                    timeliness_score = 25

                timeliness_results["timeliness_score"] = timeliness_score

        except Exception as e:
            logger.warning(f"Timeliness validation failed: {e}")
            timeliness_results["timeliness_score"] = 0

    return timeliness_results


def generate_quality_report(
    df: pd.DataFrame,
    completeness: Dict[str, Any],
    uniqueness: Dict[str, Any],
    validity: Dict[str, Any],
    consistency: Dict[str, Any],
    timeliness: Dict[str, Any],
    output_file: str,
) -> None:
    """Generate comprehensive data quality report."""

    # Calculate overall quality score
    scores = [
        completeness.get("overall_completeness", 0),
        uniqueness.get("uniqueness_score", 0),
        validity.get("validity_score", 0),
        consistency.get("consistency_score", 0),
        timeliness.get("timeliness_score", 0),
    ]

    overall_score = sum(scores) / len(scores)

    report = {
        "quality_metadata": {
            "timestamp": datetime.now().isoformat(),
            "data_file": output_file,
            "total_records": len(df),
            "overall_quality_score": round(overall_score, 2),
        },
        "completeness_check": completeness,
        "uniqueness_check": uniqueness,
        "validity_check": validity,
        "consistency_check": consistency,
        "timeliness_check": timeliness,
        "quality_summary": {
            "overall_score": round(overall_score, 2),
            "individual_scores": {
                "completeness": round(completeness.get("overall_completeness", 0), 2),
                "uniqueness": round(uniqueness.get("uniqueness_score", 0), 2),
                "validity": round(validity.get("validity_score", 0), 2),
                "consistency": round(consistency.get("consistency_score", 0), 2),
                "timeliness": round(timeliness.get("timeliness_score", 0), 2),
            },
            "quality_grade": get_quality_grade(overall_score),
            "critical_issues": count_critical_issues(
                completeness, uniqueness, validity, consistency, timeliness
            ),
            "recommendations": generate_recommendations(
                completeness, uniqueness, validity, consistency, timeliness
            ),
        },
    }

    # Save report
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"Data quality report saved to: {output_file}")


def get_quality_grade(score: float) -> str:
    """Get quality grade based on score."""
    if score >= 95:
        return "A+ (Excellent)"
    elif score >= 90:
        return "A (Very Good)"
    elif score >= 80:
        return "B (Good)"
    elif score >= 70:
        return "C (Acceptable)"
    elif score >= 60:
        return "D (Poor)"
    else:
        return "F (Critical Issues)"


def count_critical_issues(*checks) -> int:
    """Count critical issues across all checks."""
    critical_count = 0

    for check in checks:
        if isinstance(check, dict):
            # Count critical missing data
            if "critical_missing" in check:
                critical_count += len(check["critical_missing"])

            # Count duplicate records
            if "duplicate_records" in check:
                critical_count += len(check["duplicate_records"])

            # Count invalid records
            if "invalid_records" in check:
                critical_count += len(check["invalid_records"])

            # Count inconsistent records
            if "inconsistent_records" in check:
                critical_count += len(check["inconsistent_records"])

    return critical_count


def generate_recommendations(*checks) -> List[str]:
    """Generate recommendations based on quality checks."""
    recommendations = []

    for check in checks:
        if isinstance(check, dict):
            # Completeness recommendations
            if "critical_missing" in check and check["critical_missing"]:
                recommendations.append("Fix critical missing data in essential columns")

            if "overall_completeness" in check and check["overall_completeness"] < 90:
                recommendations.append("Improve data extraction to reduce missing values")

            # Uniqueness recommendations
            if "duplicate_records" in check and check["duplicate_records"]:
                recommendations.append("Implement deduplication logic to remove duplicate records")

            # Validity recommendations
            if "invalid_records" in check and check["invalid_records"]:
                recommendations.append("Review and fix data validation logic")

            # Consistency recommendations
            if "inconsistent_records" in check and check["inconsistent_records"]:
                recommendations.append(
                    "Address data consistency issues and business rule violations"
                )

            # Timeliness recommendations
            if "timeliness_score" in check and check["timeliness_score"] < 70:
                recommendations.append("Update data extraction schedule to ensure more recent data")

    return list(set(recommendations))  # Remove duplicates


def print_quality_summary(
    completeness: Dict[str, Any],
    uniqueness: Dict[str, Any],
    validity: Dict[str, Any],
    consistency: Dict[str, Any],
    timeliness: Dict[str, Any],
) -> None:
    """Print data quality summary to console."""

    print("\n" + "=" * 60)
    print("DATA QUALITY VERIFICATION SUMMARY")
    print("=" * 60)

    # Overall scores
    scores = [
        completeness.get("overall_completeness", 0),
        uniqueness.get("uniqueness_score", 0),
        validity.get("validity_score", 0),
        consistency.get("consistency_score", 0),
        timeliness.get("timeliness_score", 0),
    ]
    overall_score = sum(scores) / len(scores)

    print(f"\n📊 OVERALL QUALITY SCORE: {overall_score:.1f}% ({get_quality_grade(overall_score)})")

    # Individual scores
    print("\n📋 INDIVIDUAL SCORES:")
    print(f"   Completeness: {completeness.get('overall_completeness', 0):.1f}%")
    print(f"   Uniqueness: {uniqueness.get('uniqueness_score', 0):.1f}%")
    print(f"   Validity: {validity.get('validity_score', 0):.1f}%")
    print(f"   Consistency: {consistency.get('consistency_score', 0):.1f}%")
    print(f"   Timeliness: {timeliness.get('timeliness_score', 0):.1f}%")

    # Critical issues
    print("\n🚨 CRITICAL ISSUES:")
    critical_missing = len(completeness.get("critical_missing", []))
    duplicates = len(uniqueness.get("duplicate_records", []))
    invalid = len(validity.get("invalid_records", []))
    inconsistent = len(consistency.get("inconsistent_records", []))

    total_critical = critical_missing + duplicates + invalid + inconsistent

    if total_critical == 0:
        print("   ✅ No critical issues found")
    else:
        print(f"   Missing critical data: {critical_missing}")
        print(f"   Duplicate records: {duplicates}")
        print(f"   Invalid records: {invalid}")
        print(f"   Inconsistent records: {inconsistent}")
        print(f"   Total critical issues: {total_critical}")

    # Recommendations
    recommendations = generate_recommendations(
        completeness, uniqueness, validity, consistency, timeliness
    )
    if recommendations:
        print("\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")


def main():
    """Main data quality verification function."""
    parser = argparse.ArgumentParser(
        description="Verify data quality for North Star Metrics framework"
    )

    parser.add_argument("data_file", help="Path to unified_pilot_data.csv file")

    parser.add_argument(
        "--output-dir",
        default="validation_results",
        help="Output directory for quality reports (default: validation_results)",
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    # Setup
    logger = setup_logging(args.log_level)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    logger.info(f"Starting data quality verification for {args.data_file}")

    try:
        # Load data
        df = load_data(args.data_file)
        logger.info(f"Loaded {len(df)} records for quality verification")

        # Run quality checks
        logger.info("Running completeness checks...")
        completeness = check_completeness(df)

        logger.info("Running uniqueness checks...")
        uniqueness = check_uniqueness(df)

        logger.info("Running validity checks...")
        validity = check_validity(df)

        logger.info("Running consistency checks...")
        consistency = check_consistency(df)

        logger.info("Running timeliness checks...")
        timeliness = check_timeliness(df)

        # Generate report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = output_dir / f"data_quality_report_{timestamp}.json"

        generate_quality_report(
            df, completeness, uniqueness, validity, consistency, timeliness, str(report_file)
        )

        # Print summary
        print_quality_summary(completeness, uniqueness, validity, consistency, timeliness)

        print("\n📁 Quality verification outputs:")
        print(f"   - Report: {report_file}")
        print("\n💡 Next steps:")
        print("   1. Review the detailed quality report")
        print("   2. Address any critical issues found")
        print("   3. Implement recommended improvements")
        print("   4. Re-run quality checks after fixes")

    except Exception as e:
        logger.error(f"Data quality verification failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
