"""Instructor content; public session serializers explicitly select learner fields."""
LAB_ID = "lab_001_record_count"
HINTS = (
    "Compare datasets at the same grain. Orders use order_id; daily data uses SUM(order_count).",
    "Equal counts can hide a missing key replaced by an unexpected key. Compare key sets both ways.",
    "Use EXCEPT from Source to Target and from Target to Source; count both difference sets.",
)
SOLUTION = """SELECT
  (SELECT COUNT(*) FROM (
    SELECT order_id FROM source_orders
    EXCEPT SELECT order_id FROM target_orders
  ) AS missing_keys)
  +
  (SELECT COUNT(*) FROM (
    SELECT order_id FROM target_orders
    EXCEPT SELECT order_id FROM source_orders
  ) AS unexpected_keys) AS violation_count"""
EXPLANATION = (
    "Counts measure size, not identity. EXCEPT compares business key sets in both "
    "directions. Zero differences is clean; a missing order or equal-count key "
    "swap produces a positive violation_count. Gold uses day grain, so compare "
    "SUM(order_count), not daily row count. This exercise grades completeness "
    "only; uniqueness, null and calculation checks remain independent."
)
