#!/usr/bin/env python3
"""
North Star Metrics - Data Consistency Checker

Checks data consistency across different files and validates
business rules and logical relationships in the North Star Metrics data.
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Set up logging for consistency checking."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger(__name__)


def load_data_files(data_dir: str) -> Dict[str, pd.DataFrame]:
    """Load all relevant data files for consistency checking."""
    logger = logging.getLogger(__name__)
    data_path = Path(data_dir)

    files_to_load = {
        "unified": "unified_pilot_data.csv",
        "developer_metrics": "developer_metrics.csv",
        "raw_prs": "org_prs.csv",
        "raw_commits": "org_commits.csv",
    }

    loaded_data = {}

    for file_key, filename in files_to_load.items():
        file_path = data_path / filename
        if file_path.exists():
            try:
                df = pd.read_csv(file_path)
                loaded_data[file_key] = df
                logger.info(f"Loaded {filename}: {len(df)} records")
            except Exception as e:
                logger.warning(f"Failed to load {filename}: {e}")
        else:
            logger.warning(f"File not found: {filename}")

    return loaded_data


def check_cross_file_consistency(data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """Check consistency across different data files."""
    logger = logging.getLogger(__name__)
    logger.info("Checking cross-file consistency...")

    consistency_results = {
        "total_files": len(data),
        "cross_file_checks": {},
        "inconsistencies": [],
        "summary": {},
    }

    # Check unified vs raw data consistency
    if "unified" in data and "raw_prs" in data:
        unified_df = data["unified"]
        prs_df = data["raw_prs"]

        # Check if all PRs in unified data exist in raw PRs
        if "source_id" in unified_df.columns and "number" in prs_df.columns:
            unified_pr_ids = set(
                unified_df[unified_df["source_type"] == "PR"]["source_id"].astype(str)
            )
            raw_pr_ids = set(prs_df["number"].astype(str))

            missing_in_raw = unified_pr_ids - raw_pr_ids
            missing_in_unified = raw_pr_ids - unified_pr_ids

            consistency_results["cross_file_checks"]["unified_vs_raw_prs"] = {
                "unified_pr_count": len(unified_pr_ids),
                "raw_pr_count": len(raw_pr_ids),
                "missing_in_raw": len(missing_in_raw),
                "missing_in_unified": len(missing_in_unified),
                "consistency_percentage": round(
                    ((len(unified_pr_ids & raw_pr_ids)) / max(len(unified_pr_ids), 1)) * 100, 2
                ),
            }

            # Add inconsistencies
            for pr_id in list(missing_in_raw)[:10]:  # Limit to 10
                consistency_results["inconsistencies"].append(
                    {
                        "type": "pr_missing_in_raw",
                        "pr_id": pr_id,
                        "description": f"PR {pr_id} exists in unified data but not in raw PRs",
                    }
                )

    # Check unified vs developer metrics consistency
    if "unified" in data and "developer_metrics" in data:
        unified_df = data["unified"]
        dev_metrics_df = data["developer_metrics"]

        if "author" in unified_df.columns and "Author" in dev_metrics_df.columns:
            unified_authors = set(unified_df["author"].dropna())
            metrics_authors = set(dev_metrics_df["Author"].dropna())

            missing_in_metrics = unified_authors - metrics_authors
            extra_in_metrics = metrics_authors - unified_authors

            consistency_results["cross_file_checks"]["unified_vs_developer_metrics"] = {
                "unified_author_count": len(unified_authors),
                "metrics_author_count": len(metrics_authors),
                "missing_in_metrics": len(missing_in_metrics),
                "extra_in_metrics": len(extra_in_metrics),
                "consistency_percentage": round(
                    ((len(unified_authors & metrics_authors)) / max(len(unified_authors), 1)) * 100,
                    2,
                ),
            }

            # Add inconsistencies
            for author in list(missing_in_metrics)[:5]:  # Limit to 5
                consistency_results["inconsistencies"].append(
                    {
                        "type": "author_missing_in_metrics",
                        "author": author,
                        "description": f"Author {author} exists in unified data but not in developer metrics",
                    }
                )

    return consistency_results


def check_business_rules(data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """Check business rule compliance."""
    logger = logging.getLogger(__name__)
    logger.info("Checking business rules...")

    business_rules_results = {
        "rules_checked": [],
        "violations": [],
        "rule_compliance": {},
        "summary": {},
    }

    if "unified" not in data:
        logger.warning("Unified data not available for business rules checking")
        return business_rules_results

    df = data["unified"]
    total_violations = 0

    # Rule 1: Impact score calculation
    if all(
        col in df.columns
        for col in ["complexity_score", "risk_score", "clarity_score", "impact_score"]
    ):
        rule_name = "impact_score_calculation"
        business_rules_results["rules_checked"].append(rule_name)

        expected_impact = (
            df["complexity_score"] * 0.4 + df["risk_score"] * 0.5 + df["clarity_score"] * 0.1
        )

        violations = abs(df["impact_score"] - expected_impact) > 0.1
        violation_count = violations.sum()

        business_rules_results["rule_compliance"][rule_name] = {
            "total_records": len(df),
            "violations": violation_count,
            "compliance_percentage": round(((len(df) - violation_count) / len(df)) * 100, 2),
        }

        # Add violation details
        for idx in df[violations].head(10).index:
            row = df.loc[idx]
            business_rules_results["violations"].append(
                {
                    "rule": rule_name,
                    "index": int(idx),
                    "source_id": row.get("source_id", "unknown"),
                    "expected": round(expected_impact.loc[idx], 2),
                    "actual": round(row["impact_score"], 2),
                    "description": "Impact score does not match calculation formula",
                }
            )

        total_violations += violation_count

    # Rule 2: Score ranges (1-10)
    score_columns = ["complexity_score", "risk_score", "clarity_score", "impact_score"]
    for score_col in score_columns:
        if score_col in df.columns:
            rule_name = f"{score_col}_range"
            business_rules_results["rules_checked"].append(rule_name)

            out_of_range = (df[score_col] < 1) | (df[score_col] > 10)
            violation_count = out_of_range.sum()

            business_rules_results["rule_compliance"][rule_name] = {
                "total_records": len(df),
                "violations": violation_count,
                "compliance_percentage": round(((len(df) - violation_count) / len(df)) * 100, 2),
            }

            # Add violation details
            for idx in df[out_of_range].head(5).index:
                row = df.loc[idx]
                business_rules_results["violations"].append(
                    {
                        "rule": rule_name,
                        "index": int(idx),
                        "source_id": row.get("source_id", "unknown"),
                        "value": row[score_col],
                        "description": f"{score_col} must be between 1 and 10",
                    }
                )

            total_violations += violation_count

    # Rule 3: AI assistance consistency
    if all(col in df.columns for col in ["ai_assisted", "ai_tool_type"]):
        rule_name = "ai_assistance_consistency"
        business_rules_results["rules_checked"].append(rule_name)

        # AI assisted should have a tool type (with some exceptions for overrides)
        ai_without_tool = (df["ai_assisted"] == True) & (
            df["ai_tool_type"].isna() | (df["ai_tool_type"] == "")
        )
        no_ai_with_tool = (df["ai_assisted"] == False) & (
            df["ai_tool_type"].notna() & (df["ai_tool_type"] != "")
        )

        violation_count = ai_without_tool.sum() + no_ai_with_tool.sum()

        business_rules_results["rule_compliance"][rule_name] = {
            "total_records": len(df),
            "violations": violation_count,
            "compliance_percentage": round(((len(df) - violation_count) / len(df)) * 100, 2),
        }

        # Add violation details
        for idx in df[ai_without_tool].head(5).index:
            row = df.loc[idx]
            business_rules_results["violations"].append(
                {
                    "rule": rule_name,
                    "index": int(idx),
                    "source_id": row.get("source_id", "unknown"),
                    "description": "AI assisted work should specify the AI tool used",
                }
            )

        total_violations += violation_count

    # Rule 4: Date validity
    if "date" in df.columns:
        rule_name = "date_validity"
        business_rules_results["rules_checked"].append(rule_name)

        try:
            df["date_parsed"] = pd.to_datetime(df["date"], errors="coerce")
            invalid_dates = df["date_parsed"].isna() & df["date"].notna()
            future_dates = df["date_parsed"] > datetime.now()

            violation_count = invalid_dates.sum() + future_dates.sum()

            business_rules_results["rule_compliance"][rule_name] = {
                "total_records": len(df),
                "violations": violation_count,
                "compliance_percentage": round(((len(df) - violation_count) / len(df)) * 100, 2),
            }

            # Add violation details
            for idx in df[invalid_dates | future_dates].head(5).index:
                row = df.loc[idx]
                business_rules_results["violations"].append(
                    {
                        "rule": rule_name,
                        "index": int(idx),
                        "source_id": row.get("source_id", "unknown"),
                        "date_value": row["date"],
                        "description": "Date must be valid and not in the future",
                    }
                )

            total_violations += violation_count

        except Exception as e:
            logger.warning(f"Date validation failed: {e}")

    # Rule 5: Work type classification reasonableness
    if all(col in df.columns for col in ["work_type", "complexity_score"]):
        rule_name = "work_type_complexity_alignment"
        business_rules_results["rules_checked"].append(rule_name)

        # Check for unreasonable combinations
        unreasonable = (
            ((df["work_type"] == "Chore") & (df["complexity_score"] > 8))
            | ((df["work_type"] == "New Feature") & (df["complexity_score"] < 2))
            | ((df["work_type"] == "Documentation") & (df["complexity_score"] > 6))
        )

        violation_count = unreasonable.sum()

        business_rules_results["rule_compliance"][rule_name] = {
            "total_records": len(df),
            "violations": violation_count,
            "compliance_percentage": round(((len(df) - violation_count) / len(df)) * 100, 2),
        }

        # Add violation details
        for idx in df[unreasonable].head(5).index:
            row = df.loc[idx]
            business_rules_results["violations"].append(
                {
                    "rule": rule_name,
                    "index": int(idx),
                    "source_id": row.get("source_id", "unknown"),
                    "work_type": row["work_type"],
                    "complexity_score": row["complexity_score"],
                    "description": f"Work type '{row['work_type']}' with complexity {row['complexity_score']} seems unreasonable",
                }
            )

        total_violations += violation_count

    # Summary
    total_records = len(df) * len(business_rules_results["rules_checked"])
    compliance_rate = (
        ((total_records - total_violations) / total_records * 100) if total_records > 0 else 100
    )

    business_rules_results["summary"] = {
        "total_rules_checked": len(business_rules_results["rules_checked"]),
        "total_violations": total_violations,
        "overall_compliance_percentage": round(compliance_rate, 2),
    }

    return business_rules_results


def check_data_relationships(data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """Check logical relationships within the data."""
    logger = logging.getLogger(__name__)
    logger.info("Checking data relationships...")

    relationships_results = {
        "relationships_checked": [],
        "relationship_violations": [],
        "relationship_stats": {},
        "summary": {},
    }

    if "unified" not in data:
        return relationships_results

    df = data["unified"]

    # Relationship 1: Complexity vs Risk correlation
    if all(col in df.columns for col in ["complexity_score", "risk_score"]):
        relationship_name = "complexity_risk_correlation"
        relationships_results["relationships_checked"].append(relationship_name)

        correlation = df["complexity_score"].corr(df["risk_score"])

        # Expect some positive correlation (complex work often has higher risk)
        relationships_results["relationship_stats"][relationship_name] = {
            "correlation": round(correlation, 3),
            "expected_range": "0.2 to 0.8",
            "relationship_strength": "weak"
            if abs(correlation) < 0.3
            else "moderate"
            if abs(correlation) < 0.6
            else "strong",
        }

        if correlation < 0.1:
            relationships_results["relationship_violations"].append(
                {
                    "relationship": relationship_name,
                    "issue": "Very low correlation between complexity and risk",
                    "correlation": round(correlation, 3),
                    "description": "Complex work typically has higher risk - very low correlation may indicate classification issues",
                }
            )

    # Relationship 2: AI assistance vs complexity
    if all(col in df.columns for col in ["ai_assisted", "complexity_score"]):
        relationship_name = "ai_assistance_complexity"
        relationships_results["relationships_checked"].append(relationship_name)

        ai_avg_complexity = df[df["ai_assisted"] == True]["complexity_score"].mean()
        manual_avg_complexity = df[df["ai_assisted"] == False]["complexity_score"].mean()

        complexity_diff = ai_avg_complexity - manual_avg_complexity

        relationships_results["relationship_stats"][relationship_name] = {
            "ai_average_complexity": round(ai_avg_complexity, 2),
            "manual_average_complexity": round(manual_avg_complexity, 2),
            "difference": round(complexity_diff, 2),
        }

        # Large differences might indicate bias in AI detection or usage
        if abs(complexity_diff) > 2:
            relationships_results["relationship_violations"].append(
                {
                    "relationship": relationship_name,
                    "issue": "Large complexity difference between AI and manual work",
                    "difference": round(complexity_diff, 2),
                    "description": f"AI work complexity ({ai_avg_complexity:.1f}) differs significantly from manual work ({manual_avg_complexity:.1f})",
                }
            )

    # Relationship 3: Work type consistency within authors
    if all(col in df.columns for col in ["author", "work_type", "complexity_score"]):
        relationship_name = "author_work_consistency"
        relationships_results["relationships_checked"].append(relationship_name)

        # Check if authors have consistent complexity patterns for similar work types
        author_work_stats = (
            df.groupby(["author", "work_type"])["complexity_score"]
            .agg(["mean", "std", "count"])
            .reset_index()
        )

        # Look for authors with very different complexity scores for the same work type
        inconsistent_authors = []

        for work_type in df["work_type"].unique():
            work_type_data = author_work_stats[author_work_stats["work_type"] == work_type]
            if len(work_type_data) > 1:
                overall_mean = work_type_data["mean"].mean()
                overall_std = work_type_data["mean"].std()

                if overall_std > 0:
                    # Find authors whose average is > 2 std from the mean
                    outlier_authors = work_type_data[
                        abs(work_type_data["mean"] - overall_mean) > 2 * overall_std
                    ]

                    for _, author_row in outlier_authors.iterrows():
                        inconsistent_authors.append(
                            {
                                "author": author_row["author"],
                                "work_type": work_type,
                                "author_avg_complexity": round(author_row["mean"], 2),
                                "overall_avg_complexity": round(overall_mean, 2),
                                "difference": round(abs(author_row["mean"] - overall_mean), 2),
                            }
                        )

        relationships_results["relationship_stats"][relationship_name] = {
            "inconsistent_author_patterns": len(inconsistent_authors),
            "total_author_work_type_combinations": len(author_work_stats),
        }

        # Add violations for significant inconsistencies
        for inconsistency in inconsistent_authors[:5]:  # Limit to 5
            relationships_results["relationship_violations"].append(
                {
                    "relationship": relationship_name,
                    "issue": "Author complexity pattern inconsistent with peers",
                    "author": inconsistency["author"],
                    "work_type": inconsistency["work_type"],
                    "description": f"Author {inconsistency['author']} has significantly different complexity ({inconsistency['author_avg_complexity']}) vs peers ({inconsistency['overall_avg_complexity']}) for {inconsistency['work_type']}",
                }
            )

    # Summary
    relationships_results["summary"] = {
        "total_relationships_checked": len(relationships_results["relationships_checked"]),
        "relationship_violations": len(relationships_results["relationship_violations"]),
        "relationship_health": "good"
        if len(relationships_results["relationship_violations"]) < 3
        else "poor",
    }

    return relationships_results


def generate_consistency_report(
    cross_file: Dict[str, Any],
    business_rules: Dict[str, Any],
    relationships: Dict[str, Any],
    output_file: str,
) -> None:
    """Generate comprehensive data consistency report."""

    # Calculate overall consistency score
    cross_file_issues = len(cross_file.get("inconsistencies", []))
    business_rule_violations = business_rules.get("summary", {}).get("total_violations", 0)
    relationship_violations = len(relationships.get("relationship_violations", []))

    total_issues = cross_file_issues + business_rule_violations + relationship_violations

    # Overall compliance
    business_compliance = business_rules.get("summary", {}).get(
        "overall_compliance_percentage", 100
    )

    report = {
        "consistency_metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_consistency_issues": total_issues,
            "overall_business_compliance": business_compliance,
        },
        "cross_file_consistency": cross_file,
        "business_rules_compliance": business_rules,
        "data_relationships": relationships,
        "consistency_summary": {
            "total_issues": total_issues,
            "issue_breakdown": {
                "cross_file_inconsistencies": cross_file_issues,
                "business_rule_violations": business_rule_violations,
                "relationship_violations": relationship_violations,
            },
            "overall_grade": get_consistency_grade(business_compliance, total_issues),
            "recommendations": generate_consistency_recommendations(
                cross_file, business_rules, relationships
            ),
        },
    }

    # Save report
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"Data consistency report saved to: {output_file}")


def get_consistency_grade(compliance_rate: float, total_issues: int) -> str:
    """Get consistency grade based on compliance rate and issues."""
    if compliance_rate >= 95 and total_issues < 5:
        return "A (Excellent)"
    elif compliance_rate >= 90 and total_issues < 15:
        return "B (Good)"
    elif compliance_rate >= 80 and total_issues < 30:
        return "C (Acceptable)"
    elif compliance_rate >= 70:
        return "D (Poor)"
    else:
        return "F (Critical)"


def generate_consistency_recommendations(cross_file, business_rules, relationships) -> List[str]:
    """Generate recommendations based on consistency checks."""
    recommendations = []

    # Cross-file recommendations
    if cross_file.get("inconsistencies"):
        recommendations.append(
            "Investigate cross-file inconsistencies to ensure data extraction alignment"
        )

    # Business rules recommendations
    compliance = business_rules.get("summary", {}).get("overall_compliance_percentage", 100)
    if compliance < 90:
        recommendations.append("Address business rule violations to improve data quality")

    # Specific rule recommendations
    for rule, stats in business_rules.get("rule_compliance", {}).items():
        if stats.get("compliance_percentage", 100) < 85:
            recommendations.append(
                f"Review {rule.replace('_', ' ')} logic - compliance is only {stats['compliance_percentage']:.1f}%"
            )

    # Relationship recommendations
    if relationships.get("relationship_violations"):
        recommendations.append(
            "Investigate data relationship violations that may indicate systematic issues"
        )

    return recommendations


def print_consistency_summary(cross_file, business_rules, relationships) -> None:
    """Print data consistency summary to console."""

    print("\n" + "=" * 60)
    print("DATA CONSISTENCY SUMMARY")
    print("=" * 60)

    # Cross-file consistency
    print("\n📁 CROSS-FILE CONSISTENCY:")
    cross_issues = len(cross_file.get("inconsistencies", []))
    print(f"   Files analyzed: {cross_file.get('total_files', 0)}")
    print(f"   Inconsistencies: {cross_issues}")

    # Business rules compliance
    print("\n📋 BUSINESS RULES COMPLIANCE:")
    rules_checked = business_rules.get("summary", {}).get("total_rules_checked", 0)
    violations = business_rules.get("summary", {}).get("total_violations", 0)
    compliance = business_rules.get("summary", {}).get("overall_compliance_percentage", 100)
    print(f"   Rules checked: {rules_checked}")
    print(f"   Violations: {violations}")
    print(f"   Compliance rate: {compliance:.1f}%")

    # Data relationships
    print("\n🔗 DATA RELATIONSHIPS:")
    relationships_checked = relationships.get("summary", {}).get("total_relationships_checked", 0)
    relationship_violations = relationships.get("summary", {}).get("relationship_violations", 0)
    health = relationships.get("summary", {}).get("relationship_health", "unknown")
    print(f"   Relationships checked: {relationships_checked}")
    print(f"   Violations: {relationship_violations}")
    print(f"   Overall health: {health}")

    # Overall assessment
    total_issues = cross_issues + violations + relationship_violations
    print("\n🎯 OVERALL ASSESSMENT:")
    grade = get_consistency_grade(compliance, total_issues)
    print(f"   Grade: {grade}")
    print(f"   Total issues: {total_issues}")

    if total_issues == 0:
        print("   ✅ Excellent data consistency")
    elif total_issues < 10 and compliance > 90:
        print("   ⚠️  Good consistency with minor issues")
    elif total_issues < 25 and compliance > 80:
        print("   ❌ Moderate consistency issues - review recommended")
    else:
        print("   🚨 Significant consistency issues - investigation required")


def main():
    """Main data consistency checking function."""
    parser = argparse.ArgumentParser(
        description="Check data consistency for North Star Metrics framework"
    )

    parser.add_argument("data_dir", help="Directory containing the data files to check")

    parser.add_argument(
        "--output-dir",
        default="validation_results",
        help="Output directory for consistency reports (default: validation_results)",
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

    logger.info(f"Starting data consistency checking for {args.data_dir}")

    try:
        # Load data files
        data = load_data_files(args.data_dir)

        if not data:
            logger.error("No data files found to check")
            sys.exit(1)

        logger.info(f"Loaded {len(data)} data files")

        # Run consistency checks
        logger.info("Checking cross-file consistency...")
        cross_file_results = check_cross_file_consistency(data)

        logger.info("Checking business rules compliance...")
        business_rules_results = check_business_rules(data)

        logger.info("Checking data relationships...")
        relationships_results = check_data_relationships(data)

        # Generate report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = output_dir / f"data_consistency_report_{timestamp}.json"

        generate_consistency_report(
            cross_file_results, business_rules_results, relationships_results, str(report_file)
        )

        # Print summary
        print_consistency_summary(cross_file_results, business_rules_results, relationships_results)

        print("\n📁 Consistency check outputs:")
        print(f"   - Report: {report_file}")
        print("\n💡 Next steps:")
        print("   1. Review the detailed consistency report")
        print("   2. Address high-priority violations")
        print("   3. Implement fixes for business rule compliance")
        print("   4. Monitor consistency trends over time")

    except Exception as e:
        logger.error(f"Data consistency checking failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
