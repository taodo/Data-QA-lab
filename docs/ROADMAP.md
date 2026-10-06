# Capability roadmap

| Task | Engineering output | Learning objective | Exit evidence |
|---|---|---|---|
| 0 — Foundation | Contracts, catalog, docs, skeleton | Explain layers, grain, execution vs quality | Catalog loads; unit tests pass |
| 1 — First pipeline | PostgreSQL, Compose, seeds, Python stages, run metadata | Trace data movement and aggregation | Clean deterministic baseline across every stage; repeat runs |
| 2 — QA engine | Count, uniqueness, null and schema checks | Distinguish four defect classes | Clean PASS, defective FAIL, check errors ERROR |
| 3 — Reconciliation | Key and field comparisons | Prove source-to-target correctness | Missing/unexpected/mismatched evidence; equal-count trap |
| 4 — Fault injection | Missing, duplicate, null, wrong calculation | Investigate successful but incorrect loads | SUCCESS execution + FAIL quality; clean reset |
| 5 — Learning labs | Sessions, learner SQL, grading, hints | Design checks and justify conclusions | Read-only bounded SQL; hidden solutions; real evaluation |
| 6 — API | FastAPI endpoints and run queries | Read evidence through contracts | Integration checks including error responses |
| 7 — UI | Lab browser, pipeline, SQL, faults, history | Complete the learning loop visually | End-to-end lab with actual backend |
| 7.1 — V1 curriculum | Six bilingual ENG/VIE lessons, instructions, fixtures and graders | Learn SQL for data QA through guided practice and challenges | Every lesson evaluated against clean and faulty data |
| 7.2 — V1 release | Local Compose app, Windows D-drive setup, recovery and E2E checks | Use and resume a complete learning app | Browser learning flow and reproducible startup |
| 8.1 — Advanced SQL | JOIN/grain, CTE, ROW_NUMBER, UTC dates | Diagnose fanout, tied versions and date boundaries | Independent fixture counts and real grading |
| 8.2 — Incremental | Actual session batch/replay simulation, version-guarded merge | Prove idempotency and late-arrival handling | Replay/late-key/tied-update evidence |
| 8.3 — Freshness | Fixed clock and per-dataset SLA | Separate SUCCESS and fresh data | Missing/NULL/future/boundary tests |
| 8.4 — SCD | Type 1 current and Type 2 history lessons | Reconcile versions and half-open intervals | Current/overlap/history regression evidence |
| 9 — Learning platform | Course UI, subject/course/chapter routes, local accounts and personal evidence | Follow a guided course and resume personal progress | Two-account isolation, real signup/lesson flow, retained legacy history |
| 10 — ETL / API curriculum | Five ETL and four API lessons, real PostgreSQL and HTTP execution | Validate pipeline and ingestion contracts | Approved and merged; independent clean/fault graders, browser flow and Docker restart |
| 11 — Cloud QA | Approved 11.1–11.4: Fabric/ADF/OneLake foundations, local simulations and imported evidence | Transfer established concepts to cloud run and data evidence | Eight implemented lessons under review; live-adapter stage 11.5 remains proposed |

V1 scope is Tasks 0–7.2. Tasks 8–10 are approved and merged into
`feature/develop`, providing 22 lessons across SQL (13), ETL (5) and API (4),
local accounts and a course platform. Task 10 includes actual session PostgreSQL
batches/ingestion and loopback HTTP exercises. See TASK_10.md.
Task 11.1–11.4 was approved on 2026-10-05 and implemented on
`feature/task-11-cloud-qa`, increasing the branch catalog to 30 lessons across six
courses. It has not been merged; see TASK_11.md and TASK_11_PROGRESS.md for scope,
verification and remaining review. Live-cloud stage 11.5 requires separate approval.
Databricks, Synapse and broader Azure courses
are proposed for a following phase. No fixed completion date or QA Sentinel integration.
