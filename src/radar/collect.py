from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .db import connect


def hermes_state_path() -> Path:
    home = Path(os.environ.get("HERMES_HOME", "/root/.hermes"))
    return home / "state.db"


def snapshot_usage() -> dict:
    state = hermes_state_path()
    if not state.exists():
        raise FileNotFoundError(f"Hermes state.db not found at {state}")

    now = datetime.now(timezone.utc).isoformat()
    src = sqlite3.connect(f"file:{state}?mode=ro", uri=True)
    src.row_factory = sqlite3.Row
    dst = connect()

    usage_rows = src.execute(
        """
        SELECT session_id, model, billing_provider, task, api_call_count,
               input_tokens, output_tokens, cache_read_tokens, cache_write_tokens,
               reasoning_tokens, estimated_cost_usd, actual_cost_usd,
               first_seen, last_seen
        FROM session_model_usage
        """
    ).fetchall()

    for r in usage_rows:
        dst.execute(
            """
            INSERT OR REPLACE INTO usage_by_model VALUES (
              ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
            )
            """,
            (
                now,
                r["session_id"],
                r["model"],
                r["billing_provider"],
                r["task"],
                r["api_call_count"],
                r["input_tokens"],
                r["output_tokens"],
                r["cache_read_tokens"],
                r["cache_write_tokens"],
                r["reasoning_tokens"],
                r["estimated_cost_usd"],
                r["actual_cost_usd"],
                r["first_seen"],
                r["last_seen"],
            ),
        )

    sessions = src.execute(
        """
        SELECT id, source, model, message_count, tool_call_count,
               input_tokens, output_tokens, cache_read_tokens, cache_write_tokens,
               estimated_cost_usd, started_at, ended_at, title
        FROM sessions
        """
    ).fetchall()

    for r in sessions:
        dst.execute(
            """
            INSERT OR REPLACE INTO sessions_snapshot VALUES (
              ?,?,?,?,?,?,?,?,?,?,?,?,?,?
            )
            """,
            (
                now,
                r["id"],
                r["source"],
                r["model"],
                r["message_count"],
                r["tool_call_count"],
                r["input_tokens"],
                r["output_tokens"],
                r["cache_read_tokens"],
                r["cache_write_tokens"],
                r["estimated_cost_usd"],
                r["started_at"],
                r["ended_at"],
                r["title"],
            ),
        )

    dst.commit()
    src.close()
    dst.close()
    return {"snapshot_at": now, "usage_rows": len(usage_rows), "sessions": len(sessions)}


def main() -> None:
    result = snapshot_usage()
    print(f"Collected {result['usage_rows']} usage rows, {result['sessions']} sessions @ {result['snapshot_at']}")


if __name__ == "__main__":
    main()
