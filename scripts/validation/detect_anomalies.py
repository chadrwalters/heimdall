#!/usr/bin/env python3
"""
North Star Metrics - Anomaly Detection Script

Detects anomalies and outliers in the North Star Metrics data
to identify potential data quality issues or unusual patterns.
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Set up logging for anomaly detection."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger(__name__)


def load_data(file_path: str) -> pd.DataFrame:
    """Load data file for anomaly detection."""
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        raise ValueError(f"Failed to load data from {file_path}: {e}")


def detect_statistical_outliers(
    df: pd.DataFrame, columns: List[str], method: str = "iqr"
) -> Dict[str, Any]:
    """Detect statistical outliers using IQR or Z-score methods."""
    logger = logging.getLogger(__name__)
    logger.info(f"Detecting statistical outliers using {method} method...")

    outliers_results = {
        "method": method,
        "outliers_by_column": {},
        "outlier_records": [],
        "summary": {},
    }

    total_outliers = 0

    for col in columns:
        if col not in df.columns:
            continue

        column_data = df[col].dropna()
        if len(column_data) == 0:
            continue

        outliers_mask = np.zeros(len(df), dtype=bool)

        if method == "iqr":
            # Interquartile Range method
            Q1 = column_data.quantile(0.25)
            Q3 = column_data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers_mask = (df[col] < lower_bound) | (df[col] > upper_bound)

        elif method == "zscore":
            # Z-score method (values > 3 standard deviations)
            mean = column_data.mean()
            std = column_data.std()
            if std > 0:
                z_scores = np.abs((df[col] - mean) / std)
                outliers_mask = z_scores > 3

        outliers = df[outliers_mask]

        outliers_results["outliers_by_column"][col] = {
            "total_records": len(df),
            "outlier_count": len(outliers),
            "outlier_percentage": round((len(outliers) / len(df)) * 100, 2),
            "column_stats": {
                "mean": round(column_data.mean(), 2),
                "median": round(column_data.median(), 2),
                "std": round(column_data.std(), 2),
                "min": round(column_data.min(), 2),
                "max": round(column_data.max(), 2),
            },
        }

        # Add outlier records (limit to top 10 per column)
        for idx, row in outliers.head(10).iterrows():
            outliers_results["outlier_records"].append(
                {
                    "index": int(idx),
                    "source_id": row.get("source_id", "unknown"),
                    "column": col,
                    "value": round(row[col], 2) if pd.notna(row[col]) else None,
                    "anomaly_type": "statistical_outlier",
                    "method": method,
                }
            )

        total_outliers += len(outliers)

    outliers_results["summary"] = {
        "total_outliers": total_outliers,
        "outlier_percentage": round((total_outliers / (len(df) * len(columns))) * 100, 2),
        "columns_analyzed": len([col for col in columns if col in df.columns]),
    }

    return outliers_results


def detect_pattern_anomalies(df: pd.DataFrame) -> Dict[str, Any]:
    """Detect pattern-based anomalies in the data."""
    logger = logging.getLogger(__name__)
    logger.info("Detecting pattern anomalies...")

    pattern_results = {
        "pattern_anomalies": [],
        "distribution_anomalies": {},
        "temporal_anomalies": [],
        "summary": {},
    }

    # 1. Work type distribution anomalies
    if "work_type" in df.columns:
        work_type_dist = df["work_type"].value_counts(normalize=True)

        # Flag if any work type is > 80% or < 1% (unless very small dataset)
        for work_type, percentage in work_type_dist.items():
            if len(df) > 50:  # Only for larger datasets
                if percentage > 0.8:
                    pattern_results["pattern_anomalies"].append(
                        {
                            "anomaly_type": "dominant_work_type",
                            "work_type": work_type,
                            "percentage": round(percentage * 100, 2),
                            "severity": "high",
                            "description": f"Work type '{work_type}' represents {percentage * 100:.1f}% of all work",
                        }
                    )
                elif percentage < 0.01:
                    pattern_results["pattern_anomalies"].append(
                        {
                            "anomaly_type": "rare_work_type",
                            "work_type": work_type,
                            "percentage": round(percentage * 100, 2),
                            "severity": "medium",
                            "description": f"Work type '{work_type}' is very rare ({percentage * 100:.1f}%)",
                        }
                    )

        pattern_results["distribution_anomalies"]["work_type"] = work_type_dist.to_dict()

    # 2. AI assistance rate anomalies
    if "ai_assisted" in df.columns:
        ai_rate = df["ai_assisted"].mean()

        # Flag unusual AI rates
        if ai_rate > 0.95:
            pattern_results["pattern_anomalies"].append(
                {
                    "anomaly_type": "extremely_high_ai_usage",
                    "ai_rate": round(ai_rate * 100, 2),
                    "severity": "high",
                    "description": f"AI usage rate is extremely high ({ai_rate * 100:.1f}%)",
                }
            )
        elif ai_rate < 0.05:
            pattern_results["pattern_anomalies"].append(
                {
                    "anomaly_type": "extremely_low_ai_usage",
                    "ai_rate": round(ai_rate * 100, 2),
                    "severity": "medium",
                    "description": f"AI usage rate is extremely low ({ai_rate * 100:.1f}%)",
                }
            )

        pattern_results["distribution_anomalies"]["ai_assisted"] = {
            "ai_assisted_rate": round(ai_rate * 100, 2),
            "manual_rate": round((1 - ai_rate) * 100, 2),
        }

    # 3. Author concentration anomalies
    if "author" in df.columns:
        author_dist = df["author"].value_counts(normalize=True)

        # Flag if top author has > 50% of commits
        if len(author_dist) > 0 and author_dist.iloc[0] > 0.5:
            pattern_results["pattern_anomalies"].append(
                {
                    "anomaly_type": "author_concentration",
                    "top_author": author_dist.index[0],
                    "percentage": round(author_dist.iloc[0] * 100, 2),
                    "severity": "medium",
                    "description": f"Top author ({author_dist.index[0]}) represents {author_dist.iloc[0] * 100:.1f}% of all work",
                }
            )

        pattern_results["distribution_anomalies"]["author_concentration"] = {
            "total_authors": len(author_dist),
            "top_5_authors_percentage": round(author_dist.head(5).sum() * 100, 2),
        }

    # 4. Temporal anomalies (if date column exists)
    if "date" in df.columns:
        try:
            df["date_parsed"] = pd.to_datetime(df["date"], errors="coerce")
            valid_dates = df[df["date_parsed"].notna()]

            if len(valid_dates) > 10:  # Need sufficient data
                # Group by day and check for unusual spikes
                daily_counts = valid_dates.groupby(valid_dates["date_parsed"].dt.date).size()

                if len(daily_counts) > 7:  # At least a week of data
                    mean_daily = daily_counts.mean()
                    std_daily = daily_counts.std()

                    if std_daily > 0:
                        # Flag days with > 3 standard deviations from mean
                        threshold = mean_daily + 3 * std_daily
                        spike_days = daily_counts[daily_counts > threshold]

                        for date, count in spike_days.items():
                            pattern_results["temporal_anomalies"].append(
                                {
                                    "anomaly_type": "activity_spike",
                                    "date": str(date),
                                    "count": int(count),
                                    "expected_range": f"{mean_daily:.1f} ± {std_daily:.1f}",
                                    "severity": "medium",
                                    "description": f"Unusual activity spike on {date} ({count} records vs {mean_daily:.1f} average)",
                                }
                            )

                pattern_results["distribution_anomalies"]["temporal"] = {
                    "date_range_days": (
                        valid_dates["date_parsed"].max() - valid_dates["date_parsed"].min()
                    ).days,
                    "avg_daily_records": round(daily_counts.mean(), 2),
                    "std_daily_records": round(daily_counts.std(), 2),
                }

        except Exception as e:
            logger.warning(f"Temporal anomaly detection failed: {e}")

    # Summary
    pattern_results["summary"] = {
        "total_pattern_anomalies": len(pattern_results["pattern_anomalies"]),
        "total_temporal_anomalies": len(pattern_results["temporal_anomalies"]),
        "high_severity_count": len(
            [a for a in pattern_results["pattern_anomalies"] if a.get("severity") == "high"]
        ),
        "medium_severity_count": len(
            [a for a in pattern_results["pattern_anomalies"] if a.get("severity") == "medium"]
        ),
    }

    return pattern_results


def detect_data_drift(df: pd.DataFrame) -> Dict[str, Any]:
    """Detect data drift by comparing recent vs historical data."""
    logger = logging.getLogger(__name__)
    logger.info("Detecting data drift...")

    drift_results = {"drift_analysis": {}, "significant_drifts": [], "summary": {}}

    if "date" not in df.columns or len(df) < 50:
        logger.warning("Insufficient data for drift detection")
        return drift_results

    try:
        df["date_parsed"] = pd.to_datetime(df["date"], errors="coerce")
        valid_dates = df[df["date_parsed"].notna()].copy()

        if len(valid_dates) < 50:
            return drift_results

        # Split data into recent (last 25%) and historical (first 75%)
        valid_dates = valid_dates.sort_values("date_parsed")
        split_point = int(len(valid_dates) * 0.75)

        historical_data = valid_dates.iloc[:split_point]
        recent_data = valid_dates.iloc[split_point:]

        # Compare key metrics
        numeric_columns = ["complexity_score", "risk_score", "clarity_score", "impact_score"]

        for col in numeric_columns:
            if col in df.columns:
                hist_mean = historical_data[col].mean()
                recent_mean = recent_data[col].mean()

                hist_std = historical_data[col].std()
                recent_std = recent_data[col].std()

                # Calculate drift magnitude
                mean_drift = abs(recent_mean - hist_mean)
                std_drift = abs(recent_std - hist_std)

                # Statistical significance test (simple threshold-based)
                significant_mean_drift = mean_drift > (hist_std * 0.5) if hist_std > 0 else False
                significant_std_drift = std_drift > (hist_std * 0.3) if hist_std > 0 else False

                drift_results["drift_analysis"][col] = {
                    "historical_mean": round(hist_mean, 2),
                    "recent_mean": round(recent_mean, 2),
                    "mean_drift": round(mean_drift, 2),
                    "historical_std": round(hist_std, 2),
                    "recent_std": round(recent_std, 2),
                    "std_drift": round(std_drift, 2),
                    "significant_drift": significant_mean_drift or significant_std_drift,
                }

                if significant_mean_drift or significant_std_drift:
                    drift_results["significant_drifts"].append(
                        {
                            "column": col,
                            "drift_type": "mean" if significant_mean_drift else "std",
                            "magnitude": round(
                                mean_drift if significant_mean_drift else std_drift, 2
                            ),
                            "historical_value": round(
                                hist_mean if significant_mean_drift else hist_std, 2
                            ),
                            "recent_value": round(
                                recent_mean if significant_mean_drift else recent_std, 2
                            ),
                            "severity": "high" if mean_drift > hist_std else "medium",
                        }
                    )

        # Compare categorical distributions
        categorical_columns = ["work_type", "ai_assisted"]

        for col in categorical_columns:
            if col in df.columns:
                hist_dist = historical_data[col].value_counts(normalize=True)
                recent_dist = recent_data[col].value_counts(normalize=True)

                # Calculate distribution drift (simple comparison)
                common_values = set(hist_dist.index) & set(recent_dist.index)

                if common_values:
                    drift_sum = 0
                    for value in common_values:
                        drift_sum += abs(hist_dist.get(value, 0) - recent_dist.get(value, 0))

                    avg_drift = drift_sum / len(common_values)

                    drift_results["drift_analysis"][f"{col}_distribution"] = {
                        "historical_distribution": hist_dist.to_dict(),
                        "recent_distribution": recent_dist.to_dict(),
                        "average_drift": round(avg_drift, 3),
                        "significant_drift": avg_drift > 0.1,
                    }

                    if avg_drift > 0.1:
                        drift_results["significant_drifts"].append(
                            {
                                "column": f"{col}_distribution",
                                "drift_type": "distribution",
                                "magnitude": round(avg_drift, 3),
                                "severity": "high" if avg_drift > 0.2 else "medium",
                            }
                        )

        drift_results["summary"] = {
            "historical_records": len(historical_data),
            "recent_records": len(recent_data),
            "columns_analyzed": len(numeric_columns) + len(categorical_columns),
            "significant_drifts_count": len(drift_results["significant_drifts"]),
            "drift_detected": len(drift_results["significant_drifts"]) > 0,
        }

    except Exception as e:
        logger.warning(f"Data drift detection failed: {e}")

    return drift_results


def generate_anomaly_report(
    df: pd.DataFrame,
    statistical_outliers: Dict[str, Any],
    pattern_anomalies: Dict[str, Any],
    data_drift: Dict[str, Any],
    output_file: str,
) -> None:
    """Generate comprehensive anomaly detection report."""

    # Calculate overall anomaly score
    total_anomalies = (
        statistical_outliers.get("summary", {}).get("total_outliers", 0)
        + pattern_anomalies.get("summary", {}).get("total_pattern_anomalies", 0)
        + pattern_anomalies.get("summary", {}).get("total_temporal_anomalies", 0)
        + data_drift.get("summary", {}).get("significant_drifts_count", 0)
    )

    anomaly_rate = (total_anomalies / len(df)) * 100 if len(df) > 0 else 0

    report = {
        "anomaly_metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_records": len(df),
            "total_anomalies": total_anomalies,
            "anomaly_rate_percentage": round(anomaly_rate, 2),
        },
        "statistical_outliers": statistical_outliers,
        "pattern_anomalies": pattern_anomalies,
        "data_drift": data_drift,
        "anomaly_summary": {
            "total_anomalies": total_anomalies,
            "anomaly_rate": round(anomaly_rate, 2),
            "severity_breakdown": {
                "high": len(
                    [
                        a
                        for a in pattern_anomalies.get("pattern_anomalies", [])
                        + data_drift.get("significant_drifts", [])
                        if a.get("severity") == "high"
                    ]
                ),
                "medium": len(
                    [
                        a
                        for a in pattern_anomalies.get("pattern_anomalies", [])
                        + data_drift.get("significant_drifts", [])
                        if a.get("severity") == "medium"
                    ]
                ),
                "low": len(
                    [
                        a
                        for a in pattern_anomalies.get("pattern_anomalies", [])
                        + data_drift.get("significant_drifts", [])
                        if a.get("severity") == "low"
                    ]
                ),
            },
            "anomaly_types": {
                "statistical_outliers": statistical_outliers.get("summary", {}).get(
                    "total_outliers", 0
                ),
                "pattern_anomalies": pattern_anomalies.get("summary", {}).get(
                    "total_pattern_anomalies", 0
                ),
                "temporal_anomalies": pattern_anomalies.get("summary", {}).get(
                    "total_temporal_anomalies", 0
                ),
                "data_drift": data_drift.get("summary", {}).get("significant_drifts_count", 0),
            },
            "recommendations": generate_anomaly_recommendations(
                statistical_outliers, pattern_anomalies, data_drift
            ),
        },
    }

    # Save report
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"Anomaly detection report saved to: {output_file}")


def generate_anomaly_recommendations(
    statistical_outliers, pattern_anomalies, data_drift
) -> List[str]:
    """Generate recommendations based on anomaly detection results."""
    recommendations = []

    # Statistical outlier recommendations
    total_outliers = statistical_outliers.get("summary", {}).get("total_outliers", 0)
    if total_outliers > 0:
        outlier_rate = statistical_outliers.get("summary", {}).get("outlier_percentage", 0)
        if outlier_rate > 5:
            recommendations.append(
                f"High outlier rate ({outlier_rate:.1f}%) detected - investigate data extraction and analysis logic"
            )
        else:
            recommendations.append(
                "Review statistical outliers to identify potential data quality issues"
            )

    # Pattern anomaly recommendations
    high_severity_patterns = pattern_anomalies.get("summary", {}).get("high_severity_count", 0)
    if high_severity_patterns > 0:
        recommendations.append(
            "Address high-severity pattern anomalies that may indicate data collection issues"
        )

    # Data drift recommendations
    if data_drift.get("summary", {}).get("drift_detected", False):
        recommendations.append(
            "Investigate data drift - recent data patterns differ significantly from historical data"
        )

    # AI usage recommendations
    for anomaly in pattern_anomalies.get("pattern_anomalies", []):
        if anomaly.get("anomaly_type") in ["extremely_high_ai_usage", "extremely_low_ai_usage"]:
            recommendations.append(
                "Review AI detection configuration and developer override settings"
            )
            break

    # Work type recommendations
    for anomaly in pattern_anomalies.get("pattern_anomalies", []):
        if anomaly.get("anomaly_type") == "dominant_work_type":
            recommendations.append(
                "Verify work type classification accuracy for dominant categories"
            )
            break

    return recommendations


def print_anomaly_summary(statistical_outliers, pattern_anomalies, data_drift) -> None:
    """Print anomaly detection summary to console."""

    print("\n" + "=" * 60)
    print("ANOMALY DETECTION SUMMARY")
    print("=" * 60)

    # Statistical outliers
    print("\n📊 STATISTICAL OUTLIERS:")
    total_outliers = statistical_outliers.get("summary", {}).get("total_outliers", 0)
    outlier_rate = statistical_outliers.get("summary", {}).get("outlier_percentage", 0)
    print(f"   Total outliers: {total_outliers}")
    print(f"   Outlier rate: {outlier_rate:.1f}%")

    # Pattern anomalies
    print("\n🔍 PATTERN ANOMALIES:")
    pattern_count = pattern_anomalies.get("summary", {}).get("total_pattern_anomalies", 0)
    temporal_count = pattern_anomalies.get("summary", {}).get("total_temporal_anomalies", 0)
    high_severity = pattern_anomalies.get("summary", {}).get("high_severity_count", 0)
    print(f"   Pattern anomalies: {pattern_count}")
    print(f"   Temporal anomalies: {temporal_count}")
    print(f"   High severity: {high_severity}")

    # Data drift
    print("\n📈 DATA DRIFT:")
    drift_detected = data_drift.get("summary", {}).get("drift_detected", False)
    drift_count = data_drift.get("summary", {}).get("significant_drifts_count", 0)
    print(f"   Drift detected: {'Yes' if drift_detected else 'No'}")
    print(f"   Significant drifts: {drift_count}")

    # Overall assessment
    total_anomalies = total_outliers + pattern_count + temporal_count + drift_count
    print("\n🎯 OVERALL ASSESSMENT:")

    if total_anomalies == 0:
        print("   ✅ No significant anomalies detected")
    elif total_anomalies < 10 and high_severity == 0:
        print("   ⚠️  Minor anomalies detected - monitor closely")
    elif high_severity > 0 or total_anomalies > 20:
        print("   ❌ Significant anomalies detected - investigation required")
    else:
        print("   ⚠️  Moderate anomalies detected - review recommended")

    print(f"   Total anomalies: {total_anomalies}")


def main():
    """Main anomaly detection function."""
    parser = argparse.ArgumentParser(
        description="Detect anomalies and outliers in North Star Metrics data"
    )

    parser.add_argument("data_file", help="Path to unified_pilot_data.csv file")

    parser.add_argument(
        "--output-dir",
        default="validation_results",
        help="Output directory for anomaly reports (default: validation_results)",
    )

    parser.add_argument(
        "--method",
        choices=["iqr", "zscore"],
        default="iqr",
        help="Statistical outlier detection method (default: iqr)",
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

    logger.info(f"Starting anomaly detection for {args.data_file}")

    try:
        # Load data
        df = load_data(args.data_file)
        logger.info(f"Loaded {len(df)} records for anomaly detection")

        # Detect anomalies
        logger.info("Detecting statistical outliers...")
        numeric_columns = ["complexity_score", "risk_score", "clarity_score", "impact_score"]
        statistical_outliers = detect_statistical_outliers(df, numeric_columns, args.method)

        logger.info("Detecting pattern anomalies...")
        pattern_anomalies = detect_pattern_anomalies(df)

        logger.info("Detecting data drift...")
        data_drift = detect_data_drift(df)

        # Generate report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = output_dir / f"anomaly_detection_report_{timestamp}.json"

        generate_anomaly_report(
            df, statistical_outliers, pattern_anomalies, data_drift, str(report_file)
        )

        # Print summary
        print_anomaly_summary(statistical_outliers, pattern_anomalies, data_drift)

        print("\n📁 Anomaly detection outputs:")
        print(f"   - Report: {report_file}")
        print("\n💡 Next steps:")
        print("   1. Review the detailed anomaly report")
        print("   2. Investigate significant anomalies")
        print("   3. Consider adjusting data collection or analysis processes")
        print("   4. Monitor trends over time")

    except Exception as e:
        logger.error(f"Anomaly detection failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
