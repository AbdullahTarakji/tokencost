"""Tests for tracker module."""

import tempfile
from pathlib import Path

from tokencost.tracker.aggregator import budget_status, by_model, by_project, daily_costs, summary
from tokencost.tracker.database import delete_calls, get_calls, log_call, reset


def _tmp_db() -> str:
    """Create a temp database path."""
    return str(Path(tempfile.mktemp(suffix=".db")))


def test_log_and_get():
    """Test logging and retrieving calls."""
    db = _tmp_db()
    log_call("openai", "gpt-4o", 100, 50, 0.00075, db_path=db)
    calls = get_calls(db_path=db)
    assert len(calls) == 1
    assert calls[0]["model"] == "gpt-4o"
    assert calls[0]["input_tokens"] == 100


def test_get_filtered():
    """Test filtering calls."""
    db = _tmp_db()
    log_call("openai", "gpt-4o", 100, 50, 0.001, project="proj1", db_path=db)
    log_call("anthropic", "claude-3.5-sonnet", 200, 100, 0.002, project="proj2", db_path=db)
    calls = get_calls(provider="openai", db_path=db)
    assert len(calls) == 1
    calls = get_calls(project="proj2", db_path=db)
    assert len(calls) == 1


def test_reset():
    """Test clearing all data."""
    db = _tmp_db()
    log_call("openai", "gpt-4o", 100, 50, 0.001, db_path=db)
    reset(db_path=db)
    assert len(get_calls(db_path=db)) == 0


def test_delete_calls():
    """Test deleting old calls."""
    db = _tmp_db()
    log_call("openai", "gpt-4o", 100, 50, 0.001, db_path=db)
    # Delete everything before far future
    deleted = delete_calls("2099-01-01T00:00:00", db_path=db)
    assert deleted == 1


def test_summary():
    """Test summary aggregation."""
    db = _tmp_db()
    log_call("openai", "gpt-4o", 100, 50, 0.001, db_path=db)
    log_call("openai", "gpt-4o", 200, 100, 0.002, db_path=db)
    s = summary("all", db_path=db)
    assert s["call_count"] == 2
    assert abs(s["total_cost"] - 0.003) < 1e-10


def test_by_model():
    """Test model breakdown."""
    db = _tmp_db()
    log_call("openai", "gpt-4o", 100, 50, 0.001, db_path=db)
    log_call("anthropic", "claude-3.5-sonnet", 200, 100, 0.002, db_path=db)
    models = by_model("all", db_path=db)
    assert len(models) == 2


def test_by_project():
    """Test project breakdown."""
    db = _tmp_db()
    log_call("openai", "gpt-4o", 100, 50, 0.001, project="a", db_path=db)
    log_call("openai", "gpt-4o", 100, 50, 0.001, project="b", db_path=db)
    projects = by_project("all", db_path=db)
    assert len(projects) == 2


def test_daily_costs():
    """Test daily cost trend."""
    db = _tmp_db()
    log_call("openai", "gpt-4o", 100, 50, 0.001, db_path=db)
    costs = daily_costs(30, db_path=db)
    assert len(costs) >= 1


def test_budget_status():
    """Test budget status check."""
    db = _tmp_db()
    import tempfile

    cfg_path = tempfile.mktemp(suffix=".yaml")
    bs = budget_status(db_path=db, config_path=cfg_path)
    assert "daily" in bs
    assert "weekly" in bs
    assert "monthly" in bs
    assert bs["daily"]["exceeded"] is False
