"""Persistent showcase budgets; never prune learner evidence."""
import os
from fastapi import HTTPException
from backend.app.persistence.database import transaction

MAX_ACCOUNTS = 5
MAX_AUTH_SESSIONS = 5
MAX_LABS_PER_ACCOUNT = 12
MAX_WRITES = 500
MAX_DATABASE_BYTES = 128 * 1024 * 1024


def enabled():
    return os.getenv("DATA_QA_DEMO_MODE", "0") == "1"


def require_demo_database(connection):
    if not connection.execute("SELECT current_database()").fetchone()[0].startswith("data_qa_demo"):
        raise RuntimeError("Demo mode requires a separate data_qa_demo database; learner database refused")


def initialize(db):
    if enabled():
        with transaction(db) as connection:
            require_demo_database(connection)
            connection.execute("CREATE TABLE IF NOT EXISTS metadata.demo_budget (id BOOLEAN PRIMARY KEY CHECK(id), writes INTEGER NOT NULL)")
            connection.execute("INSERT INTO metadata.demo_budget VALUES(TRUE,0) ON CONFLICT DO NOTHING")


def account_slot(connection):
    if enabled():
        require_demo_database(connection)
        connection.execute("LOCK TABLE metadata.accounts IN SHARE ROW EXCLUSIVE MODE")
        if connection.execute("SELECT COUNT(*) FROM metadata.accounts").fetchone()[0] >= MAX_ACCOUNTS:
            raise HTTPException(429, "DEMO_ACCOUNT_LIMIT")


def trim_auth_sessions(connection, user_id):
    if enabled():
        require_demo_database(connection)
        connection.execute("SELECT user_id FROM metadata.accounts WHERE user_id=%s FOR UPDATE", (user_id,))
        connection.execute("DELETE FROM metadata.account_sessions WHERE expires_at<=NOW()")
        connection.execute("""DELETE FROM metadata.account_sessions WHERE token_hash IN
            (SELECT token_hash FROM metadata.account_sessions WHERE user_id=%s
             ORDER BY created_at DESC,token_hash DESC OFFSET %s)""", (user_id, MAX_AUTH_SESSIONS - 1))


def reserve_write(db, function, args):
    if not enabled() or function.__module__ == "backend.app.accounts":
        return
    with transaction(db) as connection:
        require_demo_database(connection)
        used = connection.execute("SELECT writes FROM metadata.demo_budget WHERE id FOR UPDATE").fetchone()[0]
        if used >= MAX_WRITES or connection.execute("SELECT pg_database_size(current_database())").fetchone()[0] >= MAX_DATABASE_BYTES:
            raise HTTPException(429, "DEMO_STORAGE_LIMIT")
        if function.__name__ == "start_session":
            count = connection.execute("SELECT COUNT(*) FROM metadata.lab_sessions WHERE owner_id=%s", (args[-1],)).fetchone()[0]
            if count >= MAX_LABS_PER_ACCOUNT:
                raise HTTPException(429, "DEMO_LAB_LIMIT")
        connection.execute("UPDATE metadata.demo_budget SET writes=writes+1 WHERE id")
