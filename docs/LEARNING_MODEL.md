# Learning loop

Read requirement → inspect grain/schema → run clean baseline → inspect layers → design SQL checks → run checks → inject a fault → rerun → collect evidence → investigate → submit conclusion → reveal explanation.

Every task produces an engineering capability and a concept the learner can explain.

1. Completeness: record counts plus key sets.
2. Uniqueness: duplicate business keys versus duplicate full rows.
3. Required fields: null counts and business constraints.
4. Schema: missing columns and incompatible types.
5. Transformation: exact net_amount calculation.
6. Reconciliation: missing/unexpected keys and field mismatches.
7. Join cardinality: unintended fan-out.
8. Aggregations: daily revenue and order counts at correct grain.
9. Incremental loads: inserts and updates without duplicates.
10. Late arrivals: lookback windows and watermark boundaries.
11. Freshness: UTC SLA and stale successful loads.
12. Referential integrity: orphan foreign keys.
13. Decimal precision: rounding rules and sums.
14. Timezones: business dates versus UTC timestamps.
15. SCD Type 2: history and overlapping validity periods.

The catalog starts with Lab 001. Later labs are planned, not executable. Grading should inspect submitted checks against clean and faulty datasets, including false positives; matching SQL text is insufficient. Correct SQL execution by itself does not prove test coverage.
