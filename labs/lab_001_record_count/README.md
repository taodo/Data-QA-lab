# Lab 001 — Record Count & Completeness

**Status: executable learning session in Task 5.**

Run a clean baseline, inspect each layer, compare counts and key sets, activate missing-row scenario, rerun, collect evidence and submit a conclusion.

Source/Bronze/Silver/Target grain: one row per order. Gold grain: one row per UTC order date. Gold row count will normally be smaller. Sum Gold `order_count` and reconcile daily amounts.

A second exercise will remove one order and introduce a different order: equal counts, unequal keys. Explain why a count-only check misses it.

Learner queries use these unqualified workspace tables: `source_orders` (immutable
Bronze snapshot), `target_orders`, `gold_daily_sales` and `target_daily_sales`.
Only the current session's copies are available. Return one integer column named
`violation_count`: zero for matching key sets, positive for missing/unexpected keys.
Grading tests clean, smaller clean, missing-key and equal-count-swapped-key data.

Challenge mode omits scenario, solution and grading case values. Sandbox mode
shows scenario/case detail. Three progressive hints are available. A passing
submission completes the session and reveals the solution; explicit `lab-reveal`
also reveals it but ends the session without a passing submission.
