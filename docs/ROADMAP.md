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
| 11 — Cloud QA | Approved and merged 11.1–11.4: Fabric/ADF/OneLake foundations | Transfer concepts to run and data evidence | PR #13 merged at 3406447; final-head CI green; stage 11.5 unapproved |
| 12 — Cloud foundations | Approved 12.1–12.4: six Databricks/Synapse/Azure local lessons and release | Prove classification, versions, fact mapping, grain, manifests and access evidence | 36 lessons across nine executable courses; verification recorded in TASK_12_PROGRESS.md |
| 13 - SQL learning guidance | Beginner explanations for 13 SQL lessons in ENG/VIE | Understand QA requirements, examples and revealed solutions | Reference-SQL example tests, bilingual UI and final-head CI; see TASK_13_PROGRESS.md |
| 14 - ETL learning guidance | Beginner explanations and simulation guidance for five ETL lessons in ENG/VIE | Interpret mappings, transformations, rejects, replay and recovery evidence | Actual reference-SQL examples, bilingual simulation/reveal checks and final-head CI; see TASK_14_PROGRESS.md |
| 17 - Databricks/Synapse/Azure guidance | Beginner explanations for six local foundation lessons in ENG/VIE | Interpret classification, explicit versions, fact mapping, reporting grain, manifests and access evidence | Actual reference-SQL examples, typed foundation import guidance, private bilingual solutions and final-head CI; see TASK_17_PROGRESS.md |
| 16 - Fabric/ADF/OneLake guidance | Beginner explanations for eight local evidence lessons in ENG/VIE | Interpret lineage, schema, layers, copy, watermark, recovery, partitions and freshness | Actual reference-SQL examples, import/provenance guidance, bilingual UI and final-head CI; see TASK_16_PROGRESS.md |
| 15 - API learning guidance | Beginner explanations for four local HTTP lessons in ENG/VIE | Interpret response contracts, pagination, bounded retries and persisted replay evidence | Actual HTTP/PostgreSQL examples, bilingual JSON/reveal UI checks and final-head CI; see TASK_15_PROGRESS.md |

V1 scope is Tasks 0–7.2. Tasks 8–10 are approved and merged into
`feature/develop`, providing 22 lessons across SQL (13), ETL (5) and API (4),
local accounts and a course platform. Task 10 includes actual session PostgreSQL
batches/ingestion and loopback HTTP exercises. See TASK_10.md.
Task 11.1–11.4 was approved and merged as PR #13 into feature/develop on
2026-10-06, reviewed merge 34064470c681816e5ea72e03a82cecabb57dbfb8.
Task 12.1–12.4 is merged as PR #14 at b0863f8798c8bba2c0ed0f8fc5d37c5e1e158fab.
Its six local lessons activate Databricks, Synapse and Azure, giving 36 ENG/VIE
lessons across nine executable courses. See TASK_12_PLAN.md and TASK_12_PROGRESS.md.
Live-cloud stage 11.5 still requires separate approval. No QA Sentinel integration.

Demo preparation is merged as PR #15. Public tunnel startup and external-device
verification remain user-operated; see DEMO_ONLINE.md and DEMO_PROGRESS.md.

Task 13 is merged as PR #18 at 2588f03, adding beginner ENG/VIE guidance to all
13 SQL lessons. Task 14 is merged as PR #19 at 221e1b4 with all five ETL lessons
explained in ENG/VIE. Task 15 is merged as PR #20 at deab838 with all four API lessons explained in ENG/VIE.
Task 16 is merged as PR #21 at e0be176 with eight Fabric/ADF/OneLake lessons explained in ENG/VIE.
Active approved task: Task 17 on feature/task-17-foundations-learning-guidance, from latest origin/feature/develop. Cover six Databricks/Synapse/Azure lessons in ENG/VIE, preserving original challenges and foundation evidence contracts. See TASK_17_PROGRESS.md. Stop at review-ready PR; no merge or next task.
