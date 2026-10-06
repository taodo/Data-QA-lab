import os
from uuid import uuid4
import unittest

from backend.app.domain.models import QualityStatus
from qa.engine.contracts import (
    ColumnExpectation, DatasetRegistry, DatasetSpec, FieldMapping,
    FieldReconciliationRule, KeyReconciliationRule, NotNullRule,
    SchemaRule, UniquenessRule, ValidationSuite,
)

DATABASE_URL = os.getenv("DATA_QA_TEST_DATABASE_URL")

@unittest.skipUnless(DATABASE_URL, "set DATA_QA_TEST_DATABASE_URL to run PostgreSQL integration tests")
class QualityEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from backend.app.persistence.database import initialize_database
        from pipeline.source.seed import seed_source
        initialize_database(DATABASE_URL)

    def setUp(self):
        from pipeline.source.seed import seed_source
        seed_source(DATABASE_URL, order_count=250)

    def pipeline_run(self):
        from pipeline.jobs.orders import run_orders_pipeline
        return run_orders_pipeline(DATABASE_URL)

    def test_clean_suite_passes_and_keeps_validation_history(self):
        from qa.engine.runner import inspect_quality_run, run_quality_suite
        pipeline = self.pipeline_run()
        first = run_quality_suite(DATABASE_URL, pipeline.run_id)
        second = run_quality_suite(DATABASE_URL, pipeline.run_id)

        self.assertEqual(first.status, QualityStatus.PASS)
        self.assertEqual(len(first.results), 26)
        self.assertTrue(all(result.status is QualityStatus.PASS for result in first.results))
        self.assertNotEqual(first.validation_run_id, second.validation_run_id)
        inspected = inspect_quality_run(DATABASE_URL, pipeline.run_id)
        self.assertEqual(inspected["validation_run_id"], str(second.validation_run_id))
        self.assertEqual(inspected["status"], "PASS")

    def test_missing_target_row_fails_quality_without_changing_execution(self):
        from backend.app.persistence.database import connect, transaction
        from qa.engine.runner import run_quality_suite
        pipeline = self.pipeline_run()
        with transaction(DATABASE_URL) as connection:
            connection.execute(
                """DELETE FROM target.orders_report WHERE run_id = %s AND order_id = (
                   SELECT MIN(order_id) FROM target.orders_report WHERE run_id = %s)""",
                (pipeline.run_id, pipeline.run_id),
            )
        quality = run_quality_suite(DATABASE_URL, pipeline.run_id)
        count_result = next(result for result in quality.results if result.rule_id == "count_target_orders")
        with connect(DATABASE_URL) as connection:
            statuses = connection.execute(
                "SELECT execution_status, data_quality_status FROM metadata.pipeline_runs WHERE run_id = %s",
                (pipeline.run_id,),
            ).fetchone()
        self.assertEqual(quality.status, QualityStatus.FAIL)
        self.assertEqual(count_result.status, QualityStatus.FAIL)
        self.assertEqual(statuses, ("SUCCESS", "FAIL"))

    def test_duplicate_null_and_schema_defects_fail_with_evidence(self):
        from backend.app.persistence.database import transaction
        from qa.engine.runner import run_quality_suite
        pipeline = self.pipeline_run()
        with transaction(DATABASE_URL) as connection:
            connection.execute("CREATE SCHEMA IF NOT EXISTS qa_fixture")
            connection.execute("DROP TABLE IF EXISTS qa_fixture.bad_orders")
            connection.execute(
                "CREATE TABLE qa_fixture.bad_orders (row_id BIGINT, order_id BIGINT, required_value TEXT)"
            )
            connection.execute(
                """INSERT INTO qa_fixture.bad_orders VALUES
                   (1, 7, 'ok'), (2, 7, NULL), (3, 8, 'ok')"""
            )
        registry = DatasetRegistry((DatasetSpec(
            "bad_orders", "qa_fixture", "bad_orders", run_scoped=False),))
        suite = ValidationSuite("fixture_defects", (
            UniquenessRule("duplicate_order_id", "bad_orders", ("order_id",)),
            NotNullRule("required_value", "bad_orders", ("required_value",)),
            SchemaRule("wrong_schema", "bad_orders", (
                ColumnExpectation("order_id", "text", True),
                ColumnExpectation("required_value", "text", True),
            ), allow_extra_columns=True),
        ))
        quality = run_quality_suite(DATABASE_URL, pipeline.run_id, suite, registry)
        self.assertEqual(quality.status, QualityStatus.FAIL)
        self.assertEqual([result.status for result in quality.results], [
            QualityStatus.FAIL, QualityStatus.FAIL, QualityStatus.FAIL])
        self.assertTrue(all(result.evidence for result in quality.results))

    def test_execution_error_is_error_and_other_checks_continue(self):
        from qa.engine.runner import run_quality_suite
        pipeline = self.pipeline_run()
        registry = DatasetRegistry((DatasetSpec(
            "missing_orders", "qa_fixture", "missing_table", run_scoped=False),))
        suite = ValidationSuite("fixture_error", (
            UniquenessRule("missing_table_one", "missing_orders", ("order_id",)),
            NotNullRule("missing_table_two", "missing_orders", ("order_id",)),
        ))
        quality = run_quality_suite(DATABASE_URL, pipeline.run_id, suite, registry)
        self.assertEqual(quality.status, QualityStatus.ERROR)
        self.assertEqual(len(quality.results), 2)
        self.assertTrue(all(result.status is QualityStatus.ERROR for result in quality.results))
        self.assertTrue(all("UndefinedTable" in result.error for result in quality.results))

    def test_empty_suite_is_not_run(self):
        from qa.engine.runner import run_quality_suite
        pipeline = self.pipeline_run()
        quality = run_quality_suite(
            DATABASE_URL, pipeline.run_id, ValidationSuite("empty_suite", ()), DatasetRegistry(()))
        self.assertEqual(quality.status, QualityStatus.NOT_RUN)
        self.assertEqual(quality.results, ())


    def test_source_changes_after_pipeline_do_not_change_run_baseline(self):
        from backend.app.persistence.database import transaction
        from qa.engine.runner import run_quality_suite
        pipeline = self.pipeline_run()
        with transaction(DATABASE_URL) as connection:
            connection.execute("DELETE FROM source.orders WHERE order_id = 1")
        quality = run_quality_suite(DATABASE_URL, pipeline.run_id)
        self.assertEqual(quality.status, QualityStatus.PASS)

    def test_validation_is_scoped_to_requested_pipeline_run(self):
        from backend.app.persistence.database import transaction
        from qa.engine.runner import run_quality_suite
        first = self.pipeline_run()
        second = self.pipeline_run()
        with transaction(DATABASE_URL) as connection:
            connection.execute(
                "DELETE FROM target.orders_report WHERE run_id = %s AND order_id = 1", (second.run_id,)
            )
        first_quality = run_quality_suite(DATABASE_URL, first.run_id)
        second_quality = run_quality_suite(DATABASE_URL, second.run_id)
        self.assertEqual(first_quality.status, QualityStatus.PASS)
        self.assertEqual(second_quality.status, QualityStatus.FAIL)

    def test_equal_count_trap_fails_key_reconciliation_with_evidence(self):
        from backend.app.persistence.database import connect, transaction
        from qa.engine.runner import run_quality_suite
        pipeline = self.pipeline_run()
        with transaction(DATABASE_URL) as connection:
            connection.execute(
                "DELETE FROM target.orders_report WHERE run_id = %s AND order_id = 1",
                (pipeline.run_id,),
            )
            connection.execute(
                """INSERT INTO target.orders_report
                   (run_id, order_id, customer_id, ordered_at, net_amount)
                   SELECT run_id, 999999, customer_id, ordered_at, net_amount
                   FROM target.orders_report WHERE run_id = %s AND order_id = 2""",
                (pipeline.run_id,),
            )
        quality = run_quality_suite(DATABASE_URL, pipeline.run_id)
        by_id = {result.rule_id: result for result in quality.results}
        self.assertEqual(by_id["count_target_orders"].status, QualityStatus.PASS)
        keys = by_id["keys_silver_to_target_orders"]
        self.assertEqual(keys.status, QualityStatus.FAIL)
        self.assertEqual(keys.actual, {"missing_count": 1, "unexpected_count": 1})
        self.assertEqual(
            {(item["kind"], item["key"]["order_id"]) for item in keys.evidence},
            {("MISSING_KEY", 1), ("UNEXPECTED_KEY", 999999)},
        )
        with connect(DATABASE_URL) as connection:
            statuses = connection.execute(
                "SELECT execution_status, data_quality_status FROM metadata.pipeline_runs WHERE run_id = %s",
                (pipeline.run_id,),
            ).fetchone()
        self.assertEqual(statuses, ("SUCCESS", "FAIL"))

    def test_field_mismatch_reports_key_expected_and_actual(self):
        from backend.app.persistence.database import transaction
        from qa.engine.runner import run_quality_suite
        pipeline = self.pipeline_run()
        with transaction(DATABASE_URL) as connection:
            connection.execute(
                """UPDATE target.orders_report SET net_amount = net_amount + 0.01
                   WHERE run_id = %s AND order_id = 1""",
                (pipeline.run_id,),
            )
        quality = run_quality_suite(DATABASE_URL, pipeline.run_id)
        result = next(
            item for item in quality.results if item.rule_id == "fields_silver_to_target_orders"
        )
        self.assertEqual(result.status, QualityStatus.FAIL)
        self.assertEqual(result.actual, {"mismatch_count": 1})
        self.assertEqual(len(result.evidence), 1)
        self.assertEqual(result.evidence[0]["kind"], "FIELD_MISMATCH")
        self.assertEqual(result.evidence[0]["key"], {"order_id": 1})
        self.assertEqual(result.evidence[0]["target_column"], "net_amount")
        self.assertNotEqual(result.evidence[0]["expected"], result.evidence[0]["actual"])

    def test_composite_keys_and_bounded_reconciliation_evidence(self):
        from backend.app.persistence.database import transaction
        from qa.engine.runner import run_quality_suite
        pipeline = self.pipeline_run()
        with transaction(DATABASE_URL) as connection:
            connection.execute("CREATE SCHEMA IF NOT EXISTS qa_fixture")
            connection.execute("DROP TABLE IF EXISTS qa_fixture.left_pairs")
            connection.execute("DROP TABLE IF EXISTS qa_fixture.right_pairs")
            connection.execute(
                "CREATE TABLE qa_fixture.left_pairs (tenant_id BIGINT, order_id BIGINT, amount NUMERIC)"
            )
            connection.execute(
                "CREATE TABLE qa_fixture.right_pairs (tenant_id BIGINT, order_id BIGINT, amount NUMERIC)"
            )
            connection.execute(
                """INSERT INTO qa_fixture.left_pairs VALUES
                   (1, 1, 10), (1, 2, 20), (2, 1, 30), (2, 2, 40)"""
            )
            connection.execute(
                """INSERT INTO qa_fixture.right_pairs VALUES
                   (1, 1, 10), (1, 9, 90), (2, 1, 30), (2, 2, 41)"""
            )
        registry = DatasetRegistry((
            DatasetSpec("left_pairs", "qa_fixture", "left_pairs", run_scoped=False),
            DatasetSpec("right_pairs", "qa_fixture", "right_pairs", run_scoped=False),
        ))
        suite = ValidationSuite("composite_reconciliation", (
            KeyReconciliationRule(
                "pair_keys", "left_pairs", "right_pairs", ("tenant_id", "order_id"),
                max_evidence=1,
            ),
            FieldReconciliationRule(
                "pair_amount", "left_pairs", "right_pairs", ("tenant_id", "order_id"),
                (FieldMapping("amount", "amount"),), max_evidence=2,
            ),
        ))
        quality = run_quality_suite(DATABASE_URL, pipeline.run_id, suite, registry)
        keys, fields = quality.results
        self.assertEqual(quality.status, QualityStatus.FAIL)
        self.assertEqual(keys.actual, {"missing_count": 1, "unexpected_count": 1})
        self.assertEqual(len(keys.evidence), 1)
        self.assertEqual(fields.actual, {"mismatch_count": 1})
        self.assertEqual(fields.evidence[0]["key"], {"tenant_id": 2, "order_id": 2})
