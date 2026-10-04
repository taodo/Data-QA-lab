"""Data QA Lab command line interface."""
import argparse
from dataclasses import asdict
from datetime import date, datetime
from decimal import Decimal
import json
from pathlib import Path
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
    subparsers.add_parser("fault-list", help="List allowlisted fault scenarios")
    fault_apply = subparsers.add_parser("fault-apply", help="Apply a fault to an isolated workspace")
    fault_apply.add_argument("scenario")
    fault_apply.add_argument("--run-id", type=UUID)
    fault_quality = subparsers.add_parser(
        "fault-quality-run", help="Validate an applied fault workspace"
    )
    fault_quality.add_argument("--fault-run-id", type=UUID, required=True)
    fault_inspect = subparsers.add_parser("fault-inspect", help="Inspect a fault run")
    fault_inspect.add_argument("--fault-run-id", type=UUID)
    fault_reset = subparsers.add_parser("fault-reset", help="Reset an applied fault workspace")
    fault_reset.add_argument("--fault-run-id", type=UUID, required=True)
    subparsers.add_parser("lab-sql-init", help="Harden the dedicated lab database's PUBLIC privileges")
    lab_start = subparsers.add_parser("lab-start", help="Start an executable learning session")
    lab_start.add_argument("lab_id")
    lab_start.add_argument("--run-id", type=UUID)
    lab_start.add_argument("--mode", choices=("CHALLENGE", "SANDBOX"), default="CHALLENGE")
    lab_start.add_argument("--scenario", help="A scenario allowed for the selected SANDBOX lesson")
    for name in ("lab-show", "lab-inspect", "lab-hint", "lab-reveal", "lab-query", "lab-submit"):
        command = subparsers.add_parser(name, help=f"Learning session operation: {name}")
        command.add_argument("--session-id", type=UUID, required=True)
        if name in {"lab-query", "lab-submit"}:
            command.add_argument("--sql-file", type=Path, required=True)
        if name == "lab-submit":
            command.add_argument("--conclusion", required=True)
    account_import = subparsers.add_parser("account-import", help="Preview or explicitly import unclaimed V1 history into a local account")
    account_import.add_argument("--username", required=True)
    account_import.add_argument("--confirm", action="store_true")
    account_reset = subparsers.add_parser("account-reset", help="Operator password recovery with a hidden interactive prompt")
    account_reset.add_argument("--username", required=True)
    return parser

def main() -> None:
    args = build_parser().parse_args()
    if args.command in {"labs", "check", "fault-list"}:
        if args.command == "fault-list":
            from faults.catalog import list_fault_scenarios
            _print([asdict(scenario) for scenario in list_fault_scenarios()])
            return
        labs = load_labs()
        if args.command == "labs":
            _print([asdict(lab) for lab in labs])
        else:
            if not labs:
                raise SystemExit("No lab definitions found")
            print(f"Foundation OK: {len(labs)} lab definition(s).")
        return

    database_url = Settings.from_env().database_url
    if args.command == "account-import":
        from backend.app.accounts import import_legacy
        _print(import_legacy(database_url,args.username,args.confirm))
    elif args.command == "account-reset":
        from getpass import getpass
        from backend.app.accounts import reset_password
        password=getpass("New password (12–128 characters): ")
        if password!=getpass("Repeat new password: "):
            raise SystemExit("Passwords do not match")
        _print(reset_password(database_url,args.username,password))
    elif args.command == "db-init":
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
    elif args.command == "fault-apply":
        from faults.service import apply_fault
        _print(asdict(apply_fault(database_url, args.scenario, args.run_id)))
    elif args.command == "fault-quality-run":
        from faults.service import run_fault_quality
        _print(asdict(run_fault_quality(database_url, args.fault_run_id)))
    elif args.command == "fault-inspect":
        from faults.service import inspect_fault
        result = inspect_fault(database_url, args.fault_run_id)
        if result is None:
            raise SystemExit("No matching fault run found")
        _print(asdict(result))
    elif args.command == "fault-reset":
        from faults.service import reset_fault
        _print(asdict(reset_fault(database_url, args.fault_run_id)))
    elif args.command == "lab-sql-init":
        from backend.app.learning.sql_runtime import initialize_sql_security
        initialize_sql_security(database_url)
        print("Dedicated lab SQL permissions initialized.")
    elif args.command == "lab-start":
        from backend.app.learning.service import start_session
        _print(start_session(database_url, args.lab_id, args.run_id, args.mode, args.scenario))
    elif args.command in {"lab-show", "lab-inspect", "lab-hint", "lab-reveal", "lab-query", "lab-submit"}:
        from backend.app.learning.service import (
            inspect_session, next_hint, reveal_solution, query_session, submit_solution,
        )
        if args.command in {"lab-show", "lab-inspect"}:
            result = inspect_session(database_url, args.session_id)
        elif args.command == "lab-hint":
            result = next_hint(database_url, args.session_id)
        elif args.command == "lab-reveal":
            result = reveal_solution(database_url, args.session_id)
        else:
            if args.sql_file.stat().st_size > 16384:
                raise SystemExit("SQL file exceeds 16 KiB")
            query = args.sql_file.read_text(encoding="utf-8-sig")
            if args.command == "lab-query":
                result = query_session(database_url, args.session_id, query)
            else:
                result = submit_solution(database_url, args.session_id, query, args.conclusion)
        _print(result)

if __name__ == "__main__":
    main()
