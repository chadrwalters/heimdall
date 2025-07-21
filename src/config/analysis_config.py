"""Analysis and AI configuration schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings

from .enums import AITool


class AIDevConfig(BaseModel):
    """Configuration for an AI developer."""

    username: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    ai_tool: AITool
    percentage: float = Field(..., ge=0.0, le=100.0)

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class AIDevsConfig(BaseModel):
    """Configuration for AI developers."""

    always_ai_developers: List[AIDevConfig] = Field(default_factory=list)

    @field_validator("always_ai_developers")
    @classmethod
    def validate_unique_developers(cls, v):
        """Ensure developers are unique by username and email."""
        usernames = set()
        emails = set()

        for dev in v:
            if dev.username.lower() in usernames:
                raise ValueError(f"Duplicate username: {dev.username}")
            if dev.email.lower() in emails:
                raise ValueError(f"Duplicate email: {dev.email}")

            usernames.add(dev.username.lower())
            emails.add(dev.email.lower())

        return v


class AnalysisState(BaseModel):
    """State tracking for analysis progress."""

    last_run_time: Optional[datetime] = None
    total_prs_processed: int = Field(default=0, ge=0)
    total_commits_processed: int = Field(default=0, ge=0)
    total_records_processed: int = Field(default=0, ge=0)
    last_pr_id: Optional[str] = None
    last_commit_sha: Optional[str] = None
    processing_errors: int = Field(default=0, ge=0)
    cache_hits: int = Field(default=0, ge=0)
    cache_misses: int = Field(default=0, ge=0)


class MetricsConfig(BaseSettings):
    """Metrics and analysis configuration."""

    model_config = {"env_prefix": "NS_METRICS_"}

    # Analysis weights
    complexity_weight: float = Field(default=0.3, ge=0.0, le=1.0, env="NS_COMPLEXITY_WEIGHT")
    risk_weight: float = Field(default=0.4, ge=0.0, le=1.0, env="NS_RISK_WEIGHT")
    clarity_weight: float = Field(default=0.3, ge=0.0, le=1.0, env="NS_CLARITY_WEIGHT")

    # Time windows
    pilot_days: int = Field(default=7, ge=1, le=30, env="NS_PILOT_DAYS")
    default_analysis_days: int = Field(default=30, ge=1, le=365, env="NS_DEFAULT_ANALYSIS_DAYS")
    max_analysis_days: int = Field(default=365, ge=30, le=1095, env="NS_MAX_ANALYSIS_DAYS")
    developer_metrics_window_weeks: int = Field(default=4, ge=1, le=52, env="NS_DEVELOPER_METRICS_WINDOW_WEEKS")

    # Thresholds
    high_impact_threshold: float = Field(default=7.0, ge=1.0, le=10.0, env="NS_HIGH_IMPACT_THRESHOLD")
    high_complexity_threshold: int = Field(default=7, ge=1, le=10, env="NS_HIGH_COMPLEXITY_THRESHOLD")
    high_risk_threshold: int = Field(default=7, ge=1, le=10, env="NS_HIGH_RISK_THRESHOLD")
    min_commits_for_analysis: int = Field(default=5, ge=1, le=100, env="NS_MIN_COMMITS_FOR_ANALYSIS")

    @field_validator("complexity_weight", "risk_weight", "clarity_weight")
    @classmethod
    def validate_weights_sum(cls, v, info):
        """Ensure weights are reasonable (will validate sum in model_validator)."""
        if v < 0.0 or v > 1.0:
            raise ValueError("Weight must be between 0.0 and 1.0")
        return v

    def model_post_init(self, __context) -> None:
        """Validate that weights sum to 1.0."""
        total_weight = self.complexity_weight + self.risk_weight + self.clarity_weight
        if abs(total_weight - 1.0) > 0.01:  # Allow small floating point differences
            raise ValueError(f"Analysis weights must sum to 1.0, got {total_weight}")
