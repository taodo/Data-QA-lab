import json
import unittest
from urllib.request import urlopen
from backend.app.learning import http_exercises as http
from backend.app.learning.lessons import lesson, course_id
from backend.app.courses import course


class ApiPlanTests(unittest.TestCase):
    def test_real_http_fixture_pagination_and_retries(self):
        rows = [
            {"order_id": i, "customer_id": 1, "net_amount": "0.01"} for i in range(1, 6)
        ]
        with http.fixture(rows, http.IDS[2], "clean") as address:
            from urllib.error import HTTPError

            for status in (429, 503):
                with self.assertRaises(HTTPError) as exc:
                    urlopen(address + "/orders?page=1&page_size=2")
                self.assertEqual(exc.exception.code, status)
            payload = json.load(urlopen(address + "/orders?page=1&page_size=2"))
            self.assertEqual(len(payload["items"]), 2)
            self.assertEqual(payload["next_page"], 2)

    def test_plans_cannot_choose_external_urls_or_unbounded_actions(self):
        invalid = [
            {"url": "http://external.invalid"},
            {"path": "http://127.0.0.1/admin"},
            {"method": "POST"},
            {"max_attempts": 4},
            {"page_size": 0},
            {"timeout_ms": 100000},
            {"paginate": 1},
            {"checks": {"eval": "anything"}},
            {"checks": {"types": {"net_amount": "float"}}},
            {"checks": {"required": ["order_id", "order_id"]}},
            {"checks": {"status": True}},
            {"checks": {"required": [[]]}},
        ]
        for patch in invalid:
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                http.parse(json.dumps({**http.BASE, **patch}))
        for value in (
            '{"checks":{"status":200},"checks":{"status":500}}',
            '{"timeout_ms":NaN}',
            "[]",
            "SELECT 0",
        ):
            with self.assertRaises(ValueError):
                http.parse(value)

    def test_course_contracts_and_solution_visibility(self):
        for course_id, count in (
            ("sql-data-qa", 13),
            ("etl-testing", 5),
            ("api-testing", 4),
        ):
            c = course(course_id, "ENG")
            labs = [l for ch in c["chapters"] for l in ch["lessons"]]
            self.assertEqual(c["lesson_count"], count)
            self.assertEqual(len(labs), count)
            self.assertEqual([l["order"] for l in labs], list(range(1, count + 1)))
            for item in labs:
                self.assertEqual(item["course_id"], course_id)
                self.assertNotIn("solution_sql", item)
        self.assertEqual(lesson(http.IDS[0], "VIE")["exercise_type"], "HTTP")

    def test_zero_decimal_boolean_and_key_metric_traps(self):
        expected = [{"order_id": 1, "customer_id": 2, "net_amount": "0.00"}]
        good = [dict(expected[0])]
        trace = [{"final": True, "status": 200}]
        self.assertEqual(
            http.count_violations(http.RULES[http.IDS[0]], good, trace, expected, []), 0
        )
        for row in (
            {**good[0], "customer_id": True},
            {**good[0], "net_amount": "NaN"},
            {"order_id": 1, "customer_id": 2},
        ):
            self.assertEqual(
                http.count_violations(
                    http.RULES[http.IDS[0]], [row], trace, expected, []
                ),
                1,
            )
        self.assertEqual(
            http.count_violations(
                {"complete": True, "unique": True},
                [good[0], good[0]],
                trace,
                expected,
                [],
            ),
            1,
        )
