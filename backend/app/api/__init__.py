"""Local account-scoped API. Arbitrary SQL goes only through the restricted runtime."""
from dataclasses import asdict
from decimal import Decimal
import json
from threading import Lock
from typing import Literal
from uuid import UUID

import psycopg
from fastapi import FastAPI, HTTPException, Request, Depends, Query as QueryParameter
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from backend.app.config import Settings
from faults.contracts import FaultStateError
from backend.app.learning.contracts import LabStateError, SqlSecurityError
from backend.app.learning.lessons import CATALOG, lesson, localize_session, course_id
from backend.app.learning import service
from backend.app.persistence.database import connect, transaction
from backend.app import accounts, courses as curriculum

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


class Simulation(Input):
    action: Literal["RESET", "NEXT", "REPLAY", "RUN", "RECOVER"]


class EvidenceImport(Input):
    filename: str = Field(min_length=1, max_length=80)
    file_format: Literal["json", "csv"]
    content: str = Field(min_length=1, max_length=49152)


class Login(Input):
    username: str = Field(min_length=3,max_length=32,pattern=r"^[A-Za-z0-9_]+$")
    password: str = Field(min_length=12,max_length=128)


class Signup(Login):
    display_name: str = Field(min_length=1,max_length=80)


class PasswordChange(Input):
    current_password: str = Field(min_length=1,max_length=128)
    new_password: str = Field(min_length=12,max_length=128)


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
    app = FastAPI(title="Data QA Lab", version="1.4.0")
    db = database_url or Settings.from_env().database_url
    gate = Lock()
    app.add_middleware(BodyLimit)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver"])

    @app.middleware("http")
    async def origin_guard(request, call_next):
        origin = request.headers.get("origin")
        if request.method not in {"GET", "HEAD", "OPTIONS"} and ((origin and origin != str(request.base_url).rstrip("/")) or request.headers.get("sec-fetch-site")=="cross-site"):
            return response({"error": {"code": "ORIGIN_DENIED"}}, 403)
        result = await call_next(request)
        result.headers["X-Content-Type-Options"] = "nosniff"
        result.headers["Referrer-Policy"] = "no-referrer"
        if request.url.path.startswith("/api/"):
            result.headers["Cache-Control"] = "no-store"
        elif request.url.path not in {"/docs","/redoc"}:
            result.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
        return result

    @app.exception_handler(HTTPException)
    async def http_error(request,exc):
        result=response({"error":{"code":str(exc.detail)}},exc.status_code)
        if exc.headers:
            result.headers.update(exc.headers)
        return result

    @app.exception_handler(Exception)
    async def unexpected(request,exc):
        return response({"error":{"code":"INTERNAL_ERROR"}},500)

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        return response({"error": {"code": "INVALID_INPUT"}}, 422)

    @app.exception_handler(LabStateError)
    async def state_error(request, exc):
        code = "NOT_FOUND" if str(exc) == "No matching lab session" else "STATE_CONFLICT"
        return response({"error": {"code": code}}, 404 if code == "NOT_FOUND" else 409)

    @app.exception_handler(FaultStateError)
    async def fault_state_error(request, exc):
        return response({"error":{"code":"STATE_CONFLICT"}},409)

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

    def principal(request: Request):
        user=accounts.current_user(db,request)
        if user is None:
            raise HTTPException(401,"AUTH_REQUIRED")
        expected=request.headers.get("x-dqa-account")
        if expected and expected!=str(user["user_id"]):
            raise HTTPException(409,"ACCOUNT_CHANGED")
        return user

    def writer(request: Request,user=Depends(principal)):
        accounts.require_csrf(request,user)
        return user

    def owned(table,key,item_id,user,allow_shared=False):
        allowed={("lab_sessions","session_id"),("pipeline_runs","run_id"),("fault_runs","fault_run_id")}
        if (table,key) not in allowed:
            raise ValueError("Invalid ownership lookup")
        from psycopg import sql
        fields="owner_id,is_shared" if table=="pipeline_runs" else "owner_id"
        with connect(db) as connection:
            row=connection.execute(sql.SQL("SELECT {} FROM metadata.{} WHERE {}=%s").format(sql.SQL(fields),sql.Identifier(table),sql.Identifier(key)),(item_id,)).fetchone()
        shared=bool(row and table=="pipeline_runs" and row[1])
        if not row or (row[0]!=user["user_id"] and not shared):
            raise HTTPException(404,"NOT_FOUND")
        if shared and not allow_shared:
            raise HTTPException(409,"READ_ONLY_BASELINE")
        return shared

    @app.get("/api/auth/me")
    def me(request: Request):
        user=accounts.current_user(db,request)
        return response({"user":accounts.public_user(user) if user else None,"csrf_token":user["csrf_token"] if user else None})

    @app.post("/api/auth/signup")
    def signup(body: Signup,request: Request):
        accounts.auth_intent(request)
        accounts.rate_limit(db,request,"signup")
        payload,token=mutate(accounts.signup,db,body.username,body.display_name,body.password)
        result=response(payload,201)
        accounts.set_cookie(result,token,request)
        return result

    @app.post("/api/auth/login")
    def login(body: Login,request: Request):
        accounts.auth_intent(request)
        accounts.rate_limit(db,request,"login",body.username)
        payload,token=mutate(accounts.login,db,body.username,body.password)
        result=response(payload)
        accounts.set_cookie(result,token,request)
        return result

    @app.post("/api/auth/logout")
    def logout(user=Depends(writer)):
        mutate(accounts.logout,db,user)
        result=response({"logged_out":True})
        result.delete_cookie(accounts.COOKIE,path="/")
        return result

    @app.post("/api/auth/password")
    def password(body: PasswordChange,request: Request,user=Depends(writer)):
        payload,token=mutate(accounts.change_password,db,user,body.current_password,body.new_password)
        result=response(payload)
        accounts.set_cookie(result,token,request)
        return result

    @app.get("/api/subjects")
    def subjects(language: Language="VIE"):
        return curriculum.subjects(language)

    @app.get("/api/courses")
    def courses(language: Language="VIE"):
        return curriculum.courses(language)

    @app.get("/api/courses/{course_id}")
    def course(course_id: str,language: Language="VIE"):
        value=curriculum.course(course_id,language)
        if value is None:
            raise HTTPException(404,"NOT_FOUND")
        return value

    @app.get("/api/enrollments")
    def enrollments(user=Depends(principal)):
        with connect(db) as connection:
            rows=connection.execute("SELECT course_id,enrolled_at FROM metadata.course_enrollments WHERE user_id=%s ORDER BY enrolled_at DESC",(user["user_id"],)).fetchall()
        return response([{"course_id":row[0],"enrolled_at":row[1]} for row in rows])

    @app.post("/api/courses/{course_id}/enroll")
    def enroll(course_id: str,user=Depends(writer)):
        if not (curriculum.course(course_id) or {}).get("available"):
            raise HTTPException(409,"COURSE_PLANNED")
        def save_enrollment():
            with transaction(db) as connection:
                connection.execute("INSERT INTO metadata.course_enrollments (user_id,course_id) VALUES (%s,%s) ON CONFLICT DO NOTHING",(user["user_id"],course_id))
        mutate(save_enrollment)
        return {"course_id":course_id,"enrolled":True}

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
    def sessions(user=Depends(principal),language: Language="VIE",lab_id: str|None=None,offset: int = QueryParameter(0,ge=0,le=100000), limit: int = QueryParameter(50,ge=1,le=50)):
        if lab_id is not None and lab_id not in CATALOG:
            raise HTTPException(404,"NOT_FOUND")
        with connect(db) as connection:
            rows = connection.execute("SELECT session_id,lab_id,mode,status,hints_used,started_at,completed_at FROM metadata.lab_sessions WHERE owner_id=%s AND (%s::text IS NULL OR lab_id=%s) ORDER BY started_at DESC,session_id DESC LIMIT %s OFFSET %s",(user["user_id"],lab_id,lab_id,limit,offset)).fetchall()
        return response([{**dict(zip(("session_id", "lab_id", "mode", "status", "hints_used", "started_at", "completed_at"), row, strict=True)),"title":CATALOG[row[1]][language]["title"],"course_id":curriculum.lesson_course(row[1])} for row in rows])

    @app.get("/api/progress")
    def progress(user=Depends(principal)):
        with connect(db) as connection:
            rows = connection.execute("SELECT lab_id,COUNT(*),BOOL_OR(status='COMPLETED') FROM metadata.lab_sessions WHERE owner_id=%s GROUP BY lab_id",(user["user_id"],)).fetchall()
        return [{"lab_id": row[0], "course_id":curriculum.lesson_course(row[0]), "attempts": row[1], "completed": row[2]} for row in rows]

    @app.post("/api/sessions", status_code=201)
    def start(body: Start,user=Depends(writer), language: Language = "VIE"):
        result = mutate(service.start_session, db, body.lab_id, body.run_id, body.mode, body.scenario,user["user_id"])
        return response(localize_session(result, language), 201)

    @app.get("/api/sessions/{session_id}")
    def session(session_id: UUID,user=Depends(principal), language: Language = "VIE"):
        owned("lab_sessions","session_id",session_id,user)
        return response(localize_session(service.inspect_session(db, session_id), language))

    @app.get("/api/sessions/{session_id}/history/{kind}")
    def history(session_id: UUID,kind: Literal["queries","submissions"],user=Depends(principal), offset: int = QueryParameter(0,ge=0,le=100000)):
        owned("lab_sessions","session_id",session_id,user)
        return response(service.history_page(db,session_id,kind,offset))

    @app.post("/api/sessions/{session_id}/query")
    def query(session_id: UUID, body: Query,user=Depends(writer)):
        owned("lab_sessions","session_id",session_id,user)
        return response(mutate(service.query_session, db, session_id, body.sql))

    @app.post("/api/sessions/{session_id}/simulation")
    def simulation(session_id: UUID, body: Simulation,user=Depends(writer), language: Language = "VIE"):
        owned("lab_sessions","session_id",session_id,user)
        return response(localize_session(mutate(service.simulate_session, db, session_id, body.action),language))

    @app.post("/api/sessions/{session_id}/evidence-import")
    def evidence_import(session_id: UUID, body: EvidenceImport,user=Depends(writer), language: Language = "VIE"):
        owned("lab_sessions", "session_id", session_id, user)
        try:
            result = mutate(service.import_cloud_evidence, db, session_id, body.filename, body.file_format, body.content)
        except LabStateError:
            raise
        except ValueError as exc:
            from backend.app.learning.cloud_contracts import localized_error
            return response({"error": {"code": "EVIDENCE_INVALID", "detail": localized_error(str(exc), language)}}, 422)
        return response(localize_session(result, language))

    @app.post("/api/sessions/{session_id}/submit")
    def submit(session_id: UUID, body: Submit,user=Depends(writer), language: Language = "VIE"):
        owned("lab_sessions","session_id",session_id,user)
        result = mutate(service.submit_solution, db, session_id, body.sql, body.conclusion)
        result["feedback_code"] = result["status"]
        # UI translates this stable code; do not ship an English fallback as VIE.
        result.pop("feedback", None)
        if "explanation" in result:
            sid = service.inspect_session(db, session_id)
            result["explanation"] = CATALOG[sid["lab_id"]][language]["explanation"]
        return response(result)

    @app.post("/api/sessions/{session_id}/hint")
    def hint(session_id: UUID,user=Depends(writer), language: Language = "VIE"):
        owned("lab_sessions","session_id",session_id,user)
        result = mutate(service.next_hint, db, session_id)
        sid = service.inspect_session(db, session_id)
        result["hint"] = CATALOG[sid["lab_id"]][language]["hints"][result["level"]-1]
        return response(result)

    @app.post("/api/sessions/{session_id}/reveal")
    def reveal(session_id: UUID,user=Depends(writer), language: Language = "VIE"):
        owned("lab_sessions","session_id",session_id,user)
        return response(localize_session(mutate(service.reveal_solution, db, session_id), language))

    @app.get("/api/runs")
    def runs(user=Depends(principal)):
        with connect(db) as connection:
            rows = connection.execute("SELECT run_id,execution_status,data_quality_status,started_at,completed_at,is_shared FROM metadata.pipeline_runs WHERE owner_id=%s OR is_shared ORDER BY is_shared ASC,started_at DESC LIMIT 100",(user["user_id"],)).fetchall()
        return response([dict(zip(("run_id", "execution_status", "data_quality_status", "started_at", "completed_at", "is_shared"), row, strict=True)) for row in rows])

    @app.get("/api/runs/{run_id}")
    def run(run_id: UUID,user=Depends(principal)):
        shared=owned("pipeline_runs","run_id",run_id,user,allow_shared=True)
        from pipeline.jobs.orders import inspect_run
        result = inspect_run(db, run_id)
        if result is None:
            raise HTTPException(404, detail="NOT_FOUND")
        result["is_shared"]=shared
        return response(result)

    @app.post("/api/runs")
    def pipeline(user=Depends(writer)):
        from pipeline.jobs.orders import run_orders_pipeline
        return response(asdict(mutate(run_orders_pipeline, db,None,user["user_id"])))

    @app.get("/api/runs/{run_id}/quality")
    def quality(run_id: UUID,user=Depends(principal)):
        owned("pipeline_runs","run_id",run_id,user,allow_shared=True)
        from qa.engine.runner import inspect_quality_run
        return response(inspect_quality_run(db, run_id))

    @app.post("/api/runs/{run_id}/quality")
    def quality_start(run_id: UUID,user=Depends(writer)):
        owned("pipeline_runs","run_id",run_id,user)
        from qa.engine.runner import run_quality_suite
        return response(asdict(mutate(run_quality_suite, db, run_id)))

    @app.get("/api/faults")
    def faults(user=Depends(principal)):
        with connect(db) as connection:
            rows = connection.execute("SELECT fault_run_id FROM metadata.fault_runs WHERE owner_id=%s ORDER BY applied_at DESC LIMIT 50",(user["user_id"],)).fetchall()
        from faults.service import inspect_fault
        return response([asdict(inspect_fault(db, row[0])) for row in rows])

    @app.post("/api/faults")
    def fault(body: Fault,user=Depends(writer)):
        owned("pipeline_runs","run_id",body.run_id,user)
        from faults.service import apply_fault
        return response(asdict(mutate(apply_fault, db, body.scenario, body.run_id,user["user_id"])))

    @app.post("/api/faults/{fault_id}/quality")
    def fault_quality(fault_id: UUID,user=Depends(writer)):
        owned("fault_runs","fault_run_id",fault_id,user)
        from faults.service import run_fault_quality
        return response(asdict(mutate(run_fault_quality, db, fault_id)))

    @app.post("/api/faults/{fault_id}/reset")
    def fault_reset(fault_id: UUID,user=Depends(writer)):
        owned("fault_runs","fault_run_id",fault_id,user)
        from faults.service import reset_fault
        return response(asdict(mutate(reset_fault, db, fault_id)))

    # Frontend is built locally or in the container. No external CDN assets.
    from pathlib import Path
    from fastapi.staticfiles import StaticFiles
    frontend = Path(__file__).resolve().parents[3] / "frontend" / "dist"
    if frontend.is_dir():
        from backend.app.api.spa import FrontendFiles
        app.mount("/", FrontendFiles(directory=frontend, html=True), name="frontend")
    return app


app = create_app()
