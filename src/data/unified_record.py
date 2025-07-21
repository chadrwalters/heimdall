"""Unified data model for analysis output."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class UnifiedRecord:
    """Unified data model for analysis output."""

    repository: str
    date: str  # ISO format
    author: str
    source_type: str  # 'PR' or 'Commit'
    source_url: str
    context_level: str  # 'High' or 'Low'
    work_type: str  # AI-classified work type
    complexity_score: float
    risk_score: float
    clarity_score: float
    analysis_summary: str
    lines_added: int
    lines_deleted: int
    files_changed: int
    impact_score: float  # Calculated metric
    ai_assisted: bool
    ai_tool_type: str | None
    linear_ticket_id: str | None
    has_linear_ticket: bool
    process_compliant: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for CSV output."""
        return asdict(self)
