"""Developer name unification across GitHub, Git, and Linear."""

import json
from pathlib import Path
from typing import Any


class NameUnifier:
    """Unify developer identities across different systems."""

    def __init__(self, config_path: str = "config/developer_names.json"):
        """Initialize name unifier with configuration file.

        Args:
            config_path: Path to developer names configuration JSON
        """
        self.config_path = Path(config_path)
        self._load_config()
        self._build_lookup_tables()

    def _load_config(self) -> None:
        """Load configuration from JSON file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path) as f:
            self.config = json.load(f)

        if "developers" not in self.config:
            raise ValueError("Config must contain 'developers' key")

    def _build_lookup_tables(self) -> None:
        """Build lookup tables for fast name resolution."""
        self.github_lookup: dict[str, str] = {}
        self.git_name_lookup: dict[str, str] = {}
        self.git_email_lookup: dict[str, str] = {}
        self.linear_lookup: dict[str, str] = {}

        for dev in self.config["developers"]:
            canonical = dev["canonical_name"]

            # GitHub handles
            for handle in dev.get("github_handles", []):
                self.github_lookup[handle.lower()] = canonical

            # Git names
            for name in dev.get("git_names", []):
                self.git_name_lookup[name.lower()] = canonical

            # Git emails
            for email in dev.get("git_emails", []):
                self.git_email_lookup[email.lower()] = canonical

            # Linear names
            for name in dev.get("linear_names", []):
                self.linear_lookup[name.lower()] = canonical

    def unify(
        self,
        github_handle: str | None = None,
        git_name: str | None = None,
        git_email: str | None = None,
        linear_name: str | None = None,
    ) -> str:
        """Unify a developer identifier to canonical name.

        Args:
            github_handle: GitHub username
            git_name: Git author name
            git_email: Git author email
            linear_name: Linear assignee name

        Returns:
            Canonical developer name, or original value if not found

        Raises:
            ValueError: If zero or multiple parameters provided
        """
        # Validate exactly one parameter provided
        params = [github_handle, git_name, git_email, linear_name]
        non_none = [p for p in params if p is not None]

        if len(non_none) == 0:
            raise ValueError("Must provide exactly one identifier parameter")
        if len(non_none) > 1:
            raise ValueError("Must provide exactly one identifier parameter")

        # Look up in appropriate table
        if github_handle is not None:
            return self.github_lookup.get(github_handle.lower(), github_handle)
        elif git_name is not None:
            return self.git_name_lookup.get(git_name.lower(), git_name)
        elif git_email is not None:
            return self.git_email_lookup.get(git_email.lower(), git_email)
        elif linear_name is not None:
            return self.linear_lookup.get(linear_name.lower(), linear_name)

        return non_none[0]  # Should never reach here
