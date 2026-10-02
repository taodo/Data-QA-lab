import unittest
from qa.checks.orders_suite import ORDERS_DATASETS, ORDERS_SUITE
from qa.engine.contracts import CheckType, validate_suite

class OrdersSuiteTests(unittest.TestCase):
    def test_suite_is_valid_and_covers_every_basic_check(self):
        validate_suite(ORDERS_SUITE, ORDERS_DATASETS)
        self.assertEqual(len(ORDERS_SUITE.rules), 20)
        self.assertEqual({rule.check_type for rule in ORDERS_SUITE.rules}, set(CheckType))
        self.assertEqual(len({rule.id for rule in ORDERS_SUITE.rules}), 20)
