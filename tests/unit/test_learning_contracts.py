from dataclasses import replace
import unittest
from uuid import uuid4

from backend.app.learning.contracts import QueryLimits, QueryResult, normalize_sql, violation_count
from backend.app.learning.service import _public
from backend.app.learning.workspace import require_schema
from backend.app.main import build_parser


class LearningContractTests(unittest.TestCase):
    def test_sql_input_bounds_and_final_semicolon(self):
        self.assertEqual(normalize_sql(" SELECT 1; \n"), "SELECT 1")
        for query in ("", " ", "SELECT '\x00'", "x" * 16385):
            with self.subTest(query=query[:15]), self.assertRaises(ValueError):
                normalize_sql(query)

    def test_query_limits_cannot_exceed_safety_defaults(self):
        for changes in ({"max_rows": 101}, {"timeout_ms": 0}, {"max_bytes": True},
                        {"watchdog_ms": 1000}, {"cell_chars": 3000}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(QueryLimits(), **changes)

    def test_grading_requires_exact_non_negative_integer_result(self):
        valid = QueryResult("SUCCESS", ("violation_count",), (("2",),))
        self.assertEqual(violation_count(valid), 2)
        for value in ("-1", "1.5", "NaN", "Infinity", "hello", None, str(2**63)):
            with self.subTest(value=value), self.assertRaises(ValueError):
                violation_count(replace(valid, rows=((value,),)))
        for result in (replace(valid, truncated=True), replace(valid, status="ERROR"),
                       replace(valid, columns=("count",)), replace(valid, rows=())):
            with self.assertRaises(ValueError):
                violation_count(result)

    def test_workspace_identifiers_are_owned_and_exact(self):
        require_schema("learner_session_" + uuid4().hex)
        for schema in ("target", "learner_query_xyz", "learner_session_" + uuid4().hex + ";"):
            with self.assertRaises(ValueError):
                require_schema(schema)

    def test_challenge_serializer_hides_instructor_fields(self):
        session = dict(session_id=uuid4(), lab_id="lab_001_record_count", pipeline_run_id=uuid4(),
                       mode="CHALLENGE", status="ACTIVE", scenario_id="equal_count_swap",
                       snapshot_schema="hidden_schema", hints_used=0, started_at=None, completed_at=None)
        public = _public(session)
        for key in ("scenario_id", "snapshot_schema", "solution_sql", "explanation"):
            self.assertNotIn(key, public)
        self.assertIn("scenario_id", _public(session | {"mode": "SANDBOX"}))
        self.assertIn("solution_sql", _public(session | {"status": "REVEALED"}))

    def test_cli_parses_lab_workflow(self):
        sid = str(uuid4())
        args = build_parser().parse_args([
            "lab-submit", "--session-id", sid, "--sql-file", "check.sql", "--conclusion", "Key mismatch",
        ])
        self.assertEqual(str(args.session_id), sid)
        self.assertEqual(args.sql_file.name, "check.sql")
