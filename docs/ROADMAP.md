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
| 9 — Cloud adapter | Optional Fabric implementation | Transfer established concepts | Explicit separate planning checkpoint |

V1 scope is Tasks 0–7.2: a local single-user app with six foundation ENG/VIE lessons, real PostgreSQL SQL execution/grading and persistent learning history. Tasks 5–7.2 are merged. Task 8.1–8.4 implementation is approved together on one Task 8 branch; it adds seven advanced lessons and awaits completed-task review before merge. Task 9 remains optional future scope. See TASK_8.md. No fixed completion date or QA Sentinel integration.
