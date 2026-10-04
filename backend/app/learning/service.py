"""Persistent lab sessions and deterministic grading without LLM dependencies."""
from dataclasses import asdict
from datetime import datetime, timezone
import json
import secrets
from uuid import UUID, uuid4

from backend.app.learning.content import LAB_ID, HINTS, SOLUTION, EXPLANATION
from backend.app.learning.contracts import LabStateError, normalize_sql, violation_count
from backend.app.learning.sql_runtime import run_sql
from backend.app.learning.workspace import create_session_snapshot, TABLES
from backend.app.persistence.database import connect, transaction
from backend.app.services.lab_catalog import load_labs


def _now():
    return datetime.now(timezone.utc)


def _get(connection, session_id):
    row = connection.execute(
        """SELECT session_id, lab_id, pipeline_run_id, mode, status, scenario_id,
                  snapshot_schema, hints_used, started_at, completed_at
           FROM metadata.lab_sessions WHERE session_id=%s""", (session_id,)
    ).fetchone()
    if row is None:
        raise LabStateError("No matching lab session")
    return dict(zip(("session_id", "lab_id", "pipeline_run_id", "mode", "status", "scenario_id",
                     "snapshot_schema", "hints_used", "started_at", "completed_at"), row, strict=True))


def _public(session):
    lab = next(lab for lab in load_labs() if lab.id == session["lab_id"])
    payload = {key: session[key] for key in (
        "session_id", "lab_id", "pipeline_run_id", "mode", "status", "hints_used",
        "started_at", "completed_at",
    )}
    payload.update(title=lab.title, requirement=lab.requirement,
                   learning_objectives=lab.learning_objectives, datasets=TABLES,
                   result_contract="one non-negative integer column: violation_count",
                   hints=HINTS[:session["hints_used"]])
    if session["mode"] == "SANDBOX" or session["status"] == "REVEALED":
        payload["scenario_id"] = session["scenario_id"]
    if session["status"] in {"COMPLETED", "REVEALED"}:
        payload.update(solution_sql=SOLUTION, explanation=EXPLANATION)
    return payload


def start_session(database_url, lab_id=LAB_ID, pipeline_run_id=None, mode="CHALLENGE", scenario=None):
    if lab_id != LAB_ID or mode not in {"CHALLENGE", "SANDBOX"}:
        raise ValueError("Unsupported lab or mode")
    if scenario is not None and (mode != "SANDBOX" or scenario not in {"missing_order", "equal_count_swap"}):
        raise ValueError("Only SANDBOX can explicitly choose a supported scenario")
    session_id = uuid4()
    schema = "learner_session_" + session_id.hex
    scenario = scenario or secrets.choice(("missing_order", "equal_count_swap"))
    with transaction(database_url) as connection:
        if pipeline_run_id is None:
            row = connection.execute(
                """SELECT run_id FROM metadata.pipeline_runs WHERE execution_status='SUCCESS'
                   AND pipeline_id='orders_v1' ORDER BY started_at DESC LIMIT 1"""
            ).fetchone()
        else:
            row = connection.execute(
                """SELECT run_id FROM metadata.pipeline_runs WHERE run_id=%s
                   AND execution_status='SUCCESS' AND pipeline_id='orders_v1'""", (pipeline_run_id,)
            ).fetchone()
        if row is None:
            raise LabStateError("Run the orders pipeline successfully before starting a lab")
        create_session_snapshot(connection, schema, row[0], scenario)
        connection.execute(
            """INSERT INTO metadata.lab_sessions
               (session_id, lab_id, pipeline_run_id, mode, status, scenario_id, snapshot_schema, started_at)
               VALUES (%s,%s,%s,%s,'ACTIVE',%s,%s,%s)""",
            (session_id, lab_id, row[0], mode, scenario, schema, _now()),
        )
    return inspect_session(database_url, session_id)


def inspect_session(database_url, session_id):
    with connect(database_url) as connection:
        session = _get(connection, session_id)
        submissions = connection.execute(
            """SELECT submission_id, sql_text, conclusion, status, submitted_at FROM metadata.lab_submissions
               WHERE session_id=%s ORDER BY submitted_at""", (session_id,)
        ).fetchall()
        queries = connection.execute(
            """SELECT query_id, sql_text, result, executed_at FROM metadata.lab_queries
               WHERE session_id=%s ORDER BY executed_at""", (session_id,)
        ).fetchall()
    payload = _public(session)
    payload["submissions"] = [dict(zip(
        ("submission_id", "sql", "conclusion", "status", "submitted_at"), row, strict=True
    )) for row in submissions]
    payload["queries"] = [dict(zip(("query_id", "sql", "result", "executed_at"), row, strict=True))
                          for row in queries]
    return payload


