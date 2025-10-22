#!/usr/bin/env python3
"""Extract ALL merged PRs using GitHub API directly (not git merge commits)."""

import os
import sys
from datetime import datetime, timedelta, timezone
import json
import requests
import pandas as pd
from pathlib import Path


def get_all_merged_prs(org: str, repo: str, since_date: str, github_token: str) -> list:
    """Get all merged PRs from GitHub API."""
    headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3+json"}

    all_prs = []
    page = 1

    while True:
        # Get merged PRs
        url = f"https://api.github.com/repos/{org}/{repo}/pulls"
        params = {
            "state": "closed",
            "sort": "updated",
            "direction": "desc",
            "per_page": 100,
            "page": page,
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"  ⚠️  Error fetching PRs: {response.status_code}")
            break

        prs = response.json()

        if not prs:
            break

        # Filter to only merged PRs within date range
        for pr in prs:
            merged_at = pr.get("merged_at")
            if merged_at and merged_at >= since_date:
                all_prs.append(pr)
            elif merged_at and merged_at < since_date:
                # PRs are sorted by update time, if we hit an old one, stop
                return all_prs

        # Check if we should continue
        if len(prs) < 100:
            break

        page += 1

        # Rate limit check
        remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
        if remaining < 10:
            print(f"  ⚠️  Rate limit low: {remaining} remaining")
            break

    return all_prs


def extract_pr_data(pr: dict, org: str, repo: str) -> dict:
    """Extract relevant PR data."""
    # Extract Linear ticket ID
    title = pr.get("title", "")
    body = pr.get("body") or ""
    linear_id = None

    # Check title and body for Linear ticket patterns
    import re

    patterns = [r"[A-Z]+-\d+", r"\[([A-Z]+-\d+)\]"]
    for pattern in patterns:
        for text in [title, body]:
            match = re.search(pattern, text)
            if match:
                linear_id = match.group(1) if "(" in pattern else match.group(0)
                break
        if linear_id:
            break

    return {
        "repository": repo,
        "pr_number": pr["number"],
        "pr_id": f"{org}/{repo}#{pr['number']}",
        "title": title,
        "author": pr.get("user", {}).get("login", ""),
        "state": pr.get("state", ""),
        "created_at": pr.get("created_at", ""),
        "merged_at": pr.get("merged_at", ""),
        "closed_at": pr.get("closed_at", ""),
        "url": pr.get("html_url", ""),
        "base_branch": pr.get("base", {}).get("ref", ""),
        "head_branch": pr.get("head", {}).get("ref", ""),
        "additions": pr.get("additions", 0),
        "deletions": pr.get("deletions", 0),
        "changed_files": pr.get("changed_files", 0),
        "commits": pr.get("commits", 0),
        "linear_ticket_id": linear_id,
        "has_linear_ticket": bool(linear_id),
        "labels": ",".join([label["name"] for label in pr.get("labels", [])]),
        "assignees": ",".join([assignee["login"] for assignee in pr.get("assignees", [])]),
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Extract merged PRs from GitHub API")
    parser.add_argument("--org", default="degree-analytics", help="Organization name")
    parser.add_argument("--days", type=int, default=294, help="Days back to extract")
    parser.add_argument(
        "--incremental", action="store_true", help="Incremental mode: deduplicate existing PRs"
    )
    parser.add_argument("--output", default="org_prs_api.csv", help="Output CSV file")
    args = parser.parse_args()

    # Get environment variables
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("❌ GITHUB_TOKEN not set")
        sys.exit(1)

    org = args.org
    days = args.days
    incremental = args.incremental
    output_file = args.output

    # Calculate since date
    since_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    print(f"📊 Extracting ALL merged PRs for {org} ({days} days)")
    print(f"📅 Since: {since_date}")
    print()

    # Load repository list
    repos_file = Path("degree-analytics_repos.json")
    if not repos_file.exists():
        print(f"❌ Repository list not found: {repos_file}")
        sys.exit(1)

    with open(repos_file) as f:
        repos_data = json.load(f)

    repos = [r["name"] for r in repos_data]
    print(f"📂 Found {len(repos)} repositories")
    print()

    all_pr_data = []

    for i, repo in enumerate(repos, 1):
        print(f"[{i}/{len(repos)}] {repo}...", end=" ", flush=True)

        try:
            prs = get_all_merged_prs(org, repo, since_date, github_token)

            for pr in prs:
                pr_data = extract_pr_data(pr, org, repo)
                all_pr_data.append(pr_data)

            print(f"✅ {len(prs)} PRs")

        except Exception as e:
            print(f"❌ Error: {e}")
            continue

    print()
    print(f"📊 Total PRs extracted: {len(all_pr_data)}")

    if all_pr_data:
        new_df = pd.DataFrame(all_pr_data)

        # Handle incremental mode with deduplication
        if incremental and Path(output_file).exists():
            print(f"📂 Loading existing PRs from {output_file}...")
            existing_df = pd.read_csv(output_file)
            combined_df = pd.concat([existing_df, new_df])
            df = combined_df.drop_duplicates(subset=["number", "repository"], keep="first")

            added_count = len(df) - len(existing_df)
            deduped_count = len(new_df) - added_count

            df.to_csv(output_file, index=False)
            print(f"✅ Added {added_count} new PRs (deduped {deduped_count}) to {output_file}")
        else:
            df = new_df
            df.to_csv(output_file, index=False)
            print(f"✅ Saved {len(df)} PRs to {output_file}")

        # Show summary stats
        print()
        print("📈 Summary:")
        print(f"  Total PRs in file: {len(df)}")
        print(
            f"  With Linear tickets: {df['has_linear_ticket'].sum()} ({df['has_linear_ticket'].mean() * 100:.1f}%)"
        )
        print(f"  Top contributors: {df['author'].value_counts().head(5).to_dict()}")
        print(f"  Top repositories: {df['repository'].value_counts().head(5).to_dict()}")
    else:
        print("⚠️  No PRs found")


if __name__ == "__main__":
    main()
