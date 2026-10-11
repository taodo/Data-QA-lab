"""Explicit public showcase identities. Mutations are trusted local CLI only.

Plaintext here is intentionally public, independent of private Argon2 hashes.
No caller can promote an existing ordinary account, even with a matching name.
"""
import os
import secrets
from uuid import uuid4
from fastapi import HTTPException
from backend.app import accounts, demo
from backend.app.persistence.database import connect, transaction

MAX_PUBLIC_ACCOUNTS = 10


def enabled():
    return demo.enabled() and os.getenv("DATA_QA_PUBLIC_DEMO_ENABLED", "0") == "1"


def _operator(connection):
    if not demo.enabled():
        raise ValueError("Public demo operations require demo mode")
    demo.require_demo_database(connection)


def listing(db):
    if not enabled():
        return []
    with connect(db) as connection:
        demo.require_demo_database(connection)
        rows = connection.execute("""SELECT a.username,p.password FROM metadata.public_demo_accounts p
            JOIN metadata.accounts a USING(user_id) WHERE p.enabled AND a.active
            ORDER BY a.username LIMIT %s""", (MAX_PUBLIC_ACCOUNTS,)).fetchall()
    return [{"username": name, "password": password} for name, password in rows]


def status(db):
    with connect(db) as connection:
        _operator(connection)
        rows = connection.execute("""SELECT a.username,a.active,p.enabled FROM metadata.accounts a
            LEFT JOIN metadata.public_demo_accounts p USING(user_id) ORDER BY a.username""").fetchall()
    return {"delivery_enabled": enabled(), "account_limit": demo.account_limit(), "accounts": [
        {"username": n, "active": a, "public_shared": p is not None, "public_enabled": p}
        for n, a, p in rows]}


def provision(db, count=10):
    if not 1 <= count <= MAX_PUBLIC_ACCOUNTS:
        raise ValueError("Public account count must be 1–10")
    names = [f"demo_{i:02d}" for i in range(1, count + 1)]
    with transaction(db) as connection:
        _operator(connection)
        connection.execute("LOCK TABLE metadata.accounts IN SHARE ROW EXCLUSIVE MODE")
        rows = connection.execute("""SELECT a.username,p.user_id FROM metadata.accounts a
            LEFT JOIN metadata.public_demo_accounts p USING(user_id)""").fetchall()
        existing = dict(rows)
        conflicts = [n for n in names if n in existing and existing[n] is None]
        missing = [n for n in names if n not in existing]
        if len(existing) + len(missing) > demo.account_limit():
            return {"created": [], "conflicts": conflicts, "missing": missing, "error": "DEMO_ACCOUNT_LIMIT",
                    "required_limit": len(existing) + len(missing)}
        if sum(v is not None for v in existing.values()) + len(missing) > MAX_PUBLIC_ACCOUNTS:
            raise HTTPException(429, "PUBLIC_DEMO_ACCOUNT_LIMIT")
        if connection.execute("SELECT pg_database_size(current_database())").fetchone()[0] >= demo.MAX_DATABASE_BYTES:
            raise HTTPException(429, "DEMO_STORAGE_LIMIT")
        for name in missing:
            user_id, password = uuid4(), secrets.token_urlsafe(24)
            connection.execute("""INSERT INTO metadata.accounts(user_id,username,display_name,password_hash)
                VALUES(%s,%s,%s,%s)""", (user_id, name, "Shared demo " + name[-2:], accounts.HASHER.hash(password)))
            connection.execute("INSERT INTO metadata.public_demo_accounts(user_id,password) VALUES(%s,%s)", (user_id, password))
    return {"created": missing, "conflicts": conflicts, "unchanged": [n for n in names if n in existing and n not in conflicts]}


def rotate(db, name, enable=False):
    password = secrets.token_urlsafe(24)
    with transaction(db) as connection:
        _operator(connection)
        row = connection.execute("""SELECT a.user_id,p.enabled FROM metadata.accounts a
            JOIN metadata.public_demo_accounts p USING(user_id) WHERE a.username=%s FOR UPDATE OF a,p""",
            (accounts.username(name),)).fetchone()
        if not row:
            raise ValueError("Unknown public demo account; ordinary account refused")
        active = row[1] or enable
        connection.execute("UPDATE metadata.accounts SET password_hash=%s,active=%s WHERE user_id=%s",
                           (accounts.HASHER.hash(password), active, row[0]))
        connection.execute("UPDATE metadata.public_demo_accounts SET password=%s,enabled=%s,updated_at=NOW() WHERE user_id=%s",
                           (password if active else None, active, row[0]))
        connection.execute("DELETE FROM metadata.account_sessions WHERE user_id=%s", (row[0],))
    return {"username": name, "rotated": True, "public_enabled": active, "sessions_revoked": True}


def disable(db, name=None):
    with transaction(db) as connection:
        _operator(connection)
        rows = connection.execute("""SELECT a.user_id FROM metadata.accounts a JOIN metadata.public_demo_accounts p
            USING(user_id) WHERE (%s::text IS NULL OR a.username=%s) FOR UPDATE OF a,p""",
            (accounts.username(name) if name else None, accounts.username(name) if name else None)).fetchall()
        if name and not rows:
            raise ValueError("Unknown public demo account; ordinary account refused")
        for (user_id,) in rows:
            connection.execute("UPDATE metadata.accounts SET active=FALSE WHERE user_id=%s", (user_id,))
            connection.execute("UPDATE metadata.public_demo_accounts SET enabled=FALSE,password=NULL,updated_at=NOW() WHERE user_id=%s", (user_id,))
            connection.execute("DELETE FROM metadata.account_sessions WHERE user_id=%s", (user_id,))
    return {"disabled": len(rows), "sessions_revoked": True}
