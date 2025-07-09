"""Configuration management for the North Star project."""

import json
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from ..exceptions import (
    ConfigurationError,
    DataValidationError,
    JSONProcessingError,
)
from pathlib import Path
from .schemas import (
    AIDevsConfig,
    AnalysisState,
    validate_ai_developers_config,
    validate_analysis_state,
)


class ConfigManager:
    """Manages configuration files for AI developers and analysis state."""

    def __init__(self, config_dir: str = "config"):
        """Initialize the ConfigManager with a configuration directory."""
        # Validate config directory path
        try:
            self.config_dir = Path(config_dir)
        except Exception as e:
            raise ConfigurationError(f"Invalid config directory: {e}", config_key="config_dir")

        self.ai_developers_file = self.config_dir / "ai_developers.json"
        self.state_file = self.config_dir / "analysis_state.json"

        # Create config directory if it doesn't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load_ai_developers(self) -> dict[str, list[dict[str, Any]]]:
        """Load AI developers configuration from file."""
        if not self.ai_developers_file.exists():
            return {"always_ai_developers": []}

        try:
            with open(self.ai_developers_file) as f:
                data = json.load(f)
                # Validate with Pydantic schema
                validated_config = validate_ai_developers_config(data)
                # Convert back to dict for backward compatibility
                return validated_config.dict()
        except json.JSONDecodeError as e:
            raise JSONProcessingError(
                f"Invalid JSON in {self.ai_developers_file}: {e}",
                file_path=str(self.ai_developers_file),
            )
        except PydanticValidationError as e:
            raise DataValidationError(
                f"Invalid AI developers config: {e}",
                field_name="ai_developers_config",
                validation_rule="schema_validation",
            )
        except (OSError, IOError) as e:
            raise ConfigurationError(
                f"Cannot read AI developers config: {e}", config_file=str(self.ai_developers_file)
            )
        except Exception as e:
            raise ConfigurationError(
                f"Error loading AI developers config: {e}", config_file=str(self.ai_developers_file)
            )

    def save_ai_developers(self, config: dict[str, list[dict[str, Any]]]) -> None:
        """Save AI developers configuration to file."""
        # Validate with Pydantic schema
        try:
            validated_config = validate_ai_developers_config(config)
        except PydanticValidationError as e:
            raise DataValidationError(
                f"Invalid AI developers config: {e}",
                field_name="ai_developers_config",
                validation_rule="schema_validation",
            )

        with open(self.ai_developers_file, "w") as f:
            json.dump(validated_config.dict(), f, indent=2)

    def load_analysis_state(self) -> dict[str, Any]:
        """Load analysis state from file."""
        if not self.state_file.exists():
            # Return default state
            default_state = AnalysisState()
            return default_state.dict()

        try:
            with open(self.state_file) as f:
                data = json.load(f)
                # Validate with Pydantic schema
                validated_state = validate_analysis_state(data)
                # Convert back to dict for backward compatibility
                return validated_state.dict()
        except json.JSONDecodeError as e:
            raise JSONProcessingError(
                f"Invalid JSON in {self.state_file}: {e}", file_path=str(self.state_file)
            )
        except PydanticValidationError as e:
            raise DataValidationError(
                f"Invalid analysis state: {e}",
                field_name="analysis_state",
                validation_rule="schema_validation",
            )
        except (OSError, IOError) as e:
            raise ConfigurationError(
                f"Cannot read analysis state: {e}", config_file=str(self.state_file)
            )
        except Exception as e:
            raise ConfigurationError(
                f"Error loading analysis state: {e}", config_file=str(self.state_file)
            )

    def save_analysis_state(self, state: dict[str, Any]) -> None:
        """Save analysis state to file."""
        # Validate with Pydantic schema
        try:
            validated_state = validate_analysis_state(state)
        except PydanticValidationError as e:
            raise DataValidationError(
                f"Invalid analysis state: {e}",
                field_name="analysis_state",
                validation_rule="schema_validation",
            )

        with open(self.state_file, "w") as f:
            json.dump(validated_state.dict(), f, indent=2)


    def update_state_after_run(
        self, new_pr_ids: list[str], new_commit_shas: list[str], records_processed: int
    ) -> None:
        """Update the analysis state after a run."""
        state = self.load_analysis_state()

        # Update last run date
        state["last_run_date"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")

        # Add new IDs to processed lists (avoiding duplicates)
        state["processed_pr_ids"] = list(set(state["processed_pr_ids"] + new_pr_ids))
        state["processed_commit_shas"] = list(set(state["processed_commit_shas"] + new_commit_shas))

        # Update total records
        state["total_records_processed"] += records_processed

        self.save_analysis_state(state)

    def is_pr_processed(self, pr_id: str) -> bool:
        """Check if a PR has already been processed."""
        state = self.load_analysis_state()
        return pr_id in state["processed_pr_ids"]

    def is_commit_processed(self, commit_sha: str) -> bool:
        """Check if a commit has already been processed."""
        state = self.load_analysis_state()
        return commit_sha in state["processed_commit_shas"]

    def get_ai_developer_info(
        self, username: str | None = None, email: str | None = None
    ) -> dict[str, Any] | None:
        """Get AI developer info by username or email."""
        config = self.load_ai_developers()

        for dev in config["always_ai_developers"]:
            if (username and dev["username"].lower() == username.lower()) or (
                email and dev["email"].lower() == email.lower()
            ):
                return dev

        return None
