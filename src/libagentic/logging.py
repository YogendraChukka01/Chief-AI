"""Structured logging configuration for chief-ai."""

import logging
import sys
from typing import Any


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
    """Context manager for structured logging with extra context."""

    def __init__(self, logger: logging.Logger, **kwargs: Any) -> None:
        self.logger = logger
        self.extra = kwargs
        self.old_factory = None

    def __enter__(self) -> "LogContext":
        old_factory = logging.getLogRecordFactory()

        def record_factory(*args: Any, **kw: Any) -> logging.LogRecord:
            record = old_factory(*args, **kw)
            for key, value in self.extra.items():
                setattr(record, key, value)
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        logging.setLogRecordFactory(self.old_factory or logging.LogRecord)
