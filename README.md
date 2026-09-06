# hermes-model-radar

Upgrade-safe **sidecar** for [Hermes Agent](https://hermes-agent.nousresearch.com/): deeper usage analytics than OpenRouter's aggregate charts, plus model recommendations that respect **prompt-cache stickiness**.

## Why
People often blame the model when the real issues are:
- bloated context (skills/MCP schemas every turn)
- expensive auxiliary/background models
- mid-task model hopping (kills cache)
- using frontier models for flash-class work

This project reads Hermes `state.db` (sessions + `session_model_usage`) and OpenRouter public pricing to answer:
- tokens / cache-read / cache-write / $ per model
- which task patterns look expensive
- which cheaper models are on the board (and discounted)
- whether you should **stay sticky** on the current model

## Architecture
```
Hermes (stock, updatable)
   └── ~/.hermes/state.db
            │
            ▼
   hermes-model-radar (this repo)
     collector → SQLite metrics mirror
     openrouter poller → live prices
     recommender → sticky + cheap alternatives
     streamlit dashboard
```

Survives `hermes update` because it never patches Hermes core.

## Quick start (VPS)
```bash
cd /root/hermes-model-radar
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.radar.collect
python -m src.radar.poll_openrouter
python -m src.radar.recommend
streamlit run src/radar/dashboard.py --server.port 8501 --server.address 0.0.0.0
```

Optional env:
- `HERMES_HOME` (default `/root/.hermes`)
- `OPENROUTER_API_KEY` (optional; public models list works without it)
- `RADAR_DB` (default `./data/radar.db`)

## Status
MVP: collector + OpenRouter price board + recommendations + dashboard.
