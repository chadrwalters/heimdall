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

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config.team_config import team_config

# Constants
BAR_GROUP_WIDTH = 0.8  # Total width for grouped bar charts


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
            name_config: Path to developer names config (for backwards compatibility)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Use centralized team config for names and colors
        self.team_config = team_config

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
        """Unify developer names using team config.

        Args:
            df: DataFrame with author column
            author_column: Name of column containing author identifier

        Returns:
            DataFrame with unified author names
        """
        df = df.copy()

        # Determine which source system based on column name
        if author_column == "author":  # GitHub handle
            df[author_column] = df[author_column].apply(
                lambda x: self.team_config.get_canonical_name(x, source="github") if pd.notna(x) else x
            )
        elif author_column == "author_name":  # Git name
            df[author_column] = df[author_column].apply(
                lambda x: self.team_config.get_canonical_name(x, source="git") if pd.notna(x) else x
            )
        elif author_column == "assignee_name":  # Linear name
            df[author_column] = df[author_column].apply(
                lambda x: self.team_config.get_canonical_name(x, source="linear") if pd.notna(x) else x
            )

        return df

    def _format_week_axis(self, ax, dates, num_points):
        """Format x-axis to show week ranges for weekly data.

        Args:
            ax: Matplotlib axis object
            dates: DatetimeIndex of dates
            num_points: Number of data points
        """
        if num_points <= 10:
            # Weekly data - show week ranges
            labels = []
            for date in dates:
                # Calculate week start (Monday) and end (Sunday)
                week_start = date - pd.Timedelta(days=date.weekday())
                week_end = week_start + pd.Timedelta(days=6)
                labels.append(f"{week_start.strftime('%b %d')}-{week_end.strftime('%d')}")

            ax.set_xticks(range(len(dates)))
            ax.set_xticklabels(labels, rotation=45, ha='right')
        else:
            # Daily data - use existing date formatting
            if num_points <= 7:
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
            elif num_points <= 31:
                interval = max(1, num_points // 10)
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=interval))
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
            else:
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))

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
            filtered = df[df["on_main_branch"]]
            print(f"  Filtered to {len(filtered)} commits on main branches")
            return filtered

        # If no branch info, return all (shouldn't happen)
        print("  ⚠️  No branch info found, using all data")
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
        color_map = self.team_config.get_color_map(developers)

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

        # Determine if this is weekly or daily data
        freq = df['period'].iloc[0].freq if len(df) > 0 else None
        is_weekly = freq == 'W' if freq else num_points <= 10

        if is_weekly:
            self._format_week_axis(ax, pivot.index, num_points)
        else:
            # Dynamic date formatting for daily data
            if num_points <= 7:
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
            elif num_points <= 31:
                interval = max(1, num_points // 10)
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=interval))
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
            else:
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
        color_map = self.team_config.get_color_map(developers)

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

        # Determine if this is weekly or daily data
        freq = df['period'].iloc[0].freq if len(df) > 0 else None
        is_weekly = freq == 'W' if freq else num_points <= 10

        if is_weekly:
            self._format_week_axis(ax, cumulative.index, num_points)
        else:
            # Dynamic date formatting for daily data
            if num_points <= 7:
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
            elif num_points <= 31:
                interval = max(1, num_points // 10)
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=interval))
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
            else:
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

        # Explicit copy to avoid SettingWithCopyWarning
        main_prs = main_prs.copy()

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

    def _create_cycle_line_chart(
        self,
        cycle_df: pd.DataFrame,
        metric_column: str,
        title: str,
        ylabel: str,
        output_file: str
    ):
        """Create line chart for cycle metrics by developer.

        Shows metric trends across cycles with one line per developer.
        Automatically applies consistent developer colors across all charts.

        Args:
            cycle_df: DataFrame with cycle data including cycle_number,
                     assignee_name, and the metric column
            metric_column: Column to aggregate - 'count' for issue count
                          or 'estimate' for story points
            title: Chart title
            ylabel: Y-axis label (e.g., "Number of Issues", "Story Points")
            output_file: Output filename (saved to self.output_dir)

        Returns:
            None. Saves chart to file and prints confirmation message.
        """
        # Treat blank/zero estimates as XS (1 point) for story points charts
        if metric_column == 'estimate':
            # Fill NaN and 0 estimates with 1 point (XS)
            cycle_df = cycle_df.copy()
            cycle_df.loc[:, "estimate"] = cycle_df["estimate"].fillna(1).replace(0, 1)

        # Group by cycle and assignee
        if metric_column == 'count':
            grouped = (
                cycle_df.groupby(["cycle_number", "assignee_name"])
                .size()
                .reset_index(name="value")
            )
        else:  # sum estimates
            grouped = (
                cycle_df.groupby(["cycle_number", "assignee_name"])[metric_column]
                .sum()
                .reset_index(name="value")
            )

        # Pivot for line chart
        pivot = grouped.pivot(
            index="cycle_number", columns="assignee_name", values="value"
        ).fillna(0)

        # Get color map for developers
        developers = pivot.columns.tolist()

        # Protect against no developers
        if len(developers) == 0:
            print("⚠️  No developers with data for this chart")
            return

        color_map = self.team_config.get_color_map(developers)

        # Create figure
        fig, ax = plt.subplots(figsize=(14, 6))

        # Plot lines for each developer
        for developer in developers:
            ax.plot(
                pivot.index,
                pivot[developer],
                label=developer,
                color=color_map[developer],
                marker='o',
                linewidth=2,
                markersize=6,
                alpha=0.8
            )

        # Configure axes
        ax.set_title(title, fontsize=16, fontweight="bold", pad=20)
        ax.set_xlabel("Cycle", fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.set_xticks(pivot.index)
        ax.set_xticklabels([f"Cycle {num}" for num in pivot.index], rotation=45, ha='right', fontsize=10)
        ax.legend(title="Developer", bbox_to_anchor=(1.05, 1), loc="upper left")
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        output_path = self.output_dir / output_file
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"✅ Saved: {output_path}")
        plt.close()

    def _create_cycle_completion_chart(
        self,
        cycle_df: pd.DataFrame,
        output_file: str
    ):
        """Create line chart showing cycle completion percentage by developer.

        Shows what percentage of started work was completed within each cycle.
        Formula: (completed / started) * 100 for each developer per cycle.

        Args:
            cycle_df: DataFrame with cycle data including cycle_number, assignee_name,
                     created_at, completed_at, cycle_start, cycle_end, state_type
            output_file: Output filename (saved to self.output_dir)

        Returns:
            None. Saves chart to file and prints confirmation message.
        """
        # Calculate started issues per dev per cycle
        started_df = cycle_df[
            (cycle_df["created_at"] >= cycle_df["cycle_start"]) &
            (cycle_df["created_at"] <= cycle_df["cycle_end"])
        ]
        started_counts = (
            started_df.groupby(["cycle_number", "assignee_name"])
            .size()
            .reset_index(name="started")
        )

        # Calculate completed issues per dev per cycle
        # Count both "completed" and "canceled" as finished (canceled = done but not delivered)
        completed_df = cycle_df[
            (cycle_df["state_type"].isin(["completed", "canceled"])) &
            (cycle_df["completed_at"].notna()) &
            (cycle_df["completed_at"] >= cycle_df["cycle_start"]) &
            (cycle_df["completed_at"] <= cycle_df["cycle_end"])
        ]
        completed_counts = (
            completed_df.groupby(["cycle_number", "assignee_name"])
            .size()
            .reset_index(name="completed")
        )

        # Merge started and completed counts
        merged = pd.merge(
            started_counts,
            completed_counts,
            on=["cycle_number", "assignee_name"],
            how="outer"
        ).fillna(0)

        # Calculate completion rate
        merged["completion_rate"] = (
            (merged["completed"] / merged["started"] * 100)
            .replace([float('inf'), -float('inf')], 0)
            .fillna(0)
        )

        # Pivot for plotting
        pivot = merged.pivot(
            index="cycle_number",
            columns="assignee_name",
            values="completion_rate"
        ).fillna(0)

        # Get color map for developers
        developers = pivot.columns.tolist()

        # Protect against no developers
        if len(developers) == 0:
            print("⚠️  No developers with data for completion chart")
            return

        color_map = self.team_config.get_color_map(developers)

        # Create figure
        fig, ax = plt.subplots(figsize=(14, 6))

        # Plot lines for each developer
        for developer in developers:
            ax.plot(
                pivot.index,
                pivot[developer],
                label=developer,
                color=color_map[developer],
                marker='o',
                linewidth=2,
                markersize=6,
                alpha=0.8
            )

        # Configure axes
        ax.set_title(
            "Cycle Completion Rate by Developer",
            fontsize=16,
            fontweight="bold",
            pad=20
        )
        ax.set_xlabel("Cycle", fontsize=12)
        ax.set_ylabel("Completion Rate (%)", fontsize=12)
        # Dynamic Y-axis to accommodate completion rates >100%
        # When teams complete carryover work, rates can exceed 100%
        max_rate = pivot.max().max() if len(pivot) > 0 else 100
        y_max = max(105, max_rate * 1.1)  # 10% headroom, minimum 105
        ax.set_ylim(0, y_max)
        ax.set_xticks(pivot.index)
        ax.set_xticklabels([f"Cycle {num}" for num in pivot.index], rotation=45, ha='right', fontsize=10)
        ax.legend(title="Developer", bbox_to_anchor=(1.05, 1), loc="upper left")
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        output_path = self.output_dir / output_file
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"✅ Saved: {output_path}")
        plt.close()

    def generate_cycle_charts(self, cycle_csv_path: str, output_dir: str | None = None):
        """Generate Linear cycle visualization charts.

        Creates five line charts showing issue and point metrics by cycle:
        - Issues Started in Each Cycle
        - Story Points Started in Each Cycle
        - Issues Completed in Each Cycle
        - Story Points Completed in Each Cycle
        - Cycle Completion Rate by Developer

        Args:
            cycle_csv_path: Path to Linear cycles CSV file. Must contain columns:
                           cycle_number, assignee_name, created_at, completed_at,
                           cycle_start, cycle_end, estimate, state_type
            output_dir: Optional output directory override (defaults to self.output_dir)

        Returns:
            None. Generates charts and saves to output directory.
        """
        print("\n📊 Generating Linear cycle charts...")

        # Load cycle data
        cycle_path = Path(cycle_csv_path)
        if not cycle_path.exists():
            print(f"❌ Cycle data file not found: {cycle_csv_path}")
            return

        cycle_df = pd.read_csv(cycle_csv_path)
        print(f"  Loaded {len(cycle_df)} cycle issues")

        # Validate required columns
        required_columns = [
            "cycle_number", "assignee_name", "created_at", "completed_at",
            "cycle_start", "cycle_end", "estimate", "state_type"
        ]
        missing = [col for col in required_columns if col not in cycle_df.columns]
        if missing:
            print(f"❌ Missing required columns: {', '.join(missing)}")
            return

        # Apply name unification BEFORE filtering
        cycle_df["assignee_name"] = cycle_df["assignee_name"].apply(
            lambda x: self.team_config.get_canonical_name(x, source="linear") if pd.notna(x) else None
        )

        # Filter for valid assignees
        valid_df = cycle_df[cycle_df["assignee_name"].notna() & (cycle_df["assignee_name"] != "")].copy()
        print(f"  Filtered to {len(valid_df)} issues with assignees")

        if len(valid_df) == 0:
            print("⚠️  No cycle data with valid assignees")
            return

        # Convert date columns
        valid_df["created_at"] = pd.to_datetime(valid_df["created_at"], utc=True)
        valid_df["completed_at"] = pd.to_datetime(valid_df["completed_at"], utc=True)
        valid_df["cycle_start"] = pd.to_datetime(valid_df["cycle_start"], utc=True)
        valid_df["cycle_end"] = pd.to_datetime(valid_df["cycle_end"], utc=True)

        # Handle missing estimates (treat as 0)
        valid_df["estimate"] = valid_df["estimate"].fillna(0)

        # Set output directory if specified
        original_output_dir = self.output_dir
        if output_dir:
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(exist_ok=True)

        try:
            # Chart 1: Issues Started (created in cycle period)
            started_df = valid_df[
                (valid_df["created_at"] >= valid_df["cycle_start"]) &
                (valid_df["created_at"] <= valid_df["cycle_end"])
            ]
            if len(started_df) > 0:
                self._create_cycle_line_chart(
                    started_df,
                    "count",
                    "Issues Started in Each Cycle by Developer",
                    "Number of Issues",
                    "cycle_issues_started.png"
                )
            else:
                print("⚠️  No issues with creation dates in cycle periods")

            # Chart 2: Points Started
            if len(started_df) > 0:
                self._create_cycle_line_chart(
                    started_df,
                    "estimate",
                    "Story Points Started in Each Cycle by Developer",
                    "Story Points",
                    "cycle_points_started.png"
                )

            # Chart 3: Issues Completed (completed in cycle period)
            # Count both "completed" and "canceled" as finished
            completed_df = valid_df[
                (valid_df["state_type"].isin(["completed", "canceled"])) &
                (valid_df["completed_at"].notna()) &
                (valid_df["completed_at"] >= valid_df["cycle_start"]) &
                (valid_df["completed_at"] <= valid_df["cycle_end"])
            ]
            if len(completed_df) > 0:
                self._create_cycle_line_chart(
                    completed_df,
                    "count",
                    "Issues Completed in Each Cycle by Developer",
                    "Number of Issues",
                    "cycle_issues_completed.png"
                )
            else:
                print("⚠️  No completed issues in cycle periods")

            # Chart 4: Points Completed
            if len(completed_df) > 0:
                self._create_cycle_line_chart(
                    completed_df,
                    "estimate",
                    "Story Points Completed in Each Cycle by Developer",
                    "Story Points",
                    "cycle_points_completed.png"
                )

            # Chart 5: Cycle Completion Rate (NEW)
            if len(started_df) > 0 and len(completed_df) > 0:
                self._create_cycle_completion_chart(
                    valid_df,
                    "cycle_completion_rate.png"
                )
            else:
                print("⚠️  Not enough data for completion rate chart")

            print("\n✅ Cycle charts generated successfully!")

        finally:
            # Restore original output directory
            if output_dir:
                self.output_dir = original_output_dir

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
        "--cycles",
        default=None,
        help="Path to Linear cycles CSV file (optional)",
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

    # Generate standard charts
    visualizer.generate_all_charts()

    # Generate cycle charts if cycle data provided
    if args.cycles:
        visualizer.generate_cycle_charts(args.cycles, args.output)


if __name__ == "__main__":
    main()
