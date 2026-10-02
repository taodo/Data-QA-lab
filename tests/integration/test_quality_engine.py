import os
from uuid import uuid4
import unittest

from backend.app.domain.models import QualityStatus
from qa.engine.contracts import (
    ColumnExpectation, DatasetRegistry, DatasetSpec, NotNullRule,
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
        self.assertEqual(len(first.results), 20)
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
