"""Developer color mapping system for consistent visualization."""

import json
import hashlib
from pathlib import Path
from typing import Dict


class DeveloperColorMapper:
    """Map developers to consistent colors across all visualizations."""

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

    def __init__(self, config_path: str = "config/developer_names.json"):
        """Initialize color mapper with developer configuration.

        Args:
            config_path: Path to developer names configuration JSON
        """
        self.config_path = Path(config_path)
        self._load_config()
        self._build_color_map()

    def _load_config(self) -> None:
        """Load configuration from JSON file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path) as f:
            self.config = json.load(f)

        if "developers" not in self.config:
            raise ValueError("Config must contain 'developers' key")

    def _build_color_map(self) -> None:
        """Build color map using deterministic hash-based assignment."""
        self.color_map: Dict[str, str] = {}

        # Sort developers by canonical name for deterministic ordering
        developers = sorted(self.config["developers"], key=lambda d: d["canonical_name"])

        for dev in developers:
            canonical = dev["canonical_name"]
            # Use hash for deterministic but distributed color assignment
            hash_value = int(hashlib.md5(canonical.encode()).hexdigest(), 16)
            color_idx = hash_value % len(self.COLOR_PALETTE)
            self.color_map[canonical] = self.COLOR_PALETTE[color_idx]

    def get_color(self, developer_name: str) -> str:
        """Get color for a developer.

        Args:
            developer_name: Canonical developer name

        Returns:
            Hex color string (e.g., "#1f77b4")
        """
        return self.color_map.get(developer_name, "#999999")  # Gray fallback

    def get_color_map(self, developer_names: list[str]) -> Dict[str, str]:
        """Get color map for multiple developers.

        Args:
            developer_names: List of canonical developer names

        Returns:
            Dictionary mapping developer names to colors
        """
        return {name: self.get_color(name) for name in developer_names}
