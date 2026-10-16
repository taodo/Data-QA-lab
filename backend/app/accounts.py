"""Local accounts, opaque cookie sessions and explicit operator recovery/import."""
from datetime import datetime, timedelta, timezone
import hashlib
import re
import secrets
from uuid import uuid4

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import HTTPException
import psycopg

from backend.app.persistence.database import connect, transaction

COOKIE = "dqa_session"
SESSION_SECONDS = 7 * 24 * 3600
HASHER = PasswordHasher()
DUMMY_HASH = HASHER.hash(secrets.token_urlsafe(32))


def username(value):
    value = value.strip().lower()
    if not re.fullmatch(r"[a-z0-9_]{3,32}", value):
        raise ValueError("Username requires 3–32 ASCII letters, numbers or underscores")
    return value


def validate_password(value):
    if not isinstance(value, str) or not 12 <= len(value) <= 128 or len(value.encode()) > 512:
        raise ValueError("Password requires 12–128 characters")
    return value


def token_hash(value):
    return hashlib.sha256(value.encode()).hexdigest()


def public_user(user):
    return {**{key: user[key] for key in ("user_id", "username", "display_name")},
            "public_shared": bool(user.get("public_shared", False))}


def _issue(connection, user):
    from backend.app.demo import trim_auth_sessions
    trim_auth_sessions(connection, user["user_id"])
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    connection.execute(
        """INSERT INTO metadata.account_sessions
           (token_hash,user_id,csrf_token,expires_at) VALUES (%s,%s,%s,%s)""",
        (token_hash(token), user["user_id"], csrf,
         datetime.now(timezone.utc) + timedelta(seconds=SESSION_SECONDS)),
    )
    return {"user": public_user(user), "csrf_token": csrf}, token


def signup(db, name, display_name, password):
    name = username(name)
    display_name = display_name.strip()
    if not display_name or len(display_name) > 80:
        raise ValueError("Display name requires 1–80 characters")
    hashed = HASHER.hash(validate_password(password))
    user = {"user_id": uuid4(), "username": name, "display_name": display_name}
    try:
        with transaction(db) as connection:
            from backend.app.demo import account_slot
            account_slot(connection)
            connection.execute(
                "INSERT INTO metadata.accounts (user_id,username,display_name,password_hash) VALUES (%s,%s,%s,%s)",
                (*user.values(), hashed),
            )
            return _issue(connection, user)
    except psycopg.errors.UniqueViolation as exc:
        raise HTTPException(409, "USERNAME_TAKEN") from exc


def login(db, name, password):
    from backend.app import public_demo
    name = username(name)
    validate_password(password)
    with transaction(db) as connection:
        row = connection.execute(
            """SELECT a.user_id,a.username,a.display_name,a.password_hash,p.enabled FROM metadata.accounts a
               LEFT JOIN metadata.public_demo_accounts p USING(user_id)
               WHERE a.username=%s AND a.active FOR UPDATE OF a""",
            (name,),
        ).fetchone()
        hashed = row[3] if row else DUMMY_HASH
        try:
            valid = HASHER.verify(hashed, password)
        except (VerificationError, InvalidHashError):
            valid = False
        if not row or not valid or (row[4] is not None and (not row[4] or not public_demo.enabled())):
            raise HTTPException(401, "AUTH_INVALID")
        if HASHER.check_needs_rehash(hashed):
            connection.execute("UPDATE metadata.accounts SET password_hash=%s WHERE user_id=%s", (HASHER.hash(password), row[0]))
        return _issue(connection, {**dict(zip(("user_id", "username", "display_name"), row[:3], strict=True)),
                                   "public_shared": row[4] is not None})


def current_user(db, request):
    from backend.app import public_demo
    token = request.cookies.get(COOKIE, "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{43}", token):
        return None
    with connect(db) as connection:
        row = connection.execute(
            """SELECT a.user_id,a.username,a.display_name,s.csrf_token,s.token_hash,p.user_id IS NOT NULL
               FROM metadata.account_sessions s JOIN metadata.accounts a USING(user_id)
               LEFT JOIN metadata.public_demo_accounts p USING(user_id)
               WHERE s.token_hash=%s AND s.expires_at>NOW() AND a.active
               AND (p.user_id IS NULL OR (p.enabled AND %s))""",
            (token_hash(token), public_demo.enabled()),
        ).fetchone()
    return dict(zip(("user_id", "username", "display_name", "csrf_token", "token_hash", "public_shared"), row, strict=True)) if row else None


def require_csrf(request, user):
    supplied = request.headers.get("x-csrf-token", "")
    if not supplied or not secrets.compare_digest(supplied, user["csrf_token"]):
        raise HTTPException(403, "CSRF_DENIED")


def auth_intent(request):
    if request.headers.get("x-dqa-intent") != "1" or not request.headers.get("content-type", "").startswith("application/json"):
        raise HTTPException(403, "CSRF_DENIED")


