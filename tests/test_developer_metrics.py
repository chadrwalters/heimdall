"""Tests for developer metrics aggregation functionality."""

import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

from src.data.developer_metrics import DeveloperMetrics, DeveloperMetricsAggregator


class TestDeveloperMetrics:
    """Test the DeveloperMetrics dataclass."""

    def test_developer_metrics_creation(self):
        """Test creating a DeveloperMetrics instance."""
        metrics = DeveloperMetrics(
            author="test@example.com",
            period="2025-W01",
            commit_frequency=2.5,
            pr_frequency=3.0,
            ai_usage_rate=75.0,
            avg_pr_size=8.5,
            avg_complexity=6.2,
            avg_impact_score=7.8,
        )

        assert metrics.author == "test@example.com"
        assert metrics.period == "2025-W01"
        assert metrics.commit_frequency == 2.5
        assert metrics.pr_frequency == 3.0
        assert metrics.ai_usage_rate == 75.0
        assert metrics.avg_pr_size == 8.5
        assert metrics.avg_complexity == 6.2
        assert metrics.avg_impact_score == 7.8

    def test_developer_metrics_to_dict(self):
        """Test converting DeveloperMetrics to dictionary."""
        metrics = DeveloperMetrics(
            author="test@example.com",
            period="2025-W01",
            commit_frequency=2.5,
            pr_frequency=3.0,
            ai_usage_rate=75.0,
            avg_pr_size=8.5,
            avg_complexity=6.2,
            avg_impact_score=7.8,
        )

        result = metrics.to_dict()
        expected = {
            "author": "test@example.com",
            "period": "2025-W01",
            "commit_frequency": 2.5,
            "pr_frequency": 3.0,
            "ai_usage_rate": 75.0,
            "avg_pr_size": 8.5,
            "avg_complexity": 6.2,
            "avg_impact_score": 7.8,
        }

        assert result == expected


