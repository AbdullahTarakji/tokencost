"""Pricing database for LLM models. Cost is per 1M tokens."""

from __future__ import annotations

import re

PRICING: dict[str, dict[str, float | str]] = {
    # OpenAI
    "gpt-4o": {"input": 2.50, "output": 10.00, "provider": "openai"},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60, "provider": "openai"},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00, "provider": "openai"},
    "gpt-4": {"input": 30.00, "output": 60.00, "provider": "openai"},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50, "provider": "openai"},
    "o1": {"input": 15.00, "output": 60.00, "provider": "openai"},
    "o1-mini": {"input": 3.00, "output": 12.00, "provider": "openai"},
    "o3-mini": {"input": 1.10, "output": 4.40, "provider": "openai"},
    # Anthropic
    "claude-opus-4": {"input": 15.00, "output": 75.00, "provider": "anthropic"},
    "claude-sonnet-4": {"input": 3.00, "output": 15.00, "provider": "anthropic"},
    "claude-3.5-sonnet": {"input": 3.00, "output": 15.00, "provider": "anthropic"},
    "claude-3.5-haiku": {"input": 0.80, "output": 4.00, "provider": "anthropic"},
    "claude-3-haiku": {"input": 0.25, "output": 1.25, "provider": "anthropic"},
    # Google
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40, "provider": "google"},
    "gemini-2.0-pro": {"input": 1.25, "output": 10.00, "provider": "google"},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00, "provider": "google"},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30, "provider": "google"},
    # Mistral
    "mistral-large": {"input": 2.00, "output": 6.00, "provider": "mistral"},
    "mistral-small": {"input": 0.20, "output": 0.60, "provider": "mistral"},
    "codestral": {"input": 0.30, "output": 0.90, "provider": "mistral"},
}


def _normalize(name: str) -> str:
    """Normalize model name for fuzzy matching."""
    return re.sub(r"[.\-_]", "", name.lower().strip())


def get_model_pricing(model: str) -> dict[str, float | str] | None:
    """Look up pricing for a model, with fuzzy matching support."""
    if model in PRICING:
        return PRICING[model]
    # Fuzzy match
    norm = _normalize(model)
    for key, val in PRICING.items():
        if _normalize(key) == norm:
            return val
    return None


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate the cost of an API call in dollars."""
    pricing = get_model_pricing(model)
    if pricing is None:
        raise ValueError(f"Unknown model: {model}")
    input_cost = float(pricing["input"]) * input_tokens / 1_000_000
    output_cost = float(pricing["output"]) * output_tokens / 1_000_000
    return input_cost + output_cost


def list_models(provider: str | None = None) -> list[dict[str, str | float]]:
    """List all models, optionally filtered by provider."""
    results = []
    for name, info in PRICING.items():
        if provider is None or info["provider"] == provider:
            results.append({"model": name, **info})
    return results
