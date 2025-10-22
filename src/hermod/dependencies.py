"""External dependency checking for ccusage tools."""
import subprocess
from typing import Dict


def check_ccusage_installed() -> bool:
    """Check if ccusage is installed and available on PATH.

    Returns:
        True if ccusage is installed, False otherwise
    """
    result = subprocess.run(
        ["which", "ccusage"],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def check_ccusage_codex_installed() -> bool:
    """Check if ccusage-codex is installed and available on PATH.

    Returns:
        True if ccusage-codex is installed, False otherwise
    """
    result = subprocess.run(
        ["which", "ccusage-codex"],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def check_all_dependencies() -> Dict[str, bool]:
    """Check all required external dependencies.

    Returns:
        Dictionary mapping tool name to installed status
    """
    return {
        "ccusage": check_ccusage_installed(),
        "ccusage-codex": check_ccusage_codex_installed()
    }
