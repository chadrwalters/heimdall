#!/usr/bin/env python3
"""Script to run load tests and generate performance reports."""

import argparse
import json
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.api.rate_limiter import AdaptiveRateLimiter
from tests.fixtures.analysis_fixtures import large_pr_data, sample_pr_data
from tests.test_load_performance import LoadTester


def run_analysis_load_test(num_requests: int = 100, concurrent_users: int = 10):
    """Run load test for analysis engine."""
    print(
        f"Running analysis load test: {num_requests} requests, {concurrent_users} concurrent users"
    )

    tester = LoadTester()

    # Mock analysis function for testing
    def mock_analyze_pr(pr_data):
        time.sleep(0.1)  # Simulate API call
        return {
            "work_type": "New Feature",
            "complexity_score": 6,
            "risk_score": 4,
            "clarity_score": 8,
            "analysis_summary": "Test analysis",
        }

    test_data = [sample_pr_data() for _ in range(num_requests)]

    metrics = tester.run_load_test(
        operation_name="pr_analysis",
        target_function=mock_analyze_pr,
        num_requests=num_requests,
        concurrent_users=concurrent_users,
        test_data=test_data,
    )

    return tester, metrics


def run_rate_limiter_test(num_requests: int = 200, concurrent_users: int = 15):
    """Run load test for rate limiter."""
    print(
        f"Running rate limiter test: {num_requests} requests, {concurrent_users} concurrent users"
    )

    tester = LoadTester()
    rate_limiter = AdaptiveRateLimiter(base_delay=0.01, max_delay=0.5)

    def rate_limited_operation(data):
        rate_limiter.wait_if_needed()
        time.sleep(0.01)  # Simulate work
        rate_limiter.record_success()
        return True

    metrics = tester.run_load_test(
        operation_name="rate_limited_requests",
        target_function=rate_limited_operation,
        num_requests=num_requests,
        concurrent_users=concurrent_users,
    )

    return tester, metrics


def run_large_data_test(num_requests: int = 50, concurrent_users: int = 5):
    """Run load test with large data payloads."""
    print(f"Running large data test: {num_requests} requests, {concurrent_users} concurrent users")

    tester = LoadTester()

    def process_large_data(pr_data):
        # Simulate processing large PR data
        time.sleep(0.2)  # Simulate more complex processing
        return {"processed": True, "size": len(str(pr_data))}

    test_data = [large_pr_data() for _ in range(num_requests)]

    metrics = tester.run_load_test(
        operation_name="large_data_processing",
        target_function=process_large_data,
        num_requests=num_requests,
        concurrent_users=concurrent_users,
        test_data=test_data,
    )

    return tester, metrics


def run_stress_test(duration_seconds: int = 60):
    """Run continuous stress test for specified duration."""
    print(f"Running stress test for {duration_seconds} seconds")

    tester = LoadTester()
    start_time = time.time()
    request_count = 0

    def stress_operation(data):
        time.sleep(0.05)  # Simulate work
        return True

    # Calculate number of requests based on duration
    estimated_requests = duration_seconds * 10  # Rough estimate

    metrics = tester.run_load_test(
        operation_name="stress_test",
        target_function=stress_operation,
        num_requests=estimated_requests,
        concurrent_users=20,
    )

    return tester, metrics


def main():
    """Main function to run load tests."""
    parser = argparse.ArgumentParser(description="Run load tests for North Star Metrics")
    parser.add_argument(
        "--test-type",
        choices=["analysis", "rate_limiter", "large_data", "stress", "all"],
        default="all",
        help="Type of load test to run",
    )
    parser.add_argument("--requests", type=int, default=100, help="Number of requests to send")
    parser.add_argument("--concurrent", type=int, default=10, help="Number of concurrent users")
    parser.add_argument(
        "--duration", type=int, default=60, help="Duration for stress test in seconds"
    )
    parser.add_argument("--output", help="Output file for performance report (JSON)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    print("🚀 North Star Metrics Load Testing")
    print("=" * 50)

    all_results = []

    try:
        if args.test_type in ["analysis", "all"]:
            tester, metrics = run_analysis_load_test(args.requests, args.concurrent)
            all_results.append(metrics)
            if args.verbose:
                print("\nAnalysis Test Results:")
                print(json.dumps(metrics.to_dict(), indent=2))

        if args.test_type in ["rate_limiter", "all"]:
            tester, metrics = run_rate_limiter_test(args.requests, args.concurrent)
            all_results.append(metrics)
            if args.verbose:
                print("\nRate Limiter Test Results:")
                print(json.dumps(metrics.to_dict(), indent=2))

        if args.test_type in ["large_data", "all"]:
            tester, metrics = run_large_data_test(
                max(args.requests // 2, 20), max(args.concurrent // 2, 3)
            )
            all_results.append(metrics)
            if args.verbose:
                print("\nLarge Data Test Results:")
                print(json.dumps(metrics.to_dict(), indent=2))

        if args.test_type in ["stress", "all"]:
            tester, metrics = run_stress_test(args.duration)
            all_results.append(metrics)
            if args.verbose:
                print("\nStress Test Results:")
                print(json.dumps(metrics.to_dict(), indent=2))

        # Generate comprehensive report
        final_tester = LoadTester()
        final_tester.results = all_results
        report = final_tester.generate_report()

        print("\n📊 PERFORMANCE SUMMARY")
        print("=" * 50)

        for result in all_results:
            print(f"\n{result.operation.upper()}:")
            print(f"  Success Rate: {result.success_rate:.1f}%")
            print(f"  Avg Response Time: {result.avg_response_time_ms:.1f}ms")
            print(f"  Throughput: {result.requests_per_second:.1f} RPS")
            print(f"  P95 Response Time: {result.p95_response_time_ms:.1f}ms")

            if result.memory_usage_mb:
                print(f"  Memory Usage: {result.memory_usage_mb:.1f}MB")

        print(f"\nOverall Success Rate: {report['test_summary']['overall_success_rate']:.1f}%")

        print("\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"  {i}. {rec}")

        # Save report if requested
        if args.output:
            with open(args.output, "w") as f:
                json.dump(report, f, indent=2)
            print(f"\n📁 Full report saved to: {args.output}")

        # Performance criteria check
        overall_success_rate = report["test_summary"]["overall_success_rate"]
        if overall_success_rate < 95:
            print(f"\n⚠️  WARNING: Overall success rate ({overall_success_rate:.1f}%) below 95%")
            sys.exit(1)

        # Check for concerning response times
        max_avg_response_time = max(r.avg_response_time_ms for r in all_results)
        if max_avg_response_time > 5000:
            print(
                f"\n⚠️  WARNING: High average response time detected ({max_avg_response_time:.1f}ms)"
            )
            sys.exit(1)

        print("\n✅ All performance tests passed!")

    except KeyboardInterrupt:
        print("\n\n⏹️  Load test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Load test failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
