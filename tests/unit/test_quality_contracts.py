import unittest
from backend.app.domain.models import QualityStatus
from qa.engine.contracts import (
    CountMode, DatasetRegistry, DatasetSpec, NotNullRule, RecordCountRule,
    UniquenessRule, ValidationSuite, aggregate_statuses, validate_suite,
)

class QualityContractTests(unittest.TestCase):
    def test_status_precedence(self):
        cases = [
            ((), QualityStatus.NOT_RUN),
            ((QualityStatus.PASS,), QualityStatus.PASS),
            ((QualityStatus.PASS, QualityStatus.NOT_RUN), QualityStatus.NOT_RUN),
            ((QualityStatus.PASS, QualityStatus.FAIL), QualityStatus.FAIL),
            ((QualityStatus.FAIL, QualityStatus.ERROR), QualityStatus.ERROR),
        ]
        for statuses, expected in cases:
            with self.subTest(statuses=statuses):
                self.assertEqual(aggregate_statuses(statuses), expected)

    def test_registry_is_allowlisted_and_immutable(self):
        registry = DatasetRegistry((DatasetSpec("orders", "silver", "orders"),))
        self.assertEqual(registry.get("orders").schema, "silver")
        with self.assertRaises(ValueError):
            registry.get("unknown")
        with self.assertRaises(ValueError):
            DatasetSpec("orders", "silver; drop schema", "orders")

    def test_sum_dataset_requires_safe_count_column(self):
        with self.assertRaises(ValueError):
            DatasetSpec("daily", "gold", "daily_sales", count_mode=CountMode.SUM)
        dataset = DatasetSpec("daily", "gold", "daily_sales", count_mode=CountMode.SUM,
                              count_column="order_count")
        self.assertEqual(dataset.count_column, "order_count")

    def test_rule_and_suite_validation(self):
        with self.assertRaises(ValueError):
            UniquenessRule("unique", "orders", ())
        with self.assertRaises(ValueError):
            NotNullRule("required", "orders", ("order_id", "order_id"))
        with self.assertRaises(ValueError):
            ValidationSuite("suite", (RecordCountRule("same", "orders"),
                                      RecordCountRule("same", "orders")))
        registry = DatasetRegistry((DatasetSpec("orders", "silver", "orders"),))
        with self.assertRaises(ValueError):
            validate_suite(ValidationSuite("suite", (RecordCountRule("count", "missing"),)), registry)
