#!/usr/bin/env python3
"""
North Star Metrics - Main Execution Script

This script orchestrates the entire data extraction, analysis, and processing pipeline
for the Engineering Impact Framework.

Usage:
    python main.py --org mycompany --mode pilot
    python main.py --org mycompany --mode incremental
    python main.py --org mycompany --mode full --days 30
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.analysis.analysis_engine import AnalysisEngine
from src.config.config_manager import ConfigManager
from src.config.state_manager import StateManager
from src.data.developer_metrics import DeveloperMetricsAggregator
from src.data.unified_processor import UnifiedDataProcessor


def setup_logging(log_level: str = "INFO", log_file: str | None = None) -> None:
    """Configure logging for the application."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    handlers = [logging.StreamHandler()]
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="North Star Metrics - Engineering Impact Analysis Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run 7-day pilot analysis
  python main.py --org mycompany --mode pilot

  # Run incremental update since last run
  python main.py --org mycompany --mode incremental

  # Run full historical analysis for 30 days
  python main.py --org mycompany --mode full --days 30

  # Run with custom configuration
  python main.py --org mycompany --mode pilot --config-dir ./custom-config --output-dir ./results

Environment Variables:
  GITHUB_TOKEN       - GitHub personal access token (required)
  LINEAR_API_KEY     - Linear API key (optional, for ticket linking)
  ANTHROPIC_API_KEY  - Anthropic API key (required for analysis)
        """
    )

    # Required arguments
    parser.add_argument(
        "--org",
        required=True,
        help="GitHub organization name"
    )

    parser.add_argument(
        "--mode",
        choices=["pilot", "incremental", "full"],
        default="pilot",
        help="Execution mode: pilot (7 days), incremental (since last run), or full (custom days)"
    )

    # Optional arguments
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to analyze (default: 7, used for pilot and full modes)"
    )

    parser.add_argument(
        "--config-dir",
        default="config",
        help="Configuration directory (default: config)"
    )

    parser.add_argument(
        "--output-dir",
        default=".",
        help="Output directory for results (default: current directory)"
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )

    parser.add_argument(
        "--log-file",
        help="Log file path (default: logs to console only)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing"
    )

    parser.add_argument(
        "--skip-extraction",
        action="store_true",
        help="Skip data extraction, use existing CSV files"
    )

    parser.add_argument(
        "--skip-analysis",
        action="store_true",
        help="Skip AI analysis, only run extraction"
    )

    parser.add_argument(
        "--max-workers",
        type=int,
        default=5,
        help="Maximum parallel workers for analysis (default: 5)"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reprocessing of already analyzed data"
    )

    return parser.parse_args()


def validate_environment() -> None:
    """Validate required environment variables."""
    required_vars = ["GITHUB_TOKEN", "ANTHROPIC_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these environment variables and try again.")
        sys.exit(1)
    
    # Optional environment variables
    optional_vars = ["LINEAR_API_KEY", "LINEAR_TOKEN"]
    has_linear = any(os.getenv(var) for var in optional_vars)
    
    print("✅ Environment Variables:")
    print(f"   GitHub Token: {'✅ Set' if os.getenv('GITHUB_TOKEN') else '❌ Not set'}")
    print(f"   Anthropic API Key: {'✅ Set' if os.getenv('ANTHROPIC_API_KEY') else '❌ Not set'}")
    print(f"   Linear API Key: {'✅ Set' if has_linear else '❌ Not set (optional)'}")


def run_extraction_scripts(
    org: str, mode: str, days: int, config_dir: str, output_dir: str, logger: logging.Logger
) -> bool:
    """Run the data extraction scripts."""
    import subprocess
    
    script_path = Path("scripts/extraction/run_extraction.sh")
    if not script_path.exists():
        logger.error("Extraction script not found")
        return False
    
    # Prepare command arguments
    cmd = ["bash", str(script_path), "--org", org]
    
    if mode == "incremental":
        cmd.append("--incremental")
    elif mode == "full":
        cmd.extend(["--days", str(days)])
    elif mode == "pilot":
        cmd.extend(["--days", str(days)])
    
    cmd.extend(["--config-dir", config_dir, "--output-dir", output_dir])
    
    try:
        logger.info(f"Running extraction: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.debug(f"Extraction output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Extraction failed: {e.stderr}")
        return False


def save_progress_checkpoint(
    results: list[dict[str, Any]], 
    step: str, 
    output_dir: str, 
    logger: logging.Logger
) -> None:
    """Save progress checkpoint for error recovery."""
    checkpoint_file = Path(output_dir) / f"checkpoint_{step}_{int(time.time())}.json"
    try:
        with open(checkpoint_file, 'w') as f:
            json.dump({
                'step': step,
                'timestamp': datetime.now().isoformat(),
                'results_count': len(results),
                'results': results
            }, f, indent=2)
        logger.info(f"Progress checkpoint saved: {checkpoint_file}")
    except Exception as e:
        logger.warning(f"Failed to save checkpoint: {e}")


def load_latest_checkpoint(output_dir: str, step: str, logger: logging.Logger) -> list[dict[str, Any]]:
    """Load the latest checkpoint for a given step."""
    checkpoint_pattern = f"checkpoint_{step}_*.json"
    checkpoint_files = list(Path(output_dir).glob(checkpoint_pattern))
    
    if not checkpoint_files:
        return []
    
    # Get the most recent checkpoint
    latest_checkpoint = max(checkpoint_files, key=lambda p: p.stat().st_mtime)
    
    try:
        with open(latest_checkpoint) as f:
            data = json.load(f)
        logger.info(f"Loaded checkpoint: {latest_checkpoint} with {data['results_count']} results")
        return data.get('results', [])
    except Exception as e:
        logger.warning(f"Failed to load checkpoint {latest_checkpoint}: {e}")
        return []


def apply_ai_developer_overrides(
    results: list[dict[str, Any]], 
    config_manager: ConfigManager, 
    logger: logging.Logger
) -> list[dict[str, Any]]:
    """Apply AI developer override configuration to detected AI assistance."""
    try:
        ai_config = config_manager.load_ai_developers()
        always_ai_developers = ai_config.get("always_ai_developers", [])
        
        if not always_ai_developers:
            logger.info("No AI developer overrides configured")
            return results
        
        override_count = 0
        
        for result in results:
            author = result.get("author", "").lower()
            
            # Check if this author is in the always-AI list
            for ai_dev in always_ai_developers:
                dev_username = ai_dev.get("username", "").lower()
                dev_email = ai_dev.get("email", "").lower()
                
                if author == dev_username or author == dev_email:
                    # Override AI detection
                    if not result.get("ai_assisted", False):
                        result["ai_assisted"] = True
                        result["ai_tool_type"] = ai_dev.get("ai_tool", "Override Configuration")
                        override_count += 1
                        logger.debug(f"Applied AI override for {author}: {ai_dev.get('ai_tool')}")
                    break
        
        if override_count > 0:
            logger.info(f"Applied AI attribution overrides to {override_count} records")
            print(f"🤖 Applied AI attribution overrides to {override_count} records")
        
        return results
        
    except Exception as e:
        logger.warning(f"Failed to apply AI developer overrides: {e}")
        return results


def cleanup_old_checkpoints(output_dir: str, keep_latest: int = 3, logger: logging.Logger = None) -> None:
    """Clean up old checkpoint files, keeping only the most recent ones."""
    checkpoint_files = list(Path(output_dir).glob("checkpoint_*.json"))
    
    if len(checkpoint_files) <= keep_latest:
        return
    
    # Sort by modification time, newest first
    checkpoint_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    
    # Remove old checkpoints
    for old_checkpoint in checkpoint_files[keep_latest:]:
        try:
            old_checkpoint.unlink()
            if logger:
                logger.debug(f"Removed old checkpoint: {old_checkpoint}")
        except Exception as e:
            if logger:
                logger.warning(f"Failed to remove checkpoint {old_checkpoint}: {e}")


def execute_pipeline(
    org: str,
    mode: str,
    days: int,
    config_dir: str,
    output_dir: str,
    skip_extraction: bool,
    skip_analysis: bool,
    max_workers: int,
    force: bool,
    state_manager: StateManager,
    config_manager: ConfigManager,
    logger: logging.Logger,
) -> bool:
    """Execute the complete data processing pipeline with error recovery."""
    
    pipeline_start_time = time.time()
    recovery_mode = False
    
    try:
        # Clean up old checkpoints at start
        cleanup_old_checkpoints(output_dir, logger=logger)
        # Step 1: Data Extraction
        if not skip_extraction:
            print("\n📊 Step 1: Extracting data from GitHub...")
            if not run_extraction_scripts(org, mode, days, config_dir, output_dir, logger):
                return False
            print("✅ Data extraction completed")
        else:
            print("\n⏭️ Skipping data extraction (using existing files)")
        
        if skip_analysis:
            print("⏭️ Skipping analysis (extraction only mode)")
            return True
        
        # Step 2: Initialize analysis components
        print("\n🧠 Step 2: Initializing AI analysis engine...")
        analysis_engine = AnalysisEngine(max_workers=max_workers)
        unified_processor = UnifiedDataProcessor(
            analysis_engine=analysis_engine,
            state_manager=state_manager
        )
        
        # Step 3: Process PR data with error recovery
        pr_results = []
        pr_file = Path(output_dir) / "org_prs.csv"
        if pr_file.exists():
            print(f"\n🔍 Step 3: Processing PR data from {pr_file}...")
            
            # Check for existing checkpoint
            if not force:
                pr_results = load_latest_checkpoint(output_dir, "prs", logger)
                if pr_results:
                    print(f"🔄 Resuming from checkpoint with {len(pr_results)} PRs")
                    recovery_mode = True
            
            if not pr_results:
                try:
                    records_processed = unified_processor.process_unified_data(
                        pr_data_file=str(pr_file),
                        commit_data_file="org_commits.csv",
                        output_file="unified_pilot_data.csv",
                        incremental=(not force)
                    )
                    pr_results = f"Processed {records_processed} records"
                    # Save checkpoint after successful processing
                    save_progress_checkpoint(pr_results, "prs", output_dir, logger)
                except Exception as e:
                    logger.error(f"PR processing failed: {e}")
                    # Try to load from checkpoint if available
                    pr_results = load_latest_checkpoint(output_dir, "prs", logger)
                    if not pr_results:
                        print(f"❌ PR processing failed and no checkpoint available: {e}")
                        return False
                    print(f"🔄 Recovered {len(pr_results)} PRs from checkpoint")
            
            print(f"✅ Processed {len(pr_results)} PRs")
        else:
            print("⚠️ No PR data file found, skipping PR analysis")
        
        # Step 4: Process commit data with error recovery
        commit_results = []
        commit_file = Path(output_dir) / "org_commits.csv"
        if commit_file.exists():
            print(f"\n🔍 Step 4: Processing commit data from {commit_file}...")
            
            # Check for existing checkpoint
            if not force:
                commit_results = load_latest_checkpoint(output_dir, "commits", logger)
                if commit_results:
                    print(f"🔄 Resuming from checkpoint with {len(commit_results)} commits")
                    recovery_mode = True
            
            if not commit_results:
                try:
                    commit_results = unified_processor.process_commits(
                        str(commit_file), skip_processed=(not force)
                    )
                    # Save checkpoint after successful processing
                    save_progress_checkpoint(commit_results, "commits", output_dir, logger)
                except Exception as e:
                    logger.error(f"Commit processing failed: {e}")
                    # Try to load from checkpoint if available
                    commit_results = load_latest_checkpoint(output_dir, "commits", logger)
                    if not commit_results:
                        print(f"❌ Commit processing failed and no checkpoint available: {e}")
                        return False
                    print(f"🔄 Recovered {len(commit_results)} commits from checkpoint")
            
            print(f"✅ Processed {len(commit_results)} commits")
        else:
            print("⚠️ No commit data file found, skipping commit analysis")
        
        # Step 5: Generate unified output
        print("\n📋 Step 5: Generating unified analysis output...")
        all_results = pr_results + commit_results
        
        if all_results:
            # Apply AI developer overrides from configuration
            print("\n🤖 Step 5a: Applying AI attribution overrides...")
            all_results = apply_ai_developer_overrides(all_results, config_manager, logger)
            output_file = Path(output_dir) / "unified_pilot_data.csv"
            unified_processor.save_unified_data(all_results, str(output_file))
            print(f"✅ Saved unified data to {output_file}")
            
            # Step 6: Generate developer metrics
            print("\n👥 Step 6: Generating developer metrics...")
            metrics_aggregator = DeveloperMetricsAggregator()
            developer_metrics = metrics_aggregator.aggregate_from_unified_data(all_results)
            
            metrics_file = Path(output_dir) / "developer_metrics.csv"
            metrics_aggregator.save_metrics(developer_metrics, str(metrics_file))
            print(f"✅ Saved developer metrics to {metrics_file}")
            
            # Step 7: Update state
            print("\n💾 Step 7: Updating processing state...")
            pr_ids = [r["source_id"] for r in pr_results if r.get("source_id")]
            commit_shas = [r["source_id"] for r in commit_results if r.get("source_id")]
            
            state_manager.update_after_batch_processing(
                pr_ids, commit_shas, len(all_results)
            )
            print("✅ State updated successfully")
            
            # Display summary statistics
            print("\n📈 Analysis Summary:")
            print(f"   Total records analyzed: {len(all_results)}")
            print(f"   PRs processed: {len(pr_results)}")
            print(f"   Commits processed: {len(commit_results)}")
            
            # Show AI assistance statistics
            ai_assisted_count = sum(1 for r in all_results if r.get("ai_assisted"))
            ai_percentage = (ai_assisted_count / len(all_results)) * 100 if all_results else 0
            print(f"   AI-assisted work: {ai_assisted_count} ({ai_percentage:.1f}%)")
            
            # Show process compliance
            with_tickets = sum(1 for r in all_results if r.get("has_linear_ticket"))
            compliance_percentage = (with_tickets / len(all_results)) * 100 if all_results else 0
            print(f"   Process compliant: {with_tickets} ({compliance_percentage:.1f}%)")
            
            # Performance monitoring
            pipeline_duration = time.time() - pipeline_start_time
            pipeline_minutes = int(pipeline_duration // 60)
            pipeline_seconds = int(pipeline_duration % 60)
            
            if recovery_mode:
                print("🔄 Pipeline completed using error recovery")
            
            print(f"⏱️ Total pipeline time: {pipeline_minutes}m {pipeline_seconds}s")
            
            # Log final statistics for monitoring
            logger.info(f"Pipeline completed successfully for {org}")
            logger.info(f"Mode: {mode}, Duration: {pipeline_duration:.2f}s")
            logger.info(f"Results: {len(all_results)} total, {len(pr_results)} PRs, {len(commit_results)} commits")
            logger.info(f"AI assistance: {ai_percentage:.1f}%, Process compliance: {compliance_percentage:.1f}%")
            
        else:
            print("⚠️ No data to process")
            logger.warning("Pipeline completed but no data was processed")
        
        return True
        
    except KeyboardInterrupt:
        logger.warning("Pipeline execution interrupted by user")
        print("\n⚠️ Pipeline interrupted by user")
        return False
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
        print(f"❌ Pipeline failed: {str(e)}")
        
        # Suggest recovery options
        print("\n🔧 Recovery Options:")
        print("   1. Run with --force to reprocess all data")
        print("   2. Check logs for detailed error information")
        print("   3. Verify API keys and network connectivity")
        
        return False


def estimate_processing_time(mode: str, days: int, org: str) -> str:
    """Estimate processing time based on mode and organization size."""
    # Rough estimates based on typical repository sizes
    if mode == "pilot":
        return "5-15 minutes"
    elif mode == "incremental":
        return "2-10 minutes"
    else:  # full
        minutes = days * 2  # Rough estimate: 2 minutes per day
        if minutes < 60:
            return f"{minutes} minutes"
        else:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            return f"{hours}h {remaining_minutes}m"


def main() -> int:
    """Main execution function."""
    args = parse_arguments()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    logger = logging.getLogger(__name__)
    
    # Print header
    print("🌟 North Star Metrics - Engineering Impact Framework")
    print("=" * 60)
    print(f"Organization: {args.org}")
    print(f"Mode: {args.mode}")
    if args.mode != "incremental":
        print(f"Days: {args.days}")
    print(f"Output: {args.output_dir}")
    print(f"Estimated time: {estimate_processing_time(args.mode, args.days, args.org)}")
    print("=" * 60)
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No actual processing will occur")
        print("=" * 60)
    
    try:
        # Validate environment
        print("\n📋 Validating environment...")
        validate_environment()
        
        # Initialize managers
        print("\n⚙️ Initializing configuration...")
        config_manager = ConfigManager(args.config_dir)
        state_manager = StateManager(f"{args.config_dir}/analysis_state.json")
        
        # Show current state
        stats = state_manager.get_statistics()
        print(f"   Last run: {stats['last_run_date'] or 'Never'}")
        print(f"   Total processed: {stats['total_records_processed']} records")
        
        if args.dry_run:
            print("\n✅ Dry run complete - environment and configuration validated")
            return 0
        
        print(f"\n🚀 Starting {args.mode} mode execution...")
        start_time = time.time()
        
        # Execute the pipeline based on mode
        success = execute_pipeline(
            args.org,
            args.mode,
            args.days,
            args.config_dir,
            args.output_dir,
            args.skip_extraction,
            args.skip_analysis,
            args.max_workers,
            args.force,
            state_manager,
            config_manager,
            logger
        )
        
        if not success:
            print("❌ Pipeline execution failed")
            return 1
        
        end_time = time.time()
        duration = end_time - start_time
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        
        print("\n✅ Pipeline completed successfully!")
        print(f"⏱️ Total execution time: {minutes}m {seconds}s")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Execution interrupted by user")
        logger.warning("Pipeline execution interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Pipeline failed: {str(e)}")
        logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
