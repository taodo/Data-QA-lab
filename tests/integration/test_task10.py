"""Independent ETL fixture counts, actual HTTP/TCP and PostgreSQL ingestion."""

import json
import os
import unittest
from unittest.mock import patch
from backend.app.learning import etl, http_exercises as http
from backend.app.learning.profiles import PROFILES
from backend.app.learning.service import (
    start_session,
    query_session,
    submit_solution,
    simulate_session,
    inspect_session,
)
from backend.app.persistence.database import connect, transaction, initialize_database

DB = os.getenv("DATA_QA_TEST_DATABASE_URL")


@unittest.skipUnless(DB, "PostgreSQL test database required")
class Task10IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from backend.app.learning.sql_runtime import initialize_sql_security
        from pipeline.source.seed import seed_source
        from pipeline.jobs.orders import run_orders_pipeline

        initialize_database(DB)
        initialize_sql_security(DB)
        seed_source(DB, 20)
        cls.baseline_run_id = run_orders_pipeline(DB).run_id
        with transaction(DB) as c:
            c.execute(
                "UPDATE metadata.pipeline_runs SET is_shared=true WHERE run_id=%s",
                (cls.baseline_run_id,),
            )

    def session(self, key, scenario="clean", mode="SANDBOX"):
        return start_session(
            DB, key, self.baseline_run_id, mode, scenario if mode == "SANDBOX" else None
        )

    def test_etl_independent_counts_and_sql_permissions(self):
        counts = {
            "etl_wrong_mapping": 1,
            "etl_missing": 1,
            "etl_rounding": 1,
            "etl_null_amount": 1,
            "etl_drop_reject": 1,
            "etl_accept_invalid": 1,
            "etl_append": 2,
            "etl_skip_late": 1,
            "etl_failed": 5,
            "etl_partial_publish": 1,
        }
        for key, (scenarios, solution) in etl.SPECS.items():
            for scenario in ("clean", *scenarios):
                with self.subTest(key=key, scenario=scenario):
                    s = self.session(key, scenario)
                    result = query_session(DB, s["session_id"], solution)
                    self.assertEqual(result["status"], "SUCCESS", result)
                    self.assertEqual(
                        result["rows"],
                        ((str(0 if scenario == "clean" else counts[scenario]),),),
                    )
                    denied = query_session(
                        DB, s["session_id"], "DELETE FROM etl_target"
                    )
                    self.assertEqual(denied["status"], "ERROR")
                    denied = query_session(
                        DB, s["session_id"], "SELECT * FROM metadata.accounts"
                    )
                    self.assertEqual(denied["status"], "ERROR")

    def test_recovery_replay_and_other_session_are_actual_and_isolated(self):
        a = self.session("lab_018_etl_recovery", "etl_failed")
        b = self.session("lab_018_etl_recovery", "clean")
        sid = a["session_id"]
        self.assertEqual(a["etl_simulation"]["steps"][-1]["execution_status"], "FAILED")
        for action in ("RECOVER", "RECOVER"):
            result = simulate_session(DB, sid, action)
            self.assertEqual(result["etl_simulation"]["steps"][-1]["checkpoint"], 1)
            self.assertEqual(query_session(DB, sid, etl.RECOVERY)["rows"], (("0",),))
        self.assertEqual(
            query_session(DB, b["session_id"], etl.RECOVERY)["rows"], (("0",),)
        )
        s = self.session("lab_017_etl_replay")
        sid = s["session_id"]
        simulate_session(DB, sid, "RESET")
        for action in ("NEXT", "REPLAY", "NEXT", "REPLAY", "NEXT", "REPLAY"):
            result = simulate_session(DB, sid, action)
            self.assertEqual(query_session(DB, sid, etl.REPLAY)["rows"], (("0",),))
        self.assertEqual(result["etl_simulation"]["batch_no"], 3)
        self.assertEqual(result["etl_simulation"]["steps"][-1]["target_rows"], 4)
        challenge = self.session("lab_017_etl_replay", mode="CHALLENGE")
        with self.assertRaises(ValueError):
            simulate_session(DB, challenge["session_id"], "RESET")

    def test_http_actual_independent_counts_and_bad_plans(self):
        for key, scenarios in http.SCENARIOS.items():
            for scenario in ("clean", *scenarios):
                with self.subTest(key=key, scenario=scenario):
                    s = self.session(key, scenario)
                    q = query_session(DB, s["session_id"], http.SOLUTIONS[key])
                    self.assertEqual(q["status"], "SUCCESS")
                    self.assertEqual(
                        q["rows"], [[str(http.expected_count(key, scenario))]]
                    )
                    self.assertGreater(q["http"]["request_count"], 0)
                    if key == http.IDS[2] and scenario == "clean":
                        self.assertEqual(
                            [r["status"] for r in q["http"]["trace"]],
                            [429, 503, 200] * 3,
                        )
                    if key == http.IDS[3] and scenario == "clean":
                        self.assertEqual(len(q["http"]["target"]), 5)
                        with connect(DB) as c:
                            from psycopg import sql

                            schema = c.execute(
                                "SELECT snapshot_schema FROM metadata.lab_sessions WHERE session_id=%s",
                                (s["session_id"],),
                            ).fetchone()[0]
                            self.assertEqual(
                                c.execute(
                                    sql.SQL(
                                        "SELECT COUNT(*) FROM {}.api_target"
                                    ).format(sql.Identifier(schema))
                                ).fetchone()[0],
                                5,
                            )
                    if scenario in ("api_timeout", "api_exhausted"):
                        self.assertEqual(q["http"]["execution_status"], "FAILED")
                    if scenario == "api_wrong_type":
                        self.assertEqual(q["http"]["execution_status"], "SUCCESS")
                        self.assertEqual(q["http"]["data_quality_status"], "FAIL")
        sid = self.session(http.IDS[0])["session_id"]
        with self.assertRaises(ValueError):
            query_session(DB, sid, '{"url":"http://external.invalid"}')

    def test_http_graders_reject_incomplete_checks_and_preserve_real_target(self):
        for key in http.IDS:
            s = self.session(key, mode="CHALLENGE")
            sid = s["session_id"]
            self.assertNotIn("scenario_id", s)
            self.assertNotIn("solution_sql", s)
            bad = submit_solution(
                DB, sid, json.dumps(http.BASE), "Only status checks are insufficient"
            )
            self.assertEqual(bad["status"], "FAIL", bad)
            self.assertNotIn("cases", bad)
            query_session(DB, sid, http.SOLUTIONS[key])
            before = inspect_session(DB, sid)["queries"][-1]["result"]
            result = submit_solution(
                DB,
                sid,
                http.SOLUTIONS[key],
                "Checked independent HTTP and database evidence",
            )
            self.assertEqual(result["status"], "PASS", result)
            self.assertEqual(inspect_session(DB, sid)["status"], "COMPLETED")
            self.assertEqual(inspect_session(DB, sid)["queries"][-1]["result"], before)
        s = self.session(http.IDS[3])
        sid = s["session_id"]
        bad = json.loads(http.SOLUTIONS[http.IDS[3]])
        bad["idempotent"] = False
        self.assertEqual(
            submit_solution(
                DB, sid, json.dumps(bad), "Append does not prove replay safety"
            )["status"],
            "FAIL",
        )

    def test_http_infrastructure_error_is_error_and_reveal_is_not_completion(self):
        s = self.session(http.IDS[0])
        sid = s["session_id"]
        with patch(
            "backend.app.learning.http_exercises.run",
            side_effect=RuntimeError("fixture failed"),
        ):
            self.assertEqual(
                submit_solution(
                    DB,
                    sid,
                    http.SOLUTIONS[http.IDS[0]],
                    "Execution error must not be a defect",
                )["status"],
                "ERROR",
            )
        from backend.app.learning.service import reveal_solution

        self.assertEqual(reveal_solution(DB, sid)["status"], "REVEALED")

    def test_course_owner_progress_resume_csrf_and_migration(self):
        from tests.auth_helpers import signed_client

        with transaction(DB) as c:
            c.execute("DELETE FROM metadata.auth_budgets")
        a, user = signed_client(DB)
        b, _ = signed_client(DB)
        all_ids = []
        for key in ("lab_014_etl_mapping", http.IDS[3]):
            r = a.post(
                "/api/sessions",
                json={"lab_id": key, "mode": "SANDBOX", "scenario": "clean"},
            )
            self.assertEqual(r.status_code, 201, r.text)
            sid = r.json()["session_id"]
            all_ids.append(sid)
            self.assertEqual(b.get("/api/sessions/" + sid).status_code, 404)
            for action, body in [
                ("query", {"sql": PROFILES[key].solution}),
                (
                    "submit",
                    {"sql": PROFILES[key].solution, "conclusion": "Checked evidence"},
                ),
                ("simulation", {"action": "RESET"}),
            ]:
                self.assertEqual(
                    b.post(
                        "/api/sessions/" + sid + "/" + action, json=body
                    ).status_code,
                    404,
                )
                self.assertEqual(
                    a.post(
                        "/api/sessions/" + sid + "/" + action,
                        json=body,
                        headers={"X-CSRF-Token": ""},
                    ).status_code,
                    403,
                )
            self.assertEqual(
                a.post(
                    "/api/sessions/" + sid + "/submit",
                    json={
                        "sql": PROFILES[key].solution,
                        "conclusion": "Validated contract",
                    },
                ).json()["status"],
                "PASS",
            )
        self.assertEqual(
            {p["course_id"] for p in a.get("/api/progress").json()},
            {"etl-testing", "api-testing"},
        )
        self.assertEqual(b.get("/api/progress").json(), [])
        initialize_database(DB)  # idempotent migration must retain accounts and work
        self.assertEqual(
            {e["course_id"] for e in a.get("/api/enrollments").json()},
            {"etl-testing", "api-testing"},
        )
        for sid in all_ids:
            self.assertEqual(
                a.get("/api/sessions/" + sid).json()["status"], "COMPLETED"
            )
