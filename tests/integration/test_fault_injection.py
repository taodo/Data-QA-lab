import os
from unittest.mock import patch
import unittest

from backend.app.domain.models import QualityStatus


DATABASE_URL = os.getenv("DATA_QA_TEST_DATABASE_URL")


@unittest.skipUnless(DATABASE_URL, "set DATA_QA_TEST_DATABASE_URL to run PostgreSQL integration tests")
class FaultInjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from backend.app.persistence.database import initialize_database
        initialize_database(DATABASE_URL)

    def setUp(self):
        from backend.app.persistence.database import transaction
        from pipeline.source.seed import seed_source

        with transaction(DATABASE_URL) as connection:
            connection.execute("DELETE FROM fault_workspace.orders_report")
            connection.execute("DELETE FROM fault_workspace.daily_sales_report")
            connection.execute("DELETE FROM metadata.fault_runs")
        seed_source(DATABASE_URL, order_count=250)

    def pipeline_run(self):
        from pipeline.jobs.orders import run_orders_pipeline
        return run_orders_pipeline(DATABASE_URL)

    def target_fingerprint(self, run_id):
        from backend.app.persistence.database import connect
        with connect(DATABASE_URL) as connection:
            return connection.execute(
                """SELECT COUNT(*), SUM(order_id), SUM(net_amount)
                   FROM target.orders_report WHERE run_id = %s""",
                (run_id,),
            ).fetchone()

    def test_each_scenario_fails_expected_rules_without_mutating_target(self):
        from backend.app.persistence.database import connect
        from faults.service import apply_fault, reset_fault, run_fault_quality
        from qa.engine.runner import run_quality_suite

        expected_failures = {
            "missing_order": {"count_target_orders", "keys_silver_to_target_orders"},
            "duplicate_order": {"count_target_orders", "unique_target_order_id"},
            "null_net_amount": {"required_target_orders", "fields_silver_to_target_orders"},
            "wrong_net_amount": {"fields_silver_to_target_orders"},
        }

        for scenario_id, required_failures in expected_failures.items():
            with self.subTest(scenario_id=scenario_id):
                pipeline = self.pipeline_run()
                before = self.target_fingerprint(pipeline.run_id)
                fault = apply_fault(DATABASE_URL, scenario_id, pipeline.run_id)
                quality = run_fault_quality(DATABASE_URL, fault.fault_run_id)
                failed = {
                    result.rule_id
                    for result in quality.results
                    if result.status is QualityStatus.FAIL
                }

                self.assertEqual(fault.mutation_evidence["key"], {"order_id": 1})
                self.assertEqual(quality.status, QualityStatus.FAIL)
                self.assertTrue(required_failures.issubset(failed))
                self.assertEqual(before, self.target_fingerprint(pipeline.run_id))
                with connect(DATABASE_URL) as connection:
                    statuses = connection.execute(
                        """SELECT execution_status, data_quality_status
                           FROM metadata.pipeline_runs WHERE run_id = %s""",
                        (pipeline.run_id,),
                    ).fetchone()
                self.assertEqual(statuses, ("SUCCESS", "FAIL"))

                reset = reset_fault(DATABASE_URL, fault.fault_run_id)
                self.assertEqual(reset.status.value, "RESET")
                clean = run_quality_suite(DATABASE_URL, pipeline.run_id)
                self.assertEqual(clean.status, QualityStatus.PASS)

    def test_active_fault_is_exclusive_and_reset_is_idempotent_and_reproducible(self):
        from faults.contracts import FaultStateError
        from faults.service import apply_fault, reset_fault

        pipeline = self.pipeline_run()
        first = apply_fault(DATABASE_URL, "wrong_net_amount", pipeline.run_id)
        with self.assertRaisesRegex(FaultStateError, "already has active fault"):
            apply_fault(DATABASE_URL, "missing_order", pipeline.run_id)

        first_reset = reset_fault(DATABASE_URL, first.fault_run_id)
        second_reset = reset_fault(DATABASE_URL, first.fault_run_id)
        self.assertEqual(first_reset, second_reset)

        repeated = apply_fault(DATABASE_URL, "wrong_net_amount", pipeline.run_id)
        self.assertNotEqual(first.fault_run_id, repeated.fault_run_id)
        self.assertEqual(first.mutation_evidence, repeated.mutation_evidence)

    def test_failed_apply_rolls_back_workspace_and_metadata(self):
        from backend.app.persistence.database import connect
        from faults.service import apply_fault

        pipeline = self.pipeline_run()
        with patch("faults.service._apply_mutation", side_effect=RuntimeError("forced failure")):
            with self.assertRaisesRegex(RuntimeError, "forced failure"):
                apply_fault(DATABASE_URL, "missing_order", pipeline.run_id)

        with connect(DATABASE_URL) as connection:
            workspace_count = connection.execute(
                "SELECT COUNT(*) FROM fault_workspace.orders_report WHERE run_id = %s",
                (pipeline.run_id,),
            ).fetchone()[0]
            metadata_count = connection.execute(
                "SELECT COUNT(*) FROM metadata.fault_runs WHERE pipeline_run_id = %s",
                (pipeline.run_id,),
            ).fetchone()[0]
        self.assertEqual(workspace_count, 0)
        self.assertEqual(metadata_count, 0)
