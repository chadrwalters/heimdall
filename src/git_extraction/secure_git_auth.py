"""Secure git authentication without exposing tokens in URLs."""

import logging
import os
import subprocess
import tempfile

logger = logging.getLogger(__name__)


class SecureGitAuth:
    """Secure git authentication using credential helpers."""

    def __init__(self, github_token: str):
        """Initialize secure git authentication.

        Args:
            github_token: GitHub token for authentication
        """
        self.github_token = github_token
        self._credential_helper_script = None

    def setup_credential_helper(self) -> str:
        """Set up a temporary credential helper script.

        Returns:
            Path to the credential helper script
        """
        if self._credential_helper_script:
            return self._credential_helper_script

        # Create temporary credential helper script
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write(f"""#!/bin/bash
case "$1" in
get)
    echo "protocol=https"
    echo "host=github.com"
    echo "username={self.github_token}"
    echo "password="
    ;;
esac
""")
            self._credential_helper_script = f.name

        # Make script executable
        os.chmod(self._credential_helper_script, 0o755)

        logger.debug(f"Created credential helper: {self._credential_helper_script}")
        return self._credential_helper_script

    def configure_git_auth(self, repo_path: str) -> None:
        """Configure git authentication for a repository.

        Args:
            repo_path: Path to the git repository
        """
        credential_helper = self.setup_credential_helper()

        # Configure git to use our credential helper
        git_commands = [
            ["git", "config", "credential.helper", f"!{credential_helper}"],
            ["git", "config", "credential.https://github.com.helper", f"!{credential_helper}"],
        ]

        for cmd in git_commands:
            try:
                subprocess.run(cmd, cwd=repo_path, check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to configure git auth: {e}")

    def get_clone_url(self, org: str, repo: str) -> str:
        """Get clone URL without embedded credentials.

        Args:
            org: Organization name
            repo: Repository name

        Returns:
            Clean clone URL
        """
        return f"https://github.com/{org}/{repo}.git"

    def cleanup(self) -> None:
        """Clean up temporary credential helper."""
        if self._credential_helper_script and os.path.exists(self._credential_helper_script):
            try:
                os.unlink(self._credential_helper_script)
                logger.debug(f"Cleaned up credential helper: {self._credential_helper_script}")
            except OSError as e:
                logger.warning(f"Failed to cleanup credential helper: {e}")
            finally:
                self._credential_helper_script = None


class GitCredentialManager:
    """Context manager for secure git credentials."""

    def __init__(self, github_token: str):
        """Initialize credential manager.

        Args:
            github_token: GitHub token for authentication
        """
        self.auth = SecureGitAuth(github_token)

    def __enter__(self) -> SecureGitAuth:
        """Enter context and set up authentication."""
        return self.auth

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context and clean up authentication."""
        self.auth.cleanup()
