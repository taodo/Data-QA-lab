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
            for path in ('/courses/fabric-testing','/courses/fabric-testing/lessons/lab_023_fabric_lineage','/subjects/onelake'):
                self.assertEqual(client.get(path).status_code,200,path)
                self.assertIn('id="root"',client.get(path).text)
            for path in ('/api/missing','/assets/missing.js','/unknown'):
                self.assertEqual(client.get(path).status_code,404,path)
