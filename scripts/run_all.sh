#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate
# load openrouter key from hermes env if present
if [[ -f /root/.hermes/.env ]]; then
  set -a
  # shellcheck disable=SC1091
  source /root/.hermes/.env
  set +a
fi
python -m src.radar.collect
python -m src.radar.poll_openrouter
python -m src.radar.recommend
echo "Dashboard: streamlit run src/radar/dashboard.py --server.port 8501 --server.address 0.0.0.0"
