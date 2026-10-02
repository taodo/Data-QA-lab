# Architecture — v1

Local, single-user learning environment. Backend domain and services are independent of transport. API comes after the pipeline/QA engines; UI comes after API.

- Source adapter: PostgreSQL orders and customers.
- Pipeline engine: Python jobs, explicit Source → Bronze → Silver → Gold → Target stages.
- Storage: PostgreSQL schemas for source, bronze, silver, gold, target; separate metadata schema for runs in Task 1. No lakehouse file format claim.
- QA engine: SQL checks and key-based comparisons produce evidence per run.
- Fault engine: deterministic scenario specifications applied to a run workspace.
- Lab engine: requirement, learning objectives, hints, learner submissions and grading.
- API: FastAPI planned for Task 6.
- UI: React planned for Task 7.

Task 0 provides domain contracts and a catalog CLI only. Docker Compose is introduced with an executable database adapter in Task 1 rather than an unused service file.

## Boundaries

Execution SUCCESS means all required job stages completed. Quality PASS means the requested validation suite completed with no failures/errors. Before any validation, quality is NOT_RUN. An ERROR signals that a check could not produce a verdict and retains failure evidence separately.

Each run will preserve immutable source snapshots, effective fault configuration, stage metrics, schema observations and logs. New runs must not overwrite evidence of earlier runs. A second run or reset must recreate a clean baseline.

Challenge mode conceals fault metadata/solutions from learner responses; sandbox mode can expose them. This boundary applies in API payloads, not only the UI.

## First pipeline grain

Source, Bronze, Silver and order-detail Target: one row per order_id.
Gold and daily-sales Target: one row per UTC order_date.
Gold count checks compare SUM(order_count); revenue checks compare decimal daily totals. Never compare aggregated row counts to source order counts.
