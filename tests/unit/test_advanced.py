import unittest
from datetime import timedelta
from decimal import Decimal
from backend.app.learning.advanced_workspace import AS_OF, DDL, merge_versions
from backend.app.learning.advanced_profiles import SPECS, ADVANCED_TABLES
from backend.app.learning.lessons import lesson


class AdvancedTests(unittest.TestCase):
    def test_keyed_merge_is_replay_safe_and_accepts_late_new_keys(self):
        old=(1,101,AS_OF-timedelta(days=2),Decimal("10.00"))
        current=(2,101,AS_OF-timedelta(days=1),Decimal("11.01"))
        late_new=(3,203,AS_OF-timedelta(days=3),Decimal("0.00"))
        result=merge_versions([current],[old,late_new,current])
        self.assertEqual(result,[current,late_new])
        self.assertEqual(merge_versions(result,[old,late_new,current]),result)
        self.assertEqual(merge_versions([],list(reversed([old,current,late_new]))),result)

    def test_equal_business_time_uses_event_id_without_float_money(self):
        low=(1,101,AS_OF,Decimal("0.00"));high=(2,101,AS_OF,Decimal("0.01"))
        self.assertEqual(merge_versions([high],[low]),[high])
        self.assertEqual(merge_versions([low],[high]),[high])
        self.assertIsInstance(merge_versions([low],[high])[0][3],Decimal)

    def test_advanced_schema_and_track_contracts_are_complete_and_public_safe(self):
        self.assertEqual(set(DDL),set(ADVANCED_TABLES))
        self.assertEqual(len(SPECS),7)
        for lab_id,spec in SPECS.items():
            for language in ("ENG","VIE"):
                public=lesson(lab_id,language)
                self.assertEqual(set(public["schema"]),set(spec[3]))
                self.assertEqual(public["level"],"ADVANCED")
                self.assertNotIn("solution",public)
                self.assertNotIn("variants",public)
                for table,definition in public["schema"].items():
                    for column in definition["columns"]:
                        self.assertIn(column,DDL[table])
