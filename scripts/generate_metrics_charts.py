#!/usr/bin/env python3
"""Generate daily/weekly metrics charts for commits, PRs, and Linear tickets.

This is the PRODUCTION chart generation system. It creates time-series
visualizations showing developer activity over time.

NO AI ANALYSIS - Just raw metrics:
- Commits: count and size (lines changed)
- PRs: count and size (lines changed)
- Linear: count and story points
"""

import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data.name_unifier import NameUnifier
from data.developer_colors import DeveloperColorMapper


class MetricsVisualizer:
    """Generate metrics visualizations from commit, PR, and Linear data."""

    def __init__(
        self,
        commits_file: str | None = None,
        prs_file: str | None = None,
        linear_file: str | None = None,
        output_dir: str = "charts",
        name_config: str = "config/developer_names.json"
    ):
        """Initialize visualizer with data files.

        Args:
            commits_file: Path to commits CSV
            prs_file: Path to PRs CSV
            linear_file: Path to Linear tickets CSV (optional)
            output_dir: Output directory for charts
            name_config: Path to developer names config
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Initialize name unifier and color mapper
        self.unifier = NameUnifier(name_config)
        self.color_mapper = DeveloperColorMapper(name_config)

        # Load commits data
        if commits_file and Path(commits_file).exists():
            print(f"Loading commits from {commits_file}...")
            self.commits_df = pd.read_csv(commits_file)
            self.commits_df["committed_date"] = pd.to_datetime(
                self.commits_df["committed_date"], utc=True
            )
            self.commits_df = self._unify_names(self.commits_df, "author_name")
            print(f"  Loaded {len(self.commits_df)} commits")
        else:
            print("No commits data available")
            self.commits_df = None

        # Load PRs data
        if prs_file and Path(prs_file).exists():
            print(f"Loading PRs from {prs_file}...")
            self.prs_df = pd.read_csv(prs_file)
            self.prs_df["merged_at"] = pd.to_datetime(
                self.prs_df["merged_at"], utc=True
            )
            self.prs_df = self._unify_names(self.prs_df, "author")
            print(f"  Loaded {len(self.prs_df)} PRs")
        else:
            print("No PRs data available")
            self.prs_df = None

        # Linear data would be loaded here if provided
        self.linear_df = None

    def _unify_names(self, df: pd.DataFrame, author_column: str) -> pd.DataFrame:
        """Unify developer names using name config.

        Args:
            df: DataFrame with author column
            author_column: Name of column containing author identifier

        Returns:
            DataFrame with unified author names
        """
        df = df.copy()

        # Determine which unification method to use based on column name
        if author_column == "author":  # GitHub handle
            df[author_column] = df[author_column].apply(
                lambda x: self.unifier.unify(github_handle=x) if pd.notna(x) else x
            )
        elif author_column == "author_name":  # Git name
            df[author_column] = df[author_column].apply(
                lambda x: self.unifier.unify(git_name=x) if pd.notna(x) else x
            )
        elif author_column == "assignee_name":  # Linear name
            df[author_column] = df[author_column].apply(
                lambda x: self.unifier.unify(linear_name=x) if pd.notna(x) else x
            )

        return df

    def _filter_main_branches(
        self, df: pd.DataFrame, date_col: str
    ) -> pd.DataFrame:
        """Filter data to main/dev branches only.

        Args:
            df: DataFrame to filter
            date_col: Name of date column (for logging)

        Returns:
            Filtered DataFrame
        """
        # For PRs: use base_branch column
        if "base_branch" in df.columns:
            filtered = df[df["base_branch"].isin(["main", "master", "dev", "develop"])]
            print(f"  Filtered to {len(filtered)} PRs merged to main branches")
            return filtered

        # For commits: use on_main_branch column
        elif "on_main_branch" in df.columns:
            filtered = df[df["on_main_branch"] == True]
            print(f"  Filtered to {len(filtered)} commits on main branches")
            return filtered

        # If no branch info, return all (shouldn't happen)
        print(f"  ⚠️  No branch info found, using all data")
        return df

    def _aggregate_by_period(
        self,
        df: pd.DataFrame,
        date_col: str,
        author_col: str,
        freq: str = "D",
        metric_col: str | None = None
    ) -> pd.DataFrame:
        """Aggregate metrics by time period and developer.

        Args:
            df: DataFrame with data
            date_col: Name of date column
            author_col: Name of author column
            freq: Pandas frequency ('D' for daily, 'W' for weekly)
            metric_col: Column to sum (for size metrics), None for count

        Returns:
            DataFrame with period, author, and count/sum columns
        """
        df = df.copy()
        df["period"] = df[date_col].dt.to_period(freq)

        if metric_col:
            # Sum the metric (e.g., additions + deletions)
            grouped = (
                df.groupby(["period", author_col])[metric_col]
                .sum()
                .reset_index(name="value")
            )
        else:
            # Count records
            grouped = (
                df.groupby(["period", author_col])
                .size()
                .reset_index(name="value")
            )

        grouped["date"] = grouped["period"].dt.to_timestamp()
        return grouped

    def _create_line_chart(
        self,
        df: pd.DataFrame,
        author_col: str,
        title: str,
        ylabel: str,
        filename: str
    ):
        """Create line chart showing per-period counts.

        Args:
            df: Aggregated data with period, author, value
            author_col: Name of author column
            title: Chart title
            ylabel: Y-axis label
            filename: Output filename
        """
        # Pivot for line chart
        pivot = df.pivot(index="date", columns=author_col, values="value").fillna(0)

        # Get color map for developers in this dataset
        developers = pivot.columns.tolist()
        color_map = self.color_mapper.get_color_map(developers)

        # Create figure
        fig, ax = plt.subplots(figsize=(14, 7))

        # Plot each developer with their assigned color
        for developer in developers:
            ax.plot(
                pivot.index,
                pivot[developer],
                label=developer,
                color=color_map[developer],
                alpha=0.8,
                linewidth=2,
                marker='o',
                markersize=4
            )

        ax.set_title(title, fontsize=16, fontweight="bold", pad=20)
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.legend(title="Developer", bbox_to_anchor=(1.05, 1), loc="upper left")
        ax.grid(True, alpha=0.3)

        # Dynamic date formatting based on number of data points
        num_points = len(pivot.index)

        if num_points <= 7:
            # Daily data for a week or less
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        elif num_points <= 10:
            # Could be weekly data (4-5 weeks) or daily data for ~10 days
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        elif num_points <= 31:
            # Daily data for a month
            interval = max(1, num_points // 10)
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=interval))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        else:
            # Longer periods
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))

        fig.autofmt_xdate()

        plt.tight_layout()
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"✅ Saved: {output_path}")
        plt.close()

    def _create_cumulative_line_chart(
        self,
        df: pd.DataFrame,
        author_col: str,
        title: str,
        ylabel: str,
        filename: str
    ):
        """Create cumulative line chart.

        Args:
            df: Aggregated data with period, author, value
            author_col: Name of author column
            title: Chart title
            ylabel: Y-axis label
            filename: Output filename
        """
        # Pivot and cumsum
        pivot = df.pivot(index="date", columns=author_col, values="value").fillna(0)
        cumulative = pivot.cumsum()

        # Get color map for developers in this dataset
        developers = cumulative.columns.tolist()
        color_map = self.color_mapper.get_color_map(developers)

        # Create figure
        fig, ax = plt.subplots(figsize=(14, 7))

        for developer in developers:
            ax.plot(
                cumulative.index,
                cumulative[developer],
                label=developer,
                color=color_map[developer],
                linewidth=2,
                marker='o',
                markersize=3
            )

        ax.set_title(title, fontsize=16, fontweight="bold", pad=20)
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.legend(title="Developer", bbox_to_anchor=(1.05, 1), loc="upper left")
        ax.grid(True, alpha=0.3)

        # Dynamic date formatting based on number of data points
        num_points = len(cumulative.index)

        if num_points <= 7:
            # Daily data for a week or less
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        elif num_points <= 10:
            # Could be weekly data (4-5 weeks) or daily data for ~10 days
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        elif num_points <= 31:
            # Daily data for a month
            interval = max(1, num_points // 10)
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=interval))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        else:
            # Longer periods
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))

        fig.autofmt_xdate()

        plt.tight_layout()
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"✅ Saved: {output_path}")
        plt.close()

    def generate_commit_charts(self, freq: str = "D"):
        """Generate commit charts for specified frequency.

        Args:
            freq: 'D' for daily, 'W' for weekly
        """
        if self.commits_df is None or len(self.commits_df) == 0:
            print("\n⚠️  No commit data available")
            return

        freq_label = "Daily" if freq == "D" else "Weekly"
        print(f"\n📊 Generating {freq_label} commit charts...")

        # Filter to main branches
        main_commits = self._filter_main_branches(self.commits_df, "committed_date")

        # Calculate size (additions + deletions)
        main_commits["size"] = main_commits["additions"] + main_commits["deletions"]

        # COUNT charts
        count_data = self._aggregate_by_period(
            main_commits, "committed_date", "author_name", freq, metric_col=None
        )

        self._create_line_chart(
            count_data,
            "author_name",
            f"{freq_label} Commits to Main/Dev by Developer",
            "Commits per Day" if freq == "D" else "Commits per Week",
            f"commits_{freq.lower()}_count_per_period.png"
        )

        self._create_cumulative_line_chart(
            count_data,
            "author_name",
            f"Cumulative Commits to Main/Dev by Developer ({freq_label})",
            "Total Commits",
            f"commits_{freq.lower()}_count_cumulative.png"
        )

        # SIZE charts
        size_data = self._aggregate_by_period(
            main_commits, "committed_date", "author_name", freq, metric_col="size"
        )

        self._create_cumulative_line_chart(
            size_data,
            "author_name",
            f"Cumulative Lines Changed (Commits) ({freq_label})",
            "Total Lines Changed",
            f"commits_{freq.lower()}_size_cumulative.png"
        )

    def generate_pr_charts(self, freq: str = "D"):
        """Generate PR charts for specified frequency.

        Args:
            freq: 'D' for daily, 'W' for weekly
        """
        if self.prs_df is None or len(self.prs_df) == 0:
            print("\n⚠️  No PR data available")
            return

        freq_label = "Daily" if freq == "D" else "Weekly"
        print(f"\n📊 Generating {freq_label} PR charts...")

        # Filter to merged PRs on main branches
        merged_prs = self.prs_df[self.prs_df["merged_at"].notna()]
        main_prs = self._filter_main_branches(merged_prs, "merged_at")

        # Calculate size
        main_prs["size"] = main_prs["additions"] + main_prs["deletions"]

        # COUNT charts
        count_data = self._aggregate_by_period(
            main_prs, "merged_at", "author", freq, metric_col=None
        )

        self._create_line_chart(
            count_data,
            "author",
            f"{freq_label} PRs Merged to Main/Dev by Developer",
            "PRs per Day" if freq == "D" else "PRs per Week",
            f"prs_{freq.lower()}_count_per_period.png"
        )

        self._create_cumulative_line_chart(
            count_data,
            "author",
            f"Cumulative PRs Merged to Main/Dev ({freq_label})",
            "Total PRs",
            f"prs_{freq.lower()}_count_cumulative.png"
        )

        # SIZE charts
        size_data = self._aggregate_by_period(
            main_prs, "merged_at", "author", freq, metric_col="size"
        )

        self._create_cumulative_line_chart(
            size_data,
            "author",
            f"Cumulative Lines Changed (PRs) ({freq_label})",
            "Total Lines Changed",
            f"prs_{freq.lower()}_size_cumulative.png"
        )

    def generate_all_charts(self):
        """Generate all chart variations."""
        print("\n🎨 Generating all metrics charts...")
        print(f"   Output directory: {self.output_dir.absolute()}")

        # Commit charts (daily and weekly)
        self.generate_commit_charts(freq="D")
        self.generate_commit_charts(freq="W")

        # PR charts (daily and weekly)
        self.generate_pr_charts(freq="D")
        self.generate_pr_charts(freq="W")

        print("\n✅ All charts generated successfully!")
        print(f"\n📂 Charts saved to: {self.output_dir.absolute()}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate metrics visualization charts"
    )
    parser.add_argument(
        "--commits",
        default="org_commits.csv",
        help="Path to commits CSV file",
    )
    parser.add_argument(
        "--prs",
        default="org_prs.csv",
        help="Path to PRs CSV file",
    )
    parser.add_argument(
        "--linear",
        default=None,
        help="Path to Linear tickets CSV file (optional)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="charts",
        help="Output directory for charts",
    )
    parser.add_argument(
        "--name-config",
        default="config/developer_names.json",
        help="Path to developer names config",
    )

    args = parser.parse_args()

    visualizer = MetricsVisualizer(
        args.commits,
        args.prs,
        args.linear,
        args.output,
        args.name_config
    )
    visualizer.generate_all_charts()


if __name__ == "__main__":
    main()
