"""Repository cloning and update functionality."""

import logging
from pathlib import Path

import git
from git import Repo

from .config import GitExtractionConfig
from .input_validation import ValidationError, validate_git_operation_inputs
from .secure_git_auth import GitCredentialManager

logger = logging.getLogger(__name__)


class RepoCloner:
    """Handle repository cloning and updates."""

    def __init__(self, config: GitExtractionConfig, cache_dir: Path):
        self.config = config
        self.cache_dir = cache_dir

    def get_repo_path(self, org: str, repo: str) -> Path:
        """Get the local path for a repository."""
        return self.cache_dir / "repos" / org / repo

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