def rate_limit(db, request, operation, name=""):
    """Persist budgets outside failed-login transactions; no forwarded IP trust."""
    host = request.client.host if request.client else "local"
    from backend.app.demo import enabled
    if enabled():
        host, name = "demo", "demo" if name else ""
    keys = [(f"{operation}:ip:{host}", 60)]
    if name:
        keys.append((f"{operation}:username:{name.strip().lower()}", 10))
    exceeded = False
    with transaction(db) as connection:
        connection.execute("DELETE FROM metadata.auth_budgets WHERE window_start<NOW()-INTERVAL '1 day'")
        for key, limit in keys:
            count = connection.execute(
                """INSERT INTO metadata.auth_budgets (budget_key,window_start,attempts)
                   VALUES (%s,NOW(),1) ON CONFLICT (budget_key) DO UPDATE SET
                   attempts=CASE WHEN metadata.auth_budgets.window_start<NOW()-INTERVAL '15 minutes'
                     THEN 1 ELSE metadata.auth_budgets.attempts+1 END,
                   window_start=CASE WHEN metadata.auth_budgets.window_start<NOW()-INTERVAL '15 minutes'
                     THEN NOW() ELSE metadata.auth_budgets.window_start END RETURNING attempts""",
                (token_hash(key),),
            ).fetchone()[0]
            exceeded |= count > limit
    if exceeded:
        raise HTTPException(429, "AUTH_RATE_LIMIT", headers={"Retry-After": "900"})


def set_cookie(response, token, request):
    response.set_cookie(COOKIE, token, max_age=SESSION_SECONDS, httponly=True,
                        secure=request.url.scheme == "https", samesite="lax", path="/")


def logout(db, user):
    with transaction(db) as connection:
        # Session lifecycle fences Banking admissions before deleting the cookie
        # record. Unknown banking receipts and revocation outbox survive logout.
        from backend.app.banking_foundation import fence_session
        fence_session(connection, user["token_hash"])
        connection.execute("DELETE FROM metadata.account_sessions WHERE token_hash=%s", (user["token_hash"],))


def change_password(db, user, old_password, new_password):
    validate_password(new_password)
    with transaction(db) as connection:
        row = connection.execute("""SELECT a.password_hash,p.user_id IS NOT NULL FROM metadata.accounts a
            LEFT JOIN metadata.public_demo_accounts p USING(user_id) WHERE a.user_id=%s FOR UPDATE OF a""", (user["user_id"],)).fetchone()
        if row[1]:
            raise HTTPException(403, "PUBLIC_DEMO_PASSWORD_LOCKED")
        try:
            HASHER.verify(row[0], old_password)
        except (VerificationError, InvalidHashError) as exc:
            raise HTTPException(401, "AUTH_INVALID") from exc
        connection.execute("UPDATE metadata.accounts SET password_hash=%s WHERE user_id=%s", (HASHER.hash(new_password), user["user_id"]))
        from backend.app.banking_foundation import fence_session
        previous = connection.execute(
            "SELECT token_hash FROM metadata.account_sessions WHERE user_id=%s FOR UPDATE",
            (user["user_id"],)).fetchall()
        for (session_hash,) in previous:
            fence_session(connection, session_hash)
        connection.execute("DELETE FROM metadata.account_sessions WHERE user_id=%s", (user["user_id"],))
        return _issue(connection, user)


def reset_password(db, name, new_password):
    """Trusted local operator only; never exposed as an HTTP endpoint."""
    hashed = HASHER.hash(validate_password(new_password))
    with transaction(db) as connection:
        row = connection.execute("UPDATE metadata.accounts SET password_hash=%s WHERE username=%s RETURNING user_id", (hashed, username(name))).fetchone()
        if not row:
            raise ValueError("Unknown local account")
        from backend.app.banking_foundation import fence_session
        previous = connection.execute(
            "SELECT token_hash FROM metadata.account_sessions WHERE user_id=%s FOR UPDATE",
            (row[0],)).fetchall()
        for (session_hash,) in previous:
            fence_session(connection, session_hash)
        connection.execute("DELETE FROM metadata.account_sessions WHERE user_id=%s", (row[0],))
        # Operator recovery keeps the deliberately public display in sync; never enables a disabled account.
        connection.execute("""UPDATE metadata.public_demo_accounts SET password=CASE WHEN enabled THEN %s ELSE NULL END,
            updated_at=NOW() WHERE user_id=%s""", (new_password, row[0]))
    return {"username": name, "password_reset": True, "sessions_revoked": True}


def import_legacy(db, name, confirm=False):
    """Atomic, explicit association. Registration never claims legacy history."""
    with transaction(db) as connection:
        row = connection.execute("SELECT user_id FROM metadata.accounts WHERE username=%s AND active", (username(name),)).fetchone()
        if not row:
            raise ValueError("Unknown local account")
        if confirm:
            connection.execute("LOCK TABLE metadata.pipeline_runs,metadata.lab_sessions,metadata.fault_runs IN SHARE ROW EXCLUSIVE MODE")
        counts = {table: connection.execute(f"SELECT COUNT(*) FROM metadata.{table} WHERE owner_id IS NULL" + (" AND NOT is_shared" if table == "pipeline_runs" else "")).fetchone()[0]
                  for table in ("pipeline_runs", "lab_sessions", "fault_runs")}
        if confirm:
            for table in counts:
                connection.execute(f"UPDATE metadata.{table} SET owner_id=%s WHERE owner_id IS NULL" + (" AND NOT is_shared" if table == "pipeline_runs" else ""), (row[0],))
            if counts["lab_sessions"]:
                from backend.app.learning.lessons import course_id
                labs=connection.execute("SELECT DISTINCT lab_id FROM metadata.lab_sessions WHERE owner_id=%s",(row[0],)).fetchall()
                for course in {course_id(lab[0]) for lab in labs}:
                    connection.execute("INSERT INTO metadata.course_enrollments (user_id,course_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (row[0],course))
            connection.execute("INSERT INTO metadata.legacy_imports (user_id,run_count,session_count,fault_count) VALUES (%s,%s,%s,%s)", (row[0], *counts.values()))
        return {"username": name, "confirmed": confirm, "counts": counts}
