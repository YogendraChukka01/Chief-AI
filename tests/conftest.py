"""Pytest configuration and fixtures for chief-ai tests."""

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set mock environment variables for testing."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")


@pytest.fixture
def mock_tavily_client() -> MagicMock:
    """Create a mock Tavily client."""
    client = MagicMock()
    client.search.return_value = {
        "results": [
            {
                "title": "Test Result",
                "url": "https://example.com",
                "content": "Test content",
            }
        ]
    }
    return client


@pytest.fixture
def sample_settings_dir(tmp_path: Path) -> Path:
    """Create a temporary settings directory."""
    settings_dir = tmp_path / ".chen"
    settings_dir.mkdir()
    return settings_dir


@pytest.fixture
def sample_settings_file(sample_settings_dir: Path) -> Path:
    """Create a sample settings file."""
    settings_file = sample_settings_dir / "settings.json"
    settings_file.write_text(
        '{"context_window": 200000, "language": "English"}'
    )
    return settings_file
