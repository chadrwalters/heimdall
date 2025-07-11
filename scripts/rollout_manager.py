#!/usr/bin/env python3
"""Command-line interface for managing gradual rollouts."""

import argparse
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.rollout.gradual_rollout import (
    GradualRolloutManager,
    RolloutConfig,
    RolloutStrategy,
    create_default_rollout_config,
)


def start_rollout(args):
    """Start a new gradual rollout."""
    print(f"🚀 Starting gradual rollout for {args.organization}")

    # Create configuration
    if args.config_file:
        with open(args.config_file, "r") as f:
            config_data = json.load(f)
        config = RolloutConfig(**config_data)
    else:
        config = create_default_rollout_config(args.organization, args.total_repositories)

        # Override with command line arguments
        if args.strategy:
            config.strategy = RolloutStrategy(args.strategy)
        if args.canary_percentage:
            config.canary_percentage = args.canary_percentage / 100
        if args.max_concurrent:
            config.max_concurrent_repositories = args.max_concurrent

    # Initialize rollout manager
    manager = GradualRolloutManager(config)

    # Start rollout
    result = manager.start_rollout()

    print("📊 Rollout Results:")
    print(json.dumps(result, indent=2, default=str))

    if result.get("status") == "pilot_failed":
        print("❌ Pilot phase failed - rollout stopped")
        sys.exit(1)
    else:
        print("✅ Pilot phase completed successfully")


def continue_rollout(args):
    """Continue an existing rollout."""
    print(f"⏭️ Continuing rollout for {args.organization}")

    # Load existing rollout
    config = create_default_rollout_config(args.organization, 100)  # Will be loaded from state
    manager = GradualRolloutManager(config)

    result = manager.continue_rollout()

    print("📊 Continue Results:")
    print(json.dumps(result, indent=2, default=str))


def pause_rollout(args):
    """Pause an active rollout."""
    print(f"⏸️ Pausing rollout for {args.organization}")

    config = create_default_rollout_config(args.organization, 100)
    manager = GradualRolloutManager(config)

    result = manager.pause_rollout()

    print("📊 Pause Results:")
    print(json.dumps(result, indent=2, default=str))


def resume_rollout(args):
    """Resume a paused rollout."""
    print(f"▶️ Resuming rollout for {args.organization}")

    config = create_default_rollout_config(args.organization, 100)
    manager = GradualRolloutManager(config)

    result = manager.resume_rollout()

    print("📊 Resume Results:")
    print(json.dumps(result, indent=2, default=str))


def rollback_rollout(args):
    """Rollback a rollout."""
    print(f"⏪ Rolling back rollout for {args.organization}")

    config = create_default_rollout_config(args.organization, 100)
    manager = GradualRolloutManager(config)

    result = manager.rollback_rollout()

    print("📊 Rollback Results:")
    print(json.dumps(result, indent=2, default=str))


def status_rollout(args):
    """Get rollout status."""
    print(f"📊 Rollout status for {args.organization}")

    config = create_default_rollout_config(args.organization, 100)
    manager = GradualRolloutManager(config)

    status = manager.get_rollout_status()

    print("Current Status:")
    print(f"  Phase: {status['current_phase']}")
    print(f"  Coverage: {status['coverage_percentage']:.1f}%")
    print(f"  Processed: {status['repositories_processed']}/{status['total_repositories']}")
    print(f"  Failed: {status['repositories_failed']}")

    if args.verbose:
        print("\nDetailed Status:")
        print(json.dumps(status, indent=2, default=str))


def report_rollout(args):
    """Generate rollout report."""
    print(f"📋 Generating rollout report for {args.organization}")

    config = create_default_rollout_config(args.organization, 100)
    manager = GradualRolloutManager(config)

    report = manager.generate_rollout_report()

    # Print summary
    summary = report["rollout_summary"]
    print("\n📊 ROLLOUT SUMMARY")
    print(f"Organization: {summary['organization']}")
    print(f"Strategy: {summary['strategy']}")
    print(f"Final Phase: {summary['final_phase']}")
    print(f"Duration: {summary['total_duration_hours']:.1f} hours")
    print(f"Success Rate: {summary['overall_success_rate']:.1%}")
    print(f"Processed: {summary['total_repositories_processed']}")
    print(f"Failed: {summary['total_repositories_failed']}")

    # Print recommendations
    print("\n💡 RECOMMENDATIONS:")
    for i, rec in enumerate(report["recommendations"], 1):
        print(f"  {i}. {rec}")

    # Save full report if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n📁 Full report saved to: {args.output}")


