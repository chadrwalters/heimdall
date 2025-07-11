"""API-related exception classes."""


class APIError(Exception):
    """Base exception for API-related errors."""

    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class APIKeyError(APIError):
    """Raised when API key is invalid or missing."""

    def __init__(self, message: str, key_type: str = None):
        super().__init__(message)
        self.key_type = key_type


class APIRateLimitError(APIError):
    """Raised when API rate limit is exceeded."""

    def __init__(self, message: str, retry_after: int = None, limit_type: str = None):
        super().__init__(message)
        self.retry_after = retry_after
        self.limit_type = limit_type


class APITimeoutError(APIError):
    """Raised when API request times out."""

    def __init__(self, message: str, timeout_seconds: int = None, endpoint: str = None):
        super().__init__(message)
        self.timeout_seconds = timeout_seconds
        self.endpoint = endpoint


class APIAuthenticationError(APIError):
    """Raised when API authentication fails."""

    def __init__(self, message: str, auth_type: str = None):
        super().__init__(message)
        self.auth_type = auth_type


class APIQuotaExceededError(APIError):
    """Raised when API quota is exceeded."""

    def __init__(self, message: str, quota_type: str = None, usage_info: dict = None):
        super().__init__(message)
        self.quota_type = quota_type
        self.usage_info = usage_info or {}


class GraphQLError(APIError):
    """Raised when GraphQL query fails."""

    def __init__(self, message: str, query: str = None, variables: dict = None):
        super().__init__(message)
        self.query = query
        self.variables = variables or {}
