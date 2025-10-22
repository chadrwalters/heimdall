#!/usr/bin/env python3
"""Generate AI usage charts from ingested data.

Creates visualizations for:
- Daily cost per developer (Claude Code + Codex combined)
- Weekly cost per developer
- Daily tokens per developer
- Weekly tokens per developer
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config.team_config import team_config


class AIUsageVisualizer:
    """Generate AI usage visualizations from ingested data."""

    def __init__(self, ingested_dir: str = "data/ai_usage/ingested", output_dir: str = "charts"):
        """Initialize visualizer.

        Args:
            ingested_dir: Directory containing ingested JSON files
            output_dir: Output directory for charts
        """
        self.ingested_dir = Path(ingested_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)

        self.team_config = team_config

        # Load and process data
        self.df = self._load_data()

        if self.df is None or len(self.df) == 0:
            print("❌ No data available for chart generation")
            sys.exit(1)

    def _load_data(self) -> pd.DataFrame:
        """Load all ingested JSON files and convert to DataFrame.

        Returns:
            DataFrame with columns: date, developer, source, cost, tokens
        """
        if not self.ingested_dir.exists():
            print(f"❌ Ingested directory not found: {self.ingested_dir}")
            return None

        json_files = list(self.ingested_dir.glob("*_ingested.json"))
        if not json_files:
            print(f"❌ No ingested files found in {self.ingested_dir}")
            return None

        print(f"📂 Loading {len(json_files)} ingested files...")

        all_records = []

        for json_file in json_files:
            try:
                with open(json_file) as f:
                    data = json.load(f)

                developer = data['developer']

                for day in data['days']:
                    date = day['date']

                    # Process Claude Code data
                    if day.get('claude_code'):
                        cc_data = day['claude_code']
                        all_records.append({
                            'date': date,
                            'developer': developer,
                            'source': 'claude_code',
                            'cost': cc_data.get('totalCost', 0),
                            'tokens': cc_data.get('totalTokens', 0)
                        })

                    # Process Codex data
                    if day.get('codex'):
                        codex_data = day['codex']
                        all_records.append({
                            'date': date,
                            'developer': developer,
                            'source': 'codex',
                            'cost': codex_data.get('costUSD', 0),
                            'tokens': codex_data.get('totalTokens', 0)
                        })

            except Exception as e:
                print(f"⚠️  Error loading {json_file.name}: {e}")
                continue

        if not all_records:
            print("❌ No data records found")
            return None

        df = pd.DataFrame(all_records)
        # Handle mixed date formats (Claude Code: "2025-10-21", Codex: "Oct 22, 2025")
        df['date'] = pd.to_datetime(df['date'], format='mixed')
        print(f"  ✅ Loaded {len(df)} records from {len(df['developer'].unique())} developers")

        return df

    def _aggregate_by_period(self, freq: str = 'D') -> pd.DataFrame:
        """Aggregate data by period (daily or weekly).

        Args:
            freq: Pandas frequency string ('D' for daily, 'W' for weekly)

        Returns:
            DataFrame with aggregated costs and tokens per developer per period
        """
        df = self.df.copy()
        df['period'] = df['date'].dt.to_period(freq)

        # Aggregate by developer and period (combining Claude Code + Codex)
        aggregated = df.groupby(['period', 'developer']).agg({
            'cost': 'sum',
            'tokens': 'sum'
        }).reset_index()

        aggregated['date'] = aggregated['period'].dt.to_timestamp()

        return aggregated

    def _create_line_chart(
        self,
        df: pd.DataFrame,
        value_col: str,
        title: str,
        ylabel: str,
        filename: str,
        is_weekly: bool = False
    ):
        """Create line chart for costs or tokens.

        Args:
            df: Aggregated data with date, developer, and value columns
            value_col: Column to plot ('cost' or 'tokens')
            title: Chart title
            ylabel: Y-axis label
            filename: Output filename
            is_weekly: Whether this is weekly data (affects formatting)
        """
        # Pivot for line chart
        pivot = df.pivot(index='date', columns='developer', values=value_col).fillna(0)

        # Get color map
        developers = pivot.columns.tolist()
        color_map = self.team_config.get_color_map(developers)

        # Create figure
        fig, ax = plt.subplots(figsize=(14, 7))

        # Plot each developer
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

        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.legend(title='Developer', bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)

        # Format axes
        if is_weekly:
            self._format_week_axis(ax, pivot.index, len(pivot.index))
        else:
            num_points = len(pivot.index)
            if num_points <= 7:
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
            elif num_points <= 31:
                interval = max(1, num_points // 10)
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=interval))
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
            else:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))

        # Special formatting for cost (add dollar sign)
        if value_col == 'cost':
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'${y:.2f}'))

        fig.autofmt_xdate()
        plt.tight_layout()

        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {output_path}")
        plt.close()

    def _format_week_axis(self, ax, dates, num_weeks):
        """Format x-axis for weekly data showing week ranges.

        Args:
            ax: Matplotlib axis
            dates: DatetimeIndex of week start dates
            num_weeks: Number of weeks in dataset
        """
        # Set tick positions at the center of each week
        ax.set_xticks(dates)

        # Create labels showing week ranges
        labels = []
        for date in dates:
            week_start = date
            week_end = date + pd.Timedelta(days=6)
            labels.append(f"{week_start.strftime('%b %d')}-{week_end.strftime('%d')}")

        ax.set_xticklabels(labels, rotation=45, ha='right')

    def _create_stacked_bar_chart(
        self,
        df: pd.DataFrame,
        value_col: str,
        title: str,
        ylabel: str,
        filename: str,
        is_weekly: bool = False
    ):
        """Create stacked bar chart showing source breakdown.

        Args:
            df: Data with date, developer, source, and value
            value_col: Column to plot ('cost' or 'tokens')
            title: Chart title
            ylabel: Y-axis label
            filename: Output filename
            is_weekly: Whether this is weekly data
        """
        # Pivot with source as columns
        pivot = df.pivot_table(
            index='date',
            columns='source',
            values=value_col,
            aggfunc='sum',
            fill_value=0
        )

        # Create figure
        fig, ax = plt.subplots(figsize=(14, 7))

        # Stacked bar chart
        pivot.plot(
            kind='bar',
            stacked=True,
            ax=ax,
            color=['#1f77b4', '#ff7f0e'],  # Blue for Claude Code, Orange for Codex
            alpha=0.8,
            width=0.8
        )

        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.legend(title='Source', labels=['Claude Code', 'Codex'])
        ax.grid(True, alpha=0.3, axis='y')

        # Format x-axis labels
        if is_weekly:
            labels = []
            for date in pivot.index:
                week_start = date
                week_end = date + pd.Timedelta(days=6)
                labels.append(f"{week_start.strftime('%b %d')}-{week_end.strftime('%d')}")
            ax.set_xticklabels(labels, rotation=45, ha='right')
        else:
            ax.set_xticklabels([d.strftime('%b %d') for d in pivot.index], rotation=45, ha='right')

        # Special formatting for cost
        if value_col == 'cost':
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'${y:.2f}'))

        plt.tight_layout()

        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {output_path}")
        plt.close()

    def generate_all_charts(self):
        """Generate all AI usage charts."""
        print("\n📊 Generating AI usage charts...")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        # Daily aggregation
        daily = self._aggregate_by_period('D')

        # Weekly aggregation
        weekly = self._aggregate_by_period('W')

        # Daily cost per developer
        self._create_line_chart(
            daily,
            'cost',
            'Daily AI Usage Cost per Developer (Claude Code + Codex)',
            'Cost ($)',
            'ai_usage_daily_cost.png',
            is_weekly=False
        )

        # Weekly cost per developer
        self._create_line_chart(
            weekly,
            'cost',
            'Weekly AI Usage Cost per Developer (Claude Code + Codex)',
            'Cost ($)',
            'ai_usage_weekly_cost.png',
            is_weekly=True
        )

        # Daily tokens per developer
        self._create_line_chart(
            daily,
            'tokens',
            'Daily AI Token Usage per Developer (Claude Code + Codex)',
            'Total Tokens',
            'ai_usage_daily_tokens.png',
            is_weekly=False
        )

        # Weekly tokens per developer
        self._create_line_chart(
            weekly,
            'tokens',
            'Weekly AI Token Usage per Developer (Claude Code + Codex)',
            'Total Tokens',
            'ai_usage_weekly_tokens.png',
            is_weekly=True
        )

        # Stacked bar charts showing source breakdown
        daily_with_source = self.df.copy()
        daily_with_source['date'] = daily_with_source['date'].dt.to_period('D').dt.to_timestamp()
        daily_grouped = daily_with_source.groupby(['date', 'source']).agg({
            'cost': 'sum',
            'tokens': 'sum'
        }).reset_index()

        self._create_stacked_bar_chart(
            daily_grouped,
            'cost',
            'Daily AI Usage Cost by Source (Organization Total)',
            'Cost ($)',
            'ai_usage_daily_cost_by_source.png',
            is_weekly=False
        )

        weekly_with_source = self.df.copy()
        weekly_with_source['date'] = weekly_with_source['date'].dt.to_period('W').dt.to_timestamp()
        weekly_grouped = weekly_with_source.groupby(['date', 'source']).agg({
            'cost': 'sum',
            'tokens': 'sum'
        }).reset_index()

        self._create_stacked_bar_chart(
            weekly_grouped,
            'cost',
            'Weekly AI Usage Cost by Source (Organization Total)',
            'Cost ($)',
            'ai_usage_weekly_cost_by_source.png',
            is_weekly=True
        )

        print("\n✅ All charts generated successfully!")


def main():
    """Main entry point."""
    ingested_dir = "data/ai_usage/ingested"
    output_dir = "charts"

    if len(sys.argv) > 1:
        ingested_dir = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]

    visualizer = AIUsageVisualizer(ingested_dir, output_dir)
    visualizer.generate_all_charts()


if __name__ == "__main__":
    main()
