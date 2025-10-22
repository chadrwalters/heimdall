#!/usr/bin/env python3
"""Test GitHub PRs extraction separately."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from git_extraction.config import GitExtractionConfig
from git_extraction.git_extractor import GitDataExtractor


def main():
    org = sys.argv[1] if len(sys.argv) > 1 else "test-org"
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 7

    print(f"Testing GITHUB PRs extraction for {org} ({days} days)...")
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

    print("\nExtracting PRs from first 3 repos for testing...")
    # repos is a list of dicts, get names
    repo_names = [r if isinstance(r, str) else r["name"] for r in repos[:3]]
    print(f"Test repos: {', '.join(repo_names)}")

    prs_df = extractor.extract_pr_data(org, repo_names, days)

    print(f"\n✅ Extracted {len(prs_df)} total PRs")
    print(f"Columns: {list(prs_df.columns)}")

    if len(prs_df) > 0:
        print("\nSample PR:")
        print(prs_df[["repository", "title", "author", "state", "merged_at"]].head(1).to_string())
        print(f"\nMerged PRs: {prs_df['state'].value_counts().get('closed', 0)}")
    else:
        print("\n⚠️ NO PRs EXTRACTED - This might be the problem!")

    output_file = Path("src") / "test_prs.csv"
    prs_df.to_csv(output_file, index=False)
    print(f"\nSaved to: {output_file}")


if __name__ == "__main__":
    main()
