from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from radar.alerts import check_discount_alerts
from radar.collect import snapshot_usage
from radar.db import connect
from radar.poll_openrouter import fetch_models, store_models
from radar.recommend import build_recommendations


st.set_page_config(page_title="Hermes Model Radar", layout="wide")

auto = st.sidebar.toggle("Auto-refresh", value=True)
interval_min = st.sidebar.slider("Every (minutes)", 1, 30, 5)
if auto:
    st_autorefresh(interval=interval_min * 60 * 1000, key="radar_ar")
if st.sidebar.button("Refresh now"):
    st.rerun()

st.title("Hermes Model Radar")

# Quiet data refresh on each load / auto-refresh tick
err = None
try:
    snapshot_usage()
    store_models(fetch_models())
    build_recommendations()
    if auto:
        check_discount_alerts()
except Exception as e:
    err = str(e)
if err:
    st.sidebar.error(err)

conn = connect()

latest = conn.execute("SELECT MAX(snapshot_at) FROM usage_by_model").fetchone()[0]
k1, k2, k3, k4 = st.columns(4)
if latest:
    agg = conn.execute(
        """
        SELECT
          SUM(input_tokens) AS tin,
          SUM(output_tokens) AS tout,
          SUM(cache_read_tokens) AS cread,
          SUM(COALESCE(actual_cost_usd, estimated_cost_usd, 0)) AS cost
        FROM usage_by_model WHERE snapshot_at = ?
        """,
        (latest,),
    ).fetchone()
    tin = int(agg["tin"] or 0)
    tout = int(agg["tout"] or 0)
    cread = int(agg["cread"] or 0)
    cost = float(agg["cost"] or 0)
    cache_ratio = cread / max(tin + cread, 1)
    k1.metric("Est. cost", f"${cost:.4f}")
    k2.metric("Input tokens", f"{tin:,}")
    k3.metric("Output tokens", f"{tout:,}")
    k4.metric("Cache-read ratio", f"{cache_ratio:.0%}")
else:
    k1.metric("Est. cost", "—")
    k2.metric("Input tokens", "—")
    k3.metric("Output tokens", "—")
    k4.metric("Cache-read ratio", "—")

c1, c2 = st.columns(2)
with c1:
    st.subheader("Cost by model")
    if latest:
        usage = pd.read_sql_query(
            """
            SELECT model,
                   SUM(COALESCE(actual_cost_usd, estimated_cost_usd, 0)) AS cost_usd
            FROM usage_by_model
            WHERE snapshot_at = ?
            GROUP BY model
            ORDER BY cost_usd DESC
            """,
            conn,
            params=(latest,),
        )
        if not usage.empty:
            st.bar_chart(usage.set_index("model"))
        else:
            st.caption("No usage yet")
    else:
        st.caption("No usage yet")

with c2:
    st.subheader("Tokens by model")
    if latest:
        tokens = pd.read_sql_query(
            """
            SELECT model,
                   SUM(input_tokens) AS input,
                   SUM(output_tokens) AS output,
                   SUM(cache_read_tokens) AS cache_read
            FROM usage_by_model
            WHERE snapshot_at = ?
            GROUP BY model
            """,
            conn,
            params=(latest,),
        )
        if not tokens.empty:
            st.bar_chart(tokens.set_index("model"))
        else:
            st.caption("No usage yet")
    else:
        st.caption("No usage yet")

st.subheader("Cache vs fresh input")
if latest:
    cache_df = pd.read_sql_query(
        """
        SELECT model,
               SUM(input_tokens) AS fresh_input,
               SUM(cache_read_tokens) AS cache_read,
               SUM(cache_write_tokens) AS cache_write
        FROM usage_by_model
        WHERE snapshot_at = ?
        GROUP BY model
        """,
        conn,
        params=(latest,),
    )
    if not cache_df.empty:
        st.bar_chart(cache_df.set_index("model"))

# Compact one-line signals only
recs = pd.read_sql_query(
    "SELECT severity, title FROM recommendations ORDER BY created_at DESC LIMIT 4",
    conn,
)
if not recs.empty:
    st.caption(" · ".join(f"{r.severity}: {r.title}" for r in recs.itertuples()))

st.subheader("OpenRouter prices")
or_latest = conn.execute("SELECT MAX(fetched_at) FROM openrouter_models").fetchone()[0]
if or_latest:
    board = pd.read_sql_query(
        """
        SELECT model_id,
               ROUND(prompt_price * 1000000, 4) AS usd_per_m_in,
               ROUND(completion_price * 1000000, 4) AS usd_per_m_out,
               ROUND(COALESCE(input_cache_read_price, 0) * 1000000, 4) AS usd_per_m_cache_read,
               context_length,
               is_free
        FROM openrouter_models
        WHERE fetched_at = ?
          AND prompt_price IS NOT NULL
          AND (
            prompt_price = 0
            OR prompt_price <= 0.00000025
            OR lower(model_id) LIKE '%flash%'
            OR lower(model_id) LIKE '%glm%'
            OR lower(model_id) LIKE '%deepseek%'
          )
        ORDER BY prompt_price ASC
        LIMIT 50
        """,
        conn,
        params=(or_latest,),
    )
    st.caption(f"Updated {or_latest}")
    st.dataframe(board, use_container_width=True, height=420)
else:
    st.caption("No price snapshot yet")

conn.close()