class TestDeveloperMetricsAggregator:
    """Test the DeveloperMetricsAggregator class."""

    @pytest.fixture
    def aggregator(self):
        """Create a DeveloperMetricsAggregator instance."""
        return DeveloperMetricsAggregator()

    @pytest.fixture
    def sample_unified_data(self):
        """Create sample unified data for testing."""
        # Create data spanning 2 weeks for 2 developers
        base_date = datetime(2025, 1, 6)  # Monday of week 1
        data = []

        # Developer 1 data - Week 1
        for i in range(5):  # 5 commits, 2 PRs
            if i < 3:  # 3 commits
                data.append(
                    {
                        "author": "dev1@example.com",
                        "date": (base_date + timedelta(days=i)).isoformat(),
                        "source_type": "Commit",
                        "complexity_score": 5.0 + i,
                        "impact_score": 6.0 + i,
                        "files_changed": 3 + i,
                        "ai_assisted": i % 2 == 0,
                        "ai_tool_type": "Claude" if i % 2 == 0 else None,
                    }
                )
            else:  # 2 PRs
                data.append(
                    {
                        "author": "dev1@example.com",
                        "date": (base_date + timedelta(days=i)).isoformat(),
                        "source_type": "PR",
                        "complexity_score": 7.0 + i,
                        "impact_score": 8.0 + i,
                        "files_changed": 10 + i,
                        "ai_assisted": True,
                        "ai_tool_type": "Copilot",
                    }
                )

        # Developer 2 data - Week 1
        for i in range(3):  # 2 commits, 1 PR
            if i < 2:  # 2 commits
                data.append(
                    {
                        "author": "dev2@example.com",
                        "date": (base_date + timedelta(days=i)).isoformat(),
                        "source_type": "Commit",
                        "complexity_score": 4.0,
                        "impact_score": 5.0,
                        "files_changed": 2,
                        "ai_assisted": False,
                        "ai_tool_type": None,
                    }
                )
            else:  # 1 PR
                data.append(
                    {
                        "author": "dev2@example.com",
                        "date": (base_date + timedelta(days=i)).isoformat(),
                        "source_type": "PR",
                        "complexity_score": 6.0,
                        "impact_score": 7.0,
                        "files_changed": 8,
                        "ai_assisted": False,
                        "ai_tool_type": None,
                    }
                )

        return pd.DataFrame(data)

    def test_load_unified_data_file_exists(self, aggregator, sample_unified_data):
        """Test loading unified data when file exists."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            sample_unified_data.to_csv(f.name, index=False)

            try:
                result = aggregator._load_unified_data(f.name)
                assert len(result) == len(sample_unified_data)
                assert "date" in result.columns
                assert pd.api.types.is_datetime64_any_dtype(result["date"])
            finally:
                os.unlink(f.name)

    def test_load_unified_data_file_not_exists(self, aggregator):
        """Test loading unified data when file doesn't exist."""
        result = aggregator._load_unified_data("nonexistent.csv")
        assert result.empty

    def test_group_by_author_and_week(self, aggregator, sample_unified_data):
        """Test grouping data by author and week."""
        # Add date column as datetime
        sample_unified_data["date"] = pd.to_datetime(sample_unified_data["date"])

        grouped = aggregator._group_by_author_and_week(sample_unified_data)

        # Should have groups for each author-week combination
        groups = list(grouped.groups.keys())
        assert len(groups) >= 2  # At least 2 developers

        # Check that week period is properly formatted
        for author, period in groups:
            assert period.startswith("2025-W")

    def test_calculate_developer_metrics(self, aggregator):
        """Test calculating metrics for a single developer-week."""
        # Create sample group data
        group_data = pd.DataFrame(
            [
                {
                    "source_type": "Commit",
                    "complexity_score": 5.0,
                    "impact_score": 6.0,
                    "files_changed": 3,
                    "ai_assisted": True,
                },
                {
                    "source_type": "Commit",
                    "complexity_score": 6.0,
                    "impact_score": 7.0,
                    "files_changed": 4,
                    "ai_assisted": False,
                },
                {
                    "source_type": "PR",
                    "complexity_score": 8.0,
                    "impact_score": 9.0,
                    "files_changed": 10,
                    "ai_assisted": True,
                },
            ]
        )

        result = aggregator._calculate_developer_metrics("test@example.com", "2025-W01", group_data)

        assert result.author == "test@example.com"
        assert result.period == "2025-W01"
        assert result.commit_frequency == 0.286  # 2 commits / 7 days, rounded to 3 decimals
        assert result.pr_frequency == 1.0  # 1 PR per week
        assert result.ai_usage_rate == 66.7  # 2/3 * 100, rounded to 1 decimal
        assert result.avg_pr_size == 10.0  # Average files changed for PRs
        assert result.avg_complexity == 6.33  # (5+6+8)/3, rounded to 2 decimals
        assert result.avg_impact_score == 7.33  # (6+7+9)/3, rounded to 2 decimals

    def test_save_developer_metrics_new_file(self, aggregator):
        """Test saving developer metrics to a new file."""
        metrics = [
            DeveloperMetrics("dev1@example.com", "2025-W01", 2.5, 3.0, 75.0, 8.5, 6.2, 7.8),
            DeveloperMetrics("dev2@example.com", "2025-W01", 1.2, 1.0, 25.0, 5.5, 4.8, 5.5),
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            try:
                result = aggregator._save_developer_metrics(metrics, f.name, False)
                assert result == 2

                # Check file was created and has correct content
                df = pd.read_csv(f.name)
                assert len(df) == 2
                assert list(df.columns) == [
                    "author",
                    "period",
                    "commit_frequency",
                    "pr_frequency",
                    "ai_usage_rate",
                    "avg_pr_size",
                    "avg_complexity",
                    "avg_impact_score",
                ]
            finally:
                os.unlink(f.name)

    def test_save_developer_metrics_incremental(self, aggregator):
        """Test saving developer metrics incrementally (avoiding duplicates)."""
        # Create initial file with existing data
        existing_metrics = [
            DeveloperMetrics("dev1@example.com", "2025-W01", 2.5, 3.0, 75.0, 8.5, 6.2, 7.8)
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            try:
                # Save initial data
                aggregator._save_developer_metrics(existing_metrics, f.name, False)

                # Try to save new data including duplicates
                new_metrics = [
                    DeveloperMetrics(
                        "dev1@example.com", "2025-W01", 2.5, 3.0, 75.0, 8.5, 6.2, 7.8
                    ),  # Duplicate
                    DeveloperMetrics(
                        "dev2@example.com", "2025-W01", 1.2, 1.0, 25.0, 5.5, 4.8, 5.5
                    ),  # New
                ]

                result = aggregator._save_developer_metrics(new_metrics, f.name, True)
                assert result == 1  # Only 1 new record saved

                # Check final file has no duplicates
                df = pd.read_csv(f.name)
                assert len(df) == 2
                assert (
                    len(df[(df["author"] == "dev1@example.com") & (df["period"] == "2025-W01")])
                    == 1
                )

            finally:
                os.unlink(f.name)

    def test_get_ai_usage_breakdown(self, aggregator, sample_unified_data):
        """Test getting AI usage breakdown by developer and tool."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            sample_unified_data.to_csv(f.name, index=False)

            try:
                result = aggregator.get_ai_usage_breakdown(f.name)

                assert "dev1@example.com" in result
                assert "dev2@example.com" in result

                dev1_data = result["dev1@example.com"]
                assert "total_work" in dev1_data
                assert "ai_assisted" in dev1_data
                assert "ai_percentage" in dev1_data
                assert "tools" in dev1_data

                # Dev1 should have AI usage, dev2 should not
                assert dev1_data["ai_percentage"] > 0
                assert result["dev2@example.com"]["ai_percentage"] == 0

            finally:
                os.unlink(f.name)

    def test_validate_developer_metrics(self, aggregator):
        """Test validating developer metrics data integrity."""
        # Create test metrics file
        test_data = pd.DataFrame(
            [
                {
                    "author": "dev1@example.com",
                    "period": "2025-W01",
                    "commit_frequency": 2.5,
                    "pr_frequency": 3.0,
                    "ai_usage_rate": 75.0,
                    "avg_pr_size": 8.5,
                    "avg_complexity": 6.2,
                    "avg_impact_score": 7.8,
                },
                {
                    "author": "dev2@example.com",
                    "period": "2025-W01",
                    "commit_frequency": 1.2,
                    "pr_frequency": 1.0,
                    "ai_usage_rate": 25.0,
                    "avg_pr_size": 5.5,
                    "avg_complexity": 4.8,
                    "avg_impact_score": 5.5,
                },
            ]
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            test_data.to_csv(f.name, index=False)

            try:
                result = aggregator.validate_developer_metrics(f.name)

                assert "total_records" in result
                assert "unique_developers" in result
                assert "date_range" in result
                assert "data_quality" in result
                assert "summary_stats" in result

                assert result["total_records"] == 2
                assert result["unique_developers"] == 2

            finally:
                os.unlink(f.name)

    def test_aggregate_developer_metrics_end_to_end(self, aggregator, sample_unified_data):
        """Test end-to-end developer metrics aggregation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as input_file:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as output_file:
                sample_unified_data.to_csv(input_file.name, index=False)

                try:
                    result = aggregator.aggregate_developer_metrics(
                        input_file.name, output_file.name, incremental=False
                    )

                    assert result >= 2  # At least 2 developer-week records

                    # Check output file was created
                    assert Path(output_file.name).exists()

                    # Check output file has correct structure
                    df = pd.read_csv(output_file.name)
                    expected_columns = [
                        "author",
                        "period",
                        "commit_frequency",
                        "pr_frequency",
                        "ai_usage_rate",
                        "avg_pr_size",
                        "avg_complexity",
                        "avg_impact_score",
                    ]
                    assert list(df.columns) == expected_columns

                finally:
                    os.unlink(input_file.name)
                    os.unlink(output_file.name)
