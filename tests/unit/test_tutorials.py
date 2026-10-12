import copy
import json
from pathlib import Path
import unittest

from pydantic import ValidationError
from fastapi.testclient import TestClient
from backend.app.api import create_app
from backend.app import courses
from backend.app.learning import tutorials as t
from backend.app.learning.lessons import CATALOG


class TutorialTests(unittest.TestCase):
    def setUp(self):
        self.raw=json.loads(Path(t.__file__).with_name('automation_curriculum.json').read_text(encoding='utf-8'))

    def test_complete_ordered_bilingual_foundation_and_legacy_catalog(self):
        manifest=t.TutorialManifest.model_validate(self.raw)
        lessons=[l for m in manifest.modules for l in m.lessons]
        self.assertEqual(len(lessons),30)
        self.assertEqual(len({l.id for l in lessons}),30)
        self.assertEqual([l.id for l in lessons if l.status=='available'],['m01-l01'])
        self.assertEqual(len(CATALOG),36)
        for language in ('ENG','VIE'):
            catalog=courses.courses(language)
            self.assertEqual(len(catalog),10)
            self.assertEqual(sum(c['lesson_count'] for c in catalog if c['learning_kind']=='executable_lab'),36)
            lesson=t.lesson('m01-l01',language)
            self.assertEqual(len(lesson['sections']),10)
            self.assertNotIn('practice_sql',lesson)
            self.assertNotIn('solution_sql',lesson)
            self.assertEqual(t.lesson('m01-l02',language)['sections'],[])

    def test_invalid_manifest_rejected_without_placeholder_content(self):
        mutations=[
            lambda d:d['modules'].pop(),
            lambda d:d['modules'][0].update(order=2),
            lambda d:d['modules'][0]['lessons'][1].update(id='m01-l01'),
            lambda d:d['modules'][0]['lessons'][1].update(order=3),
            lambda d:d['modules'][0]['lessons'][0]['content'].pop('VIE'),
            lambda d:d['modules'][0]['lessons'][0]['content']['ENG'].update(sections=[]),
            lambda d:d['modules'][0]['lessons'][1].update(status='available'),
            lambda d:d['modules'][0]['lessons'][1]['content']['ENG'].update(sections=d['modules'][0]['lessons'][0]['content']['ENG']['sections']),
            lambda d:d['modules'][0]['lessons'][0]['content']['ENG']['sections'][0].update(type='sql'),
            lambda d:d['modules'][0]['lessons'][0]['content']['ENG']['sections'][4].update(code=''),
            lambda d:d['modules'][0]['lessons'][0]['content']['VIE']['sections'].reverse(),
            lambda d:d['modules'][0]['lessons'][0].update(status='done'),
            lambda d:d['content']['VIE'].update(summary='   '),
            lambda d:d['modules'][0]['title'].update(ENG=''),
            lambda d:d['modules'][0]['lessons'][0]['content']['ENG']['sections'][1].update(id='purpose'),
            lambda d:d['modules'][0]['lessons'][0]['content']['ENG']['sections'][0].update(code='SELECT 1',language='text'),
            lambda d:d['modules'][0]['lessons'][0].update(practice_sql='SELECT 1'),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                raw=copy.deepcopy(self.raw);mutate(raw)
                with self.assertRaises(ValidationError):t.TutorialManifest.model_validate(raw)

    def test_public_contracts_work_without_database_or_identity(self):
        client=TestClient(create_app('postgresql://invalid'))
        for language in ('ENG','VIE'):
            detail=client.get('/api/courses/ai-test-automation?language='+language)
            self.assertEqual(detail.status_code,200)
            self.assertEqual(len(detail.json()['modules']),10)
            result=client.get('/api/courses/ai-test-automation/tutorials/m01-l01?language='+language)
            self.assertEqual(result.status_code,200)
            self.assertNotIn('user_id',result.text)
        self.assertEqual(client.get('/api/courses/ai-test-automation/tutorials/m01-l02').status_code,409)
        for path in ('/api/courses/ai-test-automation/tutorials/m99-l01','/api/courses/sql-data-qa/tutorials/m01-l01','/api/lessons/m01-l01'):
            self.assertEqual(client.get(path).status_code,404)
        self.assertEqual(client.get('/api/courses/ai-test-automation/tutorials/m01-l01?language=FR').status_code,422)
        self.assertEqual(client.get('/api/progress').status_code,401)
