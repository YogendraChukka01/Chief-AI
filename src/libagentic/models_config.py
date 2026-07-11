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

# OpenRouter Models
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


DEFAULT_MODELS = AgentModels()

# Model lookup by name - exact matches only for deterministic behavior
MODEL_REGISTRY: dict[str, ModelConfig] = {
    "claude-sonnet-4": ANTHROPIC_CLAUDE_SONNET_4,
    "claude-3-5-haiku": ANTHROPIC_CLAUDE_3_5_HAIKU,
    "gpt-5": OPENAI_GPT_5,
    "gpt-4o": OPENAI_GPT_4O,
    "deepseek-free": OPENROUTER_DEEPSEEK_FREE,
    "deepseek": OPENROUTER_DEEPSEEK,
}


def get_model_config(model_name: str) -> ModelConfig | None:
    """Look up model config by name with exact match priority.

    Args:
        model_name: The model name or alias to look up

    Returns:
        ModelConfig if found, None otherwise
    """
    normalized = model_name.lower().strip()

    # Exact match first (deterministic)
    if normalized in MODEL_REGISTRY:
        return MODEL_REGISTRY[normalized]

    # Check full model name in registry values
    for config in MODEL_REGISTRY.values():
        if normalized == config.name.lower():
            return config

    # Substring match in keys (prefer longer/more specific match)
    best_match: ModelConfig | None = None
    best_match_len = 0

    for key, config in MODEL_REGISTRY.items():
        if normalized in key or key in normalized:
            if len(key) > best_match_len:
                best_match = config
                best_match_len = len(key)

    return best_match


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    model: ModelConfig,
    cached_tokens: int = 0,
) -> float:
    """Calculate cost in USD for given token counts.

    Cached tokens are a SUBSET of input tokens. We charge the non-cached
    input tokens at full price and cached tokens at the cached price.

    Args:
        input_tokens: Total input tokens (including cached)
        output_tokens: Output tokens
        model: Model configuration with pricing
        cached_tokens: Number of tokens served from cache

    Returns:
        Cost in USD
    """
    # Cached tokens are a subset of input tokens - don't double count
    non_cached_input = max(0, input_tokens - cached_tokens)
    cost = (non_cached_input / 1000) * model.input_cost_per_1k
    cost += (output_tokens / 1000) * model.output_cost_per_1k

    if cached_tokens and model.cached_cost_per_1k:
        cost += (cached_tokens / 1000) * model.cached_cost_per_1k

    return round(cost, 6)
