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
| 8 — Advanced | Incremental, joins, freshness, dates, SCD | Diagnose realistic data incidents | Scenarios and regression evidence |
| 9 — Cloud adapter | Optional Fabric implementation | Transfer established concepts | Explicit separate planning checkpoint |

Current state: Tasks 1–5 are approved and merged into `feature/develop`. The user approved implementing Tasks 6, 7, 7.1 and 7.2 consecutively and merging each after passing verification. Task 6 is in progress. V1 means a local single-user app with six complete ENG/VIE lessons, real PostgreSQL SQL execution/grading and persistent learning history. Tasks 8–9 remain future scope. No promise of completion by a fixed calendar date. No QA Sentinel integration in this roadmap.
