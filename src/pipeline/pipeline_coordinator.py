"""Pipeline coordination for main execution workflow."""

from pathlib import Path

from ..analysis.analysis_engine import AnalysisEngine
from ..config.config_manager import ConfigManager
from ..config.state_manager import StateManager
from ..data.developer_metrics import DeveloperMetricsAggregator
from ..data.unified_processor import UnifiedDataProcessor
from ..structured_logging import get_structured_logger

logger = get_structured_logger(__name__)


class PipelineCoordinator:
    """Coordinates the complete data processing pipeline."""

    def __init__(self, config_manager: ConfigManager, state_manager: StateManager):
        self.config_manager = config_manager
        self.state_manager = state_manager

    def run_extraction_phase(
        self, org: str, mode: str, days: int, config_dir: str, output_dir: str
    ) -> bool:
        """Run data extraction phase."""
        import subprocess

        script_path = Path("scripts/extraction/run_extraction.sh")
        if not script_path.exists():
            logger.error("Extraction script not found")
            return False

        cmd = ["bash", str(script_path), "--org", org]
        if mode == "incremental":
            cmd.append("--incremental")
        else:
            cmd.extend(["--days", str(days)])
        cmd.extend(["--config-dir", config_dir, "--output-dir", output_dir])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.debug(f"Extraction output: {result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Extraction failed: {e.stderr}")
            return False

    def run_analysis_phase(
        self, max_workers: int, output_dir: str, force: bool
    ) -> tuple[list, list]:
        """Run analysis phase and return PR and commit results."""
        analysis_engine = AnalysisEngine(max_workers=max_workers)
        unified_processor = UnifiedDataProcessor(
            analysis_engine=analysis_engine, state_manager=self.state_manager
        )

        pr_results = self._process_prs(unified_processor, output_dir, force)
        commit_results = self._process_commits(unified_processor, output_dir, force)

        return pr_results, commit_results

    def _process_prs(self, processor: UnifiedDataProcessor, output_dir: str, force: bool) -> list:
        """Process PR data."""
        pr_file = Path(output_dir) / "org_prs.csv"
        if not pr_file.exists():
            logger.warning("No PR data file found")
            return []

        try:
            records_processed = processor.process_unified_data(
                pr_data_file=str(pr_file),
                commit_data_file="org_commits.csv",
                output_file="unified_pilot_data.csv",
                incremental=(not force),
            )
            return [f"Processed {records_processed} records"]
        except Exception as e:
            logger.error(f"PR processing failed: {e}")
            return []

    def _process_commits(
        self, processor: UnifiedDataProcessor, output_dir: str, force: bool
    ) -> list:
        """Process commit data."""
        commit_file = Path(output_dir) / "org_commits.csv"
        if not commit_file.exists():
            logger.warning("No commit data file found")
            return []

        try:
            return processor.process_commits(str(commit_file), skip_processed=(not force))
        except Exception as e:
            logger.error(f"Commit processing failed: {e}")
            return []

    def run_reporting_phase(self, all_results: list, output_dir: str) -> None:
        """Run reporting and metrics generation phase."""
        if not all_results:
            logger.warning("No data to process")
            return

        # Apply AI developer overrides
        all_results = self._apply_ai_overrides(all_results)

        # Save unified data
        output_file = Path(output_dir) / "unified_pilot_data.csv"
        processor = UnifiedDataProcessor()
        processor.save_unified_data(all_results, str(output_file))

        # Generate developer metrics
        metrics_aggregator = DeveloperMetricsAggregator()
        developer_metrics = metrics_aggregator.aggregate_from_unified_data(all_results)
        metrics_file = Path(output_dir) / "developer_metrics.csv"
        metrics_aggregator.save_metrics(developer_metrics, str(metrics_file))

    def _apply_ai_overrides(self, results: list) -> list:
        """Apply AI developer override configuration."""
        try:
            ai_config = self.config_manager.load_ai_developers()
            always_ai_developers = ai_config.get("always_ai_developers", [])

            if not always_ai_developers:
                return results

            override_count = 0
            for result in results:
                author = result.get("author", "").lower()
                for ai_dev in always_ai_developers:
                    dev_username = ai_dev.get("username", "").lower()
                    if author == dev_username:
                        if not result.get("ai_assisted", False):
                            result["ai_assisted"] = True
                            result["ai_tool_type"] = ai_dev.get("ai_tool", "Override Configuration")
                            override_count += 1
                        break

            if override_count > 0:
                logger.info(f"Applied AI attribution overrides to {override_count} records")

            return results
        except Exception as e:
            logger.warning(f"Failed to apply AI developer overrides: {e}")
            return results