def create_config(args):
    """Create a rollout configuration file."""
    print(f"⚙️ Creating rollout configuration for {args.organization}")

    config = create_default_rollout_config(args.organization, args.total_repositories)

    # Customize based on arguments
    if args.strategy:
        config.strategy = RolloutStrategy(args.strategy)
    if args.canary_percentage:
        config.canary_percentage = args.canary_percentage / 100
    if args.max_concurrent:
        config.max_concurrent_repositories = args.max_concurrent

    # Convert to dict for JSON serialization
    config_dict = {
        "organization": config.organization,
        "strategy": config.strategy.value,
        "total_repositories": config.total_repositories,
        "pilot_repositories": config.pilot_repositories,
        "canary_percentage": config.canary_percentage,
        "gradual_percentage_steps": config.gradual_percentage_steps,
        "phase_duration_hours": config.phase_duration_hours,
        "success_threshold": config.success_threshold,
        "rollback_threshold": config.rollback_threshold,
        "max_concurrent_repositories": config.max_concurrent_repositories,
        "excluded_repositories": config.excluded_repositories,
        "priority_repositories": config.priority_repositories,
    }

    output_file = args.output or f"rollout_config_{args.organization}.json"

    with open(output_file, "w") as f:
        json.dump(config_dict, f, indent=2)

    print(f"✅ Configuration saved to: {output_file}")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Gradual Rollout Manager for North Star Metrics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start a new rollout
  python rollout_manager.py start myorg --total-repositories 500
  
  # Continue an existing rollout
  python rollout_manager.py continue myorg
  
  # Check rollout status
  python rollout_manager.py status myorg
  
  # Generate rollout report
  python rollout_manager.py report myorg --output rollout_report.json
  
  # Create custom configuration
  python rollout_manager.py config myorg --strategy percentage --canary-percentage 10
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Start command
    start_parser = subparsers.add_parser("start", help="Start a new gradual rollout")
    start_parser.add_argument("organization", help="Organization name")
    start_parser.add_argument(
        "--total-repositories", type=int, required=True, help="Total number of repositories"
    )
    start_parser.add_argument(
        "--strategy",
        choices=["percentage", "repository", "team", "time", "hybrid"],
        help="Rollout strategy",
    )
    start_parser.add_argument("--canary-percentage", type=float, help="Canary percentage (0-100)")
    start_parser.add_argument("--max-concurrent", type=int, help="Maximum concurrent repositories")
    start_parser.add_argument("--config-file", help="JSON configuration file")
    start_parser.set_defaults(func=start_rollout)

    # Continue command
    continue_parser = subparsers.add_parser("continue", help="Continue an existing rollout")
    continue_parser.add_argument("organization", help="Organization name")
    continue_parser.set_defaults(func=continue_rollout)

    # Pause command
    pause_parser = subparsers.add_parser("pause", help="Pause an active rollout")
    pause_parser.add_argument("organization", help="Organization name")
    pause_parser.set_defaults(func=pause_rollout)

    # Resume command
    resume_parser = subparsers.add_parser("resume", help="Resume a paused rollout")
    resume_parser.add_argument("organization", help="Organization name")
    resume_parser.set_defaults(func=resume_rollout)

    # Rollback command
    rollback_parser = subparsers.add_parser("rollback", help="Rollback a rollout")
    rollback_parser.add_argument("organization", help="Organization name")
    rollback_parser.set_defaults(func=rollback_rollout)

    # Status command
    status_parser = subparsers.add_parser("status", help="Get rollout status")
    status_parser.add_argument("organization", help="Organization name")
    status_parser.add_argument("--verbose", action="store_true", help="Show detailed status")
    status_parser.set_defaults(func=status_rollout)

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate rollout report")
    report_parser.add_argument("organization", help="Organization name")
    report_parser.add_argument("--output", help="Output file for report")
    report_parser.set_defaults(func=report_rollout)

    # Config command
    config_parser = subparsers.add_parser("config", help="Create rollout configuration")
    config_parser.add_argument("organization", help="Organization name")
    config_parser.add_argument(
        "--total-repositories", type=int, required=True, help="Total number of repositories"
    )
    config_parser.add_argument(
        "--strategy",
        choices=["percentage", "repository", "team", "time", "hybrid"],
        help="Rollout strategy",
    )
    config_parser.add_argument("--canary-percentage", type=float, help="Canary percentage (0-100)")
    config_parser.add_argument("--max-concurrent", type=int, help="Maximum concurrent repositories")
    config_parser.add_argument("--output", help="Output file for configuration")
    config_parser.set_defaults(func=create_config)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n⏹️ Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
