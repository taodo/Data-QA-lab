"""Data QA Lab command line interface."""
import argparse
from dataclasses import asdict
from datetime import date, datetime
from decimal import Decimal
import json
from uuid import UUID

from backend.app.config import Settings
from backend.app.services.lab_catalog import load_labs

def _json_default(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (Decimal, UUID)):
        return str(value)
    raise TypeError(f"Cannot serialize {type(value).__name__}")

def _print(payload) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=_json_default))

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Data QA Lab")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("labs", help="List lab definitions")
    subparsers.add_parser("check", help="Validate the local lab catalog")
    subparsers.add_parser("db-init", help="Create Data QA Lab PostgreSQL schemas")
    seed = subparsers.add_parser("seed", help="Load deterministic source data")
    seed.add_argument("--orders", type=int, default=10_000)
    subparsers.add_parser("pipeline-run", help="Run Source through Target")
    inspect = subparsers.add_parser("inspect", help="Inspect a pipeline run")
    inspect.add_argument("--run-id", type=UUID)
    quality_run = subparsers.add_parser("quality-run", help="Run the built-in data quality suite")
    quality_run.add_argument("--run-id", type=UUID)
    quality_inspect = subparsers.add_parser("quality-inspect", help="Inspect the latest quality run")
    quality_inspect.add_argument("--run-id", type=UUID)
    return parser

def main() -> None:
    args = build_parser().parse_args()
    if args.command in {"labs", "check"}:
        labs = load_labs()
        if args.command == "labs":
            _print([asdict(lab) for lab in labs])
        else:
            if not labs:
                raise SystemExit("No lab definitions found")
            print(f"Foundation OK: {len(labs)} lab definition(s).")
        return

    database_url = Settings.from_env().database_url
    if args.command == "db-init":
        from backend.app.persistence.database import initialize_database
        initialize_database(database_url)
        print("Database initialized.")
    elif args.command == "seed":
        from pipeline.source.seed import seed_source
        _print(seed_source(database_url, args.orders))
    elif args.command == "pipeline-run":
        from pipeline.jobs.orders import run_orders_pipeline
        _print(asdict(run_orders_pipeline(database_url)))
    elif args.command == "inspect":
        from pipeline.jobs.orders import inspect_run
        result = inspect_run(database_url, args.run_id)
        if result is None:
            raise SystemExit("No matching pipeline run found")
        _print(result)
    elif args.command == "quality-run":
        from qa.engine.runner import run_quality_suite
        _print(asdict(run_quality_suite(database_url, args.run_id)))
    elif args.command == "quality-inspect":
        from qa.engine.runner import inspect_quality_run
        result = inspect_quality_run(database_url, args.run_id)
        if result is None:
            raise SystemExit("No matching quality run found")
        _print(result)

if __name__ == "__main__":
    main()
