"""Custom exception classes for North Star Metrics system."""

from .analysis_exceptions import (
    AnalysisError,
    ContextPreparationError,
    InvalidInputError,
    ProcessingTimeoutError,
    PromptEngineError,
    ResourceExhaustionError,
    ResponseParsingError,
)
from .api_exceptions import (
    APIError,
    APIKeyError,
    APIRateLimitError,
    APITimeoutError,
)
from .data_exceptions import (
    ConfigurationError,
    DataError,
    DataValidationError,
    FileProcessingError,
    InvalidDataFormatError,
    JSONProcessingError,
)
from .security_exceptions import (
    AuthenticationError,
    EncryptionError,
    SecurityError,
    ValidationError,
)

__all__ = [
    # Analysis exceptions
    "AnalysisError",
    "InvalidInputError",
    "ProcessingTimeoutError",
    "ResourceExhaustionError",
    "PromptEngineError",
    "ResponseParsingError",
    "ContextPreparationError",
    # API exceptions
    "APIError",
    "APIKeyError",
    "APIRateLimitError",
    "APITimeoutError",
    # Data exceptions
    "ConfigurationError",
    "DataError",
    "DataValidationError",
    "FileProcessingError",
    "InvalidDataFormatError",
    "JSONProcessingError",
    # Security exceptions
    "SecurityError",
    "AuthenticationError",
    "ValidationError",
    "EncryptionError",
]
