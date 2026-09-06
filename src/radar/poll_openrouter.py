from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import httpx

from .db import connect


FLASH_HINTS = ("flash", "mini", "nano", "small", "haiku", "lite")
CODING_HINTS = ("coder", "code", "glm", "deepseek", "qwen", "kimi", "minimax", "sonnet")


def fetch_models() -> list[dict]:
    headers = {"User-Agent": "hermes-model-radar/0.1"}
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        headers["Authorization"] = f"Bearer {key}"
    with httpx.Client(timeout=60) as client:
        r = client.get("https://openrouter.ai/api/v1/models", headers=headers)
        r.raise_for_status()
        return r.json().get("data", [])


def _price(val) -> float | None:
    if val is None or val == "":
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def store_models(models: list[dict]) -> int:
    now = datetime.now(timezone.utc).isoformat()
    conn = connect()
    n = 0
    for m in models:
        mid = m.get("id") or ""
        pricing = m.get("pricing") or {}
        conn.execute(
            """
            INSERT OR REPLACE INTO openrouter_models VALUES (?,?,?,?,?,?,?,?,?,?)
            """,
            (
                now,
                mid,
                m.get("name"),
                m.get("context_length"),
                _price(pricing.get("prompt")),
                _price(pricing.get("completion")),
                _price(pricing.get("input_cache_read")),
                _price(pricing.get("input_cache_write")),
                1 if (_price(pricing.get("prompt")) == 0 and _price(pricing.get("completion")) == 0) else 0,
                json.dumps(m)[:20000],
            ),
        )
        n += 1
    conn.commit()
    conn.close()
    return n


def main() -> None:
    models = fetch_models()
    n = store_models(models)
    cheap = [
        m
        for m in models
        if (m.get("pricing") or {}).get("prompt") is not None
        and float((m.get("pricing") or {}).get("prompt") or 99) <= 0.0000003  # ~$0.30/M
    ]
    print(f"Stored {n} OpenRouter models; ~{len(cheap)} look cheap on prompt price")


if __name__ == "__main__":
    main()
