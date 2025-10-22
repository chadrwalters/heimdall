#!/usr/bin/env python3
"""Command-line interface for git-based extraction."""

import argparse
import os
import sys

from .config import GitExtractionConfig
from .git_extractor import GitDataExtractor


def main():
    """Main entry point for git-based extraction CLI."""
    parser = argparse.ArgumentParser(description="Extract data using git repositories")
    parser.add_argument("--org", required=True, help="Organization name")
    parser.add_argument("--days", type=int, default=7, help="Days back to extract")
    parser.add_argument(
        "--commits-output", default="org_commits.csv", help="Output file for commits"
    )
    parser.add_argument("--prs-output", default="org_prs.csv", help="Output file for PRs")
    parser.add_argument("--cache-dir", help="Cache directory (overrides environment)")
    parser.add_argument("--batch-size", type=int, help="Batch size for processing")
    parser.add_argument("--max-commits", type=int, help="Maximum commits per query")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Incremental mode: append only new data (deduplicate by SHA/number)",
    )

    args = parser.parse_args()

    # Get GitHub token
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("❌ GITHUB_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)

    # Create configuration from environment with command line overrides
    config = GitExtractionConfig.from_environment()

    # Apply command line overrides
    if args.cache_dir:
        config.cache_dir = args.cache_dir
    if args.batch_size:
        config.batch_size = args.batch_size
    if args.max_commits:
        config.max_commits_per_query = args.max_commits
    if args.verbose:
        config.log_level = "DEBUG"

    # Setup logging with configuration
    config.configure_logging()

    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        print(f"❌ Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"🚀 Starting git-based extraction for {args.org} ({args.days} days)")
    print(f"📁 Cache directory: {config.cache_dir}")
    print(f"📄 Commits output: {args.commits_output}")
    print(f"📄 PRs output: {args.prs_output}")
    print(f"⚙️  Batch size: {config.batch_size}")
    print(f"⚙️  Max commits per query: {config.max_commits_per_query}")
    print(f"🔒 Input validation: {'enabled' if config.validate_inputs else 'disabled'}")
    print("")

    # Create extractor and run
    extractor = GitDataExtractor(github_token, config)

    try:
        summary = extractor.extract_organization_data(
            args.org, args.days, args.commits_output, args.prs_output, incremental=args.incremental
        )

        # Get cache and rate limit stats
        cache_stats = extractor.get_cache_stats()

        print("")
        print("✅ Extraction completed successfully!")
        print("📊 Summary:")
        print(f"  • Repositories processed: {summary['repositories_found']}")

        if summary.get("incremental"):
            print(
                f"  • Commits added: {summary.get('commits_added', 0)} (deduped: {summary.get('commits_deduped', 0)})"
            )
            print(
                f"  • PRs added: {summary.get('prs_added', 0)} (deduped: {summary.get('prs_deduped', 0)})"
            )
        else:
            print(f"  • Commits extracted: {summary['commits_extracted']}")
            print(f"  • PRs extracted: {summary['prs_extracted']}")
        if "process_compliance_rate" in summary:
            print(f"  • Process compliance: {summary['process_compliance_rate']}%")
        print(
            f"  • Cache stats: {cache_stats['total_repos']} repos cached ({cache_stats['total_size_bytes'] // 1024 // 1024} MB)"
        )

        # Show rate limiting stats if available
        if "rate_limit_stats" in cache_stats:
            rate_stats = cache_stats["rate_limit_stats"]
            print(
                f"  • API requests: {rate_stats['total_requests']} total, {rate_stats['rate_limited_requests']} rate limited"
            )
            if rate_stats["rate_limit_info"]:
                remaining = rate_stats["rate_limit_info"]["remaining"]
                limit = rate_stats["rate_limit_info"]["limit"]
                print(f"  • Rate limit remaining: {remaining}/{limit}")

        print(
            f"  • Files: {summary['commits_file']}, {summary['prs_file']}, {summary['repos_file']}"
        )

    except Exception as e:
        print(f"❌ Extraction failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
