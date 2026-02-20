"""Tests for pricing module."""

from tokencost.pricing.estimator import estimate_cost, estimate_tokens
from tokencost.pricing.models import calculate_cost, get_model_pricing, list_models


def test_get_model_pricing_exact():
    """Test exact model lookup."""
    p = get_model_pricing("gpt-4o")
    assert p is not None
    assert p["input"] == 2.50
    assert p["provider"] == "openai"


def test_get_model_pricing_fuzzy():
    """Test fuzzy matching with different separators."""
    p = get_model_pricing("claude-3-5-sonnet")
    assert p is not None
    assert p["provider"] == "anthropic"


def test_get_model_pricing_unknown():
    """Test unknown model returns None."""
    assert get_model_pricing("nonexistent-model") is None


def test_calculate_cost():
    """Test cost calculation."""
    cost = calculate_cost("gpt-4o", 1000, 500)
    expected = 2.50 * 1000 / 1_000_000 + 10.00 * 500 / 1_000_000
    assert abs(cost - expected) < 1e-10


def test_calculate_cost_unknown():
    """Test cost calculation with unknown model raises."""
    try:
        calculate_cost("unknown-model", 100, 100)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_list_models_all():
    """Test listing all models."""
    models = list_models()
    assert len(models) > 10


def test_list_models_filtered():
    """Test listing models by provider."""
    models = list_models("anthropic")
    assert all(m["provider"] == "anthropic" for m in models)
    assert len(models) >= 3


def test_estimate_tokens():
    """Test token estimation."""
    tokens = estimate_tokens("Hello world", "gemini-2.0-flash")
    assert tokens >= 1


def test_estimate_tokens_openai():
    """Test token estimation with tiktoken."""
    tokens = estimate_tokens("Hello world", "gpt-4o")
    assert tokens >= 1


def test_estimate_cost_fn():
    """Test cost estimation."""
    cost = estimate_cost("Hello world this is a test", "gpt-4o")
    assert cost > 0
