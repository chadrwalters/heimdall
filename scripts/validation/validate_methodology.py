#!/usr/bin/env python3
"""
North Star Metrics - Methodology Validation Script

Validates the accuracy and consistency of the AI analysis methodology
by comparing AI classifications with manual assessments and checking
data quality metrics.
"""

import argparse
import json
import logging
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.analysis.context_preparer import ContextPreparer


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Set up logging for validation."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger(__name__)


def load_validation_data(file_path: str) -> pd.DataFrame:
    """Load unified data for validation."""
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        raise ValueError(f"Failed to load validation data from {file_path}: {e}")


def sample_records(df: pd.DataFrame, sample_size: int, random_seed: int = 42) -> pd.DataFrame:
    """Sample records for manual validation."""
    random.seed(random_seed)

    if len(df) <= sample_size:
        return df

    # Stratified sampling to ensure we get diverse work types
    work_types = df["work_type"].unique()
    samples_per_type = max(1, sample_size // len(work_types))

    sampled_records = []
    for work_type in work_types:
        type_records = df[df["work_type"] == work_type]
        sample_count = min(samples_per_type, len(type_records))
        sampled = type_records.sample(n=sample_count, random_state=random_seed)
        sampled_records.append(sampled)

    result = pd.concat(sampled_records, ignore_index=True)

    # If we still need more records, randomly sample from the remainder
    if len(result) < sample_size:
        remaining = df.drop(result.index)
        additional_needed = sample_size - len(result)
        if len(remaining) > 0:
            additional = remaining.sample(
                n=min(additional_needed, len(remaining)), random_state=random_seed
            )
            result = pd.concat([result, additional], ignore_index=True)

    return result.head(sample_size)


def validate_impact_scores(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate impact score calculations."""
    validation_results = {
        "total_records": len(df),
        "calculation_errors": [],
        "score_distribution": {},
        "outliers": [],
    }

    # Check impact score calculation: 40% complexity + 50% risk + 10% clarity
    for idx, row in df.iterrows():
        expected_score = (
            row["complexity_score"] * 0.4 + row["risk_score"] * 0.5 + row["clarity_score"] * 0.1
        )
        actual_score = row["impact_score"]

        # Allow small floating point differences
        if abs(expected_score - actual_score) > 0.01:
            validation_results["calculation_errors"].append(
                {
                    "index": idx,
                    "source_id": row.get("source_id", "unknown"),
                    "expected": round(expected_score, 2),
                    "actual": round(actual_score, 2),
                    "difference": round(abs(expected_score - actual_score), 2),
                }
            )

    # Score distribution analysis
    validation_results["score_distribution"] = {
        "complexity": {
            "mean": df["complexity_score"].mean(),
            "std": df["complexity_score"].std(),
            "min": df["complexity_score"].min(),
            "max": df["complexity_score"].max(),
        },
        "risk": {
            "mean": df["risk_score"].mean(),
            "std": df["risk_score"].std(),
            "min": df["risk_score"].min(),
            "max": df["risk_score"].max(),
        },
        "clarity": {
            "mean": df["clarity_score"].mean(),
            "std": df["clarity_score"].std(),
            "min": df["clarity_score"].min(),
            "max": df["clarity_score"].max(),
        },
        "impact": {
            "mean": df["impact_score"].mean(),
            "std": df["impact_score"].std(),
            "min": df["impact_score"].min(),
            "max": df["impact_score"].max(),
        },
    }

    # Identify outliers (scores outside valid range 1-10)
    for score_type in ["complexity_score", "risk_score", "clarity_score"]:
        outliers = df[(df[score_type] < 1) | (df[score_type] > 10)]
        for idx, row in outliers.iterrows():
            validation_results["outliers"].append(
                {
                    "index": idx,
                    "source_id": row.get("source_id", "unknown"),
                    "score_type": score_type,
                    "value": row[score_type],
                    "work_type": row.get("work_type", "unknown"),
                }
            )

    return validation_results


def validate_ai_detection(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate AI detection patterns and overrides."""
    validation_results = {
        "total_records": len(df),
        "ai_assisted_count": len(df[df["ai_assisted"] == True]),
        "ai_tool_distribution": {},
        "pattern_consistency": [],
        "override_analysis": {},
    }

    # AI tool distribution
    ai_records = df[df["ai_assisted"] == True]
    if len(ai_records) > 0:
        tool_counts = ai_records["ai_tool_type"].value_counts()
        validation_results["ai_tool_distribution"] = tool_counts.to_dict()

    # Check for inconsistent patterns (basic validation)
    context_preparer = ContextPreparer()

    # Sample check for pattern consistency
    sample_size = min(50, len(df))
    sample_df = df.sample(n=sample_size, random_state=42)

    for idx, row in sample_df.iterrows():
        # Create mock data for pattern detection
        mock_data = {
            "commit": {"message": row.get("analysis_summary", "")},
            "body": row.get("analysis_summary", ""),
            "message": row.get("analysis_summary", ""),
        }

        detected_ai, detected_tool = context_preparer.detect_ai_assistance(mock_data)
        actual_ai = row["ai_assisted"]

        if detected_ai != actual_ai:
            validation_results["pattern_consistency"].append(
                {
                    "index": idx,
                    "source_id": row.get("source_id", "unknown"),
                    "detected_ai": detected_ai,
                    "actual_ai": actual_ai,
                    "detected_tool": detected_tool,
                    "actual_tool": row.get("ai_tool_type"),
                }
            )

    # AI assistance rate by author (helps identify override effectiveness)
    author_ai_rates = df.groupby("author")["ai_assisted"].agg(["count", "sum", "mean"])
    author_ai_rates["ai_rate"] = author_ai_rates["mean"]
    high_ai_users = author_ai_rates[author_ai_rates["ai_rate"] > 0.8]

    validation_results["override_analysis"] = {
        "high_ai_users": high_ai_users.to_dict("index"),
        "total_authors": len(author_ai_rates),
        "high_ai_user_count": len(high_ai_users),
    }

    return validation_results


def validate_work_classification(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate work type classifications."""
    validation_results = {
        "total_records": len(df),
        "work_type_distribution": {},
        "suspicious_classifications": [],
        "consistency_checks": {},
    }

    # Work type distribution
    work_type_counts = df["work_type"].value_counts()
    validation_results["work_type_distribution"] = work_type_counts.to_dict()

    # Check for suspicious patterns
    # 1. High complexity but marked as "Chore"
    chore_high_complexity = df[(df["work_type"] == "Chore") & (df["complexity_score"] > 7)]

    for idx, row in chore_high_complexity.iterrows():
        validation_results["suspicious_classifications"].append(
            {
                "type": "high_complexity_chore",
                "index": idx,
                "source_id": row.get("source_id", "unknown"),
                "work_type": row["work_type"],
                "complexity_score": row["complexity_score"],
                "analysis_summary": row.get("analysis_summary", "")[:100],
            }
        )

    # 2. Low complexity but marked as "New Feature"
    feature_low_complexity = df[(df["work_type"] == "New Feature") & (df["complexity_score"] < 4)]

    for idx, row in feature_low_complexity.iterrows():
        validation_results["suspicious_classifications"].append(
            {
                "type": "low_complexity_feature",
                "index": idx,
                "source_id": row.get("source_id", "unknown"),
                "work_type": row["work_type"],
                "complexity_score": row["complexity_score"],
                "analysis_summary": row.get("analysis_summary", "")[:100],
            }
        )

    # Consistency checks
    validation_results["consistency_checks"] = {
        "avg_complexity_by_type": df.groupby("work_type")["complexity_score"].mean().to_dict(),
        "avg_risk_by_type": df.groupby("work_type")["risk_score"].mean().to_dict(),
        "avg_impact_by_type": df.groupby("work_type")["impact_score"].mean().to_dict(),
    }

    return validation_results


def validate_process_compliance(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate process compliance detection."""
    validation_results = {
        "total_records": len(df),
        "compliance_rate": df["process_compliant"].mean(),
        "ticket_linkage": {},
        "compliance_by_type": {},
    }

    # Ticket linkage analysis
    has_ticket = df[df["has_linear_ticket"] == True]
    validation_results["ticket_linkage"] = {
        "records_with_tickets": len(has_ticket),
        "unique_tickets": len(has_ticket["linear_ticket_id"].dropna().unique()),
        "ticket_pattern_analysis": {},
    }

    # Analyze ticket ID patterns
    ticket_ids = has_ticket["linear_ticket_id"].dropna()
    if len(ticket_ids) > 0:
        # Common patterns: ENG-123, PROJ-456, etc.
        patterns = {}
        for ticket_id in ticket_ids:
            if "-" in str(ticket_id):
                prefix = str(ticket_id).split("-")[0]
                patterns[prefix] = patterns.get(prefix, 0) + 1

        validation_results["ticket_linkage"]["ticket_pattern_analysis"] = patterns

    # Compliance by work type
    compliance_by_type = df.groupby("work_type")["process_compliant"].agg(["count", "sum", "mean"])
    validation_results["compliance_by_type"] = compliance_by_type.to_dict("index")

    return validation_results


def generate_validation_report(
    df: pd.DataFrame,
    impact_validation: Dict[str, Any],
    ai_validation: Dict[str, Any],
    classification_validation: Dict[str, Any],
    compliance_validation: Dict[str, Any],
    sample_records: pd.DataFrame,
    output_file: str,
) -> None:
    """Generate comprehensive validation report."""

    report = {
        "validation_metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_records": len(df),
            "sample_size": len(sample_records),
            "date_range": {
                "earliest": df["date"].min() if "date" in df.columns else None,
                "latest": df["date"].max() if "date" in df.columns else None,
            },
        },
        "impact_score_validation": impact_validation,
        "ai_detection_validation": ai_validation,
        "work_classification_validation": classification_validation,
        "process_compliance_validation": compliance_validation,
        "manual_validation_sample": sample_records.to_dict("records"),
        "summary": {"critical_issues": 0, "warnings": 0, "recommendations": []},
    }

    # Count critical issues and warnings
    if impact_validation["calculation_errors"]:
        report["summary"]["critical_issues"] += len(impact_validation["calculation_errors"])

    if impact_validation["outliers"]:
        report["summary"]["warnings"] += len(impact_validation["outliers"])

    if ai_validation["pattern_consistency"]:
        report["summary"]["warnings"] += len(ai_validation["pattern_consistency"])

    if classification_validation["suspicious_classifications"]:
        report["summary"]["warnings"] += len(
            classification_validation["suspicious_classifications"]
        )

    # Generate recommendations
    recommendations = []

    if len(impact_validation["calculation_errors"]) > 0:
        recommendations.append("Review impact score calculation logic - found calculation errors")

    if len(impact_validation["outliers"]) > 0:
        recommendations.append(
            "Investigate score outliers - some scores are outside valid range (1-10)"
        )

    if ai_validation["ai_assisted_count"] / len(df) < 0.1:
        recommendations.append("AI detection rate seems low - review AI detection patterns")

    if ai_validation["ai_assisted_count"] / len(df) > 0.8:
        recommendations.append("AI detection rate seems high - verify AI developer overrides")

    if compliance_validation["compliance_rate"] < 0.5:
        recommendations.append("Process compliance is low - review Linear ticket extraction logic")

    if len(classification_validation["suspicious_classifications"]) > len(df) * 0.1:
        recommendations.append("High number of suspicious work classifications - review AI prompts")

    report["summary"]["recommendations"] = recommendations

    # Save report
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"Validation report saved to: {output_file}")


def print_validation_summary(
    impact_validation: Dict[str, Any],
    ai_validation: Dict[str, Any],
    classification_validation: Dict[str, Any],
    compliance_validation: Dict[str, Any],
) -> None:
    """Print validation summary to console."""

    print("\n" + "=" * 60)
    print("NORTH STAR METRICS - VALIDATION SUMMARY")
    print("=" * 60)

    # Impact Score Validation
    print("\n📊 IMPACT SCORE VALIDATION")
    print(f"   Calculation errors: {len(impact_validation['calculation_errors'])}")
    print(f"   Score outliers: {len(impact_validation['outliers'])}")
    print(
        f"   Average impact score: {impact_validation['score_distribution']['impact']['mean']:.2f}"
    )

    # AI Detection Validation
    print("\n🤖 AI DETECTION VALIDATION")
    ai_rate = (ai_validation["ai_assisted_count"] / ai_validation["total_records"]) * 100
    print(f"   AI-assisted work: {ai_validation['ai_assisted_count']} ({ai_rate:.1f}%)")
    print(f"   Pattern inconsistencies: {len(ai_validation['pattern_consistency'])}")
    print(f"   High AI users: {ai_validation['override_analysis']['high_ai_user_count']}")

    # Work Classification Validation
    print("\n📋 WORK CLASSIFICATION VALIDATION")
    print(
        f"   Suspicious classifications: {len(classification_validation['suspicious_classifications'])}"
    )
    top_work_type = max(
        classification_validation["work_type_distribution"].items(), key=lambda x: x[1]
    )
    print(f"   Most common work type: {top_work_type[0]} ({top_work_type[1]} records)")

    # Process Compliance Validation
    print("\n✅ PROCESS COMPLIANCE VALIDATION")
    compliance_rate = compliance_validation["compliance_rate"] * 100
    print(f"   Process compliance rate: {compliance_rate:.1f}%")
    print(
        f"   Records with tickets: {compliance_validation['ticket_linkage']['records_with_tickets']}"
    )
    print(f"   Unique tickets: {compliance_validation['ticket_linkage']['unique_tickets']}")

    # Overall Assessment
    print("\n🎯 OVERALL ASSESSMENT")
    total_issues = len(impact_validation["calculation_errors"]) + len(impact_validation["outliers"])
    total_warnings = len(ai_validation["pattern_consistency"]) + len(
        classification_validation["suspicious_classifications"]
    )

    if total_issues == 0 and total_warnings < 5:
        print("   ✅ EXCELLENT - Methodology validation passed with minimal issues")
    elif total_issues == 0 and total_warnings < 20:
        print("   ⚠️  GOOD - Minor issues found, review recommendations")
    elif total_issues < 5:
        print("   ❌ NEEDS ATTENTION - Some calculation errors found")
    else:
        print("   🚨 CRITICAL - Significant methodology issues detected")

    print(f"   Critical issues: {total_issues}")
    print(f"   Warnings: {total_warnings}")


def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(
        description="Validate North Star Metrics methodology and data quality"
    )

    parser.add_argument("data_file", help="Path to unified_pilot_data.csv file")

    parser.add_argument(
        "--sample-size",
        type=int,
        default=20,
        help="Number of records to sample for manual validation (default: 20)",
    )

    parser.add_argument(
        "--output-dir",
        default="validation_results",
        help="Output directory for validation results (default: validation_results)",
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

    logger.info(f"Starting methodology validation for {args.data_file}")

    try:
        # Load data
        df = load_validation_data(args.data_file)
        logger.info(f"Loaded {len(df)} records for validation")

        # Sample records for manual validation
        sampled_records = sample_records(df, args.sample_size)
        logger.info(f"Sampled {len(sampled_records)} records for manual validation")

        # Run validations
        logger.info("Running impact score validation...")
        impact_validation = validate_impact_scores(df)

        logger.info("Running AI detection validation...")
        ai_validation = validate_ai_detection(df)

        logger.info("Running work classification validation...")
        classification_validation = validate_work_classification(df)

        logger.info("Running process compliance validation...")
        compliance_validation = validate_process_compliance(df)

        # Generate outputs
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save sample for manual validation
        sample_file = output_dir / f"manual_validation_sample_{timestamp}.csv"
        sample_records.to_csv(sample_file, index=False)
        logger.info(f"Manual validation sample saved to: {sample_file}")

        # Generate comprehensive report
        report_file = output_dir / f"validation_report_{timestamp}.json"
        generate_validation_report(
            df,
            impact_validation,
            ai_validation,
            classification_validation,
            compliance_validation,
            sample_records,
            str(report_file),
        )

        # Print summary
        print_validation_summary(
            impact_validation, ai_validation, classification_validation, compliance_validation
        )

        print("\n📁 Validation outputs:")
        print(f"   - Report: {report_file}")
        print(f"   - Sample: {sample_file}")
        print("\n💡 Next steps:")
        print("   1. Review the validation report for detailed findings")
        print("   2. Manually validate the sampled records")
        print("   3. Address any critical issues found")
        print("   4. Consider adjusting methodology based on findings")

    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
