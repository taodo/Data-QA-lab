"""Check authored examples with the real loopback executor and persisted Target."""
import json
import os
import unittest
from decimal import Decimal
from uuid import uuid4
from psycopg import sql
from backend.app.learning import http_exercises as http
from backend.app.learning.api_guidance import GUIDANCE, LABELS
from backend.app.learning.lessons import CATALOG, lesson
from backend.app.persistence.database import connect

DB=os.getenv("DATA_QA_TEST_DATABASE_URL")


@unittest.skipUnless(DB,"PostgreSQL test database required")
class ApiGuidanceExampleTests(unittest.TestCase):
    def test_all_four_examples_through_actual_http_and_database(self):
        self.assertEqual(set(GUIDANCE),set(http.IDS))
        for lab_id in http.IDS:
            with self.subTest(lab_id=lab_id),connect(DB) as connection:
                schema="learner_query_"+uuid4().hex
                http.create(connection,schema,lab_id)
                connection.execute(sql.SQL("DELETE FROM {}.api_expected").format(sql.Identifier(schema)))
                with connection.cursor() as cursor:
                    cursor.executemany(sql.SQL("INSERT INTO {}.api_expected VALUES (%s,%s,%s)").format(sql.Identifier(schema)),[(10,7,Decimal('10.01')),(20,8,Decimal('0.00')),(30,7,Decimal('7.00'))])
                def run(variant="clean",**options):
                    plan={**json.loads(http.SOLUTIONS[lab_id]),**options}
                    return http.run(connection,schema,lab_id,json.dumps(plan),variant,persist=True)
                clean=run()
                self.assertEqual(clean['rows'],[['0']])
                self.assertEqual(clean['http']['execution_status'],'SUCCESS')
                self.assertEqual(clean['http']['data_quality_status'],'PASS')
                if lab_id==http.IDS[0]:
                    bad=run('api_missing_field')
                    self.assertEqual(bad['rows'],[['1']])
                    self.assertEqual(bad['http']['execution_status'],'SUCCESS')
                    self.assertEqual(bad['http']['data_quality_status'],'FAIL')
                    self.assertNotIn('net_amount',bad['http']['records'][-1])
                elif lab_id==http.IDS[1]:
                    self.assertEqual([t['body']['next_page'] for t in clean['http']['trace']],[2,None])
                    for variant in ('api_missing_page','api_duplicate_page'):
                        self.assertEqual(run(variant)['rows'],[['1']])
                    missing=run('api_missing_page')
                    self.assertEqual(missing['http']['trace'][0]['body']['total'],2)
                    self.assertEqual(missing['http']['trace'][0]['body']['next_page'],None)
                elif lab_id==http.IDS[2]:
                    self.assertEqual(clean['http']['request_count'],6)
                    self.assertEqual([t['status'] for t in clean['http']['trace']],[429,503,200]*2)
                    for options,variant in [({'max_attempts':2},'clean'),({},'api_timeout')]:
                        failed=run(variant,**options)
                        self.assertEqual(failed['rows'],[['4']])
                        self.assertEqual(failed['status'],'SUCCESS')
                        self.assertEqual(failed['http']['execution_status'],'FAILED')
                        self.assertEqual(failed['http']['data_quality_status'],'FAIL')
                        self.assertEqual(sum(t['final'] for t in failed['http']['trace']),1)
                else:
                    self.assertEqual(len(clean['http']['target']),3)
                    self.assertEqual(clean['http']['replayed_batches'],2)
                    appended=run(idempotent=False)
                    self.assertEqual(appended['rows'],[['3']])
                    self.assertEqual(len(appended['http']['target']),6)
                    persisted=connection.execute(sql.SQL("SELECT COUNT(*) FROM {}.api_target").format(sql.Identifier(schema))).fetchone()[0]
                    self.assertEqual(persisted,6)
                    self.assertEqual(run()['rows'],[['0']])
                    self.assertEqual(connection.execute(sql.SQL("SELECT COUNT(*) FROM {}.api_target").format(sql.Identifier(schema))).fetchone()[0],3)
                    # A non-ingesting send leaves the stored Target from the prior run intact.
                    run(ingest=False,checks={'status':200})
                    self.assertEqual(connection.execute(sql.SQL("SELECT COUNT(*) FROM {}.api_target").format(sql.Identifier(schema))).fetchone()[0],3)
                    self.assertEqual(run('api_ingest_missing')['rows'],[['2']])
                connection.rollback()  # no example schemas/data survive the check


class ApiGuidancePrivacyTests(unittest.TestCase):
    def test_four_bilingual_entries_and_private_solution_explanations(self):
        ids={key for key,value in CATALOG.items() if value.get('course_id')=='api-testing'}
        self.assertEqual(ids,set(GUIDANCE));self.assertEqual(len(ids),4)
        for lab_id in ids:
            for language in ('ENG','VIE'):
                public=lesson(lab_id,language);labels=LABELS[language]
                for index in (0,1,2,3,5):self.assertIn(labels[index],public['theory'])
                self.assertIn(labels[4],public['requirement'])
                self.assertIn('JSON',public['requirement'])
                self.assertNotIn('explanation',public)
                self.assertNotIn(labels[6],str(public))
                self.assertIn(labels[6],CATALOG[lab_id][language]['explanation'])
