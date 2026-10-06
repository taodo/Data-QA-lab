"""Validate published ETL miniature examples using unchanged reference SQL."""
from datetime import datetime, timezone
from decimal import Decimal
import os
import unittest
from psycopg import sql
from backend.app.learning.etl import DDL, SPECS
from backend.app.learning.etl_guidance import GUIDANCE, LABELS
from backend.app.learning.lessons import CATALOG, lesson
from backend.app.learning.profiles import PROFILES
from backend.app.persistence.database import connect

DB = os.getenv("DATA_QA_TEST_DATABASE_URL")


def source(key, gross, discount="0.00", code="A", batch=1, event=None):
    return (key, code, gross, discount, batch, event or key)


def target(key, amount, customer=7, event=None):
    return (key, customer, Decimal(amount) if amount is not None else None, event or key)


EXAMPLES = {
    "lab_014_etl_mapping": (3, {"etl_customers": [("A",7),("B",8)],
        "etl_source": [source(10,"10.00"),source(20,"5.00",code="B"),source(30,"0.00")],
        "etl_target": [target(10,"10.00",8),target(20,"5.00",8),target(40,"0.00")]}),
    "lab_015_etl_transform": (2, {"etl_source": [source(10,"10.01"),source(20,"5.00","5.00"),source(30,"8.00","1.00")],
        "etl_target": [target(10,"10.00"),target(20,"0.00"),target(30,None)]}),
    "lab_016_etl_quarantine": (2, {"etl_source": [source(10,"10.00"),source(20,"oops"),source(30,"1,23")],
        "etl_target": [target(10,"10.00")], "etl_rejects": [(20,"INVALID_AMOUNT"),(20,"INVALID_AMOUNT")]}),
    "lab_017_etl_replay": (3, {"etl_context": [("lab_017_etl_replay",datetime(2026,10,1,tzinfo=timezone.utc),2)],
        "etl_source": [source(10,"10.00",event=1),source(10,"12.00",batch=2,event=2),source(20,"7.00",batch=3,event=3)],
        "etl_target": [target(10,"10.00",event=1),target(10,"10.00",event=1)]}),
    "lab_018_etl_recovery": (2, {"etl_source": [source(10,"10.01","0.01"),source(20,"5.00","1.00"),source(30,"0.00")],
        "etl_target": [target(10,"10.00"),target(20,"4.00")],
        "etl_steps": [(1,"RUN","FAILED",0,0,0),(2,"RECOVER","FAILED",2,0,0)]}),
}


@unittest.skipUnless(DB, "PostgreSQL test database required")
class EtlGuidanceExampleTests(unittest.TestCase):
    def test_all_five_examples_match_reference_queries(self):
        self.assertEqual(set(EXAMPLES),set(SPECS))
        for lab_id,(expected,tables) in EXAMPLES.items():
            with self.subTest(lab_id=lab_id), connect(DB) as connection:
                for table,ddl in DDL.items():
                    connection.execute(sql.SQL("CREATE TEMP TABLE {} ({}) ON COMMIT DROP").format(sql.Identifier(table),sql.SQL(ddl)))
                    rows=tables.get(table,[])
                    if rows:
                        with connection.cursor() as cursor:
                            cursor.executemany(sql.SQL("INSERT INTO {} VALUES ({})").format(sql.Identifier(table),sql.SQL(',').join(sql.Placeholder() for _ in rows[0])),rows)
                cursor=connection.execute(PROFILES[lab_id].solution)
                self.assertEqual([column.name for column in cursor.description],["violation_count"])
                self.assertEqual(cursor.fetchall(),[(expected,)])
                for language in ("ENG","VIE"):
                    self.assertIn(f"violation_count = {expected}",GUIDANCE[lab_id][language][2])
                if lab_id=="lab_018_etl_recovery":
                    connection.execute("UPDATE etl_steps SET execution_status='SUCCESS',checkpoint=1 WHERE step_no=2")
                    self.assertEqual(connection.execute(PROFILES[lab_id].solution).fetchone(),(1,))
                    connection.execute("INSERT INTO etl_target VALUES (30,7,0.00,30)")
                    connection.execute("DELETE FROM etl_steps")
                    # Document the existing missing-step limitation, without changing grading.
                    self.assertEqual(connection.execute(PROFILES[lab_id].solution).fetchone(),(0,))


class EtlGuidancePrivacyTests(unittest.TestCase):
    def test_five_bilingual_entries_and_private_solution_gate(self):
        ids={key for key,value in CATALOG.items() if value.get("course_id")=="etl-testing"}
        self.assertEqual(ids,set(GUIDANCE)); self.assertEqual(len(ids),5)
        for lab_id in ids:
            for language in ("ENG","VIE"):
                public=lesson(lab_id,language); labels=LABELS[language]
                for index in (0,1,2,3,5):
                    self.assertIn(labels[index],public["theory"])
                self.assertIn(labels[4],public["requirement"])
                self.assertNotIn("explanation",public)
                self.assertNotIn(labels[6],str(public))
                self.assertIn(labels[6],CATALOG[lab_id][language]["explanation"])
