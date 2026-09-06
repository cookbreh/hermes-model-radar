---
name: hermes-model-radar
description: Analyze Hermes token/cache/cost usage, OpenRouter discounts, and optionally apply sticky cheap model routing.
version: 0.1.0
author: cookbreh
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [openrouter, cost, cache, models, analytics, routing]
    category: productivity
---

# Hermes Model Radar

Upgrade-safe sidecar analytics for this VPS Hermes install.

## When to Use

- User asks about token costs, cache hits, expensive models, or OpenRouter discounts
- User asks which model to use for agent work on a budget
- User asks to apply cheap sticky routing (GLM Flash + cheap aux)
- User says `/cost`, "cost report", "model radar", "discount alerts"

## Commands (run via terminal)

Working directory: `/root/hermes-model-radar`

```bash
cd /root/hermes-model-radar
source .venv/bin/activate
export PYTHONPATH=src
# load keys
set -a; source /root/.hermes/.env; set +a

python -m radar.cli_report report
python -m radar.cli_report alerts
python -m radar.cli_report apply --preview
python -m radar.cli_report apply
```

Dashboard: `http://62.238.127.240:8501`

## Safety

- Prefer `apply --preview` before applying.
- Applying rewrites `~/.hermes/config.yaml` model/auxiliary/delegation and restarts `hermes-gateway`.
- Do not paste API keys into chat.
