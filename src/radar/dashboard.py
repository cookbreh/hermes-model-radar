from __future__ import annotations

import sys
from pathlib import Path

# Streamlit runs this file as a script — make package imports work.
_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import pandas as pd
import streamlit as st

from radar.collect import snapshot_usage
from radar.db import connect
from radar.poll_openrouter import fetch_models, store_models
from radar.recommend import build_recommendations
from radar.apply import apply_recommended_routing, preview_routing
from radar.alerts import check_discount_alerts, list_recent_alerts


st.set_page_config(page_title="Hermes Model Radar", layout="wide")
st.title("Hermes Model Radar")
st.caption("Upgrade-safe sidecar · usage + cache + OpenRouter prices · sticky-model advice")

cols = st.columns(4)
with cols[0]:
    if st.button("Refresh Hermes usage"):
        result = snapshot_usage()
        st.success(f"Collected {result['usage_rows']} usage rows")
with cols[1]:
    if st.button("Refresh OpenRouter prices"):
        n = store_models(fetch_models())
        st.success(f"Stored {n} models")
with cols[2]:
    if st.button("Rebuild recommendations"):
        recs = build_recommendations()
        st.success(f"{len(recs)} recommendations")
with cols[3]:
    if st.button("Check discount alerts"):
        alerts = check_discount_alerts()
        st.success(f"{len(alerts)} alert(s)")

conn = connect()

st.subheader("Recommendations")
recs = pd.read_sql_query(
    "SELECT severity, kind, title, detail, created_at FROM recommendations ORDER BY created_at DESC",
    conn,
)
if recs.empty:
    st.info("No recommendations yet — click the refresh buttons above.")
else:
    for _, row in recs.iterrows():
        st.markdown(f"**[{row['severity']}] {row['title']}**  \n{row['detail']}")

st.subheader("Auto-apply routing (safe defaults)")
st.code(preview_routing(), language="yaml")
c1, c2 = st.columns(2)
with c1:
    if st.button("Apply sticky GLM Flash routing to Hermes"):
        out = apply_recommended_routing(restart=True)
        st.success(out)
with c2:
    st.caption("Writes ~/.hermes/config.yaml model + auxiliary cheap models, then restarts hermes-gateway.")

st.subheader("Discount / price alerts")
alerts = list_recent_alerts()
if not alerts:
    st.info("No alerts yet — click Check discount alerts.")
else:
    for a in alerts:
        st.markdown(f"- **{a['title']}**: {a['detail']}")

st.subheader("Usage by model (latest snapshot)")
latest = conn.execute("SELECT MAX(snapshot_at) FROM usage_by_model").fetchone()[0]
if latest:
    usage = pd.read_sql_query(
        """
        SELECT model,
               SUM(input_tokens) AS input_tokens,
               SUM(output_tokens) AS output_tokens,
               SUM(cache_read_tokens) AS cache_read,
               SUM(cache_write_tokens) AS cache_write,
               SUM(COALESCE(actual_cost_usd, estimated_cost_usd, 0)) AS cost_usd
        FROM usage_by_model
        WHERE snapshot_at = ?
        GROUP BY model
        ORDER BY cost_usd DESC
        """,
        conn,
        params=(latest,),
    )
    st.dataframe(usage, use_container_width=True)
else:
    st.warning("No usage snapshot yet.")

st.subheader("Sessions")
sess_latest = conn.execute("SELECT MAX(snapshot_at) FROM sessions_snapshot").fetchone()[0]
if sess_latest:
    sessions = pd.read_sql_query(
        """
        SELECT session_id, source, model, message_count, tool_call_count,
               input_tokens, output_tokens, cache_read_tokens, cache_write_tokens,
               estimated_cost_usd, started_at, title
        FROM sessions_snapshot
        WHERE snapshot_at = ?
        ORDER BY started_at DESC
        LIMIT 50
        """,
        conn,
        params=(sess_latest,),
    )
    st.dataframe(sessions, use_container_width=True)

st.subheader("OpenRouter cheap / flash-ish board")
or_latest = conn.execute("SELECT MAX(fetched_at) FROM openrouter_models").fetchone()[0]
if or_latest:
    board = pd.read_sql_query(
        """
        SELECT model_id, name,
               prompt_price * 1000000 AS usd_per_m_input,
               completion_price * 1000000 AS usd_per_m_output,
               input_cache_read_price * 1000000 AS usd_per_m_cache_read,
               context_length, is_free
        FROM openrouter_models
        WHERE fetched_at = ?
          AND prompt_price IS NOT NULL
          AND (
            prompt_price = 0
            OR prompt_price <= 0.00000025
            OR lower(model_id) LIKE '%flash%'
            OR lower(model_id) LIKE '%glm-5.3-flash%'
            OR lower(model_id) LIKE '%deepseek-v4-flash%'
          )
        ORDER BY prompt_price ASC
        LIMIT 40
        """,
        conn,
        params=(or_latest,),
    )
    st.dataframe(board, use_container_width=True)
else:
    st.info("Refresh OpenRouter prices to populate the board.")

st.markdown("---")
st.markdown("Cache tip: switching models mid-task usually resets prompt cache. Stay sticky per session.")
conn.close()
