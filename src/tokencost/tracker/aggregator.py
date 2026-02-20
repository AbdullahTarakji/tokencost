"""Aggregation queries for API call data."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from tokencost.config.settings import load_config
from tokencost.tracker.database import _get_connection


def _period_start(period: str) -> str | None:
    """Get the ISO 8601 start timestamp for a period."""
    now = datetime.now(timezone.utc)
    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "all":
        return None
    else:
        raise ValueError(f"Unknown period: {period}")
    return start.isoformat()


def summary(period: str = "today", db_path: str | Path | None = None) -> dict:
    """Get summary stats for a period."""
    conn = _get_connection(db_path)
    try:
        start = _period_start(period)
        query = (
            "SELECT COUNT(*) as count, COALESCE(SUM(cost), 0) as total_cost,"
            " COALESCE(SUM(input_tokens + output_tokens), 0) as total_tokens FROM api_calls"
        )
        params: list = []
        if start:
            query += " WHERE timestamp >= ?"
            params.append(start)
        row = conn.execute(query, params).fetchone()
        return {
            "period": period,
            "call_count": row["count"],
            "total_cost": row["total_cost"],
            "total_tokens": row["total_tokens"],
        }
    finally:
        conn.close()


def by_model(period: str = "today", db_path: str | Path | None = None) -> list[dict]:
    """Breakdown by model for a period."""
    conn = _get_connection(db_path)
    try:
        start = _period_start(period)
        query = (
            "SELECT model, provider, COUNT(*) as count, SUM(cost) as total_cost,"
            " SUM(input_tokens) as input_tokens, SUM(output_tokens) as output_tokens FROM api_calls"
        )
        params: list = []
        if start:
            query += " WHERE timestamp >= ?"
            params.append(start)
        query += " GROUP BY model ORDER BY total_cost DESC"
        return [dict(r) for r in conn.execute(query, params).fetchall()]
    finally:
        conn.close()


def by_project(period: str = "today", db_path: str | Path | None = None) -> list[dict]:
    """Breakdown by project for a period."""
    conn = _get_connection(db_path)
    try:
        start = _period_start(period)
        query = "SELECT project, COUNT(*) as count, SUM(cost) as total_cost FROM api_calls"
        params: list = []
        if start:
            query += " WHERE timestamp >= ?"
            params.append(start)
        query += " GROUP BY project ORDER BY total_cost DESC"
        return [dict(r) for r in conn.execute(query, params).fetchall()]
    finally:
        conn.close()


def by_provider(period: str = "today", db_path: str | Path | None = None) -> list[dict]:
    """Breakdown by provider for a period."""
    conn = _get_connection(db_path)
    try:
        start = _period_start(period)
        query = "SELECT provider, COUNT(*) as count, SUM(cost) as total_cost FROM api_calls"
        params: list = []
        if start:
            query += " WHERE timestamp >= ?"
            params.append(start)
        query += " GROUP BY provider ORDER BY total_cost DESC"
        return [dict(r) for r in conn.execute(query, params).fetchall()]
    finally:
        conn.close()


def daily_costs(days: int = 30, db_path: str | Path | None = None) -> list[dict]:
    """Daily cost trend for the last N days."""
    conn = _get_connection(db_path)
    try:
        start = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        rows = conn.execute(
            "SELECT DATE(timestamp) as date, SUM(cost) as total_cost, COUNT(*) as count"
            " FROM api_calls WHERE timestamp >= ? GROUP BY DATE(timestamp) ORDER BY date",
            (start,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def budget_status(db_path: str | Path | None = None, config_path: str | Path | None = None) -> dict:
    """Check current spend vs budget for all periods."""
    config = load_config(config_path)
    result = {}
    for period_name, limit in [
        ("daily", config.budgets.daily),
        ("weekly", config.budgets.weekly),
        ("monthly", config.budgets.monthly),
    ]:
        period_map = {"daily": "today", "weekly": "week", "monthly": "month"}
        s = summary(period_map[period_name], db_path)
        spent = s["total_cost"]
        remaining = max(0.0, limit - spent)
        pct = (spent / limit * 100) if limit > 0 else 0.0
        result[period_name] = {
            "limit": limit,
            "spent": spent,
            "remaining": remaining,
            "percentage": round(pct, 1),
            "exceeded": spent > limit,
        }
    return result
