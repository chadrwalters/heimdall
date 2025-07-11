"""Git-based data extractor to replace bash scripts."""

import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
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
        self.session.auth = HTTPBasicAuth(github_token, '')
        self.session.headers.update({
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        })
        
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
                'type': 'all',
                'sort': 'updated',
                'direction': 'desc',
                'per_page': per_page,
                'page': page
            }
            
            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()
                
                page_repos = response.json()
                if not page_repos:
                    break
                
                # Filter out archived repos
                active_repos = [repo for repo in page_repos if not repo.get('archived', False)]
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
    
    def get_pr_metadata(self, org: str, repo: str, pr_numbers: List[str]) -> Dict[str, Dict[str, Any]]:
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
                        'title': pr_data.get('title', ''),
                        'body': pr_data.get('body', ''),
                        'user_login': pr_data.get('user', {}).get('login', ''),
                        'created_at': pr_data.get('created_at', ''),
                        'merged_at': pr_data.get('merged_at', ''),
                        'closed_at': pr_data.get('closed_at', ''),
                        'state': pr_data.get('state', ''),
                        'html_url': pr_data.get('html_url', ''),
                        'base_ref': pr_data.get('base', {}).get('ref', ''),
                        'head_ref': pr_data.get('head', {}).get('ref', ''),
                        'labels': [label.get('name', '') for label in pr_data.get('labels', [])],
                        'assignees': [assignee.get('login', '') for assignee in pr_data.get('assignees', [])],
                        'reviewers': [reviewer.get('login', '') for reviewer in pr_data.get('requested_reviewers', [])]
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
                
                # Get last analyzed commit for incremental processing
                last_commit = self.repo_service.get_last_analyzed_commit(org, repo)
                
                # Get commits since last analysis or since date
                commits = self.repo_service.get_commits_since(
                    repo_path, 
                    since_commit=last_commit,
                    since_date=since_date
                )
                
                # Add repository name to each commit
                for commit in commits:
                    commit['repository'] = repo
                    commit['organization'] = org
                
                all_commits.extend(commits)
                
                # Update last analyzed commit
                if commits:
                    latest_commit = commits[0]['sha']  # Commits are in reverse chronological order
                    self.repo_service.update_last_analyzed_commit(org, repo, latest_commit)
                
                logger.info(f"Extracted {len(commits)} commits from {repo}")
                
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
            df['files_changed'] = df['stats'].apply(lambda x: x.get('files_changed', 0))
            df['additions'] = df['stats'].apply(lambda x: x.get('insertions', 0))
            df['deletions'] = df['stats'].apply(lambda x: x.get('deletions', 0))
            df['total_lines'] = df['stats'].apply(lambda x: x.get('lines', 0))
            
            # Add URL (GitHub format)
            df['url'] = df.apply(lambda row: f"https://github.com/{row['organization']}/{row['repository']}/commit/{row['sha']}", axis=1)
            
            # Extract co-authors using utility function
            df['co_authors'] = df['message'].apply(ExtractionUtils.extract_co_authors)
            
            # Detect AI assistance using utility function
            df['ai_assisted'] = df.apply(
                lambda row: ExtractionUtils.detect_ai_assistance(
                    row['message'], row['co_authors']
                ), axis=1
            )
            
            # Reorder columns to match expected format
            columns = [
                'repository', 'sha', 'author_name', 'author_email', 'committer_name', 
                'committer_email', 'committed_date', 'message', 'url', 'pr_number',
                'files_changed', 'additions', 'deletions', 'is_merge', 'co_authors',
                'linear_ticket_id', 'ai_assisted'
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
        """Extract PR data using local git repositories + GitHub API metadata.
        
        Args:
            org: Organization name
            repos: List of repository names
            days_back: Number of days to go back
            
        Returns:
            DataFrame with PR data
        """
        logger.info(f"Extracting PR data for {len(repos)} repositories ({days_back} days)")
        
        since_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).isoformat()
        all_prs = []
        
        for repo in repos:
            try:
                # Clone or update repository
                repo_path = self.repo_service.clone_or_update_repo(org, repo, self.github_token)
                
                # Get PR merge commits from git
                pr_commits = self.repo_service.get_pr_merge_commits(repo_path, since_date)
                
                if not pr_commits:
                    logger.info(f"No PR commits found in {repo}")
                    continue
                
                # Extract PR numbers
                pr_numbers = [commit['pr_number'] for commit in pr_commits if commit['pr_number']]
                
                # Get PR metadata from GitHub API
                pr_metadata = self.get_pr_metadata(org, repo, pr_numbers)
                
                # Combine git data with GitHub metadata
                for commit in pr_commits:
                    pr_number = commit['pr_number']
                    if pr_number and pr_number in pr_metadata:
                        metadata = pr_metadata[pr_number]
                        
                        pr_data = {
                            'repository': repo,
                            'pr_number': pr_number,
                            'pr_id': f"{org}/{repo}#{pr_number}",
                            'title': metadata['title'],
                            'author': metadata['user_login'],
                            'state': metadata['state'],
                            'created_at': metadata['created_at'],
                            'merged_at': metadata['merged_at'],
                            'closed_at': metadata['closed_at'],
                            'url': metadata['html_url'],
                            'base_branch': metadata['base_ref'],
                            'head_branch': metadata['head_ref'],
                            'files_changed': commit['stats']['files_changed'],
                            'additions': commit['stats']['insertions'],
                            'deletions': commit['stats']['deletions'],
                            'linear_ticket_id': commit['linear_ticket_id'] or ExtractionUtils.extract_linear_ticket_id(metadata['title'] + ' ' + metadata['body']),
                            'merge_commit_sha': commit['sha'],
                            'merge_commit_date': commit['committed_date'],
                            'labels': ','.join(metadata['labels']),
                            'assignees': ','.join(metadata['assignees']),
                            'reviewers': ','.join(metadata['reviewers'])
                        }
                        
                        # Add has_linear_ticket flag
                        pr_data['has_linear_ticket'] = bool(pr_data['linear_ticket_id'])
                        
                        all_prs.append(pr_data)
                
                logger.info(f"Extracted {len(pr_commits)} PR commits from {repo}")
                
            except ValidationError as e:
                logger.error(f"Input validation failed for {repo}: {e}")
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
    
    def extract_organization_data(self, org: str, days_back: int = 7, 
                                 output_commits: str = "org_commits.csv", 
                                 output_prs: str = "org_prs.csv") -> Dict[str, Any]:
        """Extract all data for an organization.
        
        Args:
            org: Organization name
            days_back: Number of days to go back
            output_commits: Output file for commits
            output_prs: Output file for PRs
            
        Returns:
            Dictionary with extraction results
        """
        logger.info(f"Starting full extraction for {org} ({days_back} days)")
        
        # Get repository list (GitHub API call)
        repos_data = self.get_organization_repos(org)
        repo_names = [repo['name'] for repo in repos_data]
        
        # Save repo list for reference
        repos_file = f"{org}_repos.json"
        with open(repos_file, 'w') as f:
            json.dump(repos_data, f, indent=2)
        
        # Extract commits data (git-based)
        commits_df = self.extract_commits_data(org, repo_names, days_back)
        if not commits_df.empty:
            commits_df.to_csv(output_commits, index=False)
            logger.info(f"Saved {len(commits_df)} commits to {output_commits}")
        
        # Extract PR data (git + GitHub API)
        prs_df = self.extract_pr_data(org, repo_names, days_back)
        if not prs_df.empty:
            prs_df.to_csv(output_prs, index=False)
            logger.info(f"Saved {len(prs_df)} PRs to {output_prs}")
        
        # Generate summary
        summary = {
            'organization': org,
            'days_back': days_back,
            'repositories_found': len(repo_names),
            'commits_extracted': len(commits_df) if not commits_df.empty else 0,
            'prs_extracted': len(prs_df) if not prs_df.empty else 0,
            'commits_file': output_commits,
            'prs_file': output_prs,
            'repos_file': repos_file,
            'extraction_time': datetime.now(timezone.utc).isoformat()
        }
        
        # Calculate process compliance
        if not prs_df.empty:
            prs_with_tickets = prs_df['has_linear_ticket'].sum()
            compliance_rate = (prs_with_tickets / len(prs_df)) * 100
            summary['process_compliance_rate'] = round(compliance_rate, 2)
            summary['prs_with_linear_tickets'] = prs_with_tickets
        
        logger.info(f"Extraction complete for {org}")
        return summary
    
    # Removed duplicate methods - now using ExtractionUtils
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = self.repo_service.get_cache_stats()
        
        # Add rate limiting statistics
        if hasattr(self.session, 'get_rate_limit_status'):
            stats['rate_limit_stats'] = self.session.get_rate_limit_status()
        
        return stats


def main():
    """Main entry point for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract data using git repositories')
    parser.add_argument('--org', required=True, help='Organization name')
    parser.add_argument('--days', type=int, default=7, help='Days back to extract')
    parser.add_argument('--commits-output', default='org_commits.csv', help='Output file for commits')
    parser.add_argument('--prs-output', default='org_prs.csv', help='Output file for PRs')
    
    args = parser.parse_args()
    
    # Get GitHub token
    github_token = os.getenv('GITHUB_TOKEN')
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
            args.org, 
            args.days, 
            args.commits_output, 
            args.prs_output
        )
        
        print(json.dumps(summary, indent=2))
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
