from __future__ import annotations

import argparse
import json

from .alerts import check_discount_alerts
from .apply import apply_recommended_routing, preview_routing
from .collect import snapshot_usage
from .poll_openrouter import fetch_models, store_models
from .recommend import build_recommendations


def cmd_report(_: argparse.Namespace) -> None:
    snapshot_usage()
    store_models(fetch_models())
    recs = build_recommendations()
    print("=== Hermes Model Radar Report ===")
    for r in recs:
        print(f"[{r['severity']}] {r['title']}\n  {r['detail']}\n")


def cmd_alerts(_: argparse.Namespace) -> None:
    for a in check_discount_alerts():
        print(f"{a['title']}: {a['detail']}")


def cmd_apply(args: argparse.Namespace) -> None:
    if args.preview:
        print(preview_routing())
        return
    print(apply_recommended_routing(restart=not args.no_restart))


def main() -> None:
    p = argparse.ArgumentParser(prog="radar")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("report", help="Collect + recommend")
    s.set_defaults(func=cmd_report)

    s = sub.add_parser("alerts", help="Discount / cheap flash alerts")
    s.set_defaults(func=cmd_alerts)

    s = sub.add_parser("apply", help="Apply sticky cheap routing to Hermes config")
    s.add_argument("--preview", action="store_true")
    s.add_argument("--no-restart", action="store_true")
    s.set_defaults(func=cmd_apply)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
