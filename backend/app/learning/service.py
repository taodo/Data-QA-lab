"""Persistent lab sessions and deterministic grading without LLM dependencies."""
from dataclasses import asdict
from datetime import datetime, timezone
import json
import secrets
from uuid import UUID, uuid4

from backend.app.learning.content import LAB_ID
from backend.app.learning.lessons import CATALOG
from backend.app.learning.profiles import PROFILES
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
    text = CATALOG[session["lab_id"]]["ENG"]
    profile = PROFILES[session["lab_id"]]
    payload = {key: session[key] for key in (
        "session_id", "lab_id", "pipeline_run_id", "mode", "status", "hints_used",
        "started_at", "completed_at",
    )}
    payload.update(title=text["title"], requirement=text["requirement"],
                   practice_sql=text["practice_sql"],
                   learning_objectives=text["objectives"], datasets=profile.datasets,
                   result_contract="one non-negative integer column: violation_count",
                   hints=text["hints"][:session["hints_used"]])
    if session["mode"] == "SANDBOX" or session["status"] == "REVEALED":
        payload["scenario_id"] = session["scenario_id"]
    if session["status"] in {"COMPLETED", "REVEALED"}:
        payload.update(solution_sql=profile.solution, explanation=text["explanation"])
    return payload


def start_session(database_url, lab_id=LAB_ID, pipeline_run_id=None, mode="CHALLENGE", scenario=None):
    if lab_id not in PROFILES or mode not in {"CHALLENGE", "SANDBOX"}:
        raise ValueError("Unsupported lab or mode")
    profile = PROFILES[lab_id]
    if scenario is not None and (mode != "SANDBOX" or scenario not in (*profile.scenarios, "clean")):
        raise ValueError("Only SANDBOX can explicitly choose a supported scenario")
    session_id = uuid4()
    schema = "learner_session_" + session_id.hex
    scenario = scenario or secrets.choice(profile.scenarios)
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
        create_session_snapshot(connection, schema, row[0], scenario, lab_id)
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
               WHERE session_id=%s ORDER BY submitted_at DESC,submission_id DESC LIMIT 20""", (session_id,)
        ).fetchall()
        queries = connection.execute(
            """SELECT query_id, sql_text, result, executed_at FROM metadata.lab_queries
               WHERE session_id=%s ORDER BY executed_at DESC,query_id DESC LIMIT 20""", (session_id,)
        ).fetchall()
        counts = connection.execute("SELECT (SELECT COUNT(*) FROM metadata.lab_queries WHERE session_id=%s), (SELECT COUNT(*) FROM metadata.lab_submissions WHERE session_id=%s)", (session_id,session_id)).fetchone()
        simulation = None
        if session["lab_id"]=="lab_010_incremental":
            from backend.app.learning.advanced_workspace import execute
            schema=session["snapshot_schema"]
            as_of=execute(connection,schema,"SELECT as_of FROM {s}.lab_context").fetchone()[0]
            steps=execute(connection,schema,"SELECT step_no,batch_no,operation,execution_status,applied_events,target_rows,watermark FROM {s}.incremental_steps ORDER BY step_no DESC LIMIT 20").fetchall()
            totals=execute(connection,schema,"SELECT COUNT(*),COALESCE(MAX(batch_no),0) FROM {s}.incremental_steps").fetchone()
            simulation={"as_of":as_of,"step_count":totals[0],"batch_no":totals[1],
                        "steps":[dict(zip(("step_no","batch_no","operation","execution_status","applied_events","target_rows","watermark"),row,strict=True)) for row in reversed(steps)]}
    payload = _public(session)
    payload["submissions"] = [dict(zip(
        ("submission_id", "sql", "conclusion", "status", "submitted_at"), row, strict=True
    )) for row in reversed(submissions)]
    payload["queries"] = [dict(zip(("query_id", "sql", "result", "executed_at"), row, strict=True))
                          for row in reversed(queries)]
    payload["query_count"],payload["submission_count"] = counts
    if simulation is not None:
        payload["simulation"]=simulation
    return payload


def history_page(database_url, session_id, kind, offset=0, limit=20):
    from psycopg import sql
    definitions = {
        "queries": ("lab_queries", "query_id,sql_text,result,executed_at", "executed_at", "query_id", ("query_id","sql","result","executed_at")),
        "submissions": ("lab_submissions", "submission_id,sql_text,conclusion,status,submitted_at", "submitted_at", "submission_id", ("submission_id","sql","conclusion","status","submitted_at")),
    }
    if kind not in definitions or not 0 <= offset <= 100000 or not 1 <= limit <= 20:
        raise ValueError("Invalid history page")
    table,fields,timestamp,key,names=definitions[kind]
    with connect(database_url) as connection:
        _get(connection,session_id)
        rows=connection.execute(sql.SQL("SELECT {} FROM metadata.{} WHERE session_id=%s ORDER BY {} DESC,{} DESC LIMIT %s OFFSET %s").format(sql.SQL(fields),sql.Identifier(table),sql.Identifier(timestamp),sql.Identifier(key)),(session_id,limit,offset)).fetchall()
    return [dict(zip(names,row,strict=True)) for row in reversed(rows)]


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
            "hint": CATALOG[session["lab_id"]]["ENG"]["hints"][session["hints_used"] - 1]}


def submit_solution(database_url, session_id, query, conclusion):
    session = _active(database_url, session_id)
    query = normalize_sql(query)
    if not isinstance(conclusion, str) or not conclusion.strip() or len(conclusion.encode("utf-8")) > 4096:
        raise ValueError("A non-empty conclusion of at most 4 KiB is required")
    cases = []
    profile = PROFILES[session["lab_id"]]
    for variant in profile.variants:
        result = run_sql(database_url, session["snapshot_schema"], query, variant)
        oracle = run_sql(database_url, session["snapshot_schema"], profile.solution, variant)
        try:
            expected = violation_count(oracle)
        except ValueError:
            cases.append({"case":variant,"status":"ERROR","count":None,"result":asdict(result)})
            continue
        try:
            count = violation_count(result)
            passed = count == expected
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
                   "PASS": "Your check accepts clean data and detects the documented violations.",
                   "FAIL": "Check the result contract, false positives, missed violations and the exact metric.",
                   "ERROR": "The SQL could not be evaluated. Test syntax, permissions and runtime limits.",
               }[status], "conclusion_grading": "retained_only"}
    if session["mode"] == "SANDBOX":
        payload["cases"] = cases
    if status == "PASS":
        payload.update(solution_sql=profile.solution, explanation=CATALOG[session["lab_id"]]["ENG"]["explanation"])
    return payload


def reveal_solution(database_url, session_id):
    with transaction(database_url) as connection:
        _get(connection, session_id)
        connection.execute(
            """UPDATE metadata.lab_sessions SET status='REVEALED', completed_at=COALESCE(completed_at,%s)
               WHERE session_id=%s AND status='ACTIVE'""", (_now(), session_id)
        )
    return inspect_session(database_url, session_id)


def simulate_session(database_url, session_id, action):
    """Trusted batch actions only; never accept learner DML or arbitrary parameters."""
    from backend.app.learning.advanced_workspace import advance_simulation, execute
    with transaction(database_url) as connection:
        session = _get(connection, session_id)
        if session["lab_id"]!="lab_010_incremental" or session["mode"]!="SANDBOX" or session["status"]!="ACTIVE":
            raise LabStateError("Simulation needs an active incremental SANDBOX")
        step=execute(connection,session["snapshot_schema"],"SELECT COALESCE(MAX(step_no),0) FROM {s}.incremental_steps").fetchone()[0]
        if step>=100 and action!="RESET":
            raise LabStateError("Reset the simulation after 100 steps")
        advance_simulation(connection,session["snapshot_schema"],session["scenario_id"],action)
    return inspect_session(database_url,session_id)
