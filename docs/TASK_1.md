# Task 1 — First working PostgreSQL pipeline

Status: completed and merged into `feature/develop`.

## Objectives

Engineering: run a deterministic PostgreSQL pipeline with retained evidence through Source, Bronze, Silver, Gold and Target.

Learning: explain extraction, raw preservation, cleaning, business transformation, reporting grain and why pipeline execution status is separate from data quality.

## Delivered behavior

- Docker Compose starts PostgreSQL 16 on loopback only.
- Six app-owned schemas isolate source, four pipeline concerns and run metadata.
- Source seed creates 1,000 customers and 10,000 orders with fixed formulas, UTC timestamps and exact decimal money.
- Every pipeline run gets a UUID. Bronze, Silver, Gold and Target rows carry it, so later runs do not overwrite prior evidence.
- Each stage commits separately. A failed stage is rolled back and logged; downstream stages are not claimed successful.
- Gold uses UTC-day grain. Its `row_count` is the number of dates; `metrics.order_count` reconciles orders.
- Target exposes an order-detail table and a daily-sales table.
- CLI supports `db-init`, `seed`, `pipeline-run` and `inspect`.
- GitHub Actions runs unit and live PostgreSQL integration tests.

## Contracts

Clean fixture:

- Customers: 1,000.
- Orders: 10,000 unique `order_id` values.
- Expected net revenue: `25,245,493.29`.
- `net_amount = gross_amount - discount_amount - refund_amount`.
- Business timestamps are timezone-aware and stored as `TIMESTAMPTZ`.

A clean run ends with execution `SUCCESS` and quality `NOT_RUN`. Task 1 does not infer quality from successful movement/transformation.

## Commands

Run from the repository root:

```text
python -m backend.app.main db-init
python -m backend.app.main seed
python -m backend.app.main pipeline-run
python -m backend.app.main inspect
```

## Scope boundary

The QA Engine, fault injection, learner SQL, API and UI remain later tasks. PostgreSQL schemas model medallion layers locally; this task does not claim to implement lakehouse file storage.
