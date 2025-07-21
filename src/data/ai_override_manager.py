"""AI override configuration management."""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AIOverrideManager:
    """Manage AI developer override configuration."""

    def __init__(self, config_path: str = "config/ai_developers.json"):
        self.config_path = Path(config_path)
        self.ai_overrides = self._load_ai_overrides()

    def _load_ai_overrides(self) -> dict[str, dict[str, Any]]:
        """Load AI developer override configuration."""
        try:
            if self.config_path.exists():
                with open(self.config_path) as f:
                    config = json.load(f)
                    # Create lookup dict by email and username
                    overrides = {}
                    for dev in config.get("always_ai_developers", []):
                        email = dev.get("email", "").lower()
                        username = dev.get("username", "").lower()
                        if email:
                            overrides[email] = dev
                        if username:
                            overrides[username] = dev
                    return overrides
            return {}
        except Exception as e:
            logger.warning(f"Could not load AI developer overrides: {e}")
            return {}

    def check_ai_override(self, author: str) -> tuple[bool, str | None]:
        """Check if author should be marked as using AI assistance."""
        author_lower = author.lower()
        if author_lower in self.ai_overrides:
            override_config = self.ai_overrides[author_lower]
            return True, override_config.get("ai_tool", "Unknown AI Tool")
        return False, None
