"""Token estimation from text."""

from __future__ import annotations

from tokencost.pricing.models import get_model_pricing


def estimate_tokens(text: str, model: str = "gpt-4o") -> int:
    """Estimate the number of tokens in text.

    Uses tiktoken for OpenAI models, otherwise approximates as len(text) / 4.
    """
    pricing = get_model_pricing(model)
    provider = pricing["provider"] if pricing else None

    if provider == "openai":
        try:
            import tiktoken

            try:
                enc = tiktoken.encoding_for_model(model)
            except KeyError:
                enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except ImportError:
            pass

    return max(1, int(len(text) / 4))


def estimate_cost(text: str, model: str = "gpt-4o") -> float:
    """Estimate the input cost for the given text and model."""
    pricing = get_model_pricing(model)
    if pricing is None:
        raise ValueError(f"Unknown model: {model}")
    tokens = estimate_tokens(text, model)
    return float(pricing["input"]) * tokens / 1_000_000
