"""Structured logging system with correlation IDs and context tracking."""

import json
import logging
import sys
import threading
import time
import uuid
from contextvars import ContextVar
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from ..config.constants import get_settings

# Context variables for correlation tracking
correlation_id_context: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
request_context: ContextVar[Dict[str, Any]] = ContextVar("request_context", default={})
user_context: ContextVar[Dict[str, Any]] = ContextVar("user_context", default={})


@dataclass
class LogContext:
    """Context information for structured logging."""

    correlation_id: Optional[str] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    operation: Optional[str] = None
    component: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None

    # Performance metrics
    start_time: Optional[float] = None
    duration_ms: Optional[float] = None

    # Business context
    organization: Optional[str] = None
    repository: Optional[str] = None
    pr_number: Optional[str] = None
    issue_id: Optional[str] = None

    # Additional context
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        result = {}
        for key, value in asdict(self).items():
            if value is not None:
                result[key] = value
        return result


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""

    def __init__(self, include_trace: bool = True, mask_sensitive: bool = True):
        super().__init__()
        self.include_trace = include_trace
        self.mask_sensitive = mask_sensitive

        # Load sensitive patterns from config
        try:
            settings = get_settings()
            self.sensitive_patterns = settings.logging.sensitive_patterns
        except Exception:
            self.sensitive_patterns = [
                r"sk-ant-[\w-]+",  # Anthropic keys
                r"ghp_[\w]+",  # GitHub tokens
                r"lin_api_[\w]+",  # Linear API keys
                r"Bearer\s+[\w.-]+",  # Bearer tokens
            ]

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # Base log structure
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": threading.current_thread().name,
            "process": record.process,
        }

        # Add correlation ID and context
        correlation_id = correlation_id_context.get()
        if correlation_id:
            log_entry["correlation_id"] = correlation_id

        request_ctx = request_context.get()
        if request_ctx:
            log_entry["request"] = request_ctx

        user_ctx = user_context.get()
        if user_ctx:
            log_entry["user"] = user_ctx

        # Add exception information
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info) if self.include_trace else None,
            }

        # Add custom fields from record
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
                "exc_info",
                "exc_text",
                "stack_info",
            ]:
                log_entry[key] = value

        # Mask sensitive information
        if self.mask_sensitive:
            log_entry = self._mask_sensitive_data(log_entry)

        return json.dumps(log_entry, default=str, separators=(",", ":"))

    def _mask_sensitive_data(self, data: Any) -> Any:
        """Recursively mask sensitive data in log entries."""
        if isinstance(data, dict):
            return {k: self._mask_sensitive_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._mask_sensitive_data(item) for item in data]
        elif isinstance(data, str):
            import re

            result = data
            for pattern in self.sensitive_patterns:
                result = re.sub(pattern, "***MASKED***", result)
            return result
        else:
            return data


class ContextualAdapter(logging.LoggerAdapter):
    """Logger adapter that adds contextual information to log records."""

    def __init__(self, logger: logging.Logger, context: Optional[LogContext] = None):
        super().__init__(logger, {})
        self.context = context or LogContext()

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """Process log message and add context."""
        # Add context to extra
        if "extra" not in kwargs:
            kwargs["extra"] = {}

        # Add context information
        context_dict = self.context.to_dict()
        kwargs["extra"].update(context_dict)

        # Add correlation ID if available
        correlation_id = correlation_id_context.get()
        if correlation_id:
            kwargs["extra"]["correlation_id"] = correlation_id

        return msg, kwargs

    def with_context(self, **context_updates) -> "ContextualAdapter":
        """Create a new adapter with updated context."""
        new_context = LogContext(**{**asdict(self.context), **context_updates})
        return ContextualAdapter(self.logger, new_context)


class CorrelationIdFilter(logging.Filter):
    """Filter to add correlation ID to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to log record if available."""
        correlation_id = correlation_id_context.get()
        if correlation_id:
            record.correlation_id = correlation_id
        return True


