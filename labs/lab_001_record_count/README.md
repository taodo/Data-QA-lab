# Lab 001 — Record Count & Completeness

**Status: definition only. Execution arrives in Task 1–5.**

Run a clean baseline, inspect each layer, compare counts and key sets, activate missing-row scenario, rerun, collect evidence and submit a conclusion.

Source/Bronze/Silver/Target grain: one row per order. Gold grain: one row per UTC order date. Gold row count will normally be smaller. Sum Gold `order_count` and reconcile daily amounts.

A second exercise will remove one order and introduce a different order: equal counts, unequal keys. Explain why a count-only check misses it.

The future learner API must omit hidden fault details and solutions in challenge mode. Sandbox mode may display the chosen fault.
