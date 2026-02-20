"""Tests for proxy module."""

from tokencost.proxy.server import _parse_usage


def test_parse_openai_usage():
    """Test parsing OpenAI response body."""
    body = {
        "model": "gpt-4o",
        "usage": {"prompt_tokens": 100, "completion_tokens": 50},
    }
    model, inp, out = _parse_usage("openai", body)
    assert model == "gpt-4o"
    assert inp == 100
    assert out == 50


def test_parse_anthropic_usage():
    """Test parsing Anthropic response body."""
    body = {
        "model": "claude-3.5-sonnet",
        "usage": {"input_tokens": 200, "output_tokens": 100},
    }
    model, inp, out = _parse_usage("anthropic", body)
    assert model == "claude-3.5-sonnet"
    assert inp == 200
    assert out == 100


def test_parse_unknown_provider():
    """Test parsing unknown provider returns zeros."""
    model, inp, out = _parse_usage("unknown", {"model": "x"})
    assert inp == 0
    assert out == 0
