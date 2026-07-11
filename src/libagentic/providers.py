"""Provider configurations for different AI model providers."""

import os

from dotenv import load_dotenv
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from libagentic.logging import get_logger

logger = get_logger("providers")


def get_openrouter_model(model_name: str = "deepseek/deepseek-chat-v3.1:free") -> OpenAIChatModel:
    """Create an OpenAI-compatible model configured for OpenRouter.

    Args:
        model_name: The model identifier from OpenRouter's model list

    Returns:
        OpenAIChatModel configured for OpenRouter
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    provider = OpenAIProvider(base_url="https://openrouter.ai/api/v1", api_key=api_key)
    return OpenAIChatModel(model_name, provider=provider)


def get_openai_model(model_name: str = "gpt-5-2025-08-07") -> OpenAIChatModel:
    """Create an OpenAI model directly using OpenAI's API.

    Args:
        model_name: The OpenAI model identifier

    Returns:
        OpenAIChatModel configured for OpenAI
    """
    return OpenAIChatModel(model_name)


def get_anthropic_model(model_name: str = "claude-sonnet-4-20250514") -> AnthropicModel:
    """Create an Anthropic model using native Anthropic provider.

    Args:
        model_name: The Anthropic model identifier

    Returns:
        AnthropicModel configured for Anthropic
    """
    return AnthropicModel(model_name=model_name)


def get_default_model(
    anthropic_model_name: str | None = "claude-sonnet-4-20250514",
    openai_model_name: str | None = "gpt-5-2025-08-07",
    openrouter_model_name: str | None = "deepseek/deepseek-chat-v3.1:free",
) -> FallbackModel:
    """Get the default model configuration with automatic provider selection.

    Args:
        anthropic_model_name: The Anthropic model identifier
        openai_model_name: The OpenAI model identifier
        openrouter_model_name: The OpenRouter model identifier

    Returns:
        FallbackModel configured for the specified providers

    Raises:
        ValueError: If no API keys are configured
    """
    load_dotenv()

    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")

    available_providers = []
    provider_names = []

    if anthropic_api_key and anthropic_model_name:
        available_providers.append(get_anthropic_model(anthropic_model_name))
        provider_names.append("Anthropic")

    if openai_api_key and openai_model_name:
        available_providers.append(get_openai_model(openai_model_name))
        provider_names.append("OpenAI")

    if openrouter_api_key and openrouter_model_name:
        available_providers.append(get_openrouter_model(openrouter_model_name))
        provider_names.append("OpenRouter")

    if not available_providers:
        raise ValueError(
            "No API keys found. Please set at least one of "
            "ANTHROPIC_API_KEY, OPENAI_API_KEY, or OPENROUTER_API_KEY."
        )

    logger.info("Using providers: %s", ", ".join(provider_names))
    return FallbackModel(*available_providers)
