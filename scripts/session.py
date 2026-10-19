"""Provider-neutral coordinator leases, task ownership and durable handoffs."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from autortl.coordination import CoordinationStore, CoordinationError


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    start = sub.add_parser("start")
    start.add_argument("--owner", required=True)
    start.add_argument("--ttl", type=int, default=3600)
    start.add_argument("--takeover-reason")
    renew = sub.add_parser("renew")
    renew.add_argument("--token", required=True)
    renew.add_argument("--ttl", type=int, default=3600)
    claim = sub.add_parser("claim-task")
    claim.add_argument("--token", required=True)
    claim.add_argument("--id", required=True)
    claim.add_argument("--title", required=True)
    claim.add_argument("--owner", required=True)
    claim.add_argument("--files", nargs="+", required=True)
    update = sub.add_parser("update-task")
    update.add_argument("--token", required=True)
    update.add_argument("--id", required=True)
    update.add_argument("--owner", required=True)
    update.add_argument("--state", choices=["active", "blocked", "done"], required=True)
    update.add_argument("--detail", default="")
    update.add_argument("--evidence", action="append", default=[])
    for name in ("checkpoint", "handoff"):
        command = sub.add_parser(name)
        command.add_argument("--token", required=True)
        command.add_argument("--summary", required=True)
        command.add_argument("--next", action="append", required=True)
        command.add_argument("--test", action="append", default=[])
    args = parser.parse_args(argv)
    store = CoordinationStore(ROOT)
    try:
        if args.command == "start":
            print(json.dumps({"token": store.claim(args.owner, args.ttl, args.takeover_reason)}))
        elif args.command == "renew": store.renew(args.token, args.ttl)
        elif args.command == "claim-task": store.claim_task(args.token, args.id, args.title, args.owner, args.files)
        elif args.command == "update-task": store.update_task(args.token, args.id, args.owner, args.state, args.detail, args.evidence)
        elif args.command in ("checkpoint", "handoff"):
            store.checkpoint(args.token, args.summary, getattr(args, "next"), args.test,
                             release=args.command == "handoff")
        else:
            store.export()
            print(json.dumps(store.status(), indent=2))
        return 0
    except CoordinationError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
