"""Extract commits and file changes from git repositories."""

import logging
import subprocess
from typing import Any, Dict, List, Optional

import git
from git import Repo

from .config import GitExtractionConfig
from .extraction_utils import ExtractionUtils
from .input_validation import InputValidator, ValidationError

logger = logging.getLogger(__name__)


class CommitExtractor:
    """Extract commit data from git repositories."""

    def __init__(self, config: GitExtractionConfig):
        self.config = config

    def get_commits_since(
        self, repo_path: str, since_commit: Optional[str] = None, since_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
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
                commit_iter = repo.iter_commits(f"{since_commit}..HEAD")
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
                    "sha": commit.hexsha,
                    "short_sha": commit.hexsha[:7],
                    "message": message,
                    "author_name": commit.author.name,
                    "author_email": commit.author.email,
                    "committer_name": commit.committer.name,
                    "committer_email": commit.committer.email,
                    "authored_date": commit.authored_datetime.isoformat(),
                    "committed_date": commit.committed_datetime.isoformat(),
                    "parents": [parent.hexsha for parent in commit.parents],
                    "is_merge": len(commit.parents) > 1,
                    "on_main_branch": self.is_on_main_branch(repo_path, commit.hexsha),
                    "stats": {
                        "total": commit.stats.total,
                        "files": commit.stats.files,
                        "insertions": commit.stats.total["insertions"],
                        "deletions": commit.stats.total["deletions"],
                        "lines": commit.stats.total["lines"],
                        "files_changed": len(commit.stats.files),
                    },
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
                raw_commits, self.config.batch_size, process_commit_batch
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

    def get_pr_merge_commits(
        self, repo_path: str, since_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
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
                            "sha": commit.hexsha,
                            "short_sha": commit.hexsha[:7],
                            "message": commit.message.strip(),
                            "author_name": commit.author.name,
                            "author_email": commit.author.email,
                            "authored_date": commit.authored_datetime.isoformat(),
                            "committed_date": commit.committed_datetime.isoformat(),
                            "pr_number": pr_number,
                            "linear_ticket_id": ExtractionUtils.extract_linear_ticket_id(
                                commit.message
                            ),
                            "is_merge": True,
                            "parents": [parent.hexsha for parent in commit.parents],
                            "stats": {
                                "total": commit.stats.total,
                                "files": commit.stats.files,
                                "insertions": commit.stats.total["insertions"],
                                "deletions": commit.stats.total["deletions"],
                                "lines": commit.stats.total["lines"],
                                "files_changed": len(commit.stats.files),
                            },
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
                        "filename": diff.b_path if diff.b_path else diff.a_path,
                        "status": "modified",
                        "additions": 0,
                        "deletions": 0,
                        "changes": 0,
                    }

                    # Determine change type
                    if diff.new_file:
                        change["status"] = "added"
                    elif diff.deleted_file:
                        change["status"] = "deleted"
                    elif diff.renamed_file:
                        change["status"] = "renamed"
                        change["previous_filename"] = diff.a_path

                    # Get line changes (if available)
                    if hasattr(diff, "diff") and diff.diff:
                        lines = diff.diff.decode("utf-8", errors="ignore").split("\n")
                        additions = sum(
                            1
                            for line in lines
                            if line.startswith("+") and not line.startswith("+++")
                        )
                        deletions = sum(
                            1
                            for line in lines
                            if line.startswith("-") and not line.startswith("---")
                        )
                        change["additions"] = additions
                        change["deletions"] = deletions
                        change["changes"] = additions + deletions

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

    def is_commit_on_branch(self, repo_path: str, commit_sha: str, branch_name: str) -> bool:
        """Check if a commit is reachable from a specific branch.

        Args:
            repo_path: Path to local repository
            commit_sha: Commit SHA to check
            branch_name: Branch name to check against

        Returns:
            True if commit is on the branch, False otherwise
        """
        try:
            result = subprocess.run(
                ["git", "branch", "--contains", commit_sha],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                logger.warning(f"Git command failed for commit {commit_sha}: {result.stderr}")
                return False

            # Parse branch list - format is "  branch-name" or "* branch-name" for current
            branches = [
                line.strip().lstrip("* ").strip()
                for line in result.stdout.split("\n")
                if line.strip()
            ]
            return branch_name in branches

        except Exception as e:
            logger.error(f"Error checking if commit {commit_sha} is on branch {branch_name}: {e}")
            return False

    def get_branches_for_commit(self, repo_path: str, commit_sha: str) -> List[str]:
        """Get all branches that contain a specific commit.

        Args:
            repo_path: Path to local repository
            commit_sha: Commit SHA to check

        Returns:
            List of branch names containing the commit
        """
        try:
            result = subprocess.run(
                ["git", "branch", "--contains", commit_sha],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                logger.warning(f"Git command failed for commit {commit_sha}: {result.stderr}")
                return []

            # Parse branch list - format is "  branch-name" or "* branch-name" for current
            branches = [
                line.strip().lstrip("* ").strip()
                for line in result.stdout.split("\n")
                if line.strip()
            ]
            return branches

        except Exception as e:
            logger.error(f"Error getting branches for commit {commit_sha}: {e}")
            return []

    def is_on_main_branch(self, repo_path: str, commit_sha: str) -> bool:
        """Check if a commit is on a main development branch (main, master, dev, develop).

        Args:
            repo_path: Path to local repository
            commit_sha: Commit SHA to check

        Returns:
            True if commit is on any main branch, False otherwise
        """
        main_branches = ["main", "master", "dev", "develop"]
        branches = self.get_branches_for_commit(repo_path, commit_sha)

        # Check if any main branch is in the list
        return any(branch in main_branches for branch in branches)
