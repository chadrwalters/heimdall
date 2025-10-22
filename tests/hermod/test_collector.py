"""Tests for AI usage data collection."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from hermod.collector import collect_usage, save_submission


def test_collect_usage_success():
    """Test successful data collection."""
    with patch("hermod.collector.run_command") as mock_run:
        # Mock ccusage response
        mock_run.side_effect = [
            {"daily": [{"date": "2025-01-22", "cost": 1.50}], "totals": {"totalCost": 1.50}},
            {"daily": [{"date": "2025-01-22", "cost": 2.00}], "totals": {"totalCost": 2.00}}
        ]

        data = collect_usage("Chad", days=7)

        assert data["metadata"]["developer"] == "Chad"
        assert data["metadata"]["date_range"]["days"] == 7
        assert "claude_code" in data
        assert "codex" in data
        assert data["claude_code"]["totals"]["totalCost"] == 1.50
        assert data["codex"]["totals"]["totalCost"] == 2.00


def test_collect_usage_handles_errors():
    """Test collection continues when one tool fails."""
    with patch("hermod.collector.run_command") as mock_run:
        # First call succeeds, second fails
        mock_run.side_effect = [
            {"daily": [], "totals": {}},
            {}  # Empty dict indicates error
        ]

        data = collect_usage("Chad", days=7)

        assert data["claude_code"] == {"daily": [], "totals": {}}
        assert data["codex"] == {}


def test_save_submission():
    """Test saving submission to file."""
    import tempfile
    from pathlib import Path

    test_data = {
        "metadata": {"developer": "Chad", "collected_at": "2025-01-22T10:00:00"},
        "claude_code": {},
        "codex": {}
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = save_submission(test_data, "Chad", output_dir=Path(tmpdir))

        assert output_path.exists()
        assert "ai_usage_Chad_" in output_path.name
        assert output_path.suffix == ".json"

        # Verify content
        import json
        with open(output_path) as f:
            loaded = json.load(f)
        assert loaded["metadata"]["developer"] == "Chad"
