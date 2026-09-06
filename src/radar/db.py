from __future__ import annotations

import sqlite3
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parents[2] / "data" / "radar.db"


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = Path(db_path or DEFAULT_DB)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS usage_by_model (
            snapshot_at TEXT NOT NULL,
            session_id TEXT NOT NULL,
            model TEXT NOT NULL,
            billing_provider TEXT,
            task TEXT,
            api_call_count INTEGER,
            input_tokens INTEGER,
            output_tokens INTEGER,
            cache_read_tokens INTEGER,
            cache_write_tokens INTEGER,
            reasoning_tokens INTEGER,
            estimated_cost_usd REAL,
            actual_cost_usd REAL,
            first_seen TEXT,
            last_seen TEXT,
            PRIMARY KEY (snapshot_at, session_id, model)
        );

        CREATE TABLE IF NOT EXISTS sessions_snapshot (
            snapshot_at TEXT NOT NULL,
            session_id TEXT NOT NULL,
            source TEXT,
            model TEXT,
            message_count INTEGER,
            tool_call_count INTEGER,
            input_tokens INTEGER,
            output_tokens INTEGER,
            cache_read_tokens INTEGER,
            cache_write_tokens INTEGER,
            estimated_cost_usd REAL,
            started_at TEXT,
            ended_at TEXT,
            title TEXT,
            PRIMARY KEY (snapshot_at, session_id)
        );

        CREATE TABLE IF NOT EXISTS openrouter_models (
            fetched_at TEXT NOT NULL,
            model_id TEXT NOT NULL,
            name TEXT,
            context_length INTEGER,
            prompt_price REAL,
            completion_price REAL,
            input_cache_read_price REAL,
            input_cache_write_price REAL,
            is_free INTEGER,
            raw_json TEXT,
            PRIMARY KEY (fetched_at, model_id)
        );

        CREATE TABLE IF NOT EXISTS recommendations (
            created_at TEXT NOT NULL,
            kind TEXT NOT NULL,
            title TEXT NOT NULL,
            detail TEXT NOT NULL,
            severity TEXT DEFAULT 'info'
        );
        """
    )
    conn.commit()
