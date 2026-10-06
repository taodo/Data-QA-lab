import unittest
from fastapi.testclient import TestClient
from backend.app.api import create_app
from backend.app.learning.lessons import CATALOG


class CourseContractTests(unittest.TestCase):
    def test_all_course_introductions_are_bilingual_distinct_and_beginner_complete(self):
        client = TestClient(create_app('postgresql://invalid'))
        definitions = set()
        examples = set()
        for language in ('ENG', 'VIE'):
            catalog = client.get('/api/courses?language='+language).json()
            subjects = {s['id']: s['title'] for s in client.get('/api/subjects?language='+language).json()}
            for course in catalog:
                with self.subTest(language=language, course=course['id']):
                    detail = client.get('/api/courses/'+course['id']+'?language='+language).json()
                    intro = detail['introduction']
                    subject = subjects[course['subject_id']]
                    self.assertEqual(intro['what_title'], f'What is {subject}?' if language == 'ENG' else f'{subject} là gì?')
                    self.assertEqual(intro['uses_title'], 'What is it used for?' if language == 'ENG' else 'Dùng để làm gì?')
                    self.assertEqual(len(intro['concepts']), 3)
                    self.assertGreaterEqual(len(intro['uses']), 2)
                    for field in ('definition', 'example', 'qa', 'course_connection'):
                        self.assertGreater(len(intro[field]), 70)
                        self.assertNotEqual(intro[field], detail['summary'])
                    self.assertNotIn(intro['definition'], definitions)
                    self.assertNotIn(intro['example'], examples)
                    definitions.add(intro['definition'])
                    examples.add(intro['example'])
                    if not course['available']:
                        self.assertEqual(detail['chapters'], [])
                        markers = ('planned',) if language == 'ENG' else ('kế hoạch', 'dự kiến')
                        self.assertTrue(any(marker in intro['course_connection'] for marker in markers))

    def test_subject_pages_have_real_curriculum_and_honest_availability(self):
        client = TestClient(create_app('postgresql://invalid'))
        for language in ('ENG','VIE'):
            subjects = client.get('/api/subjects?language='+language).json()
            self.assertEqual(len(subjects),9)
            catalog = client.get('/api/courses?language='+language).json()
            self.assertEqual(sum(c['available'] for c in catalog),6)
            for c in catalog:
                detail=client.get('/api/courses/'+c['id']+'?language='+language).json()
                if c['available']:
                    labs=[l for ch in detail['chapters'] for l in ch['lessons']]
                    self.assertEqual({l['id'] for l in labs},{k for k,v in CATALOG.items() if v.get('course_id','sql-data-qa')==c['id']})
                    self.assertEqual(len(labs),c['lesson_count'])
                    self.assertNotIn('solution_sql',str(labs))
                    self.assertNotIn('hints',str(labs))
                else:
                    self.assertEqual(detail['chapters'],[])
                    self.assertEqual(c['lesson_count'],0)
        self.assertEqual(client.get('/api/courses/missing').status_code,404)
        self.assertEqual(client.get('/api/auth/me').json()['user'],None)
        for path in ('/api/progress','/api/runs','/api/faults','/api/enrollments','/api/sessions'):
            self.assertEqual(client.get(path).status_code,401)
