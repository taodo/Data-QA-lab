import os
import unittest
from uuid import uuid4
from fastapi.testclient import TestClient
from backend.app.api import create_app
from backend.app.learning.content import LAB_ID, SOLUTION

DB = os.getenv("DATA_QA_TEST_DATABASE_URL")


@unittest.skipUnless(DB, "PostgreSQL test database required")
class ApiIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from backend.app.persistence.database import initialize_database
        from backend.app.learning.sql_runtime import initialize_sql_security
        from pipeline.source.seed import seed_source
        from pipeline.jobs.orders import run_orders_pipeline
        initialize_database(DB)
        initialize_sql_security(DB)
        seed_source(DB, 20)
        cls.run_id = str(run_orders_pipeline(DB).run_id)

    def setUp(self):
        self.client = TestClient(create_app(DB))

    def test_real_http_learning_loop_and_language_switch(self):
        result = self.client.post("/api/sessions", json={"lab_id": LAB_ID, "run_id": self.run_id})
        self.assertEqual(result.status_code, 201, result.text)
        sid = result.json()["session_id"]
        self.assertNotIn("scenario_id", result.json())
        self.assertNotIn("solution_sql", result.json())
        query = self.client.post(f"/api/sessions/{sid}/query", json={"sql": "SELECT COUNT(*) FROM source_orders"})
        self.assertEqual(query.json()["rows"], [["20"]])
        denied = self.client.post(f"/api/sessions/{sid}/query", json={"sql": "SELECT * FROM metadata.lab_sessions"})
        self.assertEqual(denied.json()["status"], "ERROR")
        hint = self.client.post(f"/api/sessions/{sid}/hint?language=VIE").json()
        self.assertIn("grain", hint["hint"])
        eng = self.client.get(f"/api/sessions/{sid}?language=ENG").json()
        self.assertEqual(eng["hints_used"], 1)
        self.assertEqual(len(eng["queries"]), 2)
        failed = self.client.post(f"/api/sessions/{sid}/submit", json={"sql": "SELECT 0 AS violation_count", "conclusion": "test"}).json()
        self.assertEqual(failed["status"], "FAIL")
        self.assertNotIn("cases", failed)
        passed = self.client.post(f"/api/sessions/{sid}/submit", json={"sql": SOLUTION, "conclusion": "Compare both directions"}).json()
        self.assertEqual(passed["status"], "PASS")
        self.assertIn("solution_sql", passed)
        resumed = self.client.get(f"/api/sessions/{sid}").json()
        self.assertEqual(resumed["status"], "COMPLETED")
        self.assertEqual(len(resumed["submissions"]), 2)
        self.assertEqual(self.client.post(f"/api/sessions/{sid}/hint").status_code, 409)

    def test_runs_errors_and_quality(self):
        self.assertEqual(self.client.get("/api/health").json()["status"], "READY")
        self.assertEqual(self.client.get(f"/api/sessions/{uuid4()}").status_code, 404)
        self.assertEqual(self.client.get(f"/api/runs/{uuid4()}").status_code, 404)
        result = self.client.post(f"/api/runs/{self.run_id}/quality")
        self.assertEqual(result.json()["status"], "PASS")
        self.assertEqual(self.client.get(f"/api/runs/{self.run_id}").json()["execution_status"], "SUCCESS")
        self.assertEqual(self.client.get(f"/api/runs/{self.run_id}/quality").json()["status"], "PASS")
