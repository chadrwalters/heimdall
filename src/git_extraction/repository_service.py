"""Git repository service for local git operations."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import git
from git import Repo

from .config import GitExtractionConfig
from .extraction_utils import ExtractionUtils
from .input_validation import InputValidator, ValidationError, validate_git_operation_inputs
from .secure_git_auth import GitCredentialManager

logger = logging.getLogger(__name__)


class GitRepositoryService:
    """Service for managing local git repositories and extracting data."""
    
    def __init__(self, config: Optional[GitExtractionConfig] = None):
        """Initialize the git repository service.
        
        Args:
            config: Configuration instance (creates default if None)
        """
        self.config = config or GitExtractionConfig.from_environment()
        self.config.validate()
        
        self.cache_dir = Path(self.config.cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for organization
        (self.cache_dir / "repos").mkdir(exist_ok=True)
        (self.cache_dir / "state").mkdir(exist_ok=True)
        
        # Configure logging
        self.config.configure_logging()
        
    def get_repo_path(self, org: str, repo: str) -> Path:
        """Get the local path for a repository."""
        return self.cache_dir / "repos" / org / repo
    
    def get_state_file(self, org: str, repo: str) -> Path:
        """Get the state file path for a repository."""
        return self.cache_dir / "state" / f"{org}_{repo}.json"
    
    def clone_or_update_repo(self, org: str, repo: str, github_token: str) -> str:
        """Clone repository or update if exists.
        
        Args:
            org: Organization name
            repo: Repository name
            github_token: GitHub token for authentication
            
        Returns:
            Path to local repository
            
        Raises:
            ValidationError: If input validation fails
            git.exc.GitError: If git operations fail
        """
        # Validate inputs
        if self.config.validate_inputs:
            try:
                validated_org, validated_repo = validate_git_operation_inputs(org, repo)
                org, repo = validated_org, validated_repo
            except ValidationError as e:
                logger.error(f"Input validation failed for {org}/{repo}: {e}")
                raise
        
        repo_path = self.get_repo_path(org, repo)
        
        try:
            # Use secure authentication
            with GitCredentialManager(github_token) as auth:
                clone_url = auth.get_clone_url(org, repo)
                
                if repo_path.exists():
                    logger.info(f"Updating existing repository: {org}/{repo}")
                    repository = Repo(repo_path)
                    
                    # Configure authentication for this repository
                    auth.configure_git_auth(str(repo_path))
                    
                    # Fetch latest changes
                    origin = repository.remotes.origin
                    origin.fetch()
                    
                    # Update default branch
                    try:
                        default_branch = repository.active_branch.name
                        repository.git.checkout(default_branch)
                        repository.git.pull()
                    except git.exc.GitError:
                        # Handle detached HEAD or other branch issues
                        logger.warning(f"Could not update default branch for {org}/{repo}")
                        repository.git.fetch('origin')
                    
                    logger.info(f"Updated repository: {org}/{repo}")
                else:
                    logger.info(f"Cloning repository: {org}/{repo}")
                    repo_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Clone with configurable depth
                    clone_kwargs = {
                        'depth': self.config.clone_depth,
                        'single_branch': self.config.single_branch_clone
                    }
                    
                    repository = Repo.clone_from(clone_url, repo_path, **clone_kwargs)
                    
                    # Configure authentication for future operations
                    auth.configure_git_auth(str(repo_path))
                    
                    logger.info(f"Cloned repository: {org}/{repo}")
            
            return str(repo_path)
            
        except git.exc.InvalidGitRepositoryError as e:
            logger.error(f"Invalid git repository for {org}/{repo}: {e}")
            raise
        except git.exc.GitCommandError as e:
            logger.error(f"Git command failed for {org}/{repo}: {e}")
            raise
        except (PermissionError, OSError) as e:
            logger.error(f"Filesystem error for {org}/{repo}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error cloning/updating {org}/{repo}: {e}")
            raise
    
    def get_last_analyzed_commit(self, org: str, repo: str) -> Optional[str]:
        """Get the last analyzed commit SHA for a repository.
        
        Args:
            org: Organization name
            repo: Repository name
            
        Returns:
            Last analyzed commit SHA or None
        """
        state_file = self.get_state_file(org, repo)
        
        if not state_file.exists():
            return None
        
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
            return state.get('last_analyzed_commit')
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Invalid state file format for {org}/{repo}: {e}")
            return None
        except (IOError, OSError) as e:
            logger.warning(f"Failed to read state file for {org}/{repo}: {e}")
            return None
    
    def update_last_analyzed_commit(self, org: str, repo: str, commit_sha: str) -> None:
        """Update the last analyzed commit SHA for a repository.
        
        Args:
            org: Organization name
            repo: Repository name
            commit_sha: Commit SHA to store
        """
        state_file = self.get_state_file(org, repo)
        state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing state or create new
        state = {}
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
            except (json.JSONDecodeError, IOError, OSError) as e:
                logger.warning(f"Failed to read existing state for {org}/{repo}: {e}")
        
        # Update state
        state.update({
            'last_analyzed_commit': commit_sha,
            'last_updated': datetime.now(timezone.utc).isoformat()
        })
        
        # Save state
        try:
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except (IOError, OSError) as e:
            logger.error(f"Failed to save state for {org}/{repo}: {e}")
            raise
    
    def get_commits_since(self, repo_path: str, since_commit: Optional[str] = None, 
                         since_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get commits since a specific commit or date.
        
        Args:
            repo_path: Path to local repository
            since_commit: Commit SHA to start from
            since_date: ISO date string to start from
            
        Returns:
            List of commit dictionaries
        """
        repo = Repo(repo_path)
        commits = []
        
        try:
            # Build commit iterator based on criteria
            if since_commit:
                # Get commits since specific commit
                commit_iter = repo.iter_commits(f'{since_commit}..HEAD')
            elif since_date:
                # Get commits since date
                commit_iter = repo.iter_commits(since=since_date)
            else:
                # Get all commits (limit to avoid memory issues)
                commit_iter = repo.iter_commits(max_count=self.config.max_commits_per_query)
            
            # Process commits in batches for memory efficiency
            raw_commits = []
            for commit in commit_iter:
                # Validate and sanitize commit message
                message = commit.message.strip()
                if self.config.sanitize_commit_messages:
                    try:
                        message = InputValidator.validate_commit_message(message)
                    except ValidationError:
                        logger.warning(f"Invalid commit message in {commit.hexsha}, using fallback")
                        message = "[Invalid commit message]"
                
                commit_data = {
                    'sha': commit.hexsha,
                    'short_sha': commit.hexsha[:7],
                    'message': message,
                    'author_name': commit.author.name,
                    'author_email': commit.author.email,
                    'committer_name': commit.committer.name,
                    'committer_email': commit.committer.email,
                    'authored_date': commit.authored_datetime.isoformat(),
                    'committed_date': commit.committed_datetime.isoformat(),
                    'parents': [parent.hexsha for parent in commit.parents],
                    'is_merge': len(commit.parents) > 1,
                    'stats': {
                        'total': commit.stats.total,
                        'files': commit.stats.files,
                        'insertions': commit.stats.total['insertions'],
                        'deletions': commit.stats.total['deletions'],
                        'lines': commit.stats.total['lines'],
                        'files_changed': len(commit.stats.files)
                    }
                }
                
                raw_commits.append(commit_data)
            
            # Process in batches for memory optimization
            def process_commit_batch(batch):
                processed_batch = []
                for commit_data in batch:
                    # Use utility function for consistent extraction
                    commit_data = ExtractionUtils.sanitize_commit_data(commit_data, self.config)
                    processed_batch.append(commit_data)
                return processed_batch
            
            commits = ExtractionUtils.batch_process_commits(
                raw_commits, 
                self.config.batch_size, 
                process_commit_batch
            )
            
            logger.info(f"Retrieved {len(commits)} commits from {repo_path}")
            return commits
            
        except git.exc.InvalidGitRepositoryError as e:
            logger.error(f"Invalid git repository at {repo_path}: {e}")
            raise
        except git.exc.GitCommandError as e:
            logger.error(f"Git command error getting commits from {repo_path}: {e}")
            raise
        except (MemoryError, OSError) as e:
            logger.error(f"System error getting commits from {repo_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting commits from {repo_path}: {e}")
            raise
    
    def get_pr_merge_commits(self, repo_path: str, since_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get PR merge commits from git log.
        
        Args:
            repo_path: Path to local repository
            since_date: ISO date string to start from
            
        Returns:
            List of PR merge commit dictionaries
        """
        repo = Repo(repo_path)
        pr_commits = []
        
        try:
            # Get merge commits (commits with multiple parents)
            if since_date:
                commits = repo.iter_commits(since=since_date)
            else:
                commits = repo.iter_commits(max_count=self.config.max_commits_per_query)
            
            for commit in commits:
                # Only process merge commits
                if len(commit.parents) > 1:
                    pr_number = ExtractionUtils.extract_pr_number(commit.message)
                    if pr_number:
                        pr_commit = {
                            'sha': commit.hexsha,
                            'short_sha': commit.hexsha[:7],
                            'message': commit.message.strip(),
                            'author_name': commit.author.name,
                            'author_email': commit.author.email,
                            'authored_date': commit.authored_datetime.isoformat(),
                            'committed_date': commit.committed_datetime.isoformat(),
                            'pr_number': pr_number,
                            'linear_ticket_id': ExtractionUtils.extract_linear_ticket_id(commit.message),
                            'is_merge': True,
                            'parents': [parent.hexsha for parent in commit.parents],
                            'stats': {
                                'total': commit.stats.total,
                                'files': commit.stats.files,
                                'insertions': commit.stats.total['insertions'],
                                'deletions': commit.stats.total['deletions'],
                                'lines': commit.stats.total['lines'],
                                'files_changed': len(commit.stats.files)
                            }
                        }
                        pr_commits.append(pr_commit)
            
            logger.info(f"Retrieved {len(pr_commits)} PR merge commits from {repo_path}")
            return pr_commits
            
        except git.exc.InvalidGitRepositoryError as e:
            logger.error(f"Invalid git repository at {repo_path}: {e}")
            raise
        except git.exc.GitCommandError as e:
            logger.error(f"Git command error getting PR merge commits from {repo_path}: {e}")
            raise
        except (MemoryError, OSError) as e:
            logger.error(f"System error getting PR merge commits from {repo_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting PR merge commits from {repo_path}: {e}")
            raise
    
    def get_file_changes(self, repo_path: str, commit_sha: str) -> List[Dict[str, Any]]:
        """Get file changes for a specific commit.
        
        Args:
            repo_path: Path to local repository
            commit_sha: Commit SHA to analyze
            
        Returns:
            List of file change dictionaries
        """
        repo = Repo(repo_path)
        
        try:
            commit = repo.commit(commit_sha)
            changes = []
            
            # Get changes between commit and its parent
            if commit.parents:
                parent = commit.parents[0]
                diffs = parent.diff(commit)
                
                for diff in diffs:
                    change = {
                        'filename': diff.b_path if diff.b_path else diff.a_path,
                        'status': 'modified',
                        'additions': 0,
                        'deletions': 0,
                        'changes': 0
                    }
                    
                    # Determine change type
                    if diff.new_file:
                        change['status'] = 'added'
                    elif diff.deleted_file:
                        change['status'] = 'deleted'
                    elif diff.renamed_file:
                        change['status'] = 'renamed'
                        change['previous_filename'] = diff.a_path
                    
                    # Get line changes (if available)
                    if hasattr(diff, 'diff') and diff.diff:
                        lines = diff.diff.decode('utf-8', errors='ignore').split('\n')
                        additions = sum(1 for line in lines if line.startswith('+') and not line.startswith('+++'))
                        deletions = sum(1 for line in lines if line.startswith('-') and not line.startswith('---'))
                        change['additions'] = additions
                        change['deletions'] = deletions
                        change['changes'] = additions + deletions
                    
                    changes.append(change)
            
            return changes
            
        except git.exc.InvalidGitRepositoryError as e:
            logger.error(f"Invalid git repository at {repo_path}: {e}")
            return []
        except git.exc.GitCommandError as e:
            logger.error(f"Git command error getting file changes for {commit_sha}: {e}")
            return []
        except (UnicodeDecodeError, MemoryError) as e:
            logger.error(f"Encoding/memory error getting file changes for {commit_sha}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting file changes for {commit_sha}: {e}")
            return []
    
    
    def cleanup_repo(self, org: str, repo: str) -> None:
        """Clean up a local repository.
        
        Args:
            org: Organization name
            repo: Repository name
        """
        repo_path = self.get_repo_path(org, repo)
        
        if repo_path.exists():
            import shutil
            shutil.rmtree(repo_path)
            logger.info(f"Cleaned up repository: {org}/{repo}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        stats = {
            'total_repos': 0,
            'total_size_bytes': 0,
            'organizations': {},
            'cache_dir': str(self.cache_dir)
        }
        
        if not self.cache_dir.exists():
            return stats
        
        repos_dir = self.cache_dir / "repos"
        if repos_dir.exists():
            for org_dir in repos_dir.iterdir():
                if org_dir.is_dir():
                    org_name = org_dir.name
                    org_repos = []
                    
                    for repo_dir in org_dir.iterdir():
                        if repo_dir.is_dir():
                            repo_size = sum(f.stat().st_size for f in repo_dir.rglob('*') if f.is_file())
                            org_repos.append({
                                'name': repo_dir.name,
                                'size_bytes': repo_size,
                                'path': str(repo_dir)
                            })
                            stats['total_size_bytes'] += repo_size
                            stats['total_repos'] += 1
                    
                    stats['organizations'][org_name] = org_repos
        
        return stats
