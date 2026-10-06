import os
from decimal import Decimal
import unittest

DATABASE_URL = os.getenv("DATA_QA_TEST_DATABASE_URL")

@unittest.skipUnless(DATABASE_URL, "set DATA_QA_TEST_DATABASE_URL to run PostgreSQL integration tests")
class PostgresPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from backend.app.persistence.database import initialize_database
        initialize_database(DATABASE_URL)

    def test_clean_pipeline_is_repeatable_and_retains_run_evidence(self):
        from pipeline.source.seed import seed_source
        from pipeline.jobs.orders import inspect_run, run_orders_pipeline
        from backend.app.persistence.database import connect

        seed = seed_source(DATABASE_URL)
        first = run_orders_pipeline(DATABASE_URL)
        second = run_orders_pipeline(DATABASE_URL)

        self.assertEqual(seed["orders"], 10_000)
        self.assertNotEqual(first.run_id, second.run_id)
        self.assertEqual(first.execution_status, "SUCCESS")
        self.assertEqual(first.data_quality_status, "NOT_RUN")
        self.assertEqual(tuple(stage.name for stage in first.stages),
                         ("SOURCE", "BRONZE", "SILVER", "GOLD", "TARGET"))
        self.assertEqual(first.stages[0].row_count, 10_000)
        self.assertEqual(first.stages[1].row_count, 10_000)
        self.assertEqual(first.stages[2].row_count, 10_000)
        self.assertEqual(first.stages[3].metrics["order_count"], 10_000)
        self.assertEqual(first.stages[4].row_count, 10_000)

        with connect(DATABASE_URL) as connection:
            count, revenue = connection.execute(
                "SELECT COUNT(*), SUM(net_amount) FROM target.orders_report WHERE run_id = %s",
                (first.run_id,),
            ).fetchone()
            old_evidence = connection.execute(
                "SELECT COUNT(*) FROM metadata.stage_runs WHERE run_id = %s", (first.run_id,)
            ).fetchone()[0]
        self.assertEqual(count, 10_000)
        self.assertEqual(revenue, Decimal("25245493.29"))
        self.assertEqual(old_evidence, 5)
        self.assertEqual(inspect_run(DATABASE_URL, first.run_id)["execution_status"], "SUCCESS")
