"""Data processing exception classes."""


class DataError(Exception):
    """Base exception for data-related errors."""

    def __init__(self, message: str, data_source: str = None, details: dict = None):
        super().__init__(message)
        self.data_source = data_source
        self.details = details or {}


class DataValidationError(DataError):
    """Raised when data validation fails."""

    def __init__(
        self, message: str, field_name: str = None, field_value=None, validation_rule: str = None
    ):
        super().__init__(message)
        self.field_name = field_name
        self.field_value = field_value
        self.validation_rule = validation_rule


class FileProcessingError(DataError):
    """Raised when file processing fails."""

    def __init__(
        self, message: str, file_path: str = None, file_type: str = None, operation: str = None
    ):
        super().__init__(message)
        self.file_path = file_path
        self.file_type = file_type
        self.operation = operation


class InvalidDataFormatError(DataError):
    """Raised when data format is invalid."""

    def __init__(self, message: str, expected_format: str = None, actual_format: str = None):
        super().__init__(message)
        self.expected_format = expected_format
        self.actual_format = actual_format


class CSVProcessingError(FileProcessingError):
    """Raised when CSV processing fails."""

    def __init__(
        self, message: str, file_path: str = None, row_number: int = None, column_name: str = None
    ):
        super().__init__(message, file_path=file_path, file_type="CSV")
        self.row_number = row_number
        self.column_name = column_name


class JSONProcessingError(FileProcessingError):
    """Raised when JSON processing fails."""

    def __init__(self, message: str, file_path: str = None, json_path: str = None):
        super().__init__(message, file_path=file_path, file_type="JSON")
        self.json_path = json_path


class DatabaseError(DataError):
    """Raised when database operations fail."""

    def __init__(self, message: str, operation: str = None, table_name: str = None):
        super().__init__(message)
        self.operation = operation
        self.table_name = table_name


class ConfigurationError(DataError):
    """Raised when configuration is invalid."""

    def __init__(self, message: str, config_file: str = None, config_key: str = None):
        super().__init__(message)
        self.config_file = config_file
        self.config_key = config_key
