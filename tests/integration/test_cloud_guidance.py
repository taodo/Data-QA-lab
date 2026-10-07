"""Run all eight published miniature examples against unchanged reference SQL."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import os
import unittest
from psycopg import sql
from backend.app.learning import cloud
from backend.app.learning.cloud_guidance import GUIDANCE, LABELS
from backend.app.learning.lessons import CATALOG, lesson
from backend.app.persistence.database import connect

DB=os.getenv('DATA_QA_TEST_DATABASE_URL')
AS_OF=datetime(2026,2,3,12,tzinfo=timezone.utc)
DAY1=datetime(2026,2,1,tzinfo=timezone.utc)


def order(key,amount,event,batch=1,updated=DAY1,run='R'):
    return (key,7,Decimal(amount),updated,event,batch,run)


ORDERS=[order(10,'10.01',1),order(20,'0.00',2),order(30,'7.00',3)]
SWAPPED=[*ORDERS[:2],(40,*ORDERS[2][1:])]
RUN=('R','SUCCESS',DAY1,AS_OF,None)
ACTIVITY=('A','R',None,'SUCCESS','source','target',3,3,None)
EXAMPLES={
    cloud.IDS[0]: (3,{'cloud_runs':[RUN],
        'cloud_activities':[('A','R',None,'SUCCESS','source','bronze',2,2,None),('B','R','X','SUCCESS',None,'target',2,2,None)],
        'cloud_target':[order(10,'10.01',1),order(20,'0.00',2,run='Z')]}),
    cloud.IDS[1]: (3,{'cloud_expected_schema':[('target','order_id','bigint'),('target','customer_id','bigint'),('target','amount','numeric(14,2)')],
        'cloud_schema':[('target','order_id','bigint'),('target','amount','float'),('target','debug','text')]}),
    cloud.IDS[2]: (2,{'cloud_source':ORDERS,'cloud_bronze':ORDERS,'cloud_silver':ORDERS,'cloud_target':SWAPPED}),
    cloud.IDS[3]: (2,{'cloud_source':ORDERS,'cloud_target':SWAPPED,'cloud_activities':[ACTIVITY]}),
    cloud.IDS[4]: (1,{'cloud_source':[order(10,'10.00',1,updated=DAY1+timedelta(days=1)),order(10,'12.00',2,batch=2),order(20,'0.00',3,batch=2,updated=AS_OF),order(30,'7.00',4,batch=2,updated=AS_OF+timedelta(seconds=1))],
        'cloud_target':[order(10,'10.00',1,updated=DAY1+timedelta(days=1)),order(20,'0.00',3,batch=2,updated=AS_OF)]}),
    cloud.IDS[5]: (3,{'cloud_source':ORDERS,'cloud_target':ORDERS[:2],
        'cloud_runs':[RUN,('OLD','FAILED',DAY1,DAY1,None)],
        'cloud_activities':[('A','R',None,'FAILED','source','bronze',3,2,None),('B','R','A','SUCCESS','silver','target',3,2,None)],
        'cloud_steps':[(1,'INITIAL','OLD','FAILED',0,0,AS_OF),(2,'RECOVER','R','FAILED',0,2,AS_OF)]}),
    cloud.IDS[6]: (2,{'cloud_expected_partitions':[('P1',3),('P2',2)],
        'cloud_manifest':[('P1','F1',1,AS_OF,'R'),('P1','F1',1,AS_OF,'R'),('P1','F2',1,AS_OF,'R')]}),
    cloud.IDS[7]: (4,{'cloud_required_references':[('orders',key,60) for key in 'ABCD'],
        'cloud_references':[('orders','A',AS_OF-timedelta(minutes=60),'R'),('orders','B',AS_OF-timedelta(minutes=60,microseconds=1),'R'),('orders','C',None,'R'),('orders','X',AS_OF-timedelta(minutes=60),'R')]}),
}


@unittest.skipUnless(DB,'Dedicated PostgreSQL test database required')
class CloudGuidanceExampleTests(unittest.TestCase):
    def test_eight_examples_match_actual_reference_sql_and_documented_boundaries(self):
        self.assertEqual(set(EXAMPLES),set(GUIDANCE))
        for lab_id,(expected,tables) in EXAMPLES.items():
            with self.subTest(lab_id=lab_id),connect(DB) as connection:
                for table,ddl in cloud.DEFINITIONS.items():
                    connection.execute(sql.SQL('CREATE TEMP TABLE {} ({}) ON COMMIT DROP').format(sql.Identifier(table),sql.SQL(ddl)))
                    rows=tables.get(table,[])
                    if table=='cloud_context':rows=[(lab_id,2 if lab_id==cloud.IDS[4] else 1,AS_OF,'local','miniature','SIMULATED',AS_OF,1)]
                    if rows:
                        with connection.cursor() as cursor:
                            cursor.executemany(sql.SQL('INSERT INTO {} VALUES ({})').format(sql.Identifier(table),sql.SQL(',').join(sql.Placeholder() for _ in rows[0])),rows)
                cursor=connection.execute(cloud.SOLUTIONS[lab_id])
                self.assertEqual([column.name for column in cursor.description],['violation_count'])
                self.assertEqual(cursor.fetchall(),[(expected,)])
                for language in ('ENG','VIE'):
                    self.assertIn(f'violation_count = {expected}',GUIDANCE[lab_id][language][2])
                if lab_id==cloud.IDS[0]:
                    connection.execute("UPDATE cloud_activities SET execution_status='FAILED',source_dataset='silver',dependency_id=NULL WHERE activity_id='B'")
                    connection.execute("UPDATE cloud_target SET run_id='R'")
                    # Lineage has no general non-SUCCESS activity rule.
                    self.assertEqual(connection.execute(cloud.SOLUTIONS[lab_id]).fetchone(),(0,))
                if lab_id==cloud.IDS[5]:
                    connection.execute('DELETE FROM cloud_steps')
                    self.assertEqual(connection.execute(cloud.SOLUTIONS[lab_id]).fetchone(),(3,))
                if lab_id==cloud.IDS[6]:
                    connection.execute('DELETE FROM cloud_manifest')
                    connection.execute("INSERT INTO cloud_manifest VALUES ('P1','known',3,%s,'R'),('P1','unknown',NULL,%s,'R'),('P2','other',2,%s,'R')",(AS_OF,AS_OF,AS_OF))
                    # A partial NULL group can match SUM: evidence completeness is separate.
                    self.assertEqual(connection.execute(cloud.SOLUTIONS[lab_id]).fetchone(),(0,))
                if lab_id==cloud.IDS[7]:
                    connection.execute("UPDATE cloud_references SET observed_at=%s WHERE reference_id='A'",(AS_OF+timedelta(microseconds=1),))
                    self.assertEqual(connection.execute(cloud.SOLUTIONS[lab_id]).fetchone(),(5,))


class CloudGuidancePrivacyTests(unittest.TestCase):
    def test_eight_bilingual_entries_provenance_import_guidance_and_private_explanations(self):
        ids={key for key,value in CATALOG.items() if value.get('course_id') in ('fabric-testing','adf-testing','onelake-testing')}
        self.assertEqual(ids,set(GUIDANCE));self.assertEqual(len(ids),8)
        for lab_id in ids:
            for language in ('ENG','VIE'):
                public=lesson(lab_id,language);labels=LABELS[language]
                for index in (0,1,2,3,5):self.assertIn(labels[index],public['theory'])
                for marker in ('SIMULATED','IMPORTED','PostgreSQL','48 KiB','CSV','batch_no','as_of','NOT_VERIFIED'):
                    self.assertIn(marker,public['theory'])
                self.assertIn(labels[4],public['requirement'])
                for private in ('explanation','hints','solution_sql'):self.assertNotIn(private,public)
                self.assertNotIn(labels[6],str(public))
                self.assertIn(labels[6],CATALOG[lab_id][language]['explanation'])
