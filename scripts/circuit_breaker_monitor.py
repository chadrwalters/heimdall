#!/usr/bin/env python3
"""Circuit breaker monitoring CLI tool."""

import argparse
import json
import sys
import time
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from resilience.monitoring import (
    export_circuit_breaker_report,
    get_circuit_breaker_details,
    get_circuit_breaker_health,
    get_circuit_breaker_trends,
)
from resilience.circuit_breaker import get_all_circuit_breaker_stats, reset_all_circuit_breakers


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Monitor and manage circuit breakers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python circuit_breaker_monitor.py status
  python circuit_breaker_monitor.py trends --hours 24
  python circuit_breaker_monitor.py details claude-api
  python circuit_breaker_monitor.py report --format summary
  python circuit_breaker_monitor.py watch --interval 5
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show current circuit breaker status")
    status_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    # Trends command
    trends_parser = subparsers.add_parser("trends", help="Show circuit breaker trends")
    trends_parser.add_argument("--hours", type=int, default=24, help="Time period in hours")
    trends_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    # Details command
    details_parser = subparsers.add_parser("details", help="Show details for a specific circuit breaker")
    details_parser.add_argument("name", help="Circuit breaker name")
    details_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Generate circuit breaker report")
    report_parser.add_argument("--format", choices=["json", "summary"], default="summary", 
                             help="Report format")
    report_parser.add_argument("--output", help="Output file path")
    
    # Watch command
    watch_parser = subparsers.add_parser("watch", help="Watch circuit breaker status")
    watch_parser.add_argument("--interval", type=int, default=5, help="Update interval in seconds")
    
    # Reset command
    reset_parser = subparsers.add_parser("reset", help="Reset all circuit breakers")
    reset_parser.add_argument("--confirm", action="store_true", help="Confirm reset action")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all circuit breakers")
    list_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "status":
            handle_status(args)
        elif args.command == "trends":
            handle_trends(args)
        elif args.command == "details":
            handle_details(args)
        elif args.command == "report":
            handle_report(args)
        elif args.command == "watch":
            handle_watch(args)
        elif args.command == "reset":
            handle_reset(args)
        elif args.command == "list":
            handle_list(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def handle_status(args):
    """Handle status command."""
    health = get_circuit_breaker_health()
    
    if args.json:
        print(json.dumps(health, indent=2))
    else:
        print(f"Overall Health: {health['overall_health'].upper()}")
        print(f"Total Breakers: {health['total_breakers']}")
        print(f"States: {health['breaker_states']}")
        
        if health['alerts']:
            print("\nAlerts:")
            for alert in health['alerts']:
                print(f"  [{alert['level'].upper()}] {alert['breaker']}: {alert['message']}")
        else:
            print("\nNo active alerts")


def handle_trends(args):
    """Handle trends command."""
    trends = get_circuit_breaker_trends(args.hours)
    
    if args.json:
        print(json.dumps(trends, indent=2))
    else:
        print(f"Trends for last {args.hours} hours:")
        print(f"Total checks: {trends.get('total_checks', 0)}")
        print(f"Average success rate: {trends.get('average_success_rate', 0):.2%}")
        print(f"Health distribution: {trends.get('health_distribution', {})}")
        
        if trends.get('most_problematic_breakers'):
            print("\nMost problematic breakers:")
            for breaker, count in trends['most_problematic_breakers'].items():
                print(f"  {breaker}: {count} issues")


def handle_details(args):
    """Handle details command."""
    details = get_circuit_breaker_details(args.name)
    
    if args.json:
        print(json.dumps(details, indent=2))
    else:
        if 'error' in details:
            print(f"Error: {details['error']}")
            return
        
        stats = details['current_stats']
        print(f"Circuit Breaker: {details['name']}")
        print(f"State: {stats['state'].upper()}")
        print(f"Total calls: {stats['total_calls']}")
        print(f"Success rate: {stats['success_rate']:.2%}")
        print(f"Consecutive failures: {stats['consecutive_failures']}")
        
        if details.get('recommendations'):
            print("\nRecommendations:")
            for rec in details['recommendations']:
                print(f"  - {rec}")


def handle_report(args):
    """Handle report command."""
    report = export_circuit_breaker_report(args.format)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Report saved to {args.output}")
    else:
        print(report)


def handle_watch(args):
    """Handle watch command."""
    print(f"Watching circuit breakers (update every {args.interval}s)...")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            # Clear screen
            import os
            os.system('clear' if os.name == 'posix' else 'cls')
            
            # Show current status
            print(f"Circuit Breaker Status - {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)
            
            health = get_circuit_breaker_health()
            print(f"Overall Health: {health['overall_health'].upper()}")
            print(f"Total Breakers: {health['total_breakers']}")
            
            # Show each breaker
            for name, stats in health['details'].items():
                status_icon = "🟢" if stats['state'] == 'closed' else "🔴" if stats['state'] == 'open' else "🟡"
                print(f"{status_icon} {name}: {stats['state']} "
                      f"({stats['success_rate']:.1%} success, "
                      f"{stats['total_calls']} calls)")
            
            if health['alerts']:
                print("\nAlerts:")
                for alert in health['alerts']:
                    print(f"  ⚠️  [{alert['level'].upper()}] {alert['breaker']}: {alert['message']}")
            
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped watching")


def handle_reset(args):
    """Handle reset command."""
    if not args.confirm:
        response = input("Are you sure you want to reset all circuit breakers? (y/N): ")
        if response.lower() != 'y':
            print("Reset cancelled")
            return
    
    reset_all_circuit_breakers()
    print("All circuit breakers have been reset")


def handle_list(args):
    """Handle list command."""
    stats = get_all_circuit_breaker_stats()
    
    if args.json:
        print(json.dumps(list(stats.keys()), indent=2))
    else:
        print("Registered circuit breakers:")
        for name in sorted(stats.keys()):
            state = stats[name]['state']
            print(f"  {name}: {state}")


if __name__ == "__main__":
    main()