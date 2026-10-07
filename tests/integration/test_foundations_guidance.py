"""Illustrative examples evaluated with the unchanged foundation reference SQL."""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import os
import unittest
from psycopg import sql
from backend.app.learning import foundations as f
from backend.app.learning.foundations_guidance import GUIDANCE, LABELS
from backend.app.learning.lessons import CATALOG, lesson
from backend.app.persistence.database import connect

DB=os.getenv('DATA_QA_TEST_DATABASE_URL')
TIME=datetime(2026,3,1,12,tzinfo=timezone.utc)
DAY=TIME.date()
D=Decimal
VERSIONS=[(10,3,D('10.01'),TIME),(20,6,D('21.02'),TIME),(30,1,D('0.00'),TIME),(40,1,D('30.03'),TIME)]
EXAMPLES={
    f.IDS[0]:(3,{'db_contract':[(10,'ACCEPTED',D('10.01')),(20,'REJECTED',D('5.00')),(30,'QUARANTINED',None),(40,'ACCEPTED',D('0.00'))],
        'db_publication':[(10,'ACCEPTED',D('10.01'),'R')]*2+[(20,'REJECTED',D('5.00'),'R'),(30,'ACCEPTED',None,'R')]}),
    f.IDS[1]:(3,{'db_before':[(10,3,D('10.01'),TIME,'R'),(20,5,D('20.02'),TIME,'R'),(30,1,D('0.00'),TIME,'R')],
        'db_incoming':[(10,2,D('9.01'),TIME,'R'),(20,6,D('21.02'),TIME,'R'),(40,1,D('30.03'),TIME,'R')],
        'db_expected_after':VERSIONS,
        'db_after':[(10,2,D('9.01'),TIME,'R'),(*VERSIONS[1],'R'),(*VERSIONS[1],'R'),(*VERSIONS[3],'R')]}),
    f.IDS[2]:(3,{'sy_expected_fact':[(10,101,D('10.01'),DAY),(20,101,D('20.02'),DAY),(30,102,D('0.00'),DAY)],
        'sy_fact':[(10,999,D('10.01'),DAY,'R'),(20,101,D('20.02'),DAY,'R'),(40,102,D('0.00'),DAY,'R')]}),
    f.IDS[3]:(1,{'sy_fact':[(10,101,D('10.01'),DAY,'R'),(20,101,D('10.01'),DAY,'R'),(30,102,D('0.00'),DAY,'R')],
        'sy_dimension':[('A',101,'North','R'),('A',101,'North','R'),('B',102,'South','R')],
        'sy_expected_report':[(DAY,'North',2,D('20.02')),(DAY,'South',1,D('0.00'))],
        'sy_report':[(DAY,'North',4,D('40.04'),'R'),(DAY,'South',1,D('0.00'),'R')]}),
    f.IDS[4]:(4,{'az_expected_files':[('F1','/orders/a.csv','orders',100),('F2','/orders/b.csv','orders',200),('F3','/orders/c.csv','orders',0)],
        'az_files':[('F1','/wrong/a.csv','customers',100,TIME,'R'),('F2','/orders/b.csv','orders',200,TIME,'R'),('F2','/orders/b.csv','orders',200,TIME,'R'),('F4','/orders/d.csv','orders',50,TIME,'R')]}),
    f.IDS[5]:(4,{'az_required_access':[(key,'user-'+key,'/orders','READ') for key in 'ABCD'],
        'az_access':[('A','user-A','/orders','READ','ALLOWED',TIME,'R'),('B','user-B','/orders','READ','DENIED',TIME,'R'),('C',None,'/orders','READ','ALLOWED',TIME,'R'),('X','user-X','/orders','READ','ALLOWED',TIME,'R')]}),
}


@unittest.skipUnless(DB,'Dedicated PostgreSQL test database required')
class FoundationsGuidanceExamples(unittest.TestCase):
    def test_all_six_examples_and_counting_boundaries_using_reference_sql(self):
        for key,(expected,tables) in EXAMPLES.items():
            with self.subTest(key=key),connect(DB) as c:
                for name in f.table_names(key):
                    c.execute(sql.SQL('CREATE TEMP TABLE {} ({}) ON COMMIT DROP').format(sql.Identifier(name),sql.SQL(f.DEFINITIONS[name])))
                    rows=tables.get(name,[])
                    if name=='cloud_context':rows=[(key,1,TIME,'local','miniature','SIMULATED',TIME,1,'standard')]
                    if rows:
                        with c.cursor() as cursor:
                            cursor.executemany(sql.SQL('INSERT INTO {} VALUES ({})').format(sql.Identifier(name),sql.SQL(',').join(sql.Placeholder() for _ in rows[0])),rows)
                result=c.execute(f.SOLUTIONS[key])
                self.assertEqual([col.name for col in result.description],['violation_count'])
                self.assertEqual(result.fetchall(),[(expected,)])
                for language in ('ENG','VIE'):self.assertIn(f'violation_count = {expected}',GUIDANCE[key][language][2])
                if key==f.IDS[0]:
                    c.execute("INSERT INTO db_publication SELECT * FROM db_publication WHERE record_id=10 LIMIT 1")
                    self.assertEqual(c.execute(f.SOLUTIONS[key]).fetchone(),(3,))
                if key==f.IDS[1]:
                    c.execute('UPDATE db_after SET run_id=NULL')
                    self.assertEqual(c.execute(f.SOLUTIONS[key]).fetchone(),(3,))
                if key==f.IDS[3]:
                    joined=c.execute('SELECT f.sale_date,d.region,COUNT(*),SUM(f.amount) FROM sy_fact f JOIN sy_dimension d USING(customer_key) GROUP BY f.sale_date,d.region ORDER BY d.region').fetchall()
                    self.assertEqual(joined,[(DAY,'North',4,D('40.04')),(DAY,'South',1,D('0.00'))])
                    self.assertEqual(c.execute('SELECT SUM(DISTINCT amount) FROM sy_fact WHERE customer_key=101').fetchone(),(D('10.01'),))
                if key==f.IDS[4]:
                    c.execute('UPDATE az_files SET observed_at=NULL')
                    self.assertEqual(c.execute(f.SOLUTIONS[key]).fetchone(),(4,))
                if key==f.IDS[5]:
                    c.execute("UPDATE az_access SET observed_at=%s WHERE observation_id='C'",(TIME+timedelta(microseconds=1),))
                    self.assertEqual(c.execute(f.SOLUTIONS[key]).fetchone(),(4,))
                    c.execute("INSERT INTO az_access SELECT * FROM az_access WHERE observation_id='B'")
                    self.assertEqual(c.execute(f.SOLUTIONS[key]).fetchone(),(6,))


class FoundationsGuidancePrivacy(unittest.TestCase):
    def test_six_by_two_sections_foundation_envelope_and_private_gate(self):
        self.assertEqual(set(GUIDANCE),set(f.IDS))
        for key in f.IDS:
            for language in ('ENG','VIE'):
                public=lesson(key,language)
                for index in (0,1,2,3,5):self.assertIn(LABELS[language][index],public['theory'])
                for marker in ('SIMULATED','IMPORTED','PostgreSQL','kind=foundations','lab_id','contract_id','48 KiB','64 KiB','NOT_VERIFIED'):
                    self.assertIn(marker,public['theory'])
                self.assertIn(LABELS[language][4],public['requirement'])
                for field in ('explanation','solution_sql','hints'):self.assertNotIn(field,public)
                self.assertNotIn(LABELS[language][6],str(public))
                self.assertIn(LABELS[language][6],CATALOG[key][language]['explanation'])
