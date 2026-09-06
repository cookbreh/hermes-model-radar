from __future__ import annotations

import os
import subprocess
from pathlib import Path

import yaml

DEFAULT_MODEL = "z-ai/glm-5.3-flash"
ALT_CHEAP = "deepseek/deepseek-v4-flash"
AUX_CHEAP = "deepseek/deepseek-v4-flash"


def hermes_config_path() -> Path:
    home = Path(os.environ.get("HERMES_HOME", "/root/.hermes"))
    return home / "config.yaml"


def preview_routing() -> str:
    data = {
        "model": {
            "default": DEFAULT_MODEL,
            "provider": "openrouter",
            "base_url": "https://openrouter.ai/api/v1",
        },
        "provider_routing": {"sort": "price"},
        "auxiliary": {
            "web_extract": {"provider": "openrouter", "model": AUX_CHEAP},
            "vision": {"provider": "openrouter", "model": AUX_CHEAP},
        },
        "delegation": {"model": ALT_CHEAP},
        "notes": "Sticky main model; cheap aux/subagents; avoid mid-task switches (cache).",
    }
    return yaml.safe_dump(data, sort_keys=False)


def apply_recommended_routing(restart: bool = True) -> str:
    path = hermes_config_path()
    cfg = yaml.safe_load(path.read_text()) if path.exists() else {}
    backup = path.with_suffix(path.suffix + ".bak.radar")
    if path.exists():
        backup.write_text(path.read_text())

    cfg["model"] = {
        "default": DEFAULT_MODEL,
        "provider": "openrouter",
        "base_url": "https://openrouter.ai/api/v1",
    }
    cfg.setdefault("provider_routing", {})
    cfg["provider_routing"]["sort"] = "price"

    aux = cfg.get("auxiliary") or {}
    for key in ("web_extract", "vision"):
        aux[key] = {"provider": "openrouter", "model": AUX_CHEAP}
    cfg["auxiliary"] = aux

    delegation = cfg.get("delegation") or {}
    delegation["model"] = ALT_CHEAP
    cfg["delegation"] = delegation

    path.write_text(yaml.safe_dump(cfg, sort_keys=False))

    msg = f"Updated {path} (backup {backup.name}). Main={DEFAULT_MODEL}, aux/delegation={AUX_CHEAP}."
    if restart:
        subprocess.run(["systemctl", "restart", "hermes-gateway"], check=False)
        msg += " Restarted hermes-gateway."
    return msg


def main() -> None:
    print(preview_routing())
    print(apply_recommended_routing(restart=True))


if __name__ == "__main__":
    main()
