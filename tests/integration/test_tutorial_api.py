import os
import unittest
from fastapi.testclient import TestClient
from backend.app.api import create_app
from backend.app.persistence.database import connect,initialize_database
from tests.auth_helpers import signed_client

DB=os.getenv('DATA_QA_TEST_DATABASE_URL')


@unittest.skipUnless(DB,'Disposable PostgreSQL test database required')
class TutorialApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):initialize_database(DB)

    def test_public_reads_preserve_account_sessions_and_tutorial_writes_rejected(self):
        client,user=signed_client(DB)
        public=TestClient(create_app(DB))
        def state():
            with connect(DB) as c:
                return tuple(c.execute('SELECT COUNT(*) FROM metadata.'+table+' WHERE '+column+'=%s',(user['user_id'],)).fetchone()[0] for table,column in (('lab_sessions','owner_id'),('course_enrollments','user_id')))
        before=state()
        for language in ('ENG','VIE'):
            subjects=public.get('/api/subjects?language='+language).json()
            self.assertEqual(next(s for s in subjects if s['id']=='ai-test-automation')['learning_kind'],'tutorial')
            self.assertEqual(len(public.get('/api/courses?language='+language).json()),10)
            self.assertEqual(len(public.get('/api/courses/ai-test-automation?language='+language).json()['modules']),10)
            result=public.get('/api/courses/ai-test-automation/tutorials/m01-l01?language='+language)
            self.assertEqual(result.status_code,200)
            self.assertNotIn(user['user_id'],result.text)
            self.assertNotIn(user['username'],result.text)
        self.assertEqual(public.get('/api/courses/ai-test-automation/tutorials/m01-l02').status_code,409)
        self.assertEqual(public.get('/api/courses/ai-test-automation/tutorials/bad').status_code,404)
        self.assertEqual(client.post('/api/courses/ai-test-automation/enroll').status_code,409)
        self.assertEqual(client.post('/api/sessions',json={'lab_id':'m01-l01'}).status_code,422)
        self.assertEqual(state(),before)
        for endpoint in ('sessions','progress','enrollments'):
            self.assertEqual(public.get('/api/'+endpoint).status_code,401)