def _active(database_url, session_id):
    with connect(database_url) as connection:
        session = _get(connection, session_id)
    if session["status"] != "ACTIVE":
        raise LabStateError("Session is not ACTIVE; start a new session to submit again")
    return session


def query_session(database_url, session_id, query):
    session = _active(database_url, session_id)
    query = normalize_sql(query)
    result = asdict(run_sql(database_url, session["snapshot_schema"], query))
    query_id = uuid4()
    with transaction(database_url) as connection:
        connection.execute(
            """INSERT INTO metadata.lab_queries (query_id, session_id, sql_text, result, executed_at)
               VALUES (%s,%s,%s,%s::jsonb,%s)""",
            (query_id, session_id, query, json.dumps(result), _now()),
        )
    return {"query_id": query_id, **result}


def next_hint(database_url, session_id):
    _active(database_url, session_id)
    with transaction(database_url) as connection:
        connection.execute(
            """UPDATE metadata.lab_sessions SET hints_used=LEAST(hints_used+1,3)
               WHERE session_id=%s AND status='ACTIVE'""", (session_id,)
        )
        session = _get(connection, session_id)
    return {"session_id": session_id, "level": session["hints_used"],
            "hint": HINTS[session["hints_used"] - 1]}


def submit_solution(database_url, session_id, query, conclusion):
    session = _active(database_url, session_id)
    query = normalize_sql(query)
    if not isinstance(conclusion, str) or not conclusion.strip() or len(conclusion.encode("utf-8")) > 4096:
        raise ValueError("A non-empty conclusion of at most 4 KiB is required")
    cases = []
    for variant in ("clean", "clean_subset", "missing", "swapped"):
        result = run_sql(database_url, session["snapshot_schema"], query, variant)
        try:
            count = violation_count(result)
            passed = (count == 0) if variant.startswith("clean") else (count > 0)
            status = "PASS" if passed else "FAIL"
        except ValueError:
            count = None
            status = "ERROR" if result.status == "ERROR" else "FAIL"
        cases.append({"case": variant, "status": status, "count": count, "result": asdict(result)})
    statuses = {case["status"] for case in cases}
    status = "ERROR" if "ERROR" in statuses else "FAIL" if "FAIL" in statuses else "PASS"
    submission_id = uuid4()
    with transaction(database_url) as connection:
        if _get(connection, session_id)["status"] != "ACTIVE":
            raise LabStateError("Session state changed during grading")
        connection.execute(
            """INSERT INTO metadata.lab_submissions
               (submission_id,session_id,sql_text,conclusion,status,private_results,submitted_at)
               VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s)""",
            (submission_id, session_id, query, conclusion.strip(), status, json.dumps(cases), _now()),
        )
        if status == "PASS":
            connection.execute(
                "UPDATE metadata.lab_sessions SET status='COMPLETED',completed_at=%s WHERE session_id=%s",
                (_now(), session_id),
            )
    payload = {"submission_id": submission_id, "session_id": session_id, "status": status,
               "feedback": {
                   "PASS": "Your check accepts clean data and detects completeness defects.",
                   "FAIL": "Check the result contract, false positives and missed key differences.",
                   "ERROR": "The SQL could not be evaluated. Test syntax, permissions and runtime limits.",
               }[status], "conclusion_grading": "retained_only"}
    if session["mode"] == "SANDBOX":
        payload["cases"] = cases
    if status == "PASS":
        payload.update(solution_sql=SOLUTION, explanation=EXPLANATION)
    return payload


def reveal_solution(database_url, session_id):
    with transaction(database_url) as connection:
        _get(connection, session_id)
        connection.execute(
            """UPDATE metadata.lab_sessions SET status='REVEALED', completed_at=COALESCE(completed_at,%s)
               WHERE session_id=%s AND status='ACTIVE'""", (_now(), session_id)
        )
    return inspect_session(database_url, session_id)
