from __future__ import annotations

from datetime import datetime, timezone

from .db import connect
from .poll_openrouter import fetch_models, store_models


WATCHLIST = (
    "z-ai/glm-5.3-flash",
    "deepseek/deepseek-v4-flash",
    "deepseek/deepseek-chat",
    "minimax/minimax-m2.7",
    "moonshotai/kimi-k2.6",
)


def ensure_alerts_table(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            created_at TEXT NOT NULL,
            title TEXT NOT NULL,
            detail TEXT NOT NULL,
            model_id TEXT,
            prompt_price REAL,
            completion_price REAL
        )
        """
    )
    conn.commit()


def check_discount_alerts() -> list[dict]:
    store_models(fetch_models())
    conn = connect()
    ensure_alerts_table(conn)
    latest = conn.execute("SELECT MAX(fetched_at) AS t FROM openrouter_models").fetchone()["t"]
    if not latest:
        return []

    rows = conn.execute(
        """
        SELECT model_id, name, prompt_price, completion_price, is_free
        FROM openrouter_models
        WHERE fetched_at = ?
        """,
        (latest,),
    ).fetchall()

    alerts: list[dict] = []
    now = datetime.now(timezone.utc).isoformat()

    for r in rows:
        mid = r["model_id"] or ""
        pp = r["prompt_price"]
        cp = r["completion_price"]
        if pp is None:
            continue
        usd_in = float(pp) * 1_000_000
        usd_out = float(cp or 0) * 1_000_000
        interesting = mid in WATCHLIST or "flash" in mid.lower()
        if not interesting:
            continue
        if r["is_free"] or usd_in <= 0.08:
            title = f"Deal: {mid}"
            detail = f"{r['name'] or mid}: ${usd_in:.4f}/M in, ${usd_out:.4f}/M out (free={bool(r['is_free'])})"
            alerts.append({"title": title, "detail": detail, "model_id": mid, "prompt_price": pp, "completion_price": cp})
            conn.execute(
                "INSERT INTO alerts VALUES (?,?,?,?,?,?)",
                (now, title, detail, mid, pp, cp),
            )

    # also surface absolute cheapest flash-like
    cheap = conn.execute(
        """
        SELECT model_id, name, prompt_price, completion_price
        FROM openrouter_models
        WHERE fetched_at = ? AND prompt_price IS NOT NULL AND prompt_price > 0
          AND lower(model_id) LIKE '%flash%'
        ORDER BY prompt_price ASC
        LIMIT 3
        """,
        (latest,),
    ).fetchall()
    if cheap:
        detail = ", ".join(
            f"{c['model_id']} (${float(c['prompt_price'])*1e6:.3f}/M in)" for c in cheap
        )
        title = "Cheapest Flash-class right now"
        alerts.append({"title": title, "detail": detail, "model_id": cheap[0]["model_id"], "prompt_price": cheap[0]["prompt_price"], "completion_price": cheap[0]["completion_price"]})
        conn.execute(
            "INSERT INTO alerts VALUES (?,?,?,?,?,?)",
            (now, title, detail, cheap[0]["model_id"], cheap[0]["prompt_price"], cheap[0]["completion_price"]),
        )

    conn.commit()
    conn.close()
    return alerts


def list_recent_alerts(limit: int = 20) -> list[dict]:
    conn = connect()
    ensure_alerts_table(conn)
    rows = conn.execute(
        "SELECT title, detail, created_at, model_id FROM alerts ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def main() -> None:
    for a in check_discount_alerts():
        print(f"{a['title']}: {a['detail']}")


if __name__ == "__main__":
    main()
