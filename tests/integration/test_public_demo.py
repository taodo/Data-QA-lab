"""Disposable DB only; generated public passwords never printed or snapshotted."""
import os
import unittest
from contextlib import redirect_stdout
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4
from fastapi import HTTPException
from fastapi.testclient import TestClient
from psycopg import sql
from psycopg.conninfo import make_conninfo
from backend.app import accounts, demo, public_demo
from backend.app.api import create_app
from backend.app.bootstrap import prepare_local
from backend.app.persistence.database import connect, transaction
from tests.auth_helpers import PASSWORD

DB = os.getenv("DATA_QA_TEST_DATABASE_URL")
HOST = "data-qa-lab.store"


@unittest.skipUnless(DB, "PostgreSQL test database required")
class PublicDemoTests(unittest.TestCase):
    def setUp(self):
        self.name = "data_qa_demo_public_test_" + uuid4().hex
        self.db = make_conninfo(DB, dbname=self.name)
        with connect(DB) as c:
            c.autocommit = True
            c.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(self.name)))
        self.env = patch.dict(os.environ, {"DATA_QA_DEMO_MODE": "1", "DATA_QA_PUBLIC_DEMO_ENABLED": "1",
            "DATA_QA_DEMO_MAX_ACCOUNTS": "15", "DATA_QA_PUBLIC_HOSTS": HOST, "DATA_QA_TRUSTED_PROXIES": "172.29.246.2"})
        self.env.start()
        prepare_local(self.db)
        self.ordinary, self.token = accounts.signup(self.db, "ordinary_user", "Ordinary", PASSWORD)
        self.client = self.client_for()

    def tearDown(self):
        self.env.stop()
        with connect(DB) as c:
            c.autocommit = True
            c.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(self.name)))

    def client_for(self):
        c = TestClient(create_app(self.db), base_url="https://" + HOST, client=("172.29.246.2", 123))
        c.headers.update({"Origin": "https://" + HOST, "X-Forwarded-Proto": "https", "X-DQA-Intent": "1"})
        return c

    def login(self, entry, client=None):
        client = client or self.client
        result = client.post("/api/auth/login", json=entry)
        self.assertEqual(result.status_code, 200)  # Never attach credential payload to failure output.
        self.assertIn("Secure", result.headers["set-cookie"])
        client.headers["X-CSRF-Token"] = result.json()["csrf_token"]
        return result.json()

    def entries(self):
        return self.client.get("/api/auth/demo").json()["accounts"]

    def test_safe_default_and_private_credentials_never_delivered(self):
        public_demo.provision(self.db, 2)
        valid_public = public_demo.listing(self.db)[0]
        with patch.dict(os.environ, {"DATA_QA_PUBLIC_DEMO_ENABLED": "0"}):
            self.assertEqual(self.entries(), [])
            self.assertEqual(self.client.post("/api/auth/login", json=valid_public).status_code, 401)
            self.login({"username": "ordinary_user", "password": PASSWORD})
        result = self.client.get("/api/auth/demo")
        self.assertEqual(result.headers["cache-control"], "no-store")
        self.assertEqual(len(result.json()["accounts"]), 2)
        for item in result.json()["accounts"]:
            self.assertEqual(set(item), {"username", "password"})
            self.assertNotEqual(item["username"], "ordinary_user")
        self.assertTrue(self.client.get("/api/auth/config").json()["demo_mode"])
        self.assertEqual(self.client.post("/api/auth/demo", json={}).status_code, 405)
        self.assertEqual(self.client.post("/api/auth/signup", json={"username": "new_user", "display_name": "New", "password": PASSWORD}).json()["error"]["code"], "DEMO_SIGNUP_DISABLED")
        with patch.dict(os.environ, {"DATA_QA_DEMO_MODE": "0"}):
            self.assertEqual(self.entries(), [])
            self.assertEqual(self.client.post("/api/auth/login", json=valid_public).status_code, 401)
            self.assertFalse(self.client.get("/api/auth/config").json()["demo_mode"])

    def test_provision_cap_conflicts_idempotency_and_restart_preservation(self):
        for i in range(4):
            accounts.signup(self.db, "private_" + str(i), "Private", PASSWORD)
        with patch.dict(os.environ, {"DATA_QA_DEMO_MAX_ACCOUNTS": "10"}):
            report = public_demo.provision(self.db)
            self.assertEqual(report["error"], "DEMO_ACCOUNT_LIMIT")
            self.assertEqual(report["required_limit"], 15)
            self.assertEqual(self.entries(), [])
        # Never promote/overwrite a conflicting ordinary account, even if its name looks public.
        accounts.signup(self.db, "demo_01", "Personal", PASSWORD)
        with connect(self.db) as c:
            before = c.execute("SELECT user_id,username,password_hash,active FROM metadata.accounts ORDER BY username").fetchall()
        result = public_demo.provision(self.db)
        self.assertEqual(result["conflicts"], ["demo_01"])
        self.assertEqual(len(result["created"]), 9)
        entries = self.entries()
        self.assertEqual(len({e["password"] for e in entries}), 9)
        with connect(self.db) as c:
            for item in entries:
                hashed = c.execute("SELECT password_hash FROM metadata.accounts WHERE username=%s", (item["username"],)).fetchone()[0]
                self.assertTrue(hashed.startswith("$argon2"))
                self.assertTrue(accounts.HASHER.verify(hashed, item["password"]))
            self.assertTrue(before == c.execute("SELECT user_id,username,password_hash,active FROM metadata.accounts WHERE username NOT IN (SELECT username FROM metadata.accounts JOIN metadata.public_demo_accounts USING(user_id)) ORDER BY username").fetchall())
        self.assertEqual(public_demo.provision(self.db)["created"], [])
        self.assertTrue(entries == self.entries())
        from backend.app.main import main
        output = StringIO()
        with patch("sys.argv", ["dqa", "public-demo", "status"]), \
             patch("backend.app.main.Settings.from_env", return_value=SimpleNamespace(database_url=self.db)), redirect_stdout(output):
            main()
        self.assertTrue(all(e["password"] not in output.getvalue() for e in entries))
        prepare_local(self.db)
        self.client = self.client_for()
        self.assertTrue(entries == self.entries())
        with self.assertRaises(HTTPException):
            accounts.signup(self.db, "excess_user", "Excess", PASSWORD)

    def test_password_lock_operator_recovery_rotation_disable_and_expiration(self):
        public_demo.provision(self.db, 1)
        old = self.entries()[0]
        user = self.login(old)
        self.assertTrue(user["user"]["public_shared"])
        denied = self.client.post("/api/auth/password", json={"current_password": old["password"], "new_password": PASSWORD})
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(denied.json()["error"]["code"], "PUBLIC_DEMO_PASSWORD_LOCKED")
        public_demo.rotate(self.db, "demo_01")
        self.assertIsNone(self.client.get("/api/auth/me").json()["user"])
        self.assertEqual(self.client.post("/api/auth/login", json=old).status_code, 401)
        rotated = self.entries()[0]
        self.assertTrue(old["password"] != rotated["password"])
        self.login(rotated)
        accounts.reset_password(self.db, "demo_01", PASSWORD)
        self.assertTrue(self.entries()[0]["password"] == PASSWORD)
        self.login(self.entries()[0])
        with transaction(self.db) as c:
            c.execute("UPDATE metadata.account_sessions SET expires_at=NOW()-INTERVAL '1 second'")
        self.assertIsNone(self.client.get("/api/auth/me").json()["user"])
        self.login(self.entries()[0])
        self.assertEqual(self.client.post("/api/auth/logout").status_code, 200)
        self.assertIsNone(self.client.get("/api/auth/me").json()["user"])
        public_demo.disable(self.db, "demo_01")
        self.assertEqual(self.entries(), [])
        self.assertEqual(self.client.post("/api/auth/login", json={"username": "demo_01", "password": PASSWORD}).status_code, 401)
        self.assertEqual(public_demo.provision(self.db, 1)["created"], [])
        self.assertEqual(self.entries(), [])
        public_demo.rotate(self.db, "demo_01", enable=True)
        self.assertEqual(len(self.entries()), 1)

    def test_ordinary_password_change_and_recovery_unaffected(self):
        self.login({"username": "ordinary_user", "password": PASSWORD})
        result = self.client.post("/api/auth/password", json={"current_password": PASSWORD, "new_password": PASSWORD + "-new"})
        self.assertEqual(result.status_code, 200)
        self.assertFalse(result.json()["user"]["public_shared"])
        with self.assertRaises(ValueError):
            public_demo.rotate(self.db, "ordinary_user")
        with self.assertRaises(ValueError):
            public_demo.disable(self.db, "ordinary_user")
        accounts.reset_password(self.db, "ordinary_user", PASSWORD)
        self.login({"username": "ordinary_user", "password": PASSWORD})

    def test_ownership_history_and_disabled_delivery_revokes_access(self):
        public_demo.provision(self.db, 2)
        first, second = self.entries()
        self.login(first)
        result = self.client.post("/api/sessions", json={"lab_id": "lab_001_record_count"})
        self.assertEqual(result.status_code, 201)
        path = "/api/sessions/" + result.json()["session_id"]
        self.assertEqual(self.client.post(path + "/query", json={"sql": "SELECT COUNT(*) FROM source_orders"}).status_code, 200)
        other = self.client_for()
        self.login(second, other)
        self.assertEqual(other.get(path).status_code, 404)
        before = self.client.get(path + "/history/queries").json()
        with patch.dict(os.environ, {"DATA_QA_PUBLIC_DEMO_ENABLED": "0"}):
            self.assertEqual(self.client.get(path).status_code, 401)
        restarted = self.client_for()
        restarted.cookies.update(self.client.cookies)
        self.assertTrue(before == restarted.get(path + "/history/queries").json())
        public_demo.disable(self.db)
        self.assertEqual(self.entries(), [])
        with connect(self.db) as c:
            self.assertEqual(c.execute("SELECT COUNT(*) FROM metadata.lab_queries").fetchone()[0], len(before))

    def test_session_budget_and_fixed_rate_limits_preserved(self):
        public_demo.provision(self.db, 1)
        entry = self.entries()[0]
        for _ in range(8):
            accounts.login(self.db, entry["username"], entry["password"])
        with connect(self.db) as c:
            self.assertEqual(c.execute("SELECT COUNT(*) FROM metadata.account_sessions s JOIN metadata.public_demo_accounts p USING(user_id)").fetchone()[0], demo.MAX_AUTH_SESSIONS)
        for i in range(11):
            result = self.client.post("/api/auth/login", json={"username": "random_" + str(i), "password": PASSWORD})
        self.assertEqual(result.status_code, 429)
        self.assertEqual(result.json()["error"]["code"], "AUTH_RATE_LIMIT")
        with connect(self.db) as c:
            self.assertEqual(c.execute("SELECT COUNT(*) FROM metadata.auth_budgets").fetchone()[0], 2)
