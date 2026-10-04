import unittest
from backend.app.learning.lessons import CATALOG, LANGUAGES, lesson
from backend.app.learning.profiles import PROFILES
from backend.app.learning.workspace import VARIANTS
from backend.app.services.lab_catalog import load_labs


class CurriculumTests(unittest.TestCase):
    def test_six_complete_bilingual_lessons_match_executable_profiles(self):
        self.assertEqual(set(CATALOG), set(PROFILES))
        self.assertEqual(set(CATALOG), {lab.id for lab in load_labs()})
        self.assertEqual(sorted(item["order"] for item in CATALOG.values()), list(range(1,7)))
        for lab_id, definition in CATALOG.items():
            profile = PROFILES[lab_id]
            self.assertLessEqual(set(profile.variants), VARIANTS)
            for language in LANGUAGES:
                text = definition[language]
                for key in ("title","summary","theory","practice_sql","practice_expected","requirement","explanation"):
                    self.assertTrue(text[key].strip(), (lab_id,language,key))
                self.assertEqual(len(text["hints"]),3)
                self.assertGreaterEqual(len(text["steps"]),4)
                self.assertGreaterEqual(len(text["objectives"]),2)
                public = lesson(lab_id,language)
                self.assertNotIn("solution_sql",public)
                self.assertNotIn("hints",public)
            self.assertNotEqual(definition["ENG"]["theory"],definition["VIE"]["theory"])
