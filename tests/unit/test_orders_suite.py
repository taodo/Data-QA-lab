import unittest
from qa.checks.orders_suite import (
    ORDERS_BASIC_SUITE, ORDERS_DATASETS, ORDERS_FAULT_DATASETS,
    ORDERS_FAULT_SUITE, ORDERS_SUITE,
)
from qa.engine.contracts import CheckType, validate_suite

class OrdersSuiteTests(unittest.TestCase):
    def test_suite_is_valid_and_covers_every_basic_check(self):
        validate_suite(ORDERS_SUITE, ORDERS_DATASETS)
        self.assertEqual(len(ORDERS_BASIC_SUITE.rules), 20)
        self.assertEqual(len(ORDERS_SUITE.rules), 26)
        self.assertEqual({rule.check_type for rule in ORDERS_SUITE.rules}, set(CheckType))
        self.assertEqual(len({rule.id for rule in ORDERS_SUITE.rules}), 26)

    def test_fault_suite_uses_isolated_targets_and_semantic_checks(self):
        validate_suite(ORDERS_FAULT_SUITE, ORDERS_FAULT_DATASETS)
        self.assertEqual(len(ORDERS_FAULT_SUITE.rules), 24)
        self.assertEqual(ORDERS_FAULT_DATASETS.get("target_orders").schema, "fault_workspace")
        self.assertEqual(
            ORDERS_FAULT_DATASETS.get("target_daily_sales").schema, "fault_workspace"
        )
        self.assertNotIn(
            "schema_target_orders", {rule.id for rule in ORDERS_FAULT_SUITE.rules}
        )
