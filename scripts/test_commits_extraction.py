#!/usr/bin/env python3
"""Test git commits extraction separately."""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from git_extraction.git_extractor import GitDataExtractor
from git_extraction.config import GitExtractionConfig


def main():
    org = sys.argv[1] if len(sys.argv) > 1 else "test-org"
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 7

    print(f"Testing GIT COMMITS extraction for {org} ({days} days)...")
    print("=" * 80)

    config = GitExtractionConfig()
    github_token = os.getenv("GITHUB_TOKEN")

    if not github_token:
        print("❌ GITHUB_TOKEN not set")
        sys.exit(1)

    extractor = GitDataExtractor(github_token, config)

    print("Fetching repository list...")
    repos = extractor.get_organization_repos(org)
    print(f"Found {len(repos)} repositories")

    print(f"\nExtracting commits from first 3 repos for testing...")
    # repos is a list of dicts, get names
    repo_names = [r if isinstance(r, str) else r["name"] for r in repos[:3]]
    print(f"Test repos: {', '.join(repo_names)}")

    commits_df = extractor.extract_commits_data(org, repo_names, days)

    print(f"\n✅ Extracted {len(commits_df)} total commits")
    print(f"Columns: {list(commits_df.columns)}")

    if len(commits_df) > 0:
        print(f"\nSample commit:")
        print(
            commits_df[["repository", "author_name", "message", "on_main_branch"]]
            .head(1)
            .to_string()
        )
        print(f"\nOn main branch: {commits_df['on_main_branch'].sum()} / {len(commits_df)}")
        print(
            f"Percentage on main: {commits_df['on_main_branch'].sum() / len(commits_df) * 100:.1f}%"
        )
    else:
        print("\n⚠️ NO COMMITS EXTRACTED - This is the problem!")

    output_file = Path("src") / "test_commits.csv"
    commits_df.to_csv(output_file, index=False)
    print(f"\nSaved to: {output_file}")


if __name__ == "__main__":
    main()
