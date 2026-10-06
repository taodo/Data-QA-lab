"""Run unchanged reference SQL against every published miniature example.

Only connection-local temporary tables are written; no learner data is touched.
"""
from datetime import datetime, timezone
from decimal import Decimal as D
import os
import unittest
from psycopg import sql
from backend.app.persistence.database import connect
from backend.app.learning.profiles import PROFILES
from backend.app.learning.advanced_workspace import DDL
from backend.app.learning.lessons import CATALOG, lesson
from backend.app.learning.sql_guidance import GUIDANCE, LABELS

DB = os.getenv("DATA_QA_TEST_DATABASE_URL")


def at(day, hour=0, minute=0):
    return datetime(2026, 1, day, hour, minute, tzinfo=timezone.utc)


def source(key, gross="10.00", discount="0.00", refund="0.00"):
    return (key, 7, at(1), D(gross), D(discount), D(refund), at(1))


def target(key, amount="10.00", customer=7):
    return (key, customer, at(1), D(amount) if amount is not None else None)


BASIC_DDL = {
    "source_orders": "order_id bigint,customer_id bigint,ordered_at timestamptz,gross_amount numeric(14,2),discount_amount numeric(14,2),refund_amount numeric(14,2),updated_at timestamptz",
    "target_orders": "order_id bigint,customer_id bigint,ordered_at timestamptz,net_amount numeric(14,2)",
    "gold_daily_sales": "order_date date,order_count bigint,net_revenue numeric(18,2)",
    "target_daily_sales": "order_date date,order_count bigint,net_revenue numeric(18,2)",
}
EXAMPLES = {
    "lab_002_sql_basics": (2, {"target_orders": [target(10, customer=7), target(20, customer=0), target(30, customer=-2)]}),
    "lab_003_nulls": (1, {"target_orders": [target(10), target(20, None), target(30, "0.00")]}),
    "lab_004_duplicates": (1, {"target_orders": [target(key) for key in (10,10,10,20,30)]}),
    "lab_001_record_count": (2, {"source_orders": [source(key) for key in (10,20,30)], "target_orders": [target(key) for key in (10,20,40)]}),
    "lab_005_calculations": (2, {"source_orders": [source(10,"100.00","10.00","5.00"),source(20,"10.01"),source(30,"0.00")], "target_orders": [target(10,"85.00"),target(20,"10.02"),target(30,None)]}),
    "lab_006_capstone": (3, {"source_orders": [source(10),source(20,"20.00"),source(30,"0.00")], "target_orders": [target(10),target(20,None),target(30,"0.00")], "gold_daily_sales": [(at(1).date(),3,D("30.00"))], "target_daily_sales": [(at(1).date(),3,D("10.00"))]}),
    "lab_007_join_grain": (1, {"order_lines": [(10,1,D("10.00")),(10,2,D("10.00")),(20,1,D("0.00"))], "order_payments": [(10,1,D("10.00")),(10,2,D("10.00")),(20,1,D("0.00"))], "target_order_totals": [(10,D("40.00")),(20,D("0.00"))]}),
    "lab_008_latest_version": (1, {"source_order_events": [(1,10,at(1,12),D("10.00")),(2,10,at(2,12),D("12.00")),(3,10,at(2,12),D("11.00")),(4,20,at(1,12),D("0.00"))], "target_current_orders": [(2,10,at(2,12),D("12.00")),(4,20,at(1,12),D("0.00"))]}),
    "lab_009_utc_dates": (2, {"source_time_orders": [(10,at(1,23,30),D("10.01")),(20,at(2),D("0.00")),(30,at(2,0,30),D("7.00"))], "target_utc_daily": [(at(2).date(),3,D("17.01"))]}),
    "lab_010_incremental": (2, {"lab_context": [("lab_010_incremental",at(4,12))], "incremental_events": [(1,10,at(1,12),at(2,12),D("10.00"),1),(2,10,at(3,12),at(3,12),D("12.00"),2),(3,20,at(1,12),at(4,12),D("7.00"),3)], "incremental_target": [(2,10,at(3,12),D("12.00")),(2,10,at(3,12),D("12.00"))]}),
    "lab_011_freshness": (2, {"freshness_requirements": [("orders",at(4,12),5),("payments",at(4,12),15),("customers",at(4,12),60)], "freshness_observations": [("orders",at(4,11,55),at(4,11,55),"SUCCESS"),("payments",at(4,11,59),at(4,11,44),"SUCCESS")]}),
    "lab_012_scd_type1": (1, {"source_customer_changes": [(1,10,at(1),"BRONZE"),(2,10,at(2),"GOLD"),(3,20,at(1),"SILVER")], "target_customers_current": [(1,10,at(1),"BRONZE"),(3,20,at(1),"SILVER")]}),
    "lab_013_scd_type2": (2, {"source_customer_changes": [(1,10,at(1),"BRONZE"),(2,10,at(2),"GOLD"),(3,20,at(1),"BRONZE")], "target_customer_history": [(1,10,"BRONZE",at(1),at(2),False),(2,10,"GOLD",at(2),None,True),(3,20,"BRONZE",at(1),None,False)]}),
}


@unittest.skipUnless(DB, "PostgreSQL test database required")
class SqlGuidanceExampleTests(unittest.TestCase):
    def test_all_thirteen_published_examples_match_actual_reference_sql(self):
        self.assertEqual(set(EXAMPLES), set(GUIDANCE))
        for lab_id, (expected, tables) in EXAMPLES.items():
            with self.subTest(lab_id=lab_id), connect(DB) as connection:
                for table in PROFILES[lab_id].datasets:
                    connection.execute(sql.SQL("CREATE TEMP TABLE {} ({}) ON COMMIT DROP").format(sql.Identifier(table),sql.SQL((BASIC_DDL | DDL)[table])))
                    rows = tables.get(table, [])
                    if rows:
                        with connection.cursor() as cursor:
                            cursor.executemany(sql.SQL("INSERT INTO {} VALUES ({})").format(sql.Identifier(table),sql.SQL(',').join(sql.Placeholder() for _ in rows[0])),rows)
                # The reference query, not a duplicated Python implementation, verifies the claim.
                cursor = connection.execute(PROFILES[lab_id].solution)
                self.assertEqual([column.name for column in cursor.description], ["violation_count"])
                self.assertEqual(cursor.fetchall(), [(expected,)])
                for language in ("ENG","VIE"):
                    self.assertIn(f"violation_count = {expected}", GUIDANCE[lab_id][language][2])
                # UTC-date result must not depend on the connection's display timezone.
                if lab_id == "lab_009_utc_dates":
                    connection.execute("SET LOCAL TIME ZONE 'Asia/Bangkok'")
                    self.assertEqual(connection.execute(PROFILES[lab_id].solution).fetchone()[0],expected)


class SqlGuidancePrivacyTests(unittest.TestCase):
    def test_coverage_and_public_content_keep_reveal_explanation_private(self):
        sql_ids = {key for key,value in CATALOG.items() if value.get("course_id","sql-data-qa")=="sql-data-qa"}
        self.assertEqual(sql_ids,set(GUIDANCE))
        self.assertEqual(len(sql_ids),13)
        for lab_id in sql_ids:
            for language in ("ENG","VIE"):
                public = lesson(lab_id,language)
                labels = LABELS[language]
                for heading in labels[:4]:
                    self.assertIn(heading,public["theory"])
                self.assertIn(labels[4],public["requirement"])
                self.assertNotIn("explanation",public)
                self.assertNotIn(labels[5],str(public))
                self.assertIn(labels[5],CATALOG[lab_id][language]["explanation"])
