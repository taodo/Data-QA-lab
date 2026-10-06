import copy
import json
import unittest
from datetime import date,datetime
from decimal import Decimal
from backend.app.learning import foundations as f, foundations_contracts as fc
from backend.app.learning.lessons import CATALOG,lesson
from backend.app.learning.profiles import PROFILES
from backend.app.courses import courses,course


def sample(key=f.IDS[0],contract='standard'):
    return dict(version=1,kind='foundations',lab_id=key,contract_id=contract,
        provider='Databricks' if key in f.IDS[:2] else 'Synapse' if key in f.IDS[2:4] else 'Azure',
        resource_id='local',as_of=f.AS_OF,batch_no=1,
        runs=[dict(run_id='run-1',execution_status='SUCCESS',started_at=f.AS_OF,ended_at=f.AS_OF)],steps=[],
        datasets={t:[dict(zip((n for n,_ in fc.columns(t)),r,strict=True)) for r in rows]
                  for t,rows in f.clean_rows(key,contract).items() if t not in f.TRUTH})


def encode(data):
    return json.dumps(data,default=lambda v:v.isoformat() if isinstance(v,(date,datetime)) else str(v))


class Task12ContractTests(unittest.TestCase):
    def test_six_distinct_bilingual_executable_lessons_and_nine_courses(self):
        self.assertEqual(len(CATALOG),36)
        self.assertEqual(sum(c['available'] for c in courses()),9)
        for key in f.IDS:
            self.assertIn(key,PROFILES)
            self.assertEqual(set(PROFILES[key].datasets),set(f.DATASETS[key]))
            for lang in ('ENG','VIE'):
                text=lesson(key,lang)
                self.assertIn(text['order'],(1,2))
                self.assertGreater(len(text['theory']),600)
                self.assertEqual(len(text['steps']),6)
                self.assertNotIn('solution_sql',text)
                detail=course(text['course_id'],lang)
                self.assertEqual(detail['lesson_count'],2)
                self.assertEqual(len(detail['chapters'][0]['lessons']),2)
                self.assertNotIn('planned',detail['introduction']['course_connection'])

    def test_typed_round_trip_all_contracts_and_exact_decimal(self):
        for key in f.IDS:
            for contract in ('standard','shifted','zero'):
                data=sample(key,contract)
                normalized=fc.parse_file('sample.json','json',encode(data))
                exported=fc.export_file(data)
                self.assertEqual(normalized,fc.parse_file(**exported))
                self.assertEqual(normalized['contract_id'],contract)
                self.assertFalse(f.TRUTH & set(normalized['datasets']))
        self.assertEqual(fc.parse_file('sample.json','json',encode(sample()))['datasets']['db_source'][0][2],Decimal('10.01'))

    def test_reject_imported_truth_missing_context_malformed_and_overflow(self):
        original=sample()
        cases=[]
        for field in ('lab_id','contract_id','as_of','batch_no'):
            data=copy.deepcopy(original);data.pop(field);cases.append(data)
        for bad in ([],{},'arbitrary'):
            cases.append({**original,'contract_id':bad})
        cases.append({**original,'datasets':{**original['datasets'],'db_contract':[]}})
        for stamp in ('0001-01-01T00:00:00+23:59','9999-12-31T23:59:59-23:59'):
            cases.append({**original,'as_of':stamp})
        for data in cases:
            with self.subTest(data=data),self.assertRaises(ValueError):
                fc.parse_file('sample.json','json',encode(data))
        with self.assertRaises(ValueError):fc.parse_file('x.csv','csv','dataset')

    def test_bounds_no_truncation_and_alternate_counts(self):
        data=sample()
        data['runs']=[{**data['runs'][0],'run_id':f'run-{i}'} for i in range(1,102)]
        self.assertEqual(len(fc.parse_file(**fc.export_file(data))['runs']),101)
        data['runs'].append({**data['runs'][0],'run_id':'too-many'})
        with self.assertRaises(ValueError):fc.export_file(data)
        data=sample(); data['datasets']['db_source']*=26
        with self.assertRaises(ValueError):fc.export_file(data)
        for scenarios in f.SCENARIOS.values():
            for variant in scenarios:
                self.assertEqual(f.expected_count('alt__'+variant),2*f.expected_count(variant))
