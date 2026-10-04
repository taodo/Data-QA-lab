"""Local single-user API. Arbitrary SQL goes only through the restricted runtime."""
from dataclasses import asdict
from decimal import Decimal
import json
from threading import Lock
from typing import Literal
from uuid import UUID

import psycopg
from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from backend.app.config import Settings
from backend.app.learning.contracts import LabStateError, SqlSecurityError
from backend.app.learning.lessons import CATALOG, lesson, localize_session
from backend.app.learning import service
from backend.app.persistence.database import connect

Language = Literal["ENG", "VIE"]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Start(Input):
    lab_id: str
    run_id: UUID | None = None
    mode: Literal["CHALLENGE", "SANDBOX"] = "CHALLENGE"
    scenario: str | None = None


class Query(Input):
    sql: str = Field(min_length=1, max_length=16384)


class Submit(Query):
    conclusion: str = Field(min_length=1, max_length=4096)


class Fault(Input):
    scenario: Literal["missing_order", "duplicate_order", "null_net_amount", "wrong_net_amount"]
    run_id: UUID


def response(data, status=200):
    return JSONResponse(jsonable_encoder(data, custom_encoder={Decimal: str}), status_code=status)


class BodyLimit:
    """Bound bytes before parsing JSON, including requests without Content-Length."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        messages, size = [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > 65536:
                return await response({"error": {"code": "BODY_LIMIT"}}, 413)(scope, receive, send)
            messages.append(message)
            if not message.get("more_body", False):
                break
        async def bounded_receive():
            return messages.pop(0) if messages else await receive()
        await self.app(scope, bounded_receive, send)


def create_app(database_url=None):
    app = FastAPI(title="Data QA Lab", version="0.8.0")
    db = database_url or Settings.from_env().database_url
    gate = Lock()
    app.add_middleware(BodyLimit)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver"])

    @app.middleware("http")
    async def origin_guard(request, call_next):
        origin = request.headers.get("origin")
        if request.method not in {"GET", "HEAD", "OPTIONS"} and origin and origin != str(request.base_url).rstrip("/"):
            return response({"error": {"code": "ORIGIN_DENIED"}}, 403)
        return await call_next(request)

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        return response({"error": {"code": "INVALID_INPUT"}}, 422)

    @app.exception_handler(LabStateError)
    async def state_error(request, exc):
        code = "NOT_FOUND" if str(exc) == "No matching lab session" else "STATE_CONFLICT"
        return response({"error": {"code": code}}, 404 if code == "NOT_FOUND" else 409)

    @app.exception_handler(ValueError)
    async def bad_input(request, exc):
        return response({"error": {"code": "INVALID_INPUT"}}, 422)

    @app.exception_handler(SqlSecurityError)
    async def unsafe(request, exc):
        return response({"error": {"code": "SQL_SECURITY_SETUP"}}, 503)

    @app.exception_handler(psycopg.Error)
    async def database_error(request, exc):
        return response({"error": {"code": "DATABASE_UNAVAILABLE"}}, 503)

    def mutate(function, *args):
        if not gate.acquire(blocking=False):
            raise HTTPException(409, detail="OPERATION_BUSY")
        try:
            return function(*args)
        finally:
            gate.release()

    @app.get("/api/health")
    def health():
        with connect(db) as connection:
            connection.execute("SELECT 1")
        return {"status": "READY", "version": app.version}

    @app.get("/api/lessons")
    def lessons(language: Language = "VIE"):
        return [lesson(key, language) for key in sorted(CATALOG, key=lambda key: CATALOG[key]["order"])]

    @app.get("/api/lessons/{lab_id}")
    def get_lesson(lab_id: str, language: Language = "VIE"):
        if lab_id not in CATALOG:
            raise HTTPException(404, detail="NOT_FOUND")
        return lesson(lab_id, language)

    @app.get("/api/sessions")
    def sessions():
        with connect(db) as connection:
            rows = connection.execute("SELECT session_id,lab_id,mode,status,hints_used,started_at,completed_at FROM metadata.lab_sessions ORDER BY started_at DESC LIMIT 200").fetchall()
        return response([dict(zip(("session_id", "lab_id", "mode", "status", "hints_used", "started_at", "completed_at"), row, strict=True)) for row in rows])

    @app.get("/api/progress")
    def progress():
        with connect(db) as connection:
            rows = connection.execute("SELECT lab_id,COUNT(*),BOOL_OR(status='COMPLETED') FROM metadata.lab_sessions GROUP BY lab_id").fetchall()
        return [{"lab_id": row[0], "attempts": row[1], "completed": row[2]} for row in rows]

    @app.post("/api/sessions", status_code=201)
    def start(body: Start, language: Language = "VIE"):
        result = mutate(service.start_session, db, body.lab_id, body.run_id, body.mode, body.scenario)
        return response(localize_session(result, language), 201)

    @app.get("/api/sessions/{session_id}")
    def session(session_id: UUID, language: Language = "VIE"):
        return response(localize_session(service.inspect_session(db, session_id), language))

    @app.post("/api/sessions/{session_id}/query")
    def query(session_id: UUID, body: Query):
        return response(mutate(service.query_session, db, session_id, body.sql))

    @app.post("/api/sessions/{session_id}/submit")
    def submit(session_id: UUID, body: Submit, language: Language = "VIE"):
        result = mutate(service.submit_solution, db, session_id, body.sql, body.conclusion)
        result["feedback_code"] = result["status"]
        # UI translates this stable code; do not ship an English fallback as VIE.
        result.pop("feedback", None)
        if "explanation" in result:
            sid = service.inspect_session(db, session_id)
            result["explanation"] = CATALOG[sid["lab_id"]][language]["explanation"]
        return response(result)

    @app.post("/api/sessions/{session_id}/hint")
    def hint(session_id: UUID, language: Language = "VIE"):
        result = mutate(service.next_hint, db, session_id)
        sid = service.inspect_session(db, session_id)
        result["hint"] = CATALOG[sid["lab_id"]][language]["hints"][result["level"]-1]
        return response(result)

    @app.post("/api/sessions/{session_id}/reveal")
    def reveal(session_id: UUID, language: Language = "VIE"):
        return response(localize_session(mutate(service.reveal_solution, db, session_id), language))

    @app.get("/api/runs")
    def runs():
        with connect(db) as connection:
            rows = connection.execute("SELECT run_id,execution_status,data_quality_status,started_at,completed_at FROM metadata.pipeline_runs ORDER BY started_at DESC LIMIT 100").fetchall()
        return response([dict(zip(("run_id", "execution_status", "data_quality_status", "started_at", "completed_at"), row, strict=True)) for row in rows])

    @app.get("/api/runs/{run_id}")
    def run(run_id: UUID):
        from pipeline.jobs.orders import inspect_run
        result = inspect_run(db, run_id)
        if result is None:
            raise HTTPException(404, detail="NOT_FOUND")
        return response(result)

    @app.post("/api/runs")
    def pipeline():
        from pipeline.jobs.orders import run_orders_pipeline
        return response(asdict(mutate(run_orders_pipeline, db)))

    @app.get("/api/runs/{run_id}/quality")
    def quality(run_id: UUID):
        from qa.engine.runner import inspect_quality_run
        return response(inspect_quality_run(db, run_id))

    @app.post("/api/runs/{run_id}/quality")
    def quality_start(run_id: UUID):
        from qa.engine.runner import run_quality_suite
        return response(asdict(mutate(run_quality_suite, db, run_id)))

    @app.get("/api/faults")
    def faults():
        with connect(db) as connection:
            rows = connection.execute("SELECT fault_run_id FROM metadata.fault_runs ORDER BY applied_at DESC LIMIT 50").fetchall()
        from faults.service import inspect_fault
        return response([asdict(inspect_fault(db, row[0])) for row in rows])

    @app.post("/api/faults")
    def fault(body: Fault):
        from faults.service import apply_fault
        return response(asdict(mutate(apply_fault, db, body.scenario, body.run_id)))

    @app.post("/api/faults/{fault_id}/quality")
    def fault_quality(fault_id: UUID):
        from faults.service import run_fault_quality
        return response(asdict(mutate(run_fault_quality, db, fault_id)))

    @app.post("/api/faults/{fault_id}/reset")
    def fault_reset(fault_id: UUID):
        from faults.service import reset_fault
        return response(asdict(mutate(reset_fault, db, fault_id)))

    # Frontend is built locally or in the container. No external CDN assets.
    from pathlib import Path
    from fastapi.staticfiles import StaticFiles
    frontend = Path(__file__).resolve().parents[3] / "frontend" / "dist"
    if frontend.is_dir():
        app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")
    return app


app = create_app()
