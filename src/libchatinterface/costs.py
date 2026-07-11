"""Cost tracking and calculation utilities for chat sessions."""

import re
from dataclasses import dataclass, field

from pydantic_ai.usage import RunUsage


@dataclass
class ModelCosts:
    """Represents costs for a specific model."""

    input_cost_per_1k: float  # USD per 1K input tokens
    output_cost_per_1k: float  # USD per 1K output tokens
    cached_cost_per_1k: float | None = None  # USD per 1K cached tokens (if supported)


# Model pricing configuration - values are per-1K tokens in USD
MODEL_PRICING: dict[str, ModelCosts] = {
    "claude-3-5-sonnet-20241022": ModelCosts(0.003, 0.015),
    "claude-3-5-sonnet-latest": ModelCosts(0.003, 0.015),
    "claude-sonnet-4-20250514": ModelCosts(0.015, 0.075),
    "claude-3-5-haiku-20241022": ModelCosts(0.00025, 0.00125),
    "claude-3-5-haiku-latest": ModelCosts(0.00025, 0.00125),
    "claude-3-haiku-20240307": ModelCosts(0.00025, 0.00125),
    "gpt-4o": ModelCosts(0.0025, 0.01),
    "gpt-4o-2024-11-20": ModelCosts(0.0025, 0.01),
    "gpt-5-2025-08-07": ModelCosts(0.005, 0.02),
    "gpt-4o-mini": ModelCosts(0.00015, 0.0006),
    "gpt-4-turbo": ModelCosts(0.01, 0.03),
    "deepseek/deepseek-chat-v3.1:free": ModelCosts(0.0, 0.0),
    "deepseek/deepseek-chat-v3.1": ModelCosts(0.00014, 0.00028),
    "anthropic/claude-3.5-sonnet": ModelCosts(0.003, 0.015),
    "anthropic/claude-3.5-haiku": ModelCosts(0.00025, 0.00125),
    "openai/gpt-4o": ModelCosts(0.0025, 0.01),
    "openai/gpt-4o-mini": ModelCosts(0.00015, 0.0006),
}


@dataclass
class UsageCosts:
    """Represents token usage and associated costs."""

    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    total_tokens: int = 0
    requests: int = 0
    cost_usd: float | None = None
    model_name: str | None = None


@dataclass
class SessionCosts:
    """Aggregated costs for an entire session."""

    total_usage: UsageCosts = field(default_factory=UsageCosts)
    model_breakdown: dict[str, UsageCosts] = field(default_factory=dict)


def normalize_model_name(model_name: str) -> str:
    """Normalize model name for pricing lookup."""
    if not model_name:
        return model_name

    # Single combined regex to strip all known prefixes
    model_name = re.sub(
        r"^(anthropic/|openai/|google/|google-gla:|deepseek/|anthropic:|openai:)",
        "",
        model_name,
        flags=re.IGNORECASE,
    )

    return model_name.lower()


def calculate_usage_cost(usage: RunUsage, model_name: str | None = None) -> UsageCosts:
    """Calculate costs for a RunUsage object.

    Args:
        usage: Pydantic AI RunUsage object
        model_name: Name of the model used

    Returns:
        UsageCosts object with token counts and calculated costs
    """
    costs = UsageCosts(
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cached_tokens=getattr(usage, "cache_read_tokens", 0) or getattr(usage, "cached_tokens", 0),
        total_tokens=usage.total_tokens,
        requests=usage.requests,
        model_name=model_name,
    )

    if model_name:
        normalized_name = normalize_model_name(model_name)
        model_costs = MODEL_PRICING.get(normalized_name)

        if not model_costs:
            for pricing_key, pricing in MODEL_PRICING.items():
                if normalized_name == pricing_key.lower():
                    model_costs = pricing
                    break

        if model_costs:
            non_cached_input = max(0, costs.input_tokens - costs.cached_tokens)
            input_cost = (non_cached_input / 1000.0) * model_costs.input_cost_per_1k
            output_cost = (costs.output_tokens / 1000.0) * model_costs.output_cost_per_1k
            cached_cost = 0.0

            if costs.cached_tokens and model_costs.cached_cost_per_1k:
                cached_cost = (costs.cached_tokens / 1000.0) * model_costs.cached_cost_per_1k

            costs.cost_usd = input_cost + output_cost + cached_cost

    return costs


def add_usage_to_session(session_costs: SessionCosts, usage_costs: UsageCosts) -> None:
    """Add usage costs to session totals."""
    session_costs.total_usage.input_tokens += usage_costs.input_tokens
    session_costs.total_usage.output_tokens += usage_costs.output_tokens
    session_costs.total_usage.cached_tokens += usage_costs.cached_tokens
    session_costs.total_usage.total_tokens += usage_costs.total_tokens
    session_costs.total_usage.requests += usage_costs.requests

    if usage_costs.cost_usd is not None:
        if session_costs.total_usage.cost_usd is None:
            session_costs.total_usage.cost_usd = 0.0
        session_costs.total_usage.cost_usd += usage_costs.cost_usd

    if usage_costs.model_name:
        model_key = usage_costs.model_name
        if model_key not in session_costs.model_breakdown:
            session_costs.model_breakdown[model_key] = UsageCosts(model_name=model_key)

        model_costs = session_costs.model_breakdown[model_key]
        model_costs.input_tokens += usage_costs.input_tokens
        model_costs.output_tokens += usage_costs.output_tokens
        model_costs.cached_tokens += usage_costs.cached_tokens
        model_costs.total_tokens += usage_costs.total_tokens
        model_costs.requests += usage_costs.requests

        if usage_costs.cost_usd is not None:
            if model_costs.cost_usd is None:
                model_costs.cost_usd = 0.0
            model_costs.cost_usd += usage_costs.cost_usd


def format_token_count(count: int) -> str:
    """Format token count with k/M notation for readability."""
    if count < 1000:
        return str(count)
    elif count < 1000000:
        return f"{count / 1000:.1f}k"
    else:
        return f"{count / 1000000:.1f}M"


def format_session_costs_for_metadata(session_costs: SessionCosts) -> dict:
    """Format SessionCosts for inclusion in metadata.json."""
    def format_usage_costs(costs: UsageCosts) -> dict:
        result = {
            "input_tokens": costs.input_tokens,
            "output_tokens": costs.output_tokens,
            "total_tokens": costs.total_tokens,
            "requests": costs.requests,
        }
        if costs.cached_tokens > 0:
            result["cached_tokens"] = costs.cached_tokens
        if costs.cost_usd is not None:
            result["cost_usd"] = round(costs.cost_usd, 6)
        return result

    result = {"total": format_usage_costs(session_costs.total_usage)}

    if session_costs.model_breakdown:
        result["models"] = {
            model_name: format_usage_costs(costs) for model_name, costs in session_costs.model_breakdown.items()
        }

    return result
