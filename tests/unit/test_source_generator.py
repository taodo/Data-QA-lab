from datetime import timezone
from decimal import Decimal
import unittest
from pipeline.source.generator import generate_customers, generate_orders, expected_net_revenue

class SourceGeneratorTests(unittest.TestCase):
    def test_default_dataset_is_deterministic_and_well_formed(self):
        customers = generate_customers()
        first = generate_orders()
        second = generate_orders()
        self.assertEqual(first, second)
        self.assertEqual(len(customers), 1_000)
        self.assertEqual(len(first), 10_000)
        self.assertEqual(len({row.order_id for row in first}), 10_000)
        self.assertTrue(all(1 <= row.customer_id <= len(customers) for row in first))
        self.assertTrue(all(row.ordered_at.tzinfo == timezone.utc for row in first))
        self.assertTrue(all(row.net_amount == row.gross_amount - row.discount_amount - row.refund_amount for row in first))

    def test_revenue_fixture_is_exact(self):
        self.assertEqual(expected_net_revenue(generate_orders()), Decimal("25245493.29"))

    def test_invalid_counts_are_rejected(self):
        with self.assertRaises(ValueError):
            generate_customers(0)
        with self.assertRaises(ValueError):
            generate_orders(0)
