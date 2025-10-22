"""Git-based data extractor to replace bash scripts."""

import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from requests.auth import HTTPBasicAuth

from .config import GitExtractionConfig
from .extraction_utils import ExtractionUtils
from .input_validation import ValidationError, validate_git_operation_inputs
from .rate_limiter import RateLimitedSession
from .repository_service import GitRepositoryService

logger = logging.getLogger(__name__)


class GitDataExtractor:
    """Extract data using local git repositories with minimal GitHub API calls."""

    def __init__(self, github_token: str, config: Optional[GitExtractionConfig] = None):
        """Initialize the git data extractor.

        Args:
            github_token: GitHub token for authentication
            config: Configuration instance (creates default if None)
        """
        self.github_token = github_token
        self.config = config or GitExtractionConfig.from_environment()
        self.config.validate()

        self.repo_service = GitRepositoryService(self.config)

        # Use rate-limited session for GitHub API calls
        self.session = RateLimitedSession()
        self.session.auth = HTTPBasicAuth(github_token, "")
        self.session.headers.update(
            {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        )

        # Configure logging
        self.config.configure_logging()

    def get_organization_repos(self, org: str) -> List[Dict[str, Any]]:
        """Get list of repositories for an organization.

        This is one of the few operations that requires GitHub API.

        Args:
            org: Organization name

        Returns:
            List of repository dictionaries

        Raises:
            ValidationError: If input validation fails
            requests.exceptions.RequestException: If API calls fail
        """
        # Validate organization name
        if self.config.validate_inputs:
            try:
                org = validate_git_operation_inputs(org, "dummy")[0]
            except ValidationError as e:
                logger.error(f"Invalid organization name '{org}': {e}")
                raise

        logger.info(f"Fetching repository list for {org}")

        repos = []
        page = 1
        per_page = 100

        while True:
            url = f"https://api.github.com/orgs/{org}/repos"
            params = {
                "type": "all",
                "sort": "updated",
                "direction": "desc",
                "per_page": per_page,
                "page": page,
            }

            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()

                page_repos = response.json()
                if not page_repos:
                    break

                # Filter out archived repos
                active_repos = [repo for repo in page_repos if not repo.get("archived", False)]
                repos.extend(active_repos)

                logger.info(f"Retrieved {len(active_repos)} active repos from page {page}")

                if len(page_repos) < per_page:
                    break

                page += 1

            except requests.exceptions.RequestException as e:
                logger.error(f"API request failed for {org}: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error fetching repos for {org}: {e}")
                raise

        logger.info(f"Found {len(repos)} total active repositories for {org}")
        return repos

    def get_pr_metadata(
        self, org: str, repo: str, pr_numbers: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Get PR metadata from GitHub API for specific PR numbers.

        Args:
            org: Organization name
            repo: Repository name
            pr_numbers: List of PR numbers to fetch

        Returns:
            Dictionary mapping PR numbers to PR metadata
        """
        if not pr_numbers:
            return {}

        logger.info(f"Fetching metadata for {len(pr_numbers)} PRs from {org}/{repo}")

        pr_metadata = {}

        for pr_number in pr_numbers:
            try:
                url = f"https://api.github.com/repos/{org}/{repo}/pulls/{pr_number}"
                response = self.session.get(url)

                if response.status_code == 200:
                    pr_data = response.json()
                    pr_metadata[pr_number] = {
                        "title": pr_data.get("title", ""),
                        "body": pr_data.get("body", ""),
                        "user_login": pr_data.get("user", {}).get("login", ""),
                        "created_at": pr_data.get("created_at", ""),
                        "merged_at": pr_data.get("merged_at", ""),
                        "closed_at": pr_data.get("closed_at", ""),
                        "state": pr_data.get("state", ""),
                        "html_url": pr_data.get("html_url", ""),
                        "base_ref": pr_data.get("base", {}).get("ref", ""),
                        "head_ref": pr_data.get("head", {}).get("ref", ""),
                        "labels": [label.get("name", "") for label in pr_data.get("labels", [])],
                        "assignees": [
                            assignee.get("login", "") for assignee in pr_data.get("assignees", [])
                        ],
                        "reviewers": [
                            reviewer.get("login", "")
                            for reviewer in pr_data.get("requested_reviewers", [])
                        ],
                    }
                else:
                    logger.warning(f"Failed to fetch PR #{pr_number}: {response.status_code}")

            except requests.exceptions.RequestException as e:
                logger.error(f"API request failed for PR #{pr_number} from {org}/{repo}: {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error fetching PR #{pr_number} from {org}/{repo}: {e}")
                continue

        logger.info(f"Retrieved metadata for {len(pr_metadata)} PRs")
        return pr_metadata

    def extract_commits_data(self, org: str, repos: List[str], days_back: int = 7) -> pd.DataFrame:
        """Extract commit data using local git repositories.

        Args:
            org: Organization name
            repos: List of repository names
            days_back: Number of days to go back

        Returns:
            DataFrame with commit data
        """
        logger.info(f"Extracting commit data for {len(repos)} repositories ({days_back} days)")

        since_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).isoformat()
        all_commits = []

        for repo in repos:
            try:
                # Clone or update repository
                repo_path = self.repo_service.clone_or_update_repo(org, repo, self.github_token)

                # CHANGED: Use get_commits_since to get ALL commits, not just PR merges
                # Start from date, not last analyzed commit for full extraction
                commits = self.repo_service.get_commits_since(
                    repo_path,
                    since_commit=None,  # Start from date, not last analyzed commit
                    since_date=since_date,
                )

                # Filter to main/dev branches only
                main_branch_commits = [c for c in commits if c.get("on_main_branch", False)]

                # Add repository name to each commit
                for commit in main_branch_commits:
                    commit["repository"] = repo
                    commit["organization"] = org

                all_commits.extend(main_branch_commits)

                # Update last analyzed commit
                if main_branch_commits:
                    latest_commit = main_branch_commits[0][
                        "sha"
                    ]  # Commits are in reverse chronological order
                    self.repo_service.update_last_analyzed_commit(org, repo, latest_commit)

                logger.info(f"Extracted {len(main_branch_commits)} commits from {repo}")

            except ValidationError as e:
                logger.error(f"Input validation failed for {repo}: {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error extracting commits from {repo}: {e}")
                continue

        # Convert to DataFrame
        if all_commits:
            df = pd.DataFrame(all_commits)

            # Flatten stats
            df["files_changed"] = df["stats"].apply(lambda x: x.get("files_changed", 0))
            df["additions"] = df["stats"].apply(lambda x: x.get("insertions", 0))
            df["deletions"] = df["stats"].apply(lambda x: x.get("deletions", 0))
            df["total_lines"] = df["stats"].apply(lambda x: x.get("lines", 0))

            # Add URL (GitHub format)
            df["url"] = df.apply(
                lambda row: f"https://github.com/{row['organization']}/{row['repository']}/commit/{row['sha']}",
                axis=1,
            )

            # Extract co-authors using utility function
            df["co_authors"] = df["message"].apply(ExtractionUtils.extract_co_authors)

            # Detect AI assistance using utility function
            df["ai_assisted"] = df.apply(
                lambda row: ExtractionUtils.detect_ai_assistance(row["message"], row["co_authors"]),
                axis=1,
            )

            # Reorder columns to match expected format
            columns = [
                "repository",
                "sha",
                "author_name",
                "author_email",
                "committer_name",
                "committer_email",
                "committed_date",
                "message",
                "url",
                "pr_number",
                "files_changed",
                "additions",
                "deletions",
                "is_merge",
                "on_main_branch",
                "co_authors",
                "linear_ticket_id",
                "ai_assisted",
            ]

            # Only include columns that exist
            existing_columns = [col for col in columns if col in df.columns]
            df = df[existing_columns]

            logger.info(f"Extracted {len(df)} total commits")
            return df
        else:
            logger.warning("No commits extracted")
            return pd.DataFrame()

    def extract_pr_data(self, org: str, repos: List[str], days_back: int = 7) -> pd.DataFrame:
        """Extract PR data directly from GitHub API.

        Args:
            org: Organization name
            repos: List of repository names
            days_back: Number of days to go back

        Returns:
            DataFrame with PR data
        """
        logger.info(f"Extracting PR data for {len(repos)} repositories ({days_back} days)")

        since_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        all_prs = []

        for repo in repos:
            try:
                # Get PRs directly from GitHub API
                logger.info(f"Fetching PRs from {org}/{repo} via GitHub API")

                # Get merged PRs using GitHub API
                url = f"https://api.github.com/repos/{org}/{repo}/pulls"
                params = {
                    "state": "closed",  # Get closed PRs
                    "sort": "updated",
                    "direction": "desc",
                    "per_page": 100,
                }

                page = 1
                repo_prs = []

                while True:
                    params["page"] = page
                    response = self.session.get(url, params=params)
                    response.raise_for_status()

                    prs = response.json()
                    if not prs:
                        break

                    # Filter PRs by merge date
                    for pr in prs:
                        merged_at = pr.get("merged_at")
                        if merged_at:
                            merged_date = datetime.fromisoformat(merged_at.replace("Z", "+00:00"))
                            if merged_date >= since_date:
                                repo_prs.append(pr)
                            else:
                                # PRs are sorted by updated date, so stop if we hit old PRs
                                break

                    # Stop if we've gone past our date range
                    if prs and not pr.get("merged_at"):
                        # Check updated_at if no merged_at
                        last_updated = datetime.fromisoformat(
                            prs[-1]["updated_at"].replace("Z", "+00:00")
                        )
                        if last_updated < since_date:
                            break

                    if len(prs) < 100:
                        break

                    page += 1
                    if page > 10:  # Safety limit
                        break

                # Fetch detailed PR information to get file statistics
                logger.info(f"Fetching details for {len(repo_prs)} PRs from {repo}")
                for pr in repo_prs:
                    # Fetch individual PR to get file statistics
                    pr_detail_url = (
                        f"https://api.github.com/repos/{org}/{repo}/pulls/{pr['number']}"
                    )
                    try:
                        pr_detail_response = self.session.get(pr_detail_url)
                        pr_detail_response.raise_for_status()
                        pr_detail = pr_detail_response.json()

                        # Update PR with detailed file statistics
                        pr["additions"] = pr_detail.get("additions", 0)
                        pr["deletions"] = pr_detail.get("deletions", 0)
                        pr["changed_files"] = pr_detail.get("changed_files", 0)

                    except requests.exceptions.RequestException as e:
                        logger.warning(f"Failed to fetch details for PR #{pr['number']}: {e}")
                        # Keep defaults of 0 if detail fetch fails
                        pass

                # Process each PR
                for pr in repo_prs:
                    pr_data = {
                        "repository": repo,
                        "pr_number": str(pr["number"]),
                        "pr_id": f"{org}/{repo}#{pr['number']}",
                        "title": pr.get("title", ""),
                        "body": pr.get("body", ""),
                        "author": pr.get("user", {}).get("login", ""),
                        "state": "merged" if pr.get("merged_at") else pr.get("state", ""),
                        "created_at": pr.get("created_at", ""),
                        "merged_at": pr.get("merged_at", ""),
                        "closed_at": pr.get("closed_at", ""),
                        "url": pr.get("html_url", ""),
                        "base_branch": pr.get("base", {}).get("ref", ""),
                        "head_branch": pr.get("head", {}).get("ref", ""),
                        "files_changed": pr.get("changed_files", 0),
                        "additions": pr.get("additions", 0),
                        "deletions": pr.get("deletions", 0),
                        "merge_commit_sha": pr.get("merge_commit_sha", ""),
                        "labels": ",".join(
                            [label.get("name", "") for label in pr.get("labels", [])]
                        ),
                        "assignees": ",".join(
                            [assignee.get("login", "") for assignee in pr.get("assignees", [])]
                        ),
                    }

                    # Extract Linear ticket ID from title or body
                    pr_data["linear_ticket_id"] = ExtractionUtils.extract_linear_ticket_id(
                        pr_data["title"] + " " + (pr_data["body"] or "")
                    )
                    pr_data["has_linear_ticket"] = bool(pr_data["linear_ticket_id"])

                    all_prs.append(pr_data)

                logger.info(f"Extracted {len(repo_prs)} PRs from {repo}")

            except ValidationError as e:
                logger.error(f"Input validation failed for {repo}: {e}")
                continue
            except requests.exceptions.RequestException as e:
                logger.error(f"API request failed for {org}/{repo}: {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error extracting PRs from {repo}: {e}")
                continue

        # Convert to DataFrame
        if all_prs:
            df = pd.DataFrame(all_prs)
            logger.info(f"Extracted {len(df)} total PRs")
            return df
        else:
            logger.warning("No PRs extracted")
            return pd.DataFrame()

    def extract_organization_data(
        self,
        org: str,
        days_back: int = 7,
        output_commits: str = "org_commits.csv",
        output_prs: str = "org_prs.csv",
        incremental: bool = False,
    ) -> Dict[str, Any]:
        """Extract all data for an organization.

        Args:
            org: Organization name
            days_back: Number of days to go back
            output_commits: Output file for commits
            output_prs: Output file for PRs
            incremental: If True, append only new data (deduplicate)

        Returns:
            Dictionary with extraction results
        """
        logger.info(f"Starting full extraction for {org} ({days_back} days)")

        # Get repository list (GitHub API call)
        repos_data = self.get_organization_repos(org)
        repo_names = [repo["name"] for repo in repos_data]

        # Save repo list for reference
        repos_file = f"{org}_repos.json"
        with open(repos_file, "w") as f:
            json.dump(repos_data, f, indent=2)

        # Extract commits data (git-based)
        commits_df = self.extract_commits_data(org, repo_names, days_back)
        commits_added = 0
        commits_deduped = 0
        if not commits_df.empty:
            if incremental and Path(output_commits).exists():
                # Load existing and deduplicate
                existing_commits = pd.read_csv(output_commits)
                combined = pd.concat([existing_commits, commits_df])
                deduped = combined.drop_duplicates(subset=["sha"], keep="first")
                commits_added = len(deduped) - len(existing_commits)
                commits_deduped = len(commits_df) - commits_added
                deduped.to_csv(output_commits, index=False)
                logger.info(
                    f"Added {commits_added} new commits (deduped {commits_deduped}) to {output_commits}"
                )
            else:
                commits_df.to_csv(output_commits, index=False)
                commits_added = len(commits_df)
                logger.info(f"Saved {len(commits_df)} commits to {output_commits}")

        # Extract PR data (git + GitHub API)
        prs_df = self.extract_pr_data(org, repo_names, days_back)
        prs_added = 0
        prs_deduped = 0
        if not prs_df.empty:
            if incremental and Path(output_prs).exists():
                # Load existing and deduplicate by (number, repository)
                existing_prs = pd.read_csv(output_prs)
                combined = pd.concat([existing_prs, prs_df])
                deduped = combined.drop_duplicates(subset=["number", "repository"], keep="first")
                prs_added = len(deduped) - len(existing_prs)
                prs_deduped = len(prs_df) - prs_added
                deduped.to_csv(output_prs, index=False)
                logger.info(f"Added {prs_added} new PRs (deduped {prs_deduped}) to {output_prs}")
            else:
                prs_df.to_csv(output_prs, index=False)
                prs_added = len(prs_df)
                logger.info(f"Saved {len(prs_df)} PRs to {output_prs}")

        # Generate summary
        summary = {
            "organization": org,
            "days_back": days_back,
            "repositories_found": len(repo_names),
            "commits_extracted": len(commits_df) if not commits_df.empty else 0,
            "prs_extracted": len(prs_df) if not prs_df.empty else 0,
            "commits_file": output_commits,
            "prs_file": output_prs,
            "repos_file": repos_file,
            "extraction_time": datetime.now(timezone.utc).isoformat(),
            "incremental": incremental,
        }

        if incremental:
            summary["commits_added"] = commits_added
            summary["commits_deduped"] = commits_deduped
            summary["prs_added"] = prs_added
            summary["prs_deduped"] = prs_deduped

        # Calculate process compliance
        if not prs_df.empty:
            prs_with_tickets = prs_df["has_linear_ticket"].sum()
            compliance_rate = (prs_with_tickets / len(prs_df)) * 100
            summary["process_compliance_rate"] = round(compliance_rate, 2)
            summary["prs_with_linear_tickets"] = prs_with_tickets

        logger.info(f"Extraction complete for {org}")
        return summary

    # Removed duplicate methods - now using ExtractionUtils

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = self.repo_service.get_cache_stats()

        # Add rate limiting statistics
        if hasattr(self.session, "get_rate_limit_status"):
            stats["rate_limit_stats"] = self.session.get_rate_limit_status()

        return stats


def main():
    """Main entry point for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract data using git repositories")
    parser.add_argument("--org", required=True, help="Organization name")
    parser.add_argument("--days", type=int, default=7, help="Days back to extract")
    parser.add_argument(
        "--commits-output", default="org_commits.csv", help="Output file for commits"
    )
    parser.add_argument("--prs-output", default="org_prs.csv", help="Output file for PRs")

    args = parser.parse_args()

    # Get GitHub token
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        logger.error("GITHUB_TOKEN environment variable not set")
        sys.exit(1)

    # Setup logging
    config = GitExtractionConfig.from_environment()
    config.configure_logging()

    # Create extractor and run
    config = GitExtractionConfig.from_environment()
    extractor = GitDataExtractor(github_token, config)

    try:
        summary = extractor.extract_organization_data(
            args.org, args.days, args.commits_output, args.prs_output
        )

        print(json.dumps(summary, indent=2))

    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
