import os
import unittest
from uuid import uuid4
from unittest.mock import patch

DB = os.getenv("DATA_QA_TEST_DATABASE_URL")


@unittest.skipUnless(DB, "PostgreSQL test database required")
class BootstrapTests(unittest.TestCase):
    def test_fresh_setup_and_restart_preserve_history_and_baseline(self):
        from psycopg import sql
        from psycopg.conninfo import make_conninfo
        from backend.app.persistence.database import connect
        from backend.app.bootstrap import prepare_local
        from backend.app.learning.service import start_session, query_session, inspect_session
        name="release_test_"+uuid4().hex
        isolated=make_conninfo(DB,dbname=name)
        with connect(DB) as admin:
            admin.autocommit=True
            admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
        try:
            initial=prepare_local(isolated)
            self.assertTrue(initial["created_baseline"])
            session=start_session(isolated)
            sid=session["session_id"]
            query_session(isolated,sid,"SELECT COUNT(*) FROM source_orders")
            # Emulate the approved V1 scenario constraint before upgrading in place.
            with connect(isolated) as connection:
                connection.execute("ALTER TABLE metadata.lab_sessions DROP CONSTRAINT lab_sessions_scenario_id_check")
                connection.execute("ALTER TABLE metadata.lab_sessions ADD CONSTRAINT lab_sessions_scenario_id_check CHECK (scenario_id IN ('clean','missing_order','equal_count_swap','invalid_customer','null_net_amount','duplicate_order','wrong_net_amount','mixed_order_faults','daily_wrong'))")
            second=prepare_local(isolated)
            self.assertFalse(second["created_baseline"])
            self.assertEqual(initial["run_id"],second["run_id"])
            self.assertEqual(inspect_session(isolated,sid)["queries"][0]["result"]["rows"],[["1000"]])
            advanced=start_session(isolated,"lab_010_incremental",initial["run_id"],"SANDBOX","inc_append")
            third=prepare_local(isolated)
            self.assertEqual(third["run_id"],initial["run_id"])
            self.assertEqual(inspect_session(isolated,advanced["session_id"])["simulation"]["step_count"],4)
            self.assertEqual(inspect_session(isolated,sid)["query_count"],1)
        finally:
            with connect(DB) as admin:
                admin.autocommit=True
                admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))
