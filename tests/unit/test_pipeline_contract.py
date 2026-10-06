import unittest
from pipeline.jobs.orders import STAGES, STAGE_FUNCTIONS

class PipelineContractTests(unittest.TestCase):
    def test_stage_order_is_explicit(self):
        self.assertEqual(STAGES, ("SOURCE", "BRONZE", "SILVER", "GOLD", "TARGET"))
        self.assertEqual(tuple(name for name, _ in STAGE_FUNCTIONS), STAGES)
