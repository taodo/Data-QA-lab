import unittest
from decimal import Decimal
from fastapi.testclient import TestClient
from backend.app.api import create_app, response
from backend.app.learning.lessons import CATALOG, lesson


class ApiContractTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app("postgresql://invalid"))

    def test_bilingual_content_does_not_publish_solutions(self):
        for language in ("ENG", "VIE"):
            result = self.client.get("/api/lessons", params={"language": language})
            self.assertEqual(result.status_code, 200)
            for item in result.json():
                self.assertNotIn("hints", item)
                self.assertNotIn("solution_sql", item)
                self.assertNotIn("explanation", item)
                self.assertEqual(item["language"], language)
        self.assertEqual(self.client.get("/api/lessons?language=FR").status_code, 422)

    def test_input_origin_host_and_body_limits(self):
        self.assertEqual(self.client.post("/api/sessions", json={"lab_id": "x", "admin": True}).status_code, 401)
        self.assertEqual(self.client.post("/api/sessions", json={"lab_id": "x"}, headers={"Origin": "https://evil.example"}).status_code, 403)
        self.assertEqual(self.client.get("/api/lessons", headers={"Host": "evil.example"}).status_code, 400)
        self.assertEqual(self.client.post("/api/sessions", content=b"x" * 65537).status_code, 413)
        self.assertEqual(self.client.get("/api/sessions/not-a-uuid").status_code, 401)
        self.assertEqual(self.client.get("/api/lessons/unknown").status_code, 404)

    def test_exact_decimal_encoding(self):
        self.assertIn(b'"12345678901234.01"', response({"amount": Decimal("12345678901234.01")}).body)

    def test_history_bounds_and_private_failures_are_safe(self):
        from unittest.mock import patch
        self.assertEqual(self.client.get("/api/sessions?limit=51").status_code,401)
        self.assertEqual(self.client.get("/api/sessions?offset=-1").status_code,401)
        with patch("backend.app.api.connect",side_effect=RuntimeError("private credential detail")):
            result=TestClient(create_app("postgresql://invalid"),raise_server_exceptions=False).get("/api/health")
        self.assertEqual(result.status_code,500)
        self.assertEqual(result.json()["error"]["code"],"INTERNAL_ERROR")
        self.assertNotIn("private credential",result.text)
        lesson=self.client.get("/api/lessons")
        self.assertEqual(lesson.headers["Cache-Control"],"no-store")
