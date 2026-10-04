import unittest
from fastapi.testclient import TestClient
from backend.app.api import create_app
from backend.app.learning.lessons import CATALOG


class CourseContractTests(unittest.TestCase):
    def test_subject_pages_have_real_curriculum_and_honest_availability(self):
        client = TestClient(create_app('postgresql://invalid'))
        for language in ('ENG','VIE'):
            subjects = client.get('/api/subjects?language='+language).json()
            self.assertEqual(len(subjects),9)
            catalog = client.get('/api/courses?language='+language).json()
            self.assertEqual(sum(c['available'] for c in catalog),1)
            for c in catalog:
                detail=client.get('/api/courses/'+c['id']+'?language='+language).json()
                if c['available']:
                    labs=[l for ch in detail['chapters'] for l in ch['lessons']]
                    self.assertEqual({l['id'] for l in labs},set(CATALOG))
                    self.assertEqual(len(labs),13)
                    self.assertNotIn('solution_sql',str(labs))
                    self.assertNotIn('hints',str(labs))
                else:
                    self.assertEqual(detail['chapters'],[])
                    self.assertEqual(c['lesson_count'],0)
        self.assertEqual(client.get('/api/courses/missing').status_code,404)
        self.assertEqual(client.get('/api/auth/me').json()['user'],None)
        for path in ('/api/progress','/api/runs','/api/faults','/api/enrollments','/api/sessions'):
            self.assertEqual(client.get(path).status_code,401)
