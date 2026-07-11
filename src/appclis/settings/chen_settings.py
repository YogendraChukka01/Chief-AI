"""Chen settings model with validation."""

from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ChenSettings(BaseSettings):
    """Configuration settings for Chen AI agent."""

    anthropic_api_key: str | None = Field(
        None, description="Anthropic API key, https://console.anthropic.com/settings/keys"
    )
    openai_api_key: str | None = Field(None, description="OpenAI API key, https://platform.openai.com/api-keys")
    openrouter_api_key: str | None = Field(None, description="OpenRouter API key, https://openrouter.ai/settings/keys")
    tavily_api_key: str | None = Field(None, description="Tavily API key, https://app.tavily.com/home")
    context_window: int | None = Field(200_000, gt=1, description="Context window size to trigger compression")
    language: str | None = Field("English", description="Language for the AI to use")

    model_config = SettingsConfigDict(case_sensitive=False)

    @model_validator(mode="after")
    def validate_api_keys(self) -> Self:
        """Validate that at least one API key is configured."""
        if not any([self.anthropic_api_key, self.openai_api_key, self.openrouter_api_key]):
            raise ValueError("At least one API key must be set: Anthropic, OpenAI, or OpenRouter.")
        return self