def setup_structured_logging(
    level: str = "INFO",
    enable_console: bool = True,
    enable_file: bool = True,
    log_file: Optional[str] = None,
    max_file_size: int = 100 * 1024 * 1024,  # 100MB
    backup_count: int = 5,
    include_trace: bool = True,
    mask_sensitive: bool = True,
) -> None:
    """Setup structured logging configuration."""

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create formatters
    json_formatter = StructuredFormatter(include_trace=include_trace, mask_sensitive=mask_sensitive)

    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(json_formatter)
        console_handler.addFilter(CorrelationIdFilter())
        root_logger.addHandler(console_handler)

    # File handler
    if enable_file:
        from logging.handlers import RotatingFileHandler

        if not log_file:
            log_file = f"logs/north_star_{datetime.now().strftime('%Y%m%d')}.log"

        # Create logs directory if it doesn't exist
        import os

        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_file_size, backupCount=backup_count
        )
        file_handler.setFormatter(json_formatter)
        file_handler.addFilter(CorrelationIdFilter())
        root_logger.addHandler(file_handler)

    # Set logging level for external libraries
    logging.getLogger("anthropic").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_structured_logger(name: str, context: Optional[LogContext] = None) -> ContextualAdapter:
    """Get a structured logger with contextual information."""
    base_logger = logging.getLogger(name)
    return ContextualAdapter(base_logger, context)


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """Set correlation ID for current context."""
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    correlation_id_context.set(correlation_id)
    return correlation_id


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID."""
    return correlation_id_context.get()


def set_request_context(**context) -> None:
    """Set request context for current context."""
    current_context = request_context.get() or {}
    current_context.update(context)
    request_context.set(current_context)


def set_user_context(**context) -> None:
    """Set user context for current context."""
    current_context = user_context.get() or {}
    current_context.update(context)
    user_context.set(current_context)


def clear_context() -> None:
    """Clear all context variables."""
    correlation_id_context.set(None)
    request_context.set({})
    user_context.set({})


class LoggerContextManager:
    """Context manager for scoped logging context."""

    def __init__(self, correlation_id: Optional[str] = None, **context):
        self.correlation_id = correlation_id
        self.context = context
        self.old_correlation_id = None
        self.old_request_context = None
        self.old_user_context = None

    def __enter__(self):
        """Enter context and set logging context."""
        # Save old context
        self.old_correlation_id = correlation_id_context.get()
        self.old_request_context = request_context.get()
        self.old_user_context = user_context.get()

        # Set new context
        if self.correlation_id:
            set_correlation_id(self.correlation_id)

        if self.context:
            set_request_context(**self.context)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and restore old context."""
        # Restore old context
        correlation_id_context.set(self.old_correlation_id)
        request_context.set(self.old_request_context or {})
        user_context.set(self.old_user_context or {})


def with_logging_context(correlation_id: Optional[str] = None, **context):
    """Decorator to add logging context to a function."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            with LoggerContextManager(correlation_id, **context):
                return func(*args, **kwargs)

        return wrapper

    return decorator


class PerformanceLogger:
    """Logger for performance metrics."""

    def __init__(self, logger: ContextualAdapter, operation: str):
        self.logger = logger
        self.operation = operation
        self.start_time = None
        self.context = {}

    def __enter__(self):
        """Start performance measurement."""
        self.start_time = time.time()
        self.logger.info(
            f"Starting {self.operation}", extra={"operation": self.operation, "event": "start"}
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End performance measurement and log results."""
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000

            log_data = {
                "operation": self.operation,
                "event": "complete",
                "duration_ms": round(duration_ms, 2),
                "success": exc_type is None,
            }

            if exc_type:
                log_data["error"] = str(exc_val)

            log_data.update(self.context)

            self.logger.info(f"Completed {self.operation}", extra=log_data)

    def add_context(self, **context):
        """Add additional context to performance log."""
        self.context.update(context)


def log_performance(logger: ContextualAdapter, operation: str):
    """Context manager for performance logging."""
    return PerformanceLogger(logger, operation)


# Convenience functions for common logging patterns
def log_api_call(
    logger: ContextualAdapter,
    method: str,
    url: str,
    status_code: int = None,
    duration_ms: float = None,
    **extra,
):
    """Log API call with structured format."""
    logger.info(
        f"API call: {method} {url}",
        extra={
            "event": "api_call",
            "method": method,
            "url": url,
            "status_code": status_code,
            "duration_ms": duration_ms,
            **extra,
        },
    )


def log_business_event(
    logger: ContextualAdapter, event_type: str, entity_type: str, entity_id: str, **extra
):
    """Log business event with structured format."""
    logger.info(
        f"Business event: {event_type}",
        extra={
            "event": "business_event",
            "event_type": event_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            **extra,
        },
    )


def log_error(logger: ContextualAdapter, error: Exception, context: str = "", **extra):
    """Log error with structured format."""
    logger.error(
        f"Error in {context}: {str(error)}",
        extra={
            "event": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            **extra,
        },
        exc_info=True,
    )


def log_security_event(
    logger: ContextualAdapter, event_type: str, severity: str, description: str, **extra
):
    """Log security event with structured format."""
    logger.warning(
        f"Security event: {event_type}",
        extra={
            "event": "security_event",
            "event_type": event_type,
            "severity": severity,
            "description": description,
            **extra,
        },
    )


# Initialize structured logging on import
try:
    settings = get_settings()
    setup_structured_logging(
        level=settings.logging.default_log_level.value,
        enable_console=True,
        enable_file=True,
        include_trace=settings.logging.enable_structured_logging,
        mask_sensitive=True,
    )
except Exception:
    # Fallback to basic logging if config fails
    setup_structured_logging()
