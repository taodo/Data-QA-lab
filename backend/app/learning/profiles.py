"""Allowlisted instructor SQL and independent grading fixtures per lesson."""
from dataclasses import dataclass
from backend.app.learning.content import LAB_ID, SOLUTION

FILTER_SQL = "SELECT COUNT(*) AS violation_count FROM target_orders WHERE customer_id <= 0"
NULL_SQL = "SELECT COUNT(*) AS violation_count FROM target_orders WHERE net_amount IS NULL"
DUPLICATE_SQL = "SELECT COUNT(*) AS violation_count FROM (SELECT order_id FROM target_orders GROUP BY order_id HAVING COUNT(*) > 1) AS duplicate_keys"
CALC_SQL = """SELECT COUNT(*) AS violation_count
FROM source_orders s JOIN target_orders t ON s.order_id=t.order_id
WHERE t.net_amount IS DISTINCT FROM (s.gross_amount-s.discount_amount-s.refund_amount)"""
DAILY_SQL = """SELECT COUNT(*) AS violation_count
FROM gold_daily_sales g FULL JOIN target_daily_sales t USING (order_date)
WHERE g.order_date IS NULL OR t.order_date IS NULL
   OR g.order_count IS DISTINCT FROM t.order_count
   OR g.net_revenue IS DISTINCT FROM t.net_revenue"""
CAPSTONE_SQL = f"""SELECT
({SOLUTION}) + ({NULL_SQL}) + ({DUPLICATE_SQL}) +
({CALC_SQL}) + ({DAILY_SQL}) AS violation_count"""


@dataclass(frozen=True)
class Profile:
    scenarios: tuple[str, ...]
    variants: tuple[str, ...]
    solution: str


PROFILES = {
    "lab_002_sql_basics": Profile(("invalid_customer",), ("clean", "clean_subset", "invalid_customer", "invalid_customer_last", "invalid_customer_two"), FILTER_SQL),
    "lab_003_nulls": Profile(("null_net_amount",), ("clean", "clean_subset", "clean_zero", "null_net_amount", "null_last", "null_two"), NULL_SQL),
    "lab_004_duplicates": Profile(("duplicate_order",), ("clean", "clean_subset", "duplicate_order", "duplicate_last", "duplicate_twice", "duplicate_triple"), DUPLICATE_SQL),
    LAB_ID: Profile(("missing_order", "equal_count_swap"), ("clean", "clean_subset", "missing", "swapped"), SOLUTION),
    "lab_005_calculations": Profile(("wrong_net_amount",), ("clean", "clean_subset", "clean_zero", "wrong_net_amount", "wrong_last", "wrong_two", "null_net_amount"), CALC_SQL),
    "lab_006_capstone": Profile(("mixed_order_faults", "daily_wrong"), ("clean", "clean_subset", "clean_zero", "missing", "swapped", "null_net_amount", "duplicate_order", "wrong_net_amount", "daily_wrong", "daily_missing", "mixed_order_faults"), CAPSTONE_SQL),
}
