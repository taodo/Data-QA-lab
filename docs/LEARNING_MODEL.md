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

Lab 001 is executable through learning sessions and the CLI. Later labs remain planned.
It grades key completeness by executing submitted SQL against two clean and two
defective snapshots. Matching SQL text is never required. A correct count query
can execute successfully yet FAIL grading because it misses equal-count key swaps.

Sessions are ACTIVE until a passing submission marks them COMPLETED or explicit
reveal marks them REVEALED. Failed/error submissions allow another attempt. Hints
advance through three levels. Completion/reveal exposes the instructor solution;
revealed sessions cannot submit for credit. History survives process restarts.

Conclusions are required and preserved for review, but their reasoning is not
semantically graded in this deterministic V1. Challenge mode hides scenario and
grading fixture values in service responses; it is not secrecy against a local
administrator with access to repository files or the database.
