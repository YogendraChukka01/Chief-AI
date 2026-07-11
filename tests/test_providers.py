"""Tests for provider configurations."""

import os
from unittest.mock import patch

import pytest

from libagentic.providers import (
    get_anthropic_model,
    get_default_model,
    get_openai_model,
    get_openrouter_model,
)


class TestProviderCreation:
    """Tests for model provider creation."""

    def test_create_anthropic_model(self) -> None:
        """Should create Anthropic model successfully."""
        model = get_anthropic_model()
        assert model is not None

    def test_create_openai_model(self) -> None:
        """Should create OpenAI model successfully."""
        model = get_openai_model()
        assert model is not None

    def test_create_openrouter_model(self) -> None:
        """Should create OpenRouter model successfully."""
        model = get_openrouter_model()
        assert model is not None

    def test_create_anthropic_model_custom_name(self) -> None:
        """Should create Anthropic model with custom name."""
        model = get_anthropic_model("claude-3-5-haiku-latest")
        assert model is not None

    def test_openrouter_requires_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should raise ValueError when OPENROUTER_API_KEY not set."""
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
            get_openrouter_model()


class TestDefaultModel:
    """Tests for default model selection."""

    def test_default_model_requires_api_keys(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should raise ValueError when no API keys set."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

        # Mock load_dotenv to prevent reading .env file
        with patch("libagentic.providers.load_dotenv"):
            with pytest.raises(ValueError, match="No API keys found"):
                get_default_model()

    def test_default_model_with_anthropic_only(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should create fallback with Anthropic only."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

        with patch("libagentic.providers.load_dotenv"):
            model = get_default_model(openai_model_name=None, openrouter_model_name=None)
            assert model is not None

    def test_default_model_with_multiple_providers(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create fallback with multiple providers."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

        with patch("libagentic.providers.load_dotenv"):
            model = get_default_model()
            assert model is not None
