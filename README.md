# hermes-model-radar

Upgrade-safe **sidecar** for Hermes Agent: usage/cache/cost analytics, OpenRouter cheap-model board, discount alerts, and optional auto-apply of sticky routing.

## Live
- Dashboard: http://62.238.127.240:8501
- Planning notes: [`docs/planning/`](docs/planning/) (also `/root/HERMES_BIG_PLAN` on the VPS)

## Features
- Collect from Hermes `state.db` (`session_model_usage`, cache tokens, costs)
- Poll OpenRouter model prices
- Recommendations (cache stickiness, cheap alternatives)
- Discount / Flash-class alerts
- Auto-apply sticky GLM Flash + cheap aux/delegation to `~/.hermes/config.yaml`
- Hermes skill for Telegram: `hermes-model-radar`

## CLI
```bash
cd /root/hermes-model-radar
source .venv/bin/activate
export PYTHONPATH=src
set -a; source /root/.hermes/.env; set +a
python -m radar.cli_report report
python -m radar.cli_report alerts
python -m radar.cli_report apply --preview
python -m radar.cli_report apply
```

## Telegram
Ask Hermes things like:
- "Run the model radar cost report"
- "Any OpenRouter discount alerts?"
- "Preview cheap sticky routing"
- "Apply cheap sticky routing"

## Why not fork Hermes?
Weekly upstream updates. This repo stays outside Hermes core so `hermes update` does not wipe your improvements.
