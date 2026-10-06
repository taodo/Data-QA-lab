import os
import unittest
from backend.app.learning.profiles import PROFILES as ALL_PROFILES
from backend.app.learning.http_exercises import IDS
PROFILES={key:value for key,value in ALL_PROFILES.items() if key not in IDS}
from backend.app.learning.service import start_session, submit_solution, inspect_session, query_session

DB = os.getenv("DATA_QA_TEST_DATABASE_URL")


@unittest.skipUnless(DB, "PostgreSQL test database required")
class CurriculumIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from backend.app.persistence.database import initialize_database
        from backend.app.learning.sql_runtime import initialize_sql_security
        from pipeline.source.seed import seed_source
        from pipeline.jobs.orders import run_orders_pipeline
        initialize_database(DB)
        initialize_sql_security(DB)
        seed_source(DB, 40)
        cls.pipeline = run_orders_pipeline(DB)

    def session(self, lab_id, mode="CHALLENGE", scenario=None):
        return start_session(DB,lab_id,self.pipeline.run_id,mode,scenario)

    def test_all_lessons_reject_constants_and_accept_real_checks(self):
        from backend.app.persistence.database import connect
        for lab_id,profile in PROFILES.items():
            with self.subTest(lab_id=lab_id):
                session = self.session(lab_id)
                self.assertNotIn("scenario_id",session)
                for constant in (0,1):
                    result=submit_solution(DB,session["session_id"],f"SELECT {constant} AS violation_count","Constant is not a check")
                    self.assertEqual(result["status"],"FAIL")
                    self.assertNotIn("cases",result)
                passed=submit_solution(DB,session["session_id"],profile.solution,"Validated the documented rule")
                self.assertEqual(passed["status"],"PASS",passed)
                self.assertEqual(inspect_session(DB,session["session_id"])["status"],"COMPLETED")
        with connect(DB) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM target.orders_report WHERE run_id=%s",(self.pipeline.run_id,)).fetchone()[0],40)

    def test_valid_zero_wrong_null_and_duplicate_metric_traps(self):
        cases=(
            ("lab_003_nulls","SELECT COUNT(*) AS violation_count FROM target_orders WHERE net_amount IS NULL OR net_amount=0"),
            ("lab_003_nulls","SELECT COUNT(*) AS violation_count FROM target_orders WHERE net_amount=NULL"),
            ("lab_004_duplicates","SELECT COUNT(*)-COUNT(DISTINCT order_id) AS violation_count FROM target_orders"),
            ("lab_005_calculations","SELECT COUNT(*) AS violation_count FROM source_orders s JOIN target_orders t USING(order_id) WHERE t.net_amount <> s.gross_amount-s.discount_amount-s.refund_amount"),
            ("lab_006_capstone",PROFILES["lab_001_record_count"].solution),
        )
        for lab_id,query in cases:
            with self.subTest(lab_id=lab_id,query=query):
                sid=self.session(lab_id)["session_id"]
                self.assertEqual(submit_solution(DB,sid,query,"Incomplete check")["status"],"FAIL")

    def test_each_sandbox_scenario_and_clean_baseline_are_runnable(self):
        for lab_id,profile in PROFILES.items():
            for scenario in (*profile.scenarios,"clean"):
                with self.subTest(lab_id=lab_id,scenario=scenario):
                    session=self.session(lab_id,"SANDBOX",scenario)
                    result=query_session(DB,session["session_id"],profile.solution)
                    self.assertEqual(result["status"],"SUCCESS",result)
                    count=int(result["rows"][0][0])
                    self.assertEqual(count,0) if scenario=="clean" else self.assertGreater(count,0)
        with self.assertRaises(ValueError):
            self.session("lab_003_nulls","CHALLENGE","null_net_amount")
        with self.assertRaises(ValueError):
            self.session("lab_003_nulls","SANDBOX","duplicate_order")

    def test_oracle_execution_errors_do_not_fail_the_learner(self):
        from unittest.mock import patch
        from backend.app.learning.contracts import QueryResult
        from backend.app.learning.sql_runtime import run_sql
        lab_id="lab_003_nulls"
        sid=self.session(lab_id)["session_id"]
        def failing_oracle(database_url,snapshot,query,variant="current"):
            if query==PROFILES[lab_id].solution:
                return QueryResult("ERROR",error="TIMEOUT")
            return run_sql(database_url,snapshot,query,variant)
        with patch("backend.app.learning.service.run_sql",side_effect=failing_oracle):
            result=submit_solution(DB,sid,"SELECT 1 AS violation_count","A reference evaluation error is not a learner defect.")
        self.assertEqual(result["status"],"ERROR")
        self.assertEqual(inspect_session(DB,sid)["status"],"ACTIVE")
