"""Git repository service for local git operations."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .cache_stats import CacheStatsManager
from .commit_extractor import CommitExtractor
from .config import GitExtractionConfig
from .repo_cloner import RepoCloner
from .state_manager import RepoStateManager

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
        
        # Initialize specialized components
        self.repo_cloner = RepoCloner(self.config, self.cache_dir)
        self.state_manager = RepoStateManager(self.cache_dir)
        self.commit_extractor = CommitExtractor(self.config)
        self.cache_stats_manager = CacheStatsManager(self.cache_dir)

    # Repository path and state management - delegate to components
    def get_repo_path(self, org: str, repo: str) -> Path:
        """Get the local path for a repository."""
        return self.repo_cloner.get_repo_path(org, repo)
    
    def get_state_file(self, org: str, repo: str) -> Path:
        """Get the state file path for a repository."""
        return self.state_manager.get_state_file(org, repo)
    
    # Repository cloning and updating - delegate to RepoCloner
    def clone_or_update_repo(self, org: str, repo: str, github_token: str) -> str:
        """Clone repository or update if exists."""
        return self.repo_cloner.clone_or_update_repo(org, repo, github_token)
    
    def cleanup_repo(self, org: str, repo: str) -> None:
        """Clean up a local repository."""
        self.repo_cloner.cleanup_repo(org, repo)
    
    # State management - delegate to RepoStateManager
    def get_last_analyzed_commit(self, org: str, repo: str) -> Optional[str]:
        """Get the last analyzed commit SHA for a repository."""
        return self.state_manager.get_last_analyzed_commit(org, repo)
    
    def update_last_analyzed_commit(self, org: str, repo: str, commit_sha: str) -> None:
        """Update the last analyzed commit SHA for a repository."""
        self.state_manager.update_last_analyzed_commit(org, repo, commit_sha)
    
    # Commit extraction - delegate to CommitExtractor
    def get_commits_since(self, repo_path: str, since_commit: Optional[str] = None, 
                         since_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get commits since a specific commit or date."""
        return self.commit_extractor.get_commits_since(repo_path, since_commit, since_date)
    
    def get_pr_merge_commits(self, repo_path: str, since_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get PR merge commits from git log."""
        return self.commit_extractor.get_pr_merge_commits(repo_path, since_date)
    
    def get_file_changes(self, repo_path: str, commit_sha: str) -> List[Dict[str, Any]]:
        """Get file changes for a specific commit."""
        return self.commit_extractor.get_file_changes(repo_path, commit_sha)
    
    # Cache statistics - delegate to CacheStatsManager
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.cache_stats_manager.get_cache_stats()
