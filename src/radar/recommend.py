from __future__ import annotations

from datetime import datetime, timezone

from .db import connect


def build_recommendations() -> list[dict]:
    conn = connect()
    recs: list[dict] = []

    # Aggregate latest usage snapshot
    latest = conn.execute("SELECT MAX(snapshot_at) AS t FROM usage_by_model").fetchone()["t"]
    if not latest:
        recs.append(
            {
                "kind": "setup",
                "title": "No Hermes usage yet",
                "detail": "Run the collector after some Telegram/agent sessions.",
                "severity": "info",
            }
        )
        _save(conn, recs)
        return recs

    rows = conn.execute(
        """
        SELECT model,
               SUM(input_tokens) AS tin,
               SUM(output_tokens) AS tout,
               SUM(cache_read_tokens) AS cread,
               SUM(cache_write_tokens) AS cwrite,
               SUM(COALESCE(actual_cost_usd, estimated_cost_usd, 0)) AS cost
        FROM usage_by_model
        WHERE snapshot_at = ?
        GROUP BY model
        ORDER BY cost DESC
        """,
        (latest,),
    ).fetchall()

    total_cost = sum(float(r["cost"] or 0) for r in rows)
    total_in = sum(int(r["tin"] or 0) for r in rows)
    total_cread = sum(int(r["cread"] or 0) for r in rows)

    if total_in > 0:
        cache_hit = total_cread / max(total_in + total_cread, 1)
        if cache_hit < 0.05 and len(rows) > 1:
            recs.append(
                {
                    "kind": "cache",
                    "title": "Low cache reuse — model hopping suspected",
                    "detail": (
                        f"Cache-read share looks low across {len(rows)} models. "
                        "Stay sticky on one Flash model per session; switch only at task boundaries."
                    ),
                    "severity": "warn",
                }
            )
        elif cache_hit >= 0.2:
            recs.append(
                {
                    "kind": "cache",
                    "title": "Cache looking healthy",
                    "detail": f"Approx cache-read ratio ~{cache_hit:.0%}. Keep sticky sessions.",
                    "severity": "info",
                }
            )

    # Suggest cheaper OpenRouter alternatives for expensive models
    expensive = [r for r in rows if float(r["cost"] or 0) > 0.01]
    or_latest = conn.execute("SELECT MAX(fetched_at) AS t FROM openrouter_models").fetchone()["t"]
    if or_latest and expensive:
        cheap = conn.execute(
            """
            SELECT model_id, name, prompt_price, completion_price
            FROM openrouter_models
            WHERE fetched_at = ?
              AND prompt_price IS NOT NULL
              AND prompt_price > 0
              AND prompt_price <= 0.0000002
              AND (
                lower(model_id) LIKE '%flash%'
                OR lower(model_id) LIKE '%glm%'
                OR lower(model_id) LIKE '%deepseek%'
                OR lower(model_id) LIKE '%mini%'
              )
            ORDER BY prompt_price ASC
            LIMIT 8
            """,
            (or_latest,),
        ).fetchall()
        if cheap:
            listing = ", ".join(f"{c['model_id']} (${(c['prompt_price'] or 0)*1e6:.3f}/M in)" for c in cheap[:5])
            recs.append(
                {
                    "kind": "pricing",
                    "title": "Cheap agentic candidates on OpenRouter",
                    "detail": listing,
                    "severity": "info",
                }
            )

    top = rows[0] if rows else None
    if top:
        recs.append(
            {
                "kind": "usage",
                "title": f"Top spend model: {top['model']}",
                "detail": (
                    f"~${float(top['cost'] or 0):.4f} | in={top['tin']} out={top['tout']} "
                    f"cache_read={top['cread']} cache_write={top['cwrite']} | total~${total_cost:.4f}"
                ),
                "severity": "info",
            }
        )

    recs.append(
        {
            "kind": "policy",
            "title": "Recommended routing policy",
            "detail": (
                "Daily agenting: z-ai/glm-5.3-flash (sticky). "
                "Alt cheap: deepseek/deepseek-v4-flash. "
                "Hard coding only: bump temporarily, then switch back. "
                "Never switch mid-tool-loop if you care about cache."
            ),
            "severity": "info",
        }
    )

    _save(conn, recs)
    conn.close()
    return recs


def _save(conn, recs: list[dict]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("DELETE FROM recommendations")
    for r in recs:
        conn.execute(
            "INSERT INTO recommendations VALUES (?,?,?,?,?)",
            (now, r["kind"], r["title"], r["detail"], r.get("severity", "info")),
        )
    conn.commit()


def main() -> None:
    recs = build_recommendations()
    for r in recs:
        print(f"[{r['severity']}] {r['title']}\n  {r['detail']}\n")


if __name__ == "__main__":
    main()
