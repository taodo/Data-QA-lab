# Task 2 — Basic Data Quality Engine

Status: completed and merged into `feature/develop`.

## Objectives

Engineering: execute safe, run-scoped validation rules and persist reproducible evidence.

Learning: distinguish completeness, uniqueness, required-field and schema checks; explain `PASS`, `FAIL`, `ERROR` and `NOT_RUN`.

## Delivered behavior

- Dataset registry allowlists schema, table and column identifiers.
- Check SQL composes identifiers with `psycopg.sql.Identifier` and executes in read-only transactions.
- Built-in executors cover record count, uniqueness, nulls and schema contracts.
- Orders suite contains 20 deterministic rules across Bronze, Silver, Gold and Target.
- Count checks use the recorded Source stage count. They do not read mutable Source data after the pipeline run.
- Gold and daily Target compare `SUM(order_count)` because their grain is UTC day.
- Every suite execution creates a validation UUID and stores structured expected, actual, evidence and error fields.
- Quality aggregation priority is `ERROR → FAIL → NOT_RUN → PASS`.
- Updating quality never changes pipeline execution status.
- Repeated validation runs retain history; inspection returns the latest run for a pipeline by default.

## Commands

Existing Task 1 databases must rerun idempotent initialization once to create Task 2 metadata tables:

```text
python -m backend.app.main db-init
python -m backend.app.main quality-run --run-id <pipeline UUID>
python -m backend.app.main quality-inspect --run-id <pipeline UUID>
```

Omit `--run-id` to use the latest successful pipeline run.

## Negative-test boundary

Task 1 analytical tables enforce keys and required columns. Task 2 tests duplicate, null and incompatible-schema behavior through isolated PostgreSQL fixtures. Task 4 will add controlled fault injection while preserving the core requirement that a technically successful pipeline can still fail quality checks.

## Out of scope

Field-level reconciliation, fault injection, learner SQL, API, UI and external data-quality frameworks remain later tasks.
