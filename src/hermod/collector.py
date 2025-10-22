"""AI usage data collection from ccusage and ccusage-codex."""
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any


def run_command(cmd: list[str]) -> Dict[str, Any]:
    """Run command and return parsed JSON output.

    Args:
        cmd: Command and arguments to run

    Returns:
        Parsed JSON output, or empty dict on error
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return {}


def collect_usage(developer: str, days: int = 7) -> Dict[str, Any]:
    """Collect usage data from both ccusage and ccusage-codex.

    Args:
        developer: Developer canonical name
        days: Number of days to collect (default: 7)

    Returns:
        Combined usage data with metadata
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    since_str = start_date.strftime("%Y%m%d")

    # Collect Claude Code usage
    claude_data = run_command([
        "ccusage", "daily", "--json", "--since", since_str
    ])

    # Collect Codex usage
    codex_data = run_command([
        "ccusage-codex", "daily", "--json", "--since", since_str
    ])

    # Combine with metadata
    return {
        "metadata": {
            "developer": developer,
            "collected_at": datetime.now().isoformat(),
            "date_range": {
                "start": start_date.date().isoformat(),
                "end": end_date.date().isoformat(),
                "days": days
            },
            "version": "1.0"
        },
        "claude_code": claude_data,
        "codex": codex_data
    }


def save_submission(
    data: Dict[str, Any],
    developer: str,
    output_dir: Path = None
) -> Path:
    """Save submission data to JSON file.

    Args:
        data: Usage data to save
        developer: Developer name for filename
        output_dir: Output directory (default: data/ai_usage/submissions)

    Returns:
        Path to saved file
    """
    if output_dir is None:
        output_dir = Path("data/ai_usage/submissions")

    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_str = datetime.now().strftime("%Y%m%d")
    output_file = output_dir / f"ai_usage_{developer}_{date_str}_{timestamp}.json"

    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)

    return output_file
