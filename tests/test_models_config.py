"""Tests for model configuration module."""

import pytest

from libagentic.models_config import (
    ANTHROPIC_CLAUDE_SONNET_4,
    MODEL_REGISTRY,
    OPENROUTER_DEEPSEEK_FREE,
    ModelConfig,
    calculate_cost,
    get_model_config,
)


class TestModelConfig:
    """Tests for ModelConfig dataclass."""

    def test_model_config_is_frozen(self) -> None:
        """Model configs should be immutable."""
        with pytest.raises(AttributeError):
            ANTHROPIC_CLAUDE_SONNET_4.name = "modified"  # type: ignore[misc]

    def test_model_config_fields(self) -> None:
        """Model config should have all required fields."""
        assert ANTHROPIC_CLAUDE_SONNET_4.name == "claude-sonnet-4-20250514"
        assert ANTHROPIC_CLAUDE_SONNET_4.provider == "anthropic"
        assert ANTHROPIC_CLAUDE_SONNET_4.input_cost_per_1k > 0
        assert ANTHROPIC_CLAUDE_SONNET_4.output_cost_per_1k > 0

    def test_free_model_has_zero_cost(self) -> None:
        """Free models should have zero cost."""
        assert OPENROUTER_DEEPSEEK_FREE.input_cost_per_1k == 0.0
        assert OPENROUTER_DEEPSEEK_FREE.output_cost_per_1k == 0.0


class TestModelRegistry:
    """Tests for model registry lookup."""

    def test_exact_match(self) -> None:
        """Should find model by exact name."""
        result = get_model_config("claude-sonnet-4")
        assert result is not None
        assert result.name == "claude-sonnet-4-20250514"

    def test_partial_match(self) -> None:
        """Should find model by partial name."""
        result = get_model_config("gpt")
        assert result is not None
        assert "gpt" in result.name.lower()

    def test_unknown_model_returns_none(self) -> None:
        """Unknown model should return None."""
        result = get_model_config("unknown-model-xyz")
        assert result is None

    def test_registry_contains_all_models(self) -> None:
        """Registry should contain all defined models."""
        assert len(MODEL_REGISTRY) >= 6


class TestCalculateCost:
    """Tests for cost calculation."""

    def test_zero_tokens(self) -> None:
        """Zero tokens should result in zero cost."""
        cost = calculate_cost(0, 0, ANTHROPIC_CLAUDE_SONNET_4)
        assert cost == 0.0

    def test_basic_cost(self) -> None:
        """Should calculate basic cost correctly."""
        cost = calculate_cost(1000, 1000, ANTHROPIC_CLAUDE_SONNET_4)
        # 1000/1000 * 0.003 + 1000/1000 * 0.015 = 0.018
        assert cost == pytest.approx(0.018, rel=1e-3)

    def test_free_model_cost(self) -> None:
        """Free model should always return zero cost."""
        cost = calculate_cost(10000, 10000, OPENROUTER_DEEPSEEK_FREE)
        assert cost == 0.0

    def test_cached_tokens(self) -> None:
        """Should include cached token cost when available."""
        cost_without = calculate_cost(1000, 1000, ANTHROPIC_CLAUDE_SONNET_4)
        cost_with = calculate_cost(1000, 1000, ANTHROPIC_CLAUDE_SONNET_4, cached_tokens=500)
        assert cost_with < cost_without
