"""Configuration management for the North Star project."""

import json
from datetime import UTC, datetime
from typing import Any

from ..exceptions import (
    ConfigurationError,
    DataValidationError,
    JSONProcessingError,
)
from ..validation.input_validator import InputValidator, ValidationError


class ConfigManager:
    """Manages configuration files for AI developers and analysis state."""

    def __init__(self, config_dir: str = "config"):
        """Initialize the ConfigManager with a configuration directory."""
        # Validate config directory path
        try:
            validated_path = InputValidator.validate_file_path(config_dir)
            self.config_dir = validated_path
        except ValidationError as e:
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
                self._validate_ai_developers_config(data)
                return data
        except json.JSONDecodeError as e:
            raise JSONProcessingError(
                f"Invalid JSON in {self.ai_developers_file}: {e}",
                file_path=str(self.ai_developers_file),
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
        self._validate_ai_developers_config(config)

        with open(self.ai_developers_file, "w") as f:
            json.dump(config, f, indent=2)

    def _validate_ai_developers_config(self, config: dict[str, Any]) -> None:
        """Validate AI developers configuration structure."""
        if not isinstance(config, dict):
            raise DataValidationError(
                "Configuration must be a dictionary",
                field_name="config",
                validation_rule="type_check",
            )

        if "always_ai_developers" not in config:
            raise DataValidationError(
                "Configuration must contain 'always_ai_developers' key",
                field_name="always_ai_developers",
                validation_rule="required_field",
            )

        if not isinstance(config["always_ai_developers"], list):
            raise DataValidationError(
                "'always_ai_developers' must be a list",
                field_name="always_ai_developers",
                validation_rule="type_check",
            )

        for idx, dev in enumerate(config["always_ai_developers"]):
            if not isinstance(dev, dict):
                raise DataValidationError(
                    f"Developer at index {idx} must be a dictionary",
                    field_name=f"developers[{idx}]",
                    validation_rule="type_check",
                )

            required_fields = ["username", "email", "ai_tool", "percentage"]
            for field in required_fields:
                if field not in dev:
                    raise DataValidationError(
                        f"Developer at index {idx} missing required field: {field}",
                        field_name=f"developers[{idx}].{field}",
                        validation_rule="required_field",
                    )

            if not isinstance(dev["percentage"], (int, float)) or not 0 <= dev["percentage"] <= 100:
                raise DataValidationError(
                    f"Developer at index {idx} has invalid percentage: {dev['percentage']}",
                    field_name=f"developers[{idx}].percentage",
                    field_value=dev["percentage"],
                    validation_rule="range_check",
                )

    def load_analysis_state(self) -> dict[str, Any]:
        """Load analysis state from file."""
        if not self.state_file.exists():
            # Return default state
            return {
                "last_run_date": None,
                "processed_pr_ids": [],
                "processed_commit_shas": [],
                "total_records_processed": 0,
            }

        try:
            with open(self.state_file) as f:
                data = json.load(f)
                self._validate_analysis_state(data)
                return data
        except json.JSONDecodeError as e:
            raise JSONProcessingError(
                f"Invalid JSON in {self.state_file}: {e}", file_path=str(self.state_file)
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
        self._validate_analysis_state(state)

        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)

    def _validate_analysis_state(self, state: dict[str, Any]) -> None:
        """Validate analysis state structure."""
        if not isinstance(state, dict):
            raise DataValidationError(
                "State must be a dictionary", field_name="state", validation_rule="type_check"
            )

        required_fields = [
            "last_run_date",
            "processed_pr_ids",
            "processed_commit_shas",
            "total_records_processed",
        ]
        for field in required_fields:
            if field not in state:
                raise DataValidationError(
                    f"State missing required field: {field}",
                    field_name=field,
                    validation_rule="required_field",
                )

        if state["last_run_date"] is not None and not isinstance(state["last_run_date"], str):
            raise DataValidationError(
                "last_run_date must be a string or null",
                field_name="last_run_date",
                validation_rule="type_check",
            )

        if not isinstance(state["processed_pr_ids"], list):
            raise DataValidationError(
                "processed_pr_ids must be a list",
                field_name="processed_pr_ids",
                validation_rule="type_check",
            )

        if not isinstance(state["processed_commit_shas"], list):
            raise DataValidationError(
                "processed_commit_shas must be a list",
                field_name="processed_commit_shas",
                validation_rule="type_check",
            )

        if (
            not isinstance(state["total_records_processed"], int)
            or state["total_records_processed"] < 0
        ):
            raise DataValidationError(
                "total_records_processed must be a non-negative integer",
                field_name="total_records_processed",
                field_value=state["total_records_processed"],
                validation_rule="range_check",
            )

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
