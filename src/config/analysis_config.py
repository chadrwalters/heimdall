"""Analysis configuration schemas."""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

from .enums import AITool


class MetricsConfig(BaseModel):
    """Configuration for metrics calculation and analysis."""

    # Impact score weights
    complexity_weight: float = Field(default=0.4, ge=0, le=1)
    risk_weight: float = Field(default=0.5, ge=0, le=1)
    clarity_weight: float = Field(default=0.1, ge=0, le=1)

    # Analysis time periods
    pilot_days: int = Field(default=7, gt=0)
    default_analysis_days: int = Field(default=30, gt=0)
    max_analysis_days: int = Field(default=365, gt=0)

    # Thresholds
    high_impact_threshold: float = Field(default=7.0, ge=1, le=10)
    high_complexity_threshold: int = Field(default=7, ge=1, le=10)
    high_risk_threshold: int = Field(default=7, ge=1, le=10)

    # Developer metrics
    developer_metrics_window_weeks: int = Field(default=4, gt=0)
    min_commits_for_analysis: int = Field(default=5, gt=0)


class AIDevConfig(BaseModel):
    """Configuration for an individual AI developer."""

    username: str
    email: str | None = None
    ai_tool: AITool | None = None
    percentage: int = Field(default=100, ge=0, le=100)


class AIDevsConfig(BaseModel):
    """Configuration for AI developers."""

    always_ai_developers: list[AIDevConfig] = Field(default_factory=list)


class AnalysisState(BaseModel):
    """State tracking for incremental analysis."""

    last_run_date: datetime | None = None
    processed_pr_ids: list[str] = Field(default_factory=list)
    processed_commit_shas: list[str] = Field(default_factory=list)
    total_records_processed: int = 0
