"""SQLite storage for API call records."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tokencost.config.settings import DEFAULT_DB_PATH, _ensure_dir


def _get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Get a database connection, creating the table if needed.

    Args:
        db_path: Optional path to the SQLite database file.
            If None, uses the default path from settings.

    Returns:
        An open SQLite connection with row_factory set to sqlite3.Row.
    """
    path = str(db_path) if db_path else str(DEFAULT_DB_PATH)
    if db_path is None:
        _ensure_dir()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            provider TEXT NOT NULL,
            model TEXT NOT NULL,
            input_tokens INTEGER NOT NULL,
            output_tokens INTEGER NOT NULL,
            cost REAL NOT NULL,
            project TEXT DEFAULT 'default',
            tags TEXT DEFAULT '[]',
            metadata TEXT DEFAULT '{}'
        )
    """)
    conn.commit()
    return conn


def log_call(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cost: float,
    project: str = "default",
    tags: list[str] | None = None,
    metadata: dict | None = None,
    db_path: str | Path | None = None,
) -> int:
    """Log an API call to the database.

    Args:
        provider: The API provider (e.g., 'openai', 'anthropic').
        model: The model name (e.g., 'gpt-4o').
        input_tokens: Number of input/prompt tokens.
        output_tokens: Number of output/completion tokens.
        cost: Calculated cost in USD.
        project: Project name for grouping calls.
        tags: Optional list of tags for categorization.
        metadata: Optional metadata dictionary.
        db_path: Optional database path override.

    Returns:
        The row ID of the inserted record.
    """
    conn = _get_connection(db_path)
    try:
        cursor = conn.execute(
            "INSERT INTO api_calls"
            " (timestamp, provider, model, input_tokens, output_tokens, cost, project, tags, metadata)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                datetime.now(timezone.utc).isoformat(),
                provider,
                model,
                input_tokens,
                output_tokens,
                cost,
                project,
                json.dumps(tags or []),
                json.dumps(metadata or {}),
            ),
        )
        conn.commit()
        return cursor.lastrowid or 0
    finally:
        conn.close()


def get_calls(
    start_date: str | None = None,
    end_date: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    project: str | None = None,
    db_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Query API calls with optional filters.

    Args:
        start_date: ISO 8601 start date filter (inclusive).
        end_date: ISO 8601 end date filter (inclusive).
        provider: Filter by provider name.
        model: Filter by model name.
        project: Filter by project name.
        db_path: Optional database path override.

    Returns:
        A list of call records as dictionaries.
    """
    conn = _get_connection(db_path)
    try:
        query = "SELECT * FROM api_calls WHERE 1=1"
        params: list = []

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        if provider:
            query += " AND provider = ?"
            params.append(provider)
        if model:
            query += " AND model = ?"
            params.append(model)
        if project:
            query += " AND project = ?"
            params.append(project)

        query += " ORDER BY timestamp DESC"
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def delete_calls(before_date: str, db_path: str | Path | None = None) -> int:
    """Delete calls recorded before a given date.

    Args:
        before_date: ISO 8601 date string; calls before this are deleted.
        db_path: Optional database path override.

    Returns:
        The number of records deleted.
    """
    conn = _get_connection(db_path)
    try:
        cursor = conn.execute("DELETE FROM api_calls WHERE timestamp < ?", (before_date,))
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def reset(db_path: str | Path | None = None) -> None:
    """Clear all data from the database.

    Args:
        db_path: Optional database path override.
    """
    conn = _get_connection(db_path)
    try:
        conn.execute("DELETE FROM api_calls")
        conn.commit()
    finally:
        conn.close()
