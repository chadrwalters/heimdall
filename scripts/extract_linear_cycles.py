#!/usr/bin/env python3
"""Extract Linear cycle data for metrics analysis."""
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.linear.linear_client import LinearClient
from src.data.name_unifier import NameUnifier


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

    # Initialize clients
    client = LinearClient()
    unifier = NameUnifier(name_config)

    # Get all cycles for team
    print("Fetching cycles...")
    cycles = client.get_cycles(team_key=team_key)
    print(f"  Found {len(cycles)} cycles")

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
        issues = client.get_cycle_issues(cycle_id)
        print(f"  Found {len(issues)} issues")

        for issue in issues:
            assignee_name = issue.get("assignee", {}).get("name") if issue.get("assignee") else None
            if assignee_name:
                assignee_name = unifier.unify(linear_name=assignee_name)

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

    # Create DataFrame and save
    df = pd.DataFrame(all_data)
    df.to_csv(output_file, index=False)

    print(f"\n✅ Saved {len(all_data)} cycle issues to: {output_file}")

    # Print summary
    if len(df) > 0:
        print("\nSummary by Cycle:")
        summary = df.groupby(["cycle_number", "cycle_name"]).agg({
            "issue_identifier": "count",
            "estimate": "sum"
        }).rename(columns={
            "issue_identifier": "issue_count",
            "estimate": "total_estimate"
        })
        print(summary)


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
