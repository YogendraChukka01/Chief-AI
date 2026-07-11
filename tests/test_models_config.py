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
        """Should find model by exact alias."""
        result = get_model_config("claude-sonnet-4")
        assert result is not None
        assert result.name == "claude-sonnet-4-20250514"

    def test_exact_full_name_match(self) -> None:
        """Should find model by full model name."""
        result = get_model_config("claude-sonnet-4-20250514")
        assert result is not None
        assert result.provider == "anthropic"

    def test_unknown_model_returns_none(self) -> None:
        """Unknown model should return None."""
        result = get_model_config("unknown-model-xyz")
        assert result is None

    def test_registry_contains_all_models(self) -> None:
        """Registry should contain all defined models."""
        assert len(MODEL_REGISTRY) >= 6

    def test_deepseek_returns_paid_by_default(self) -> None:
        """'deepseek' should match the paid model (longer key wins)."""
        result = get_model_config("deepseek")
        assert result is not None
        assert result.name == "deepseek/deepseek-chat-v3.1"

    def test_deepseek_free_explicit(self) -> None:
        """'deepseek-free' should match the free model."""
        result = get_model_config("deepseek-free")
        assert result is not None
        assert "free" in result.name


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

    def test_cached_tokens_reduce_cost(self) -> None:
        """Cached tokens should reduce cost (charged at lower cached rate)."""
        cost_without = calculate_cost(1000, 1000, ANTHROPIC_CLAUDE_SONNET_4, cached_tokens=0)
        cost_with = calculate_cost(1000, 1000, ANTHROPIC_CLAUDE_SONNET_4, cached_tokens=500)
        # With caching, cost should be LOWER because cached tokens are cheaper
        assert cost_with < cost_without

    def test_cached_tokens_formula(self) -> None:
        """Verify correct cached token formula."""
        model = ANTHROPIC_CLAUDE_SONNET_4
        input_tokens = 1000
        cached_tokens = 400
        output_tokens = 500

        cost = calculate_cost(input_tokens, output_tokens, model, cached_tokens)

        # Non-cached input: 600 tokens * 0.003/1k = 0.0018
        # Cached input: 400 tokens * 0.0003/1k = 0.00012
        # Output: 500 tokens * 0.015/1k = 0.0075
        # Total: 0.00942
        expected = (600 / 1000 * 0.003) + (400 / 1000 * 0.0003) + (500 / 1000 * 0.015)
        assert cost == pytest.approx(expected, rel=1e-4)
