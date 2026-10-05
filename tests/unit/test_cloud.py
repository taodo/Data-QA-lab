import copy
import json
import unittest
from pathlib import Path
from decimal import Decimal
from backend.app.learning import cloud, cloud_contracts as cc
from backend.app.learning.lessons import lesson
from backend.app.courses import course

ROOT = Path(__file__).resolve().parents[2]


class CloudFileTests(unittest.TestCase):
    def sample(self):
        return json.loads((ROOT/'examples/cloud-evidence-v1.json').read_text())

    def parse(self, data):
        return cc.parse_file('evidence.json', 'json', json.dumps(data))

    def test_json_and_csv_normalize_exact_money_and_aware_utc(self):
        for format, filename in (('json','cloud-evidence-v1.json'),('csv','cloud-snapshots-v1.csv')):
            data=cc.parse_file(filename,format,(ROOT/'examples'/filename).read_text())
            row=data['datasets']['source'][0]
            self.assertEqual(row[2],Decimal('1.01'))
            self.assertEqual(row[3].utcoffset().total_seconds(),0)
        data=self.sample();data['runs'][0]['execution_status']='ProviderNewState'
        normalized=self.parse(data)
        self.assertEqual(normalized['runs'][0][1],'UNKNOWN')
        self.assertEqual(normalized['runs'][0][-1]['execution_status'],'ProviderNewState')
        data['activities'][0].pop('rows_read')
        self.assertIsNone(self.parse(data)['activities'][0][6])
        data['datasets']['target'][0]['amount']=None
        self.assertIsNone(self.parse(data)['datasets']['target'][0][2])

    def test_versions_types_bounds_and_unsafe_inputs_are_rejected(self):
        patches=[{'version':2},{'version':True},{'provider':[]},{'url':'https://external.invalid'},
                 {'credentials':'secret'},{'as_of':'2026-01-03T12:00:00'},
                 {'runs':[{'run_id':'r','token':'secret'}]}, {'datasets':{'other':[]}},
                 {'activities':[{'activity_id':'a','run_id':'r','rows_read':True}]}]
        for patch in patches:
            with self.subTest(patch=patch),self.assertRaises(ValueError):
                self.parse({**self.sample(),**patch})
        for field,value in [('amount',1.01),('amount','NaN'),('amount','0.001'),('order_id',True),('updated_at','2026-01-01')]:
            data=self.sample();data['datasets']['source'][0][field]=value
            with self.subTest(field=field,value=value),self.assertRaises(ValueError):self.parse(data)
        for filename,format,text in [('../e.json','json','{}'),('e.zip','json','{}'),('e.json','json',' '* (cc.MAX_BYTES+1)),
                                     ('e.json','json','{"version":1,"version":1}'),('e.json','json','{"version":NaN}'),
                                     ('e.csv','csv','dataset,amount\ntarget,0.00'),('e.csv','csv',','.join(cc.CSV_FIELDS)+'\nunknown,1,1,0.00,2026-01-01T00:00:00Z,1,1,r')]:
            with self.subTest(filename=filename),self.assertRaises(ValueError):cc.parse_file(filename,format,text)
        data=self.sample();row=data['datasets']['target'][0]
        data['datasets']={'target':[row]*101}
        with self.assertRaises(ValueError):self.parse(data)
        with self.assertRaises(ValueError):cc.parse_file('broken.csv','csv',','.join(cc.CSV_FIELDS)+'\n"unclosed')

    def test_duplicate_rows_are_evidence_and_missing_metadata_stays_unknown(self):
        data=self.sample();data['datasets']['target'].append(copy.deepcopy(data['datasets']['target'][0]))
        self.assertEqual(len(self.parse(data)['datasets']['target']),5)
        normalized=self.parse({'version':1,'provider':'ADF','as_of':'2026-01-03T12:00:00Z','runs':[{'run_id':'r'}]})
        self.assertEqual(normalized['runs'][0][1],'UNKNOWN')
        self.assertIsNone(normalized['runs'][0][2]);self.assertIsNone(normalized['resource_id'])

    def test_three_courses_bilingual_contracts_and_hidden_solutions(self):
        for cid,n in [('fabric-testing',3),('adf-testing',3),('onelake-testing',2)]:
            for lang in ('ENG','VIE'):
                c=course(cid,lang);labs=[l for ch in c['chapters'] for l in ch['lessons']]
                self.assertTrue(c['available']);self.assertEqual(len(labs),n)
                self.assertEqual([l['order'] for l in labs],list(range(1,n+1)))
                for l in labs:
                    self.assertNotIn('solution_sql',l);self.assertNotIn('hints',l)
                    self.assertEqual(set(l['schema']),set(cloud.TABLES))
        self.assertIn('NUMERIC',lesson(cloud.IDS[1],'ENG')['theory'])

    def test_quality_requires_a_complete_check_and_known_evidence(self):
        from backend.app.learning.service import _cloud_quality
        good={'status':'SUCCESS','columns':['violation_count'],'rows':[['0']],'truncated':False}
        self.assertEqual(_cloud_quality('AVAILABLE',good),'PASS')
        self.assertEqual(_cloud_quality('NOT_VERIFIED',good),'NOT_VERIFIED')
        self.assertEqual(_cloud_quality('AVAILABLE',{**good,'rows':[['2']]}),'FAIL')
        self.assertEqual(_cloud_quality('NOT_VERIFIED',{**good,'status':'ERROR'}),'ERROR')
        for patch in ({'truncated':True},{'columns':['rows']},{'rows':[['-1']]},{'rows':[['NaN']]},
                      {'rows':[['1.5']]},{'rows':[['9223372036854775808']]},{'rows':[]}):
            self.assertEqual(_cloud_quality('AVAILABLE',{**good,**patch}),'NOT_RUN')

    def test_import_validation_feedback_is_bilingual(self):
        self.assertEqual(cc.localized_error('Unsupported evidence version','ENG'),'Unsupported evidence version')
        self.assertIn('version 1',cc.localized_error('Unsupported evidence version','VIE'))
        self.assertIn('100 dòng',cc.localized_error('Dataset exceeds 100 rows','VIE'))
