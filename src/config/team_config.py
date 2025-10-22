"""Centralized team configuration for names, colors, and mappings.

This is the SINGLE SOURCE OF TRUTH for:
- Developer canonical names
- Developer color assignments
- Name unification across Git/GitHub/Linear

Used by:
- Chart generation (commits, PRs, cycles)
- Data extraction scripts
- Name unification utilities
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List


class TeamConfig:
    """Centralized team configuration singleton.

    Provides unified access to:
    - Developer canonical names
    - Name mappings across systems (Git, GitHub, Linear)
    - Consistent color assignments for visualizations
    """

    _instance = None

    # Distinct, visually appealing color palette (20 colors for better distribution)
    COLOR_PALETTE = [
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",  # Original 5
        "#8c564b",
        "#e377c2",
        "#7f7f7f",
        "#bcbd22",
        "#17becf",  # Original 10
        "#aec7e8",
        "#ffbb78",
        "#98df8a",
        "#ff9896",
        "#c5b0d5",  # +5 (15)
        "#c49c94",
        "#f7b6d2",
        "#c7c7c7",
        "#dbdb8d",
        "#9edae5",  # +5 (20)
    ]

    def __new__(cls, config_path: str = "config/developer_names.json"):
        """Singleton pattern - only one instance allowed."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: str = "config/developer_names.json"):
        """Initialize configuration (only runs once due to singleton)."""
        if self._initialized:
            return

        self.config_path = Path(config_path)
        self._load_config()
        self._build_mappings()
        self._build_color_map()
        self._initialized = True

    def _load_config(self) -> None:
        """Load configuration from JSON file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path) as f:
            data = json.load(f)

        if "developers" not in data:
            raise ValueError("Config must contain 'developers' key")

        self.developers = data["developers"]

    def _build_mappings(self) -> None:
        """Build lookup mappings from configuration."""
        # Get all canonical names
        self.canonical_names = [d["canonical_name"] for d in self.developers]

        # Git name -> canonical
        self.git_to_canonical: Dict[str, str] = {}
        for dev in self.developers:
            canonical = dev["canonical_name"]
            for git_name in dev.get("git_names", []):
                self.git_to_canonical[git_name.lower()] = canonical

        # Git email -> canonical
        self.git_email_to_canonical: Dict[str, str] = {}
        for dev in self.developers:
            canonical = dev["canonical_name"]
            for email in dev.get("git_emails", []):
                self.git_email_to_canonical[email.lower()] = canonical

        # GitHub handle -> canonical
        self.github_to_canonical: Dict[str, str] = {}
        for dev in self.developers:
            canonical = dev["canonical_name"]
            for handle in dev.get("github_handles", []):
                self.github_to_canonical[handle.lower()] = canonical

        # Linear name -> canonical
        self.linear_to_canonical: Dict[str, str] = {}
        for dev in self.developers:
            canonical = dev["canonical_name"]
            for linear_name in dev.get("linear_names", []):
                self.linear_to_canonical[linear_name.lower()] = canonical

    def _build_color_map(self) -> None:
        """Build color map using deterministic hash-based assignment."""
        self.color_map: Dict[str, str] = {}

        # Sort developers by canonical name for deterministic ordering
        sorted_names = sorted(self.canonical_names)

        for canonical in sorted_names:
            # Use hash for deterministic but distributed color assignment
            hash_value = int(hashlib.md5(canonical.encode()).hexdigest(), 16)
            color_idx = hash_value % len(self.COLOR_PALETTE)
            self.color_map[canonical] = self.COLOR_PALETTE[color_idx]

    def get_canonical_name(self, name: str | None, source: str = "auto") -> str | None:
        """Get canonical name from any source.

        Args:
            name: Name/identifier to unify
            source: Source system - "git", "git_email", "github", "linear", or "auto"

        Returns:
            Canonical developer name, or original name if not found
        """
        if name is None:
            return None

        name_lower = name.lower()

        if source == "git":
            return self.git_to_canonical.get(name_lower, name)
        elif source == "git_email":
            return self.git_email_to_canonical.get(name_lower, name)
        elif source == "github":
            return self.github_to_canonical.get(name_lower, name)
        elif source == "linear":
            return self.linear_to_canonical.get(name_lower, name)
        else:  # auto - try all mappings
            if name_lower in self.git_to_canonical:
                return self.git_to_canonical[name_lower]
            if name_lower in self.git_email_to_canonical:
                return self.git_email_to_canonical[name_lower]
            if name_lower in self.github_to_canonical:
                return self.github_to_canonical[name_lower]
            if name_lower in self.linear_to_canonical:
                return self.linear_to_canonical[name_lower]
            return name

    def get_color(self, canonical_name: str) -> str:
        """Get consistent color for developer.

        Args:
            canonical_name: Canonical developer name

        Returns:
            Hex color string (e.g., "#1f77b4")
        """
        return self.color_map.get(canonical_name, "#999999")  # Gray fallback

    def get_color_map(self, developer_names: List[str]) -> Dict[str, str]:
        """Get color map for multiple developers.

        Args:
            developer_names: List of canonical developer names

        Returns:
            Dictionary mapping developer names to colors
        """
        return {name: self.get_color(name) for name in developer_names}


# Global singleton instance - use this throughout the application
team_config = TeamConfig()
