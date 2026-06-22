from __future__ import annotations

import argparse
import json

from .pipeline import bootstrap, build_warehouse, export_outputs, validate_warehouse


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cisco Sales Insights Lab")
    sub = parser.add_subparsers(dest="command", required=True)

    bootstrap_parser = sub.add_parser(
        "bootstrap", help="Generate synthetic data and build warehouse"
    )
    bootstrap_parser.add_argument("--accounts", type=int, default=250)
    bootstrap_parser.add_argument("--assets", type=int, default=25_000)
    bootstrap_parser.add_argument("--seed", type=int, default=42)

    sub.add_parser("build", help="Rebuild warehouse from existing raw CSV files")
    sub.add_parser("export", help="Export AE playbook and audit outputs")
    sub.add_parser("validate", help="Run warehouse invariants")
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "bootstrap":
        path = bootstrap(account_count=args.accounts, asset_count=args.assets, seed=args.seed)
        print(f"Built: {path}")
        print(json.dumps(validate_warehouse(), ensure_ascii=False, indent=2))
    elif args.command == "build":
        path = build_warehouse()
        print(f"Built: {path}")
        print(json.dumps(validate_warehouse(), ensure_ascii=False, indent=2))
    elif args.command == "export":
        for path in export_outputs():
            print(path)
    elif args.command == "validate":
        print(json.dumps(validate_warehouse(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
