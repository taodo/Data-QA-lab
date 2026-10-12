import tempfile
import unittest
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.app.api.spa import FrontendFiles


class SpaRoutesTests(unittest.TestCase):
    def test_deep_course_reload_works_without_swallowing_api_or_assets(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder,'index.html').write_text('<div id="root"></div>')
            app=FastAPI();app.mount('/',FrontendFiles(directory=folder,html=True))
            client=TestClient(app)
            for path in ('/courses/fabric-testing','/courses/fabric-testing/lessons/lab_023_fabric_lineage','/subjects/onelake','/courses/ai-test-automation','/courses/ai-test-automation/tutorials/m01-l01','/learn/data','/learn/banking','/learn/automation','/learn/lab_001_record_count','/my-learning','/history','/pipeline','/login','/signup','/account'):
                self.assertEqual(client.get(path).status_code,200,path)
                self.assertIn('id="root"',client.get(path).text)
            for path in ('/api/missing','/assets/missing.js','/unknown','/courses/sql-data-qa/tutorials/m01-l01','/courses/ai-test-automation/tutorials/invalid','/learn/not-a-track','/learn/banking/simulator','/learn/automation/playground','/learn/data/extra','/learn/data.js'):
                self.assertEqual(client.get(path).status_code,404,path)
            for path in ('/learn/data','/learn/banking','/learn/automation'):
                self.assertEqual(client.head(path).status_code,200)
                self.assertEqual(client.post(path).status_code,405)
