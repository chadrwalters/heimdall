"""Shared enums for configuration schemas."""

from enum import Enum


class LogLevel(str, Enum):
    """Valid log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class APIKeyType(str, Enum):
    """Valid API key types."""

    ANTHROPIC = "anthropic"
    GITHUB = "github"
    LINEAR = "linear"
    GENERIC = "generic"


class AITool(str, Enum):
    """Valid AI tools."""

    CLAUDE = "claude"
    COPILOT = "copilot"
    CURSOR = "cursor"
    CODEIUM = "codeium"
    OTHER = "other"


class WorkType(str, Enum):
    """Valid work types for analysis."""

    NEW_FEATURE = "New Feature"
    BUG_FIX = "Bug Fix"
    REFACTORING = "Refactoring"
    DOCUMENTATION = "Documentation"
    PERFORMANCE = "Performance"
    SECURITY = "Security"
    INFRASTRUCTURE = "Infrastructure"
    TESTING = "Testing"


class BlastRadius(str, Enum):
    """Valid blast radius levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
