# Architecture — v1

Local, single-user learning environment. Backend domain and services are independent of transport. API comes after the pipeline/QA engines; UI comes after API.

- Source adapter: PostgreSQL orders and customers.
- Pipeline engine: Python jobs, explicit Source → Bronze → Silver → Gold → Target stages.
- Storage: PostgreSQL schemas for source, bronze, silver, gold and target; isolated `fault_workspace` copies; separate metadata for pipeline, validation and fault runs. No lakehouse file format claim.
- QA engine: allowlisted PostgreSQL checks and reconciliation rules run in read-only transactions and persist expected, actual, bounded evidence and errors per pipeline run.
- Fault engine: deterministic scenario specifications applied to a run workspace.
- Lab engine: requirement, learning objectives, hints, learner submissions and grading.
- API: FastAPI learning/pipeline/quality/fault routes with local Host/Origin guards, bounded inputs/history and safe error responses.
- UI: React/TypeScript with CodeMirror SQL editor, six complete ENG/VIE lessons, hints, deterministic grading, progress/history and pipeline evidence.
- Local release: Compose app + PostgreSQL, non-root app OS user, one worker, idempotent dedicated-database bootstrap and persistent D-drive bind mount.

Task 1 added the executable PostgreSQL pipeline. Task 2 added an allowlisted, read-only QA Engine with persisted validation runs and structured evidence. Task 3 added key and field reconciliation without accepting arbitrary SQL in rule contracts. Task 4 adds allowlisted, atomic fault scenarios against isolated Target copies.

## Boundaries

Execution SUCCESS means all required job stages completed. Quality PASS means the requested validation suite completed with no failures/errors. Before any validation, quality is NOT_RUN. An ERROR signals that a check could not produce a verdict and retains failure evidence separately.

Each run preserves a Bronze source snapshot plus run-scoped Silver, Gold and Target rows, stage metrics, timestamps and errors. New runs do not overwrite earlier evidence. Source reseeding changes only Data QA Lab source tables; existing run evidence remains available.

Reconciliation treats Bronze as the immutable source-side baseline for raw order fields, compares Silver to the order-detail Target, and compares Gold to the daily Target. Key rules find missing and unexpected keys independently, so equal row counts cannot hide swapped records. Field rules compare only matching keys with PostgreSQL `IS DISTINCT FROM`, preserving null semantics and exact `NUMERIC` values.

Fault application copies one successful run's two Target datasets into `fault_workspace` inside a transaction, then performs exactly one deterministic mutation. The original Target and every unrelated run remain unchanged. A partial unique index permits one active fault per pipeline run. Reset removes only that run's workspace rows and is safe to repeat. Fault validation reuses the QA Engine with an explicit workspace registry; pipeline execution status remains `SUCCESS` when the deliberately corrupted copy fails quality.

Challenge mode conceals fault metadata/solutions from learner responses; sandbox mode can expose them. This boundary applies in API payloads, not only the UI.

Task 5 implements this visibility boundary in transport-independent learning
services and CLI serializers. Session snapshots are private and admin-owned;
each query/grade uses another isolated copy with a fresh restricted PostgreSQL
LOGIN. SQL never executes on the provisioning connection. PUBLIC privilege audits,
read-only transactions, streamed bounded outputs and independent cancellation
protect the local execution boundary. See SQL_SECURITY.md for the exact design.
Behavioral grading is independent of both pipeline execution and quality status:
it records a learner submission verdict without updating pipeline status.

## First pipeline grain

Source, Bronze, Silver and order-detail Target: one row per order_id.
Gold and daily-sales Target: one row per UTC order_date.
Gold count checks compare SUM(order_count); revenue checks compare decimal daily totals. Never compare aggregated row counts to source order counts.
