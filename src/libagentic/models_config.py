"""Centralized model configuration for all LLM providers."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ModelConfig:
    """Immutable model configuration."""

    name: str
    provider: str
    input_cost_per_1k: float
    output_cost_per_1k: float
    cached_cost_per_1k: float | None = None
    max_context: int = 128_000


# Anthropic Models
ANTHROPIC_CLAUDE_SONNET_4 = ModelConfig(
    name="claude-sonnet-4-20250514",
    provider="anthropic",
    input_cost_per_1k=0.003,
    output_cost_per_1k=0.015,
    cached_cost_per_1k=0.0003,
    max_context=200_000,
)

ANTHROPIC_CLAUDE_3_5_HAIKU = ModelConfig(
    name="claude-3-5-haiku-latest",
    provider="anthropic",
    input_cost_per_1k=0.00025,
    output_cost_per_1k=0.00125,
    max_context=200_000,
)

# OpenAI Models
OPENAI_GPT_5 = ModelConfig(
    name="gpt-5-2025-08-07",
    provider="openai",
    input_cost_per_1k=0.005,
    output_cost_per_1k=0.02,
    max_context=128_000,
)

OPENAI_GPT_4O = ModelConfig(
    name="gpt-4o",
    provider="openai",
    input_cost_per_1k=0.0025,
    output_cost_per_1k=0.01,
    max_context=128_000,
)

# OpenRouter Models (Free tier)
OPENROUTER_DEEPSEEK_FREE = ModelConfig(
    name="deepseek/deepseek-chat-v3.1:free",
    provider="openrouter",
    input_cost_per_1k=0.0,
    output_cost_per_1k=0.0,
    max_context=128_000,
)

OPENROUTER_DEEPSEEK = ModelConfig(
    name="deepseek/deepseek-chat-v3.1",
    provider="openrouter",
    input_cost_per_1k=0.00014,
    output_cost_per_1k=0.00028,
    max_context=128_000,
)


@dataclass(frozen=True)
class AgentModels:
    """Default models for each agent type."""

    primary: ModelConfig = field(default_factory=lambda: ANTHROPIC_CLAUDE_SONNET_4)
    fallback_1: ModelConfig = field(default_factory=lambda: OPENAI_GPT_5)
    fallback_2: ModelConfig = field(default_factory=lambda: OPENROUTER_DEEPSEEK_FREE)
    title_generator: ModelConfig = field(default_factory=lambda: ANTHROPIC_CLAUDE_3_5_HAIKU)
    compressor: ModelConfig = field(default_factory=lambda: OPENROUTER_DEEPSEEK_FREE)


# Global defaults
DEFAULT_MODELS = AgentModels()

# Model lookup by name (normalized)
MODEL_REGISTRY: dict[str, ModelConfig] = {
    "claude-sonnet-4": ANTHROPIC_CLAUDE_SONNET_4,
    "claude-3-5-haiku": ANTHROPIC_CLAUDE_3_5_HAIKU,
    "gpt-5": OPENAI_GPT_5,
    "gpt-4o": OPENAI_GPT_4O,
    "deepseek-free": OPENROUTER_DEEPSEEK_FREE,
    "deepseek": OPENROUTER_DEEPSEEK,
}


def get_model_config(model_name: str) -> ModelConfig | None:
    """Look up model config by name or partial match."""
    normalized = model_name.lower().strip()

    # Exact match
    if normalized in MODEL_REGISTRY:
        return MODEL_REGISTRY[normalized]

    # Partial match
    for key, config in MODEL_REGISTRY.items():
        if normalized in key or key in normalized:
            return config

    return None


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    model: ModelConfig,
    cached_tokens: int = 0,
) -> float:
    """Calculate cost in USD for given token counts."""
    cost = (input_tokens / 1000) * model.input_cost_per_1k
    cost += (output_tokens / 1000) * model.output_cost_per_1k

    if cached_tokens and model.cached_cost_per_1k:
        cost += (cached_tokens / 1000) * model.cached_cost_per_1k

    return round(cost, 6)
