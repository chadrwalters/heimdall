"""Hermod CLI - AI usage collection tool."""
import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from hermod import __version__
from hermod.collector import collect_usage, save_submission
from hermod.dependencies import check_all_dependencies
from hermod.git_detector import detect_developer

app = typer.Typer(
    name="hermod",
    help="AI usage collection tool for developers",
    no_args_is_help=True,
)
console = Console()


def version_callback(value: bool):
    """Show version and exit."""
    if value:
        console.print(f"Hermod version: {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    )
):
    """Hermod - AI usage collection tool."""
    pass


@app.command()
def collect(
    developer: Optional[str] = typer.Option(
        None,
        "--developer",
        "-d",
        help="Developer canonical name (auto-detected from git if not provided)",
    ),
    days: int = typer.Option(
        7,
        "--days",
        "-n",
        help="Number of days to collect usage data for",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output results as JSON",
    ),
):
    """Collect AI usage data from ccusage and ccusage-codex."""
    # Check dependencies
    deps = check_all_dependencies()
    if not all(deps.values()):
        missing = [tool for tool, installed in deps.items() if not installed]
        if json_output:
            console.print(json.dumps({"error": f"Dependencies not installed: {', '.join(missing)}"}))
        else:
            console.print(f"[red]Error:[/red] The following dependencies are not installed:")
            for tool in missing:
                console.print(f"  - {tool}")
            console.print("\nPlease install missing dependencies and try again.")
        raise typer.Exit(code=1)

    # Detect or use provided developer
    if developer is None:
        try:
            developer = detect_developer()
        except Exception as e:
            if json_output:
                console.print(json.dumps({"error": f"Failed to detect developer: {e}"}))
            else:
                console.print(f"[red]Error:[/red] Failed to detect developer: {e}")
            raise typer.Exit(code=1)

    # Collect usage data
    if not json_output:
        console.print(f"[blue]Collecting AI usage data for {developer}...[/blue]")

    try:
        data = collect_usage(developer, days)
    except Exception as e:
        if json_output:
            console.print(json.dumps({"error": f"Failed to collect usage data: {e}"}))
        else:
            console.print(f"[red]Error:[/red] Failed to collect usage data: {e}")
        raise typer.Exit(code=1)

    # Save submission
    try:
        output_file = save_submission(data, developer)
    except Exception as e:
        if json_output:
            console.print(json.dumps({"error": f"Failed to save submission: {e}"}))
        else:
            console.print(f"[red]Error:[/red] Failed to save submission: {e}")
        raise typer.Exit(code=1)

    # Output results
    if json_output:
        output_data = {
            "developer": developer,
            "days": days,
            "output_file": str(output_file),
            "claude_code": data.get("claude_code", {}),
            "codex": data.get("codex", {}),
        }
        console.print(json.dumps(output_data, indent=2))
    else:
        console.print(f"[green]✓[/green] Successfully collected usage data for {developer}")
        console.print(f"[blue]Date range:[/blue] {data['metadata']['date_range']['start']} to {data['metadata']['date_range']['end']}")
        console.print(f"[blue]Output file:[/blue] {output_file}")

        # Show summary table
        table = Table(title="Usage Summary")
        table.add_column("Tool", style="cyan")
        table.add_column("Total Cost", style="green")

        claude_total = data.get("claude_code", {}).get("totals", {}).get("totalCost", 0)
        codex_total = data.get("codex", {}).get("totals", {}).get("totalCost", 0)

        table.add_row("Claude Code", f"${claude_total:.2f}" if claude_total else "N/A")
        table.add_row("Codex", f"${codex_total:.2f}" if codex_total else "N/A")
        table.add_row("Total", f"${claude_total + codex_total:.2f}", style="bold")

        console.print(table)


if __name__ == "__main__":
    app()
