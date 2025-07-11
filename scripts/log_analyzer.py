#!/usr/bin/env python3
"""Log analysis utility for structured JSON logs."""

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def parse_log_line(line: str) -> Optional[Dict[str, Any]]:
    """Parse a JSON log line."""
    try:
        return json.loads(line.strip())
    except json.JSONDecodeError:
        return None


def analyze_logs(log_file: str, hours: int = 24) -> Dict[str, Any]:
    """Analyze structured logs from file."""
    if not Path(log_file).exists():
        raise FileNotFoundError(f"Log file not found: {log_file}")

    # Time filtering
    cutoff_time = datetime.now() - timedelta(hours=hours)

    # Analysis containers
    entries = []
    error_count = 0
    warning_count = 0
    info_count = 0
    debug_count = 0

    correlation_ids = set()
    components = Counter()
    operations = Counter()
    api_calls = []
    business_events = []
    errors = []
    performance_metrics = []

    # Read and parse log file
    with open(log_file, "r") as f:
        for line in f:
            entry = parse_log_line(line)
            if not entry:
                continue

            # Time filtering
            try:
                entry_time = datetime.fromisoformat(
                    entry.get("timestamp", "").replace("Z", "+00:00")
                )
                if entry_time < cutoff_time:
                    continue
            except (ValueError, TypeError):
                continue  # Skip entries with invalid timestamps

            entries.append(entry)

            # Count by level
            level = entry.get("level", "INFO")
            if level == "ERROR":
                error_count += 1
            elif level == "WARNING":
                warning_count += 1
            elif level == "INFO":
                info_count += 1
            elif level == "DEBUG":
                debug_count += 1

            # Track correlation IDs
            if "correlation_id" in entry:
                correlation_ids.add(entry["correlation_id"])

            # Track components
            if "component" in entry:
                components[entry["component"]] += 1

            # Track operations
            if "operation" in entry:
                operations[entry["operation"]] += 1

            # Categorize special events
            event_type = entry.get("event")
            if event_type == "api_call":
                api_calls.append(entry)
            elif event_type == "business_event":
                business_events.append(entry)
            elif event_type == "error":
                errors.append(entry)
            elif event_type in ["start", "complete"] and "duration_ms" in entry:
                performance_metrics.append(entry)

    # Calculate performance statistics
    perf_stats = analyze_performance(performance_metrics)

    # Calculate API call statistics
    api_stats = analyze_api_calls(api_calls)

    # Calculate error statistics
    error_stats = analyze_errors(errors)

    return {
        "summary": {
            "total_entries": len(entries),
            "time_range_hours": hours,
            "log_levels": {
                "ERROR": error_count,
                "WARNING": warning_count,
                "INFO": info_count,
                "DEBUG": debug_count,
            },
            "unique_correlation_ids": len(correlation_ids),
            "active_components": len(components),
            "operations_performed": len(operations),
        },
        "components": dict(components.most_common()),
        "operations": dict(operations.most_common()),
        "api_calls": api_stats,
        "business_events": len(business_events),
        "errors": error_stats,
        "performance": perf_stats,
        "recent_errors": errors[-10:] if errors else [],  # Last 10 errors
        "slow_operations": get_slow_operations(performance_metrics),
    }


