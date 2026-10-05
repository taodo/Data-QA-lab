"""Independent numeric expectations and real PostgreSQL session/permission checks."""
import os
import unittest
from backend.app.learning.advanced_profiles import SPECS, UTC_SQL, FRESHNESS_SQL, SCD2_SQL
from backend.app.learning.contracts import violation_count, LabStateError
from backend.app.learning.service import start_session, query_session, submit_solution, simulate_session, inspect_session
from backend.app.learning.sql_runtime import run_sql
from backend.app.persistence.database import connect

DB=os.getenv("DATA_QA_TEST_DATABASE_URL")


@unittest.skipUnless(DB,"PostgreSQL test database required")
class AdvancedIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from backend.app.persistence.database import initialize_database
        from backend.app.learning.sql_runtime import initialize_sql_security
        from pipeline.source.seed import seed_source
        from pipeline.jobs.orders import run_orders_pipeline
        initialize_database(DB);initialize_sql_security(DB)
        seed_source(DB,20);cls.pipeline=run_orders_pipeline(DB)

    def session(self,lab_id,scenario="clean",mode="SANDBOX"):
        return start_session(DB,lab_id,self.pipeline.run_id,mode,scenario if mode=="SANDBOX" else None)

    def schema(self,sid):
        with connect(DB) as connection:
            return connection.execute("SELECT snapshot_schema FROM metadata.lab_sessions WHERE session_id=%s",(sid,)).fetchone()[0]

    def test_reference_counts_match_independent_fixture_expectations(self):
        expectations={
          "lab_007_join_grain":{"join_fanout":1,"join_fanout_two":2,"join_missing":1,"join_unexpected":1,"join_null":1,"join_zero":0},
          "lab_008_latest_version":{"latest_stale":1,"latest_stale_two":2,"latest_tie":1,"latest_missing":1,"latest_null":1},
          "lab_009_utc_dates":{"utc_connection_zone":0,"utc_local_day":3,"utc_missing":1,"utc_null":1},
          "lab_010_incremental":{"inc_append":8,"inc_event_watermark":3,"inc_stale":3,"inc_missing":1},
          "lab_011_freshness":{"fresh_boundary":0,"fresh_stale":1,"fresh_load_stale":1,"fresh_missing":1,"fresh_null":1,"fresh_future":1,"fresh_failed":1,"fresh_multiple":2},
          "lab_012_scd_type1":{"scd1_stale":1,"scd1_tie":1,"scd1_missing":1,"scd1_null":1},
          "lab_013_scd_type2":{"scd2_overlap":2,"scd2_two_current":2,"scd2_missing":1,"scd2_invalid":2,"scd2_duplicate":3,"scd2_wrong_tier":1,"scd2_gap":1},
        }
        for lab_id,counts in expectations.items():
            schema=self.schema(self.session(lab_id)["session_id"])
            counts={"clean":0,"adv_shifted":0,**counts}
            self.assertEqual(set(counts),set(SPECS[lab_id][1]))
            for variant,expected in counts.items():
                with self.subTest(lab_id=lab_id,variant=variant):
                    result=run_sql(DB,schema,SPECS[lab_id][2],variant)
                    self.assertEqual(violation_count(result),expected,result)

    def test_semantic_traps_are_rejected_by_real_grading(self):
        bad_join=SPECS["lab_007_join_grain"][2].replace("SUM(net_amount)","SUM(DISTINCT net_amount)")
        bad_latest=SPECS["lab_008_latest_version"][2].replace("updated_at DESC,event_id DESC","updated_at DESC,event_id ASC")
        bad_utc=UTC_SQL.replace("(ordered_at AT TIME ZONE 'UTC')::date","ordered_at::date")
        bad_fresh=FRESHNESS_SQL.replace(" > r.sla_minutes", " >= r.sla_minutes")
        bad_future=FRESHNESS_SQL.replace(" OR o.last_success_at > r.as_of OR o.last_event_at > r.as_of", "")
        bad_overlap=SCD2_SQL.replace("a.valid_from<COALESCE", "a.valid_from<=COALESCE").replace("b.valid_from<COALESCE", "b.valid_from<=COALESCE")
        for lab_id,query in (("lab_007_join_grain",bad_join),("lab_008_latest_version",bad_latest),("lab_009_utc_dates",bad_utc),("lab_011_freshness",bad_fresh),("lab_011_freshness",bad_future),("lab_013_scd_type2",bad_overlap)):
            with self.subTest(lab_id=lab_id,query=query):
                sid=self.session(lab_id)["session_id"]
                result=submit_solution(DB,sid,query,"This deliberately incomplete check must fail.")
                self.assertEqual(result["status"],"FAIL",result)

    def test_incremental_real_replay_late_arrival_and_session_isolation(self):
        first=self.session("lab_010_incremental");sid=first["session_id"]
        other=self.session("lab_010_incremental","inc_append")
        baseline_other=other["simulation"]
        simulate_session(DB,sid,"RESET")
        self.assertEqual(query_session(DB,sid,"SELECT COUNT(*) FROM incremental_target")["rows"],(("0",),))
        for op,rows in (("NEXT",2),("NEXT",3),("REPLAY",3),("NEXT",4),("REPLAY",4)):
            state=simulate_session(DB,sid,op)
            self.assertEqual(state["simulation"]["steps"][-1]["target_rows"],rows)
            self.assertEqual(violation_count(run_sql(DB,self.schema(sid),SPECS["lab_010_incremental"][2])),0)
        target=query_session(DB,sid,"SELECT event_id FROM incremental_target ORDER BY order_id")["rows"]
        self.assertEqual(target,(("3",),("6",),("7",),("5",)))
        self.assertEqual(inspect_session(DB,other["session_id"])["simulation"],baseline_other)
        with self.assertRaises(LabStateError):simulate_session(DB,sid,"NEXT")
        self.assertEqual(submit_solution(DB,sid,SPECS["lab_010_incremental"][2],"Arrival availability and greatest business version preserve replay safety.")["status"],"PASS")
        with self.assertRaises(LabStateError):simulate_session(DB,sid,"RESET")
        with connect(DB) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM target.orders_report WHERE run_id=%s",(self.pipeline.run_id,)).fetchone()[0],20)

    def test_advanced_permissions_and_simulation_inputs_stay_bounded(self):
        from fastapi.testclient import TestClient
        from backend.app.api import create_app
        from backend.app.learning.service import reveal_solution
        sandbox=self.session("lab_010_incremental");challenge=self.session("lab_010_incremental",mode="CHALLENGE")
        other=self.session("lab_011_freshness")
        sid=sandbox["session_id"]
        for query in ("SELECT * FROM metadata.lab_sessions","SELECT * FROM source_orders",f"SELECT * FROM {self.schema(other['session_id'])}.freshness_observations","DELETE FROM incremental_target","SELECT * FROM target_customer_history"):
            self.assertEqual(query_session(DB,sid,query)["status"],"ERROR",query)
        from tests.auth_helpers import signed_client
        from backend.app.persistence.database import transaction
        client, user = signed_client(DB)
        with transaction(DB) as connection:
            for item in (sandbox, challenge, other):
                connection.execute('UPDATE metadata.lab_sessions SET owner_id=%s WHERE session_id=%s',(user['user_id'],item['session_id']))
        with client:
            path=f"/api/sessions/{sid}/simulation"
            self.assertEqual(client.post(path,json={"action":"NEXT","sql":"DELETE FROM incremental_target"}).status_code,422)
            self.assertEqual(client.post(path,json={"action":"DROP"}).status_code,422)
            self.assertEqual(client.post(path,json={"action":"RESET"}).status_code,200)
            self.assertEqual(client.post(f"/api/sessions/{challenge['session_id']}/simulation",json={"action":"RESET"}).status_code,409)
            self.assertEqual(client.post(f"/api/sessions/{other['session_id']}/simulation",json={"action":"RESET"}).status_code,409)
            visible=client.get(f"/api/sessions/{challenge['session_id']}?language=VIE").json()
            self.assertNotIn("scenario_id",visible);self.assertNotIn("snapshot_schema",visible);self.assertNotIn("solution_sql",visible)
        reveal_solution(DB,sid)
        with self.assertRaises(LabStateError):simulate_session(DB,sid,"RESET")

    def test_simulation_history_limit_and_reset_preserve_queries(self):
        from backend.app.learning.advanced_workspace import execute
        sid=self.session("lab_010_incremental")["session_id"]
        query_session(DB,sid,"SELECT COUNT(*) FROM incremental_target")
        simulate_session(DB,sid,"RESET")
        schema=self.schema(sid)
        with connect(DB) as connection:
            execute(connection,schema,"INSERT INTO {s}.incremental_steps SELECT n,1,'REPLAY','SUCCESS',0,0,c.as_of FROM generate_series(1,100) n CROSS JOIN {s}.lab_context c")
        state=inspect_session(DB,sid)
        self.assertEqual(state["simulation"]["step_count"],100)
        self.assertEqual(len(state["simulation"]["steps"]),20)
        self.assertEqual(state["query_count"],1)
        with self.assertRaises(LabStateError):simulate_session(DB,sid,"REPLAY")
        state=simulate_session(DB,sid,"RESET")
        self.assertEqual(state["simulation"]["step_count"],0)
        self.assertEqual(state["query_count"],1)
