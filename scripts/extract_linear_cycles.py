#!/usr/bin/env python3
"""Extract Linear cycle data for metrics analysis."""
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.linear.linear_client import LinearClient
from src.config.team_config import team_config


def extract_cycle_data(
    team_key: str = "ENG",
    output_file: str = "linear_cycles.csv",
    name_config: str = "config/developer_names.json"
):
    """Extract cycle data from Linear.

    Args:
        team_key: Linear team key to filter cycles
        output_file: Output CSV filename
        name_config: Path to developer names config
    """
    print(f"Extracting Linear cycles for team: {team_key}")

    try:
        # Initialize Linear client (team config is already initialized as singleton)
        client = LinearClient()
    except Exception as e:
        print(f"❌ Error initializing Linear client: {e}")
        print("Please check your LINEAR_API_KEY environment variable.")
        sys.exit(1)

    # Get all cycles for team
    print("Fetching cycles...")
    try:
        cycles = client.get_cycles(team_key=team_key)
        if not cycles:
            print(f"⚠️  No cycles found for team: {team_key}")
            print("This could mean:")
            print("  - The team key is incorrect")
            print("  - The team has no cycles yet")
            print("  - Your API key doesn't have access to this team")
            return
        print(f"  Found {len(cycles)} cycles")
    except Exception as e:
        print(f"❌ Error fetching cycles: {e}")
        print("Please verify:")
        print("  - Your Linear API key is valid")
        print("  - The team key is correct")
        print("  - You have access to this team's data")
        sys.exit(1)

    # Extract issues for each cycle
    all_data = []

    for cycle in cycles:
        cycle_id = cycle["id"]
        cycle_num = cycle["number"]
        cycle_name = cycle["name"]
        cycle_start = cycle["startsAt"]
        cycle_end = cycle["endsAt"]

        print(f"\nProcessing Cycle {cycle_num}: {cycle_name}")
        print(f"  Period: {cycle_start} to {cycle_end}")

        # Get issues for this cycle
        try:
            issues = client.get_cycle_issues(cycle_id)
            if not issues:
                print(f"  ⚠️  No issues found in this cycle")
                continue
            print(f"  Found {len(issues)} issues")
        except Exception as e:
            print(f"  ❌ Error fetching issues for cycle {cycle_num}: {e}")
            print(f"  Skipping this cycle and continuing...")
            continue

        for issue in issues:
            try:
                assignee_name = issue.get("assignee", {}).get("name") if issue.get("assignee") else None
                if assignee_name:
                    assignee_name = team_config.get_canonical_name(assignee_name, source="linear")

                data = {
                    "cycle_id": cycle_id,
                    "cycle_number": cycle_num,
                    "cycle_name": cycle_name,
                    "cycle_start": cycle_start,
                    "cycle_end": cycle_end,
                    "issue_id": issue["id"],
                    "issue_identifier": issue["identifier"],
                    "issue_title": issue["title"],
                    "assignee_name": assignee_name,
                    "estimate": issue.get("estimate"),
                    "priority": issue.get("priority"),
                    "state_type": issue.get("state", {}).get("type"),
                    "state_name": issue.get("state", {}).get("name"),
                    "created_at": issue.get("createdAt"),
                    "completed_at": issue.get("completedAt"),
                }
                all_data.append(data)
            except Exception as e:
                print(f"  ⚠️  Error processing issue {issue.get('identifier', 'unknown')}: {e}")
                print(f"  Skipping this issue and continuing...")
                continue

    # Create DataFrame and save
    if not all_data:
        print("\n⚠️  No data extracted. No output file created.")
        print("Please check the warnings above for details.")
        return

    try:
        df = pd.DataFrame(all_data)
        df.to_csv(output_file, index=False)
        print(f"\n✅ Saved {len(all_data)} cycle issues to: {output_file}")
    except Exception as e:
        print(f"\n❌ Error saving to CSV: {e}")
        sys.exit(1)

    # Print summary
    if len(df) > 0:
        print("\nSummary by Cycle:")
        try:
            summary = df.groupby(["cycle_number", "cycle_name"]).agg({
                "issue_identifier": "count",
                "estimate": "sum"
            }).rename(columns={
                "issue_identifier": "issue_count",
                "estimate": "total_estimate"
            })
            print(summary)
        except Exception as e:
            print(f"⚠️  Error generating summary: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract Linear cycle data")
    parser.add_argument(
        "--team",
        default="ENG",
        help="Linear team key (default: ENG)"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="linear_cycles.csv",
        help="Output CSV file"
    )
    parser.add_argument(
        "--name-config",
        default="config/developer_names.json",
        help="Developer names configuration"
    )

    args = parser.parse_args()
    extract_cycle_data(args.team, args.output, args.name_config)
