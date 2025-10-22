#!/usr/bin/env python3
"""Collect AI usage data from ccusage and ccusage-codex.

Generates combined JSON file with Claude Code and Codex usage for specified time period.
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any


def run_command(cmd: list[str]) -> Dict[str, Any]:
    """Run command and return parsed JSON output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running {cmd[0]}: {e.stderr}", file=sys.stderr)
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from {cmd[0]}: {e}", file=sys.stderr)
        return {}


def collect_usage(developer: str, days: int = 7) -> Dict[str, Any]:
    """Collect usage data from both ccusage and ccusage-codex.

    Args:
        developer: Developer canonical name
        days: Number of days to collect (default: 7)

    Returns:
        Combined usage data with metadata
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    since_str = start_date.strftime("%Y%m%d")

    print(f"📊 Collecting AI usage for {developer} (last {days} days)")
    print(f"   Date range: {start_date.date()} to {end_date.date()}")

    # Collect Claude Code usage
    print("   Fetching Claude Code usage...")
    claude_data = run_command([
        "ccusage", "daily", "--json", "--since", since_str
    ])

    # Collect Codex usage
    print("   Fetching Codex usage...")
    codex_data = run_command([
        "ccusage-codex", "daily", "--json", "--since", since_str
    ])

    # Combine with metadata
    combined = {
        "metadata": {
            "developer": developer,
            "collected_at": datetime.now().isoformat(),
            "date_range": {
                "start": start_date.date().isoformat(),
                "end": end_date.date().isoformat(),
                "days": days
            },
            "version": "1.0"
        },
        "claude_code": claude_data,
        "codex": codex_data
    }

    return combined


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python collect_ai_usage.py <developer> [days=7]")
        print("Example: python collect_ai_usage.py Chad 7")
        sys.exit(1)

    developer = sys.argv[1]
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 7

    # Collect data
    data = collect_usage(developer, days)

    # Generate output filename
    output_dir = Path("data/ai_usage/submissions")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_str = datetime.now().strftime("%Y%m%d")
    output_file = output_dir / f"ai_usage_{developer}_{date_str}_{timestamp}.json"

    # Write output
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\n✅ Usage data collected: {output_file}")
    print(f"   Claude Code: {len(data['claude_code'].get('daily', []))} days")
    print(f"   Codex: {len(data['codex'].get('daily', []))} days")

    # Show totals
    claude_totals = data['claude_code'].get('totals', {})
    codex_totals = data['codex'].get('totals', {})

    if claude_totals:
        print(f"\n💰 Claude Code Total Cost: ${claude_totals.get('totalCost', 0):.2f}")
        print(f"   Total Tokens: {claude_totals.get('totalTokens', 0):,}")

    if codex_totals:
        print(f"\n💰 Codex Total Cost: ${codex_totals.get('totalCost', 0):.2f}")
        print(f"   Total Tokens: {codex_totals.get('totalTokens', 0):,}")


if __name__ == "__main__":
    main()
