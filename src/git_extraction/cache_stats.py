"""Cache statistics and management utilities."""

import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


class CacheStatsManager:
    """Manage cache statistics and utilities."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        stats = {
            "total_repos": 0,
            "total_size_bytes": 0,
            "organizations": {},
            "cache_dir": str(self.cache_dir),
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
                            repo_size = sum(
                                f.stat().st_size for f in repo_dir.rglob("*") if f.is_file()
                            )
                            org_repos.append(
                                {
                                    "name": repo_dir.name,
                                    "size_bytes": repo_size,
                                    "path": str(repo_dir),
                                }
                            )
                            stats["total_size_bytes"] += repo_size
                            stats["total_repos"] += 1

                    stats["organizations"][org_name] = org_repos

        return stats
