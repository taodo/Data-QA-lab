"""Real isolated demo DB: HTTPS proxy auth, ownership, SQL and durable budgets."""
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from uuid import uuid4
from psycopg import sql
from psycopg.conninfo import make_conninfo
from fastapi import HTTPException
from fastapi.testclient import TestClient
from backend.app import accounts, demo
from backend.app.api import create_app
from backend.app.bootstrap import prepare_local
from backend.app.persistence.database import connect, transaction
from tests.auth_helpers import PASSWORD

DB = os.getenv("DATA_QA_TEST_DATABASE_URL")
HOST = "demo-verified.trycloudflare.com"
ENV = {"DATA_QA_DEMO_MODE": "1", "DATA_QA_PUBLIC_HOSTS": HOST, "DATA_QA_TRUSTED_PROXIES": "172.29.246.2"}


@unittest.skipUnless(DB, "PostgreSQL test database required")
class DemoIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.name = "data_qa_demo_test_" + uuid4().hex
        self.db = make_conninfo(DB, dbname=self.name)
        with connect(DB) as admin:
            admin.autocommit = True
            admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(self.name)))
        self.env = patch.dict(os.environ, ENV)
        self.env.start()
        prepare_local(self.db)
        self.user, token = accounts.signup(self.db, "demo_learner", "Demo learner", PASSWORD)
        accounts.logout(self.db, {"token_hash": accounts.token_hash(token)})
        self.client = TestClient(create_app(self.db), base_url="https://" + HOST, client=("172.29.246.2", 123))
        self.client.headers.update({"Origin": "https://" + HOST, "X-Forwarded-Proto": "https", "X-DQA-Intent": "1"})

    def tearDown(self):
        self.env.stop()
        with connect(DB) as admin:
            admin.autocommit = True
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(self.name)))

    def login(self):
        result = self.client.post("/api/auth/login", json={"username": "demo_learner", "password": PASSWORD})
        self.assertEqual(result.status_code, 200, result.text)
        self.assertIn("Secure", result.headers["set-cookie"])
        self.assertIn("HttpOnly", result.headers["set-cookie"])
        self.client.headers["X-CSRF-Token"] = result.json()["csrf_token"]
        return result

    def test_https_navigation_sql_submission_history_and_csrf(self):
        self.login()
        self.assertEqual(self.client.get("/api/auth/me").json()["user"]["username"], "demo_learner")
        for language in ("ENG", "VIE"):
            self.assertEqual(len(self.client.get("/api/courses?language=" + language).json()), 9)
            self.assertEqual(self.client.get("/api/courses/sql-data-qa?language=" + language).status_code, 200)
        result = self.client.post("/api/sessions", json={"lab_id": "lab_001_record_count", "mode": "SANDBOX", "scenario": "clean"})
        self.assertEqual(result.status_code, 201, result.text)
        path = "/api/sessions/" + result.json()["session_id"]
        self.assertEqual(self.client.post(path + "/query", json={"sql": "SELECT COUNT(*) FROM source_orders"}).json()["status"], "SUCCESS")
        check = (Path(__file__).parents[2] / "examples/lab_001_key_check.sql").read_text()
        result = self.client.post(path + "/submit", json={"sql": check, "conclusion": "Compared independent source and target keys."})
        self.assertEqual(result.json()["status"], "PASS", result.text)
        before = [self.client.get(path + "/history/" + kind).json() for kind in ("queries", "submissions")]
        restarted = TestClient(create_app(self.db), base_url="https://" + HOST, client=("172.29.246.2", 123))
        restarted.cookies.update(self.client.cookies)
        restarted.headers.update(self.client.headers)
        self.assertEqual(before, [restarted.get(path + "/history/" + kind).json() for kind in ("queries", "submissions")])
        for headers in ({"X-CSRF-Token": "wrong"}, {"Origin": "https://other.trycloudflare.com"}):
            self.assertEqual(self.client.post(path + "/hint", headers=headers).status_code, 403)
        anonymous = TestClient(create_app(self.db), base_url="https://" + HOST, client=("172.29.246.2", 123))
        anonymous.headers["X-Forwarded-Proto"] = "https"
        self.assertEqual(anonymous.get(path).status_code, 401)
        self.assertEqual(self.client.post("/api/auth/signup", json={"username": "new_user", "display_name": "new", "password": PASSWORD}).status_code, 403)

    def test_account_tokens_labs_storage_and_restart_limits(self):
        for _ in range(8):
            self.login()
        with connect(self.db) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM metadata.account_sessions").fetchone()[0], demo.MAX_AUTH_SESSIONS)
        for index in range(demo.MAX_ACCOUNTS - 1):
            accounts.signup(self.db, "demo_" + str(index), "Demo", PASSWORD)
        with self.assertRaises(HTTPException) as error:
            accounts.signup(self.db, "demo_excess", "Demo", PASSWORD)
        self.assertEqual(error.exception.detail, "DEMO_ACCOUNT_LIMIT")
        with patch.object(demo, "MAX_LABS_PER_ACCOUNT", 1):
            self.assertEqual(self.client.post("/api/sessions", json={"lab_id": "lab_001_record_count"}).status_code, 201)
            self.assertEqual(self.client.post("/api/sessions", json={"lab_id": "lab_001_record_count"}).json()["error"]["code"], "DEMO_LAB_LIMIT")
        with patch.object(demo, "MAX_DATABASE_BYTES", 1):
            self.assertEqual(self.client.post("/api/runs").json()["error"]["code"], "DEMO_STORAGE_LIMIT")
        with transaction(self.db) as connection:
            connection.execute("UPDATE metadata.demo_budget SET writes=%s", (demo.MAX_WRITES,))
        prepare_local(self.db)
        self.assertEqual(self.client.post("/api/runs").status_code, 429)
        self.assertEqual(self.client.get("/api/sessions").status_code, 200)
        self.assertEqual(self.client.post("/api/auth/logout").status_code, 200)

    def test_rate_budget_has_fixed_cardinality_and_demo_refuses_learner_db(self):
        for index in range(15):
            result = self.client.post("/api/auth/login", json={"username": "random_" + str(index), "password": PASSWORD}, headers={"X-Forwarded-For": str(index)})
        self.assertEqual(result.status_code, 429)
        with connect(self.db) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM metadata.auth_budgets").fetchone()[0], 2)
        with connect(DB) as connection:
            if not connection.execute("SELECT current_database()").fetchone()[0].startswith("data_qa_demo"):
                with self.assertRaises(RuntimeError):
                    demo.require_demo_database(connection)
