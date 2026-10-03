import json
import os
import time
import unittest
from unittest.mock import patch
from uuid import uuid4

from backend.app.learning.content import SOLUTION
from backend.app.learning.contracts import QueryLimits, LabStateError, SqlSecurityError

DATABASE_URL = os.getenv("DATA_QA_TEST_DATABASE_URL")


@unittest.skipUnless(DATABASE_URL, "set DATA_QA_TEST_DATABASE_URL to run PostgreSQL integration tests")
class LearningLabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from backend.app.persistence.database import initialize_database
        from backend.app.learning.sql_runtime import initialize_sql_security
        initialize_database(DATABASE_URL)
        initialize_sql_security(DATABASE_URL)

    def setUp(self):
        from pipeline.source.seed import seed_source
        from pipeline.jobs.orders import run_orders_pipeline
        from backend.app.learning.service import start_session
        from backend.app.persistence.database import connect
        seed_source(DATABASE_URL, 20)
        self.pipeline = run_orders_pipeline(DATABASE_URL)
        self.session = start_session(DATABASE_URL, pipeline_run_id=self.pipeline.run_id,
                                     mode="SANDBOX", scenario="equal_count_swap")
        self.sid = self.session["session_id"]
        with connect(DATABASE_URL) as connection:
            self.schema = connection.execute(
                "SELECT snapshot_schema FROM metadata.lab_sessions WHERE session_id=%s", (self.sid,)
            ).fetchone()[0]

    def tearDown(self):
        from psycopg import sql
        from backend.app.persistence.database import transaction
        with transaction(DATABASE_URL) as connection:
            schemas = connection.execute(
                "SELECT snapshot_schema FROM metadata.lab_sessions WHERE pipeline_run_id=%s",
                (self.pipeline.run_id,),
            ).fetchall()
            for (schema,) in schemas:
                connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))

    def query(self, query, **kwargs):
        from backend.app.learning.sql_runtime import run_sql
        return run_sql(DATABASE_URL, self.schema, query, **kwargs)

    def test_real_restricted_identity_and_direct_database_permissions(self):
        from backend.app.learning.sql_runtime import restricted_workspace
        import psycopg
        from psycopg import sql
        with restricted_workspace(DATABASE_URL, self.schema) as (connection, schema, role):
            identity = connection.execute("SELECT current_user, session_user").fetchone()
            self.assertEqual(identity, (role, role))
            # Direct statements test database enforcement, independent of cursor parsing.
            for statement in (
                "INSERT INTO target_orders SELECT * FROM target_orders",
                "UPDATE target_orders SET order_id=99", "DELETE FROM target_orders",
                "CREATE TABLE arbitrary (id int)", "CREATE TEMP TABLE arbitrary (id int)",
                "SELECT * FROM metadata.fault_runs", "SELECT * FROM target.orders_report",
                "COPY target_orders TO '/tmp/learner-export'", "SET ROLE data_qa_lab",
                "SELECT pg_read_file('/etc/passwd')",
            ):
                with self.subTest(statement=statement):
                    with self.assertRaises(psycopg.Error):
                        with connection.transaction():
                            connection.execute(statement)

    def test_read_queries_ctes_and_cleanup(self):
        result = self.query("WITH orders AS (SELECT * FROM source_orders) SELECT COUNT(*) AS n FROM orders;")
        self.assertEqual(result.status, "SUCCESS")
        self.assertEqual(result.rows, (("20",),))
        from backend.app.persistence.database import connect
        with connect(DATABASE_URL) as connection:
            role_count = connection.execute("SELECT COUNT(*) FROM pg_roles WHERE rolname LIKE 'learner_role_%'").fetchone()[0]
            schema_count = connection.execute("SELECT COUNT(*) FROM pg_namespace WHERE nspname LIKE 'learner_query_%'").fetchone()[0]
        self.assertEqual((role_count, schema_count), (0, 0))

    def test_single_statement_and_writes_are_rejected_without_mutation(self):
        for query in ("SELECT 1; SELECT 2", "DELETE FROM target_orders RETURNING order_id",
                      "WITH gone AS (DELETE FROM target_orders RETURNING *) SELECT * FROM gone",
                      "SELECT * INTO bad_copy FROM target_orders", "SELECT * FROM metadata.lab_sessions"):
            with self.subTest(query=query):
                self.assertEqual(self.query(query).status, "ERROR")
        self.assertEqual(self.query("SELECT COUNT(*) FROM source_orders").rows, (("20",),))

    def test_row_column_cell_and_byte_limits(self):
        rows = self.query("SELECT generate_series(1,1000)")
        self.assertTrue(rows.truncated)
        self.assertEqual(len(rows.rows), 100)
        cell = self.query("SELECT repeat('x',10000)")
        self.assertTrue(cell.truncated)
        self.assertEqual(len(cell.rows[0][0]), 2048)
        columns = self.query("SELECT " + ",".join(f"{i} AS c{i}" for i in range(21)))
        self.assertEqual(columns.error, "COLUMN_LIMIT")
        total = self.query("SELECT repeat('x',100) FROM generate_series(1,100)", limits=QueryLimits(max_bytes=256))
        self.assertTrue(total.truncated)
        self.assertLessEqual(len(json.dumps([total.columns, total.rows]).encode()), 280)

    def test_server_timeout_and_independent_watchdog(self):
        from backend.app.learning.sql_runtime import _terminate_execution
        limits = QueryLimits(timeout_ms=100, watchdog_ms=400)
        for index, query in enumerate((
            "SELECT pg_sleep(10)",
            "SELECT CASE WHEN set_config('statement_timeout','0',false)='0' THEN pg_sleep(10) END",
        )):
            with self.subTest(query=query):
                started = time.monotonic()
                with patch("backend.app.learning.sql_runtime._terminate_execution", wraps=_terminate_execution) as watchdog:
                    result = self.query(query, limits=limits)
                    self.assertEqual(watchdog.call_count, index)
                self.assertEqual(result.error, "TIMEOUT")
                self.assertLess(time.monotonic() - started, 5)
        self.assertEqual(self.query("SELECT 1").status, "SUCCESS")

    def test_good_submission_passes_and_retains_history_across_resume(self):
        from backend.app.learning.service import submit_solution, inspect_session
        result = submit_solution(DATABASE_URL, self.sid, SOLUTION, "Counts alone miss replaced keys.")
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(len(result["cases"]), 4)
        resumed = inspect_session(DATABASE_URL, self.sid)
        self.assertEqual(resumed["status"], "COMPLETED")
        self.assertEqual(resumed["submissions"][0]["submission_id"], result["submission_id"])
        self.assertIn("solution_sql", resumed)
        with self.assertRaises(LabStateError):
            submit_solution(DATABASE_URL, self.sid, SOLUTION, "again")

    def test_false_positive_false_negative_and_bad_contract_fail(self):
        from backend.app.learning.service import submit_solution
        queries = (
            "SELECT 1 AS violation_count", "SELECT 0 AS violation_count",
            "SELECT abs((SELECT COUNT(*) FROM source_orders)-(SELECT COUNT(*) FROM target_orders)) AS violation_count",
            "SELECT COUNT(*) AS n FROM target_orders", "SELECT -1 AS violation_count",
        )
        for query in queries:
            with self.subTest(query=query):
                self.assertEqual(submit_solution(DATABASE_URL, self.sid, query, "test")["status"], "FAIL")
        self.assertEqual(submit_solution(DATABASE_URL, self.sid, "SELECT invalid_column", "test")["status"], "ERROR")

    def test_challenge_visibility_hints_and_reveal_lifecycle(self):
        from backend.app.learning.service import (
            start_session, next_hint, inspect_session, submit_solution, reveal_solution, query_session,
        )
        challenge = start_session(DATABASE_URL, pipeline_run_id=self.pipeline.run_id)
        sid = challenge["session_id"]
        for key in ("scenario_id", "snapshot_schema", "solution_sql"):
            self.assertNotIn(key, challenge)
        for expected in (1, 2, 3, 3):
            self.assertEqual(next_hint(DATABASE_URL, sid)["level"], expected)
        failure = submit_solution(DATABASE_URL, sid, "SELECT 0 AS violation_count", "test")
        self.assertNotIn("cases", failure)
        self.assertNotIn("solution_sql", failure)
        query_session(DATABASE_URL, sid, "SELECT COUNT(*) FROM target_orders")
        resumed = inspect_session(DATABASE_URL, sid)
        self.assertEqual(len(resumed["queries"]), 1)
        self.assertNotIn("scenario_id", resumed)
        revealed = reveal_solution(DATABASE_URL, sid)
        self.assertEqual(revealed["status"], "REVEALED")
        self.assertIn("solution_sql", revealed)
        with self.assertRaises(LabStateError):
            submit_solution(DATABASE_URL, sid, SOLUTION, "after reveal")

    def test_sessions_and_pipeline_data_are_isolated(self):
        from backend.app.learning.service import start_session
        from backend.app.persistence.database import connect
        other = start_session(DATABASE_URL, pipeline_run_id=self.pipeline.run_id,
                              mode="SANDBOX", scenario="missing_order")
        with connect(DATABASE_URL) as connection:
            other_schema = connection.execute("SELECT snapshot_schema FROM metadata.lab_sessions WHERE session_id=%s",
                                               (other["session_id"],)).fetchone()[0]
            count = connection.execute("SELECT COUNT(*) FROM target.orders_report WHERE run_id=%s",
                                       (self.pipeline.run_id,)).fetchone()[0]
        self.assertEqual(count, 20)
        self.assertEqual(self.query(f"SELECT * FROM {other_schema}.target_orders").status, "ERROR")
        self.assertEqual(self.query("SELECT COUNT(*) FROM target_orders").rows, (("20",),))

    def test_public_privilege_misconfiguration_fails_closed(self):
        from backend.app.persistence.database import transaction
        with transaction(DATABASE_URL) as connection:
            connection.execute("GRANT USAGE ON SCHEMA target TO PUBLIC")
        try:
            with self.assertRaises(SqlSecurityError):
                self.query("SELECT 1")
        finally:
            with transaction(DATABASE_URL) as connection:
                connection.execute("REVOKE USAGE ON SCHEMA target FROM PUBLIC")

    def test_user_schema_with_pg_like_name_is_not_a_system_schema(self):
        from psycopg import sql
        from backend.app.persistence.database import transaction
        schema = "pguser_" + uuid4().hex
        with transaction(DATABASE_URL) as connection:
            connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
            connection.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO PUBLIC").format(sql.Identifier(schema)))
        try:
            with self.assertRaises(SqlSecurityError):
                self.query("SELECT 1")
        finally:
            with transaction(DATABASE_URL) as connection:
                connection.execute(sql.SQL("DROP SCHEMA {}").format(sql.Identifier(schema)))
