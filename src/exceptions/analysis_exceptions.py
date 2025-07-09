"""Analysis-specific exception classes."""


class AnalysisError(Exception):
    """Base exception for analysis-related errors."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details or {}


class InvalidInputError(AnalysisError):
    """Raised when analysis input is invalid."""

    def __init__(self, message: str, input_type: str = None, input_value: str = None):
        super().__init__(message)
        self.input_type = input_type
        self.input_value = input_value


class ProcessingTimeoutError(AnalysisError):
    """Raised when analysis processing times out."""

    def __init__(self, message: str, timeout_seconds: int = None, operation: str = None):
        super().__init__(message)
        self.timeout_seconds = timeout_seconds
        self.operation = operation


class ResourceExhaustionError(AnalysisError):
    """Raised when system resources are exhausted during analysis."""

    def __init__(self, message: str, resource_type: str = None, usage_info: dict = None):
        super().__init__(message)
        self.resource_type = resource_type
        self.usage_info = usage_info or {}


class PromptEngineError(AnalysisError):
    """Raised when prompt engineering fails."""

    def __init__(self, message: str, prompt_type: str = None):
        super().__init__(message)
        self.prompt_type = prompt_type


class ResponseParsingError(AnalysisError):
    """Raised when AI response parsing fails."""

    def __init__(self, message: str, raw_response: str = None):
        super().__init__(message)
        self.raw_response = raw_response


class ContextPreparationError(AnalysisError):
    """Raised when context preparation fails."""

    def __init__(self, message: str, context_type: str = None):
        super().__init__(message)
        self.context_type = context_type
