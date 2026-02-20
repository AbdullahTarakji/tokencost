"""Configuration loading and saving."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

DEFAULT_DIR = Path.home() / ".tokencost"
DEFAULT_CONFIG_PATH = DEFAULT_DIR / "config.yaml"
DEFAULT_DB_PATH = DEFAULT_DIR / "tokencost.db"


@dataclass
class Budgets:
    """Budget limits per period."""

    daily: float = 5.00
    weekly: float = 25.00
    monthly: float = 100.00


@dataclass
class Config:
    """Application configuration."""

    database_path: str = str(DEFAULT_DB_PATH)
    default_project: str = "default"
    proxy_port: int = 8800
    budgets: Budgets = field(default_factory=Budgets)
    custom_models: dict[str, dict[str, float | str]] = field(default_factory=dict)


def _ensure_dir() -> None:
    """Create the config directory if it doesn't exist."""
    DEFAULT_DIR.mkdir(parents=True, exist_ok=True)


def load_config(path: str | Path | None = None) -> Config:
    """Load configuration from YAML file, using defaults if missing."""
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    config = Config()

    if config_path.exists():
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}

        config.database_path = data.get("database_path", config.database_path)
        config.default_project = data.get("default_project", config.default_project)
        config.proxy_port = data.get("proxy_port", config.proxy_port)

        if "budgets" in data:
            b = data["budgets"]
            config.budgets = Budgets(
                daily=b.get("daily", 5.00),
                weekly=b.get("weekly", 25.00),
                monthly=b.get("monthly", 100.00),
            )

        config.custom_models = data.get("custom_models", {})

    return config


def save_config(config: Config, path: str | Path | None = None) -> None:
    """Save configuration to YAML file."""
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    _ensure_dir()

    data = {
        "database_path": config.database_path,
        "default_project": config.default_project,
        "proxy_port": config.proxy_port,
        "budgets": {
            "daily": config.budgets.daily,
            "weekly": config.budgets.weekly,
            "monthly": config.budgets.monthly,
        },
        "custom_models": config.custom_models,
    }

    with open(config_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
