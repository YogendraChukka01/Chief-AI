"""Tests for logging configuration."""

import logging

from libagentic.logging import get_logger, setup_logger


class TestSetupLogger:
    """Tests for logger setup."""

    def test_setup_logger_returns_logger(self) -> None:
        """Should return a configured logger."""
        logger = setup_logger("test-logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test-logger"

    def test_setup_logger_with_level(self) -> None:
        """Should set the correct log level."""
        logger = setup_logger("test-debug", level="DEBUG")
        assert logger.level == logging.DEBUG

    def test_setup_logger_prevents_duplicate_handlers(self) -> None:
        """Should not add handlers if already configured."""
        logger1 = setup_logger("test-dedup")
        handler_count = len(logger1.handlers)
        logger2 = setup_logger("test-dedup")
        assert len(logger2.handlers) == handler_count


class TestGetLogger:
    """Tests for logger retrieval."""

    def test_get_logger_returns_root(self) -> None:
        """Should return root logger when no name given."""
        logger = get_logger()
        assert logger.name == "chief-ai"

    def test_get_logger_with_name(self) -> None:
        """Should return child logger with correct name."""
        logger = get_logger("test-module")
        assert logger.name == "chief-ai.test-module"
