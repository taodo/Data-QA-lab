# Task 3 — Key and field reconciliation

Status: approved and merged into `feature/develop`.

## Objectives

Engineering: reconcile run-scoped datasets by business key and exact field value with bounded, reproducible evidence.

Learning: explain why equal row counts do not prove equal data, distinguish missing and unexpected keys, and locate field mismatches on matching records.

## Delivered behavior

- `KEY_RECONCILIATION` finds missing and unexpected key sets independently with PostgreSQL `EXCEPT`.
- `FIELD_RECONCILIATION` joins matching business keys and uses `IS DISTINCT FROM` for null-safe comparisons.
- Rules support composite keys, explicit field mappings and evidence limits from 1 to 100.
- Dataset pairs and every schema, table and column identifier remain allowlisted; rules cannot contain arbitrary SQL.
- Run-scoped filters are applied to both sides, preventing evidence leakage between pipeline runs.
- The default orders suite now has 26 rules and reconciles Bronze → Silver, Silver → order Target and Gold → daily Target.
- Evidence records exact keys and field values but is bounded independently from total mismatch counts.
- Existing Task 2 databases upgrade idempotently through `db-init`; validation history is preserved.

## Equal-count trap

The key scenario removes order `1` from the order Target and inserts unexpected order `999999`. The target still contains the expected number of rows, so its record-count rule passes. Key reconciliation fails with both the missing and unexpected key, demonstrating why counts alone are insufficient.

## Commands

Existing local databases must run initialization once to extend the validation-result constraint:

```text
python -m backend.app.main db-init
python -m backend.app.main pipeline-run
python -m backend.app.main quality-run
python -m backend.app.main quality-inspect
```

## Out of scope

User-authored SQL, transformations expressed as arbitrary formulas, API and UI remain later tasks. Derived `net_amount` is reconciled from Silver to Target after the pipeline computes it; Task 3 does not introduce an expression language. Fault-scenario orchestration is delivered separately in Task 4.
