# Master Plan — Hermes Model Intelligence + Audience

Date saved: 2026-09-07
Owner: cookbreh (GitHub) / Hermes on Hetzner VPS 62.238.127.240

## Stack already live
- Hetzner CX23 Ubuntu VPS, Hermes Agent v0.21.0 gateway (Telegram + Discord tokens)
- OpenRouter pay-as-you-go, default model `z-ai/glm-5.3-flash`, `provider_routing.sort=price`
- Weekly OpenRouter credit limit ~$10
- GitHub CLI on VPS authenticated as **cookbreh**
- This repo: https://github.com/cookbreh/hermes-model-radar
- Dashboard: http://62.238.127.240:8501

## Core problem we are solving
OpenRouter aggregate stats are not enough. We want per-session/task:
- input/output/cache tokens and $
- whether the model fits the task
- discounts / cheap alternatives
- an agent that can recommend and apply routing changes
- all without forking Hermes (weekly updates would wipe forks)

## Phases
### Phase 1 — MVP (DONE / expanding)
Sidecar radar: collect from Hermes state.db, OpenRouter prices, recommendations, Streamlit UI.

### Phase 1b — Agent actions (IN PROGRESS)
- Telegram skill `hermes-model-radar`
- Auto-apply sticky cheap routing
- Discount alerts

### Phase 2 — Live market board polish
Track promo/discount deltas over time, Telegram push when watchlist models get cheaper.

### Phase 3 — Package for other Hermes users
Plugin packaging + docs “survives hermes update”.

### Phase 4 — Audience system
Draft LinkedIn + X posts from weekly cost reports; manual publish first.

## Design rules
- Never patch Hermes core; only ~/.hermes config, skills, plugins, sidecars
- Sticky model per session to protect prompt cache
- Cheap auxiliary + delegation models
- Keep monthly spend under casual budget (~$10/week key limit)

## Non-goals (MVP)
- Fork Hermes
- Full LinkedIn API auto-posting
- Training custom models
