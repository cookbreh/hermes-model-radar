#!/usr/bin/env bash
set -euo pipefail
cd /root/hermes-model-radar
source .venv/bin/activate
export PYTHONPATH=src
set -a; source /root/.hermes/.env; set +a
python -m radar.cli_report "$@"