def analyze_performance(performance_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze performance metrics."""
    if not performance_metrics:
        return {"message": "No performance metrics found"}

    # Group by operation
    operation_times = defaultdict(list)
    for metric in performance_metrics:
        if "duration_ms" in metric and "operation" in metric:
            operation_times[metric["operation"]].append(metric["duration_ms"])

    # Calculate statistics
    stats = {}
    for operation, times in operation_times.items():
        if times:
            stats[operation] = {
                "count": len(times),
                "avg_ms": sum(times) / len(times),
                "min_ms": min(times),
                "max_ms": max(times),
                "total_ms": sum(times),
            }

    # Overall statistics
    all_times = [t for times in operation_times.values() for t in times]
    overall_stats = {
        "total_operations": len(all_times),
        "avg_duration_ms": sum(all_times) / len(all_times) if all_times else 0,
        "total_time_ms": sum(all_times),
        "operations": stats,
    }

    return overall_stats


def analyze_api_calls(api_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze API call statistics."""
    if not api_calls:
        return {"message": "No API calls found"}

    # Group by method and URL
    call_stats = defaultdict(lambda: {"count": 0, "total_duration": 0, "status_codes": Counter()})

    for call in api_calls:
        key = f"{call.get('method', 'UNKNOWN')} {call.get('url', 'unknown')}"
        call_stats[key]["count"] += 1

        if "duration_ms" in call:
            call_stats[key]["total_duration"] += call["duration_ms"]

        if "status_code" in call:
            call_stats[key]["status_codes"][call["status_code"]] += 1

    # Calculate averages
    for key, stats in call_stats.items():
        if stats["count"] > 0:
            stats["avg_duration_ms"] = stats["total_duration"] / stats["count"]

    return {
        "total_calls": len(api_calls),
        "unique_endpoints": len(call_stats),
        "calls_by_endpoint": dict(call_stats),
    }


def analyze_errors(errors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze error statistics."""
    if not errors:
        return {"message": "No errors found"}

    error_types = Counter()
    error_contexts = Counter()
    error_components = Counter()

    for error in errors:
        if "error_type" in error:
            error_types[error["error_type"]] += 1
        if "context" in error:
            error_contexts[error["context"]] += 1
        if "component" in error:
            error_components[error["component"]] += 1

    return {
        "total_errors": len(errors),
        "error_types": dict(error_types.most_common()),
        "error_contexts": dict(error_contexts.most_common()),
        "error_components": dict(error_components.most_common()),
    }


def get_slow_operations(
    performance_metrics: List[Dict[str, Any]], threshold_ms: float = 1000
) -> List[Dict[str, Any]]:
    """Get operations that took longer than threshold."""
    slow_ops = []

    for metric in performance_metrics:
        if metric.get("duration_ms", 0) > threshold_ms:
            slow_ops.append(
                {
                    "operation": metric.get("operation"),
                    "duration_ms": metric.get("duration_ms"),
                    "timestamp": metric.get("timestamp"),
                    "correlation_id": metric.get("correlation_id"),
                }
            )

    return sorted(slow_ops, key=lambda x: x.get("duration_ms", 0), reverse=True)


def format_analysis(analysis: Dict[str, Any], format_type: str = "summary") -> str:
    """Format analysis results."""
    if format_type == "json":
        return json.dumps(analysis, indent=2, default=str)

    # Summary format
    lines = []
    lines.append("=" * 60)
    lines.append("LOG ANALYSIS REPORT")
    lines.append("=" * 60)

    # Summary
    summary = analysis["summary"]
    lines.append(f"Total Entries: {summary['total_entries']:,}")
    lines.append(f"Time Range: {summary['time_range_hours']} hours")
    lines.append(f"Unique Correlations: {summary['unique_correlation_ids']:,}")
    lines.append("")

    # Log levels
    lines.append("Log Levels:")
    for level, count in summary["log_levels"].items():
        lines.append(f"  {level}: {count:,}")
    lines.append("")

    # Components
    if analysis["components"]:
        lines.append("Top Components:")
        for component, count in list(analysis["components"].items())[:5]:
            lines.append(f"  {component}: {count:,}")
        lines.append("")

    # Operations
    if analysis["operations"]:
        lines.append("Top Operations:")
        for operation, count in list(analysis["operations"].items())[:5]:
            lines.append(f"  {operation}: {count:,}")
        lines.append("")

    # API Calls
    api_calls = analysis["api_calls"]
    if isinstance(api_calls, dict) and "total_calls" in api_calls:
        lines.append(f"API Calls: {api_calls['total_calls']:,}")
        lines.append(f"Unique Endpoints: {api_calls['unique_endpoints']:,}")
        lines.append("")

    # Performance
    perf = analysis["performance"]
    if isinstance(perf, dict) and "total_operations" in perf:
        lines.append("Performance Metrics:")
        lines.append(f"  Total Operations: {perf['total_operations']:,}")
        lines.append(f"  Average Duration: {perf['avg_duration_ms']:.2f}ms")
        lines.append(f"  Total Time: {perf['total_time_ms']:.2f}ms")
        lines.append("")

    # Errors
    errors = analysis["errors"]
    if isinstance(errors, dict) and "total_errors" in errors:
        lines.append(f"Errors: {errors['total_errors']:,}")
        if errors.get("error_types"):
            lines.append("  Top Error Types:")
            for error_type, count in list(errors["error_types"].items())[:3]:
                lines.append(f"    {error_type}: {count:,}")
        lines.append("")

    # Slow operations
    slow_ops = analysis.get("slow_operations", [])
    if slow_ops:
        lines.append("Slow Operations (>1000ms):")
        for op in slow_ops[:5]:
            lines.append(f"  {op['operation']}: {op['duration_ms']:.2f}ms")
        lines.append("")

    lines.append("=" * 60)

    return "\n".join(lines)


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Analyze structured JSON logs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python log_analyzer.py /path/to/logfile.log
  python log_analyzer.py /path/to/logfile.log --hours 12
  python log_analyzer.py /path/to/logfile.log --format json
  python log_analyzer.py /path/to/logfile.log --slow-threshold 500
        """,
    )

    parser.add_argument("log_file", help="Path to log file")
    parser.add_argument("--hours", type=int, default=24, help="Hours to analyze (default: 24)")
    parser.add_argument(
        "--format",
        choices=["summary", "json"],
        default="summary",
        help="Output format (default: summary)",
    )
    parser.add_argument(
        "--slow-threshold",
        type=float,
        default=1000,
        help="Threshold for slow operations in ms (default: 1000)",
    )
    parser.add_argument("--output", help="Output file (default: stdout)")

    args = parser.parse_args()

    try:
        # Analyze logs
        analysis = analyze_logs(args.log_file, args.hours)

        # Update slow operations threshold
        analysis["slow_operations"] = get_slow_operations(
            analysis.get("performance", {}).get("operations", []), args.slow_threshold
        )

        # Format results
        output = format_analysis(analysis, args.format)

        # Write output
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"Analysis saved to {args.output}")
        else:
            print(output)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
