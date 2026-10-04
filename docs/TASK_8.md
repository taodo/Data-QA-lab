# Task 8 — Advanced SQL and pipeline QA (8.1–8.4)

Engineering objective: seven real PostgreSQL lessons with deterministic fixtures,
lesson-specific restricted datasets, exact reference grading, and a persisted
batch/replay simulator. Learning objective: prove grain, latest-state correctness,
arrival/version ordering, freshness and dimension history using observable evidence.

One approved task branch: `feature/task-8-advanced-labs`, based on develop V1
`c43e504dcb97fe472f9430aa7da81096b0852bee`. Review the full task before merging.

| Part | Lessons | Evidence to learn |
|---|---|---|
| 8.1 | 007 JOIN/grain, 008 latest event, 009 UTC dates | Fanout, CTE aggregation, deterministic ROW_NUMBER ties, explicit timezone |
| 8.2 | 010 incremental | Three actual batch loads, replay, keyed greatest-version merge, late new keys and corrections |
| 8.3 | 011 freshness | Successful stale load, per-dataset SLA, missing/NULL/future timestamps, equality boundary |
| 8.4 | 012 Type 1, 013 Type 2 | Current overwrite, LEAD history, simultaneous correction, half-open intervals, current flags |

## Use through the app

The catalog now has six foundation and seven advanced lessons, filterable by track.
Every lesson has ENG/VIE theory, objectives, guided steps, executable practice SQL,
an explicit count contract, three hints and a post-completion explanation. Challenge
hides the selected fault; Sandbox exposes only selected scenario metadata. Grading
runs independent clean/faulty fixtures, including shifted keys/times/event IDs.

Incremental Sandbox starts fully loaded. Reset clears only this session's simulated
target/step timeline; it retains query/submission history and does not change the
original pipeline. Run Next for batches 1 and 2, Replay batch 2, then Next for batch 3.
Replay does not consume a new batch. The fixed `lab_context.as_of` advances with
arrival cutoff. Read `incremental_steps`, `incremental_events` and
`incremental_target` with learner SQL. Completed/revealed sessions cannot mutate;
Challenge cannot invoke simulation actions. A timeline retains 100 steps (latest
20 shown); Reset allows a new sequence.

All advanced fixtures are small synthetic teaching datasets attached to the chosen
successful `orders_v1` run/session. They are not measurements of the live source,
wall-clock monitoring or a production CDC pipeline. Their fixed January 2026 clock
is intentional; do not replace freshness evaluation with NOW(). The original four
foundation tables and existing sessions continue working unchanged.

## Verification

```bash
python -m unittest discover -s tests/unit -v
DATA_QA_TEST_DATABASE_URL=postgresql://... python -m unittest discover -s tests/integration -v
cd frontend && npm ci && npm run build
DATA_QA_TEST_DATABASE_URL=postgresql://... python -m unittest discover -s tests/e2e -v
docker compose up -d --build --wait --wait-timeout 180
python scripts/container_smoke.py
docker compose restart app
docker compose up -d --wait
python scripts/container_smoke.py resume
```

Tests assert independent exact oracle counts, clean/shifted/tied/zero/SLA-equality/
adjacent-history cases, wrong-metric rejection, permission denial, preserved run and
cross-session isolation. Browser tests cover all thirteen lessons, track selection,
simulation replay, ENG/VIE switch, reload and mobile width. Container restart verifies
both completed foundation history and an in-progress incremental timeline.

Local unit/build results and final CI evidence will be recorded before handoff.

## Limits and interpretation

No new dependency, AI key, cloud, authentication, scheduler, CDC connector or delete
events. Incremental merge is an atomic operator-controlled keyed replacement in a
small session snapshot; it is not a general production upsert service. SCD datasets
are materialized fixtures for validation, not a customer ingestion connector.
Incremental and SCD2 scores sum rule violations and can count one root defect under
multiple rules. Conclusions are retained, not semantically AI-graded. Reference
execution failures are ERROR, not learner FAIL. Existing local single-user SQL
security/time/output boundaries apply to every new dataset.
