import unittest

from faults.catalog import get_fault_scenario, list_fault_scenarios
from faults.contracts import FaultScenario


class FaultCatalogTests(unittest.TestCase):
    def test_catalog_contains_only_the_four_allowlisted_scenarios(self):
        scenarios = list_fault_scenarios()
        self.assertEqual(
            tuple(item.id for item in scenarios),
            ("missing_order", "duplicate_order", "null_net_amount", "wrong_net_amount"),
        )
        self.assertTrue(all(item.expected_rule_ids for item in scenarios))

    def test_unknown_scenario_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown fault scenario"):
            get_fault_scenario("drop_everything")

    def test_scenario_contract_rejects_unsafe_or_ambiguous_metadata(self):
        with self.assertRaisesRegex(ValueError, "Invalid fault scenario id"):
            FaultScenario("bad-id", "description", ("rule",))
        with self.assertRaisesRegex(ValueError, "description"):
            FaultScenario("valid_id", " ", ("rule",))
        with self.assertRaisesRegex(ValueError, "unique"):
            FaultScenario("valid_id", "description", ("rule", "rule"))
