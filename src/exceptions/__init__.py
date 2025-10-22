"""Custom exception classes for North Star Metrics system."""

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
