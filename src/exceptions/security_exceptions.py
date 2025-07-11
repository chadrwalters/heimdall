"""Security-related exception classes."""


class SecurityError(Exception):
    """Base exception for security-related errors."""

    def __init__(self, message: str, security_context: str = None, details: dict = None):
        super().__init__(message)
        self.security_context = security_context
        self.details = details or {}


class AuthenticationError(SecurityError):
    """Raised when authentication fails."""

    def __init__(self, message: str, auth_method: str = None, username: str = None):
        super().__init__(message, security_context="authentication")
        self.auth_method = auth_method
        self.username = username


class ValidationError(SecurityError):
    """Raised when input validation fails for security reasons."""

    def __init__(self, message: str, input_field: str = None, validation_type: str = None):
        super().__init__(message, security_context="validation")
        self.input_field = input_field
        self.validation_type = validation_type


class EncryptionError(SecurityError):
    """Raised when encryption/decryption operations fail."""

    def __init__(self, message: str, operation: str = None, key_type: str = None):
        super().__init__(message, security_context="encryption")
        self.operation = operation
        self.key_type = key_type


class InputSanitizationError(SecurityError):
    """Raised when input sanitization fails."""

    def __init__(self, message: str, input_type: str = None, sanitization_rule: str = None):
        super().__init__(message, security_context="sanitization")
        self.input_type = input_type
        self.sanitization_rule = sanitization_rule


class InjectionDetectedError(SecurityError):
    """Raised when potential injection attack is detected."""

    def __init__(self, message: str, injection_type: str = None, detected_pattern: str = None):
        super().__init__(message, security_context="injection_detection")
        self.injection_type = injection_type
        self.detected_pattern = detected_pattern


class KeyManagementError(SecurityError):
    """Raised when key management operations fail."""

    def __init__(self, message: str, key_operation: str = None, key_name: str = None):
        super().__init__(message, security_context="key_management")
        self.key_operation = key_operation
        self.key_name = key_name


class AccessDeniedError(SecurityError):
    """Raised when access is denied."""

    def __init__(self, message: str, resource: str = None, required_permission: str = None):
        super().__init__(message, security_context="access_control")
        self.resource = resource
        self.required_permission = required_permission
