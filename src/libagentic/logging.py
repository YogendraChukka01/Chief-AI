"""Structured logging configuration for chief-ai."""

import logging
import sys
from contextvars import ContextVar
from typing import Any

# Context variable for extra log fields — safe for async code.
_log_context: ContextVar[dict[str, Any]] = ContextVar("_log_context", default={})


class LogContextFilter(logging.Filter):
    """Add contextvar fields to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        for key, value in _log_context.get().items():
            setattr(record, key, value)
        return True


def setup_logger(
    name: str = "chief-ai",
    level: str = "INFO",
    log_file: str | None = None,
) -> logging.Logger:
    """Configure and return a logger with proper formatting.

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Attach LogContextFilter so contextvar fields appear on every record.
    # Add to the root logger so all children inherit it.
    root = logging.getLogger()
    if not any(isinstance(f, LogContextFilter) for f in root.filters):
        root.addFilter(LogContextFilter())

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Get an existing logger or create a child logger.

    Args:
        name: Optional child logger name

    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"chief-ai.{name}")
    return logging.getLogger("chief-ai")


class LogContext:
    """Context manager for structured logging with extra context.

    Uses ``contextvars`` so that async code with overlapping contexts
    does not leak fields between coroutines.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize with extra context fields.

        Args:
            kwargs: Key-value pairs to add to log records
        """
        self.extra = kwargs
        self._token: Any = None

    def __enter__(self) -> "LogContext":
        """Merge extra fields into the current contextvar."""
        old = _log_context.get()
        merged = {**old, **self.extra}
        self._token = _log_context.set(merged)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Restore the previous contextvar value."""
        if self._token is not None:
            _log_context.reset(self._token)
