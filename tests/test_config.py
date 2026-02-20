"""Tests for config module."""

import tempfile

from tokencost.config.settings import Config, load_config, save_config


def test_load_defaults():
    """Test loading config with no file returns defaults."""
    cfg = load_config(path=tempfile.mktemp(suffix=".yaml"))
    assert cfg.default_project == "default"
    assert cfg.proxy_port == 8800
    assert cfg.budgets.daily == 5.00


def test_save_and_load():
    """Test saving and loading config roundtrips."""
    path = tempfile.mktemp(suffix=".yaml")
    cfg = Config()
    cfg.budgets.daily = 10.00
    cfg.default_project = "myproject"
    save_config(cfg, path=path)

    loaded = load_config(path=path)
    assert loaded.budgets.daily == 10.00
    assert loaded.default_project == "myproject"


def test_custom_models():
    """Test custom models in config."""
    path = tempfile.mktemp(suffix=".yaml")
    cfg = Config()
    cfg.custom_models = {"my-model": {"input": 5.0, "output": 15.0, "provider": "openai"}}
    save_config(cfg, path=path)

    loaded = load_config(path=path)
    assert "my-model" in loaded.custom_models
