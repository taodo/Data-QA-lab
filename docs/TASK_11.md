# Task 11 — local cloud QA foundations

Engineering objective: auditable session-owned run/activity and snapshot evidence,
bounded imports and eight executable lessons in the existing account/course platform.
Learning objective: prove lineage, schema, keys, exact amounts, replay, recovery,
partitions and freshness independently from successful cloud execution metadata.

Scope 11.1–11.4 approved on 2026-10-05. Branch feature/task-11-cloud-qa is based
on approved Task 10 merge 6799950642e2a3b621826268dfe10a7f8ff06aa0. Version 1.4.0.
Implementation and verification were completed here; plan/review occurred in the
user's separate ChatGPT chat. PR #13 is approved and merged at
34064470c681816e5ea72e03a82cecabb57dbfb8 (2026-10-06). Reviewed head 81d06a3 passed
full CI run 37300698537. Task 12.1–12.4 is separately approved; stage 11.5 is not.

## Curriculum and evidence

Thirty ENG/VIE lessons across six executable courses: SQL 13, ETL 5, API 4,
Fabric 3, ADF 3 and OneLake 2. Existing lesson/session IDs, accounts, drafts,
history, enrollment and progress are retained. Written answers are saved, not
semantically graded. Reveal does not award completion.

| Lesson | Defined check |
|---|---|
| 023 Fabric lineage | Run/activity/Target linkage, same-run dependencies and UNKNOWN evidence |
| 024 Fabric schema | Missing/extra/type-changed reported fields and duplicate field groups |
| 025 Fabric layers | Source→Bronze→Silver→Gold key/field differences and duplicate output groups |
| 026 ADF copy | Actual Source/Target reconciliation plus bounded copy metrics and state evidence |
| 027 ADF watermark | Latest visible event, late arrivals, inclusive UTC as-of boundary and unique replay |
| 028 ADF recovery | Data completeness, current activity state and latest execution/checkpoint |
| 029 OneLake partitions | Expected partition row counts and duplicate file-key groups |
| 030 OneLake references | Missing/NULL/future/stale references; exact SLA equality remains fresh |

Source grain is event_id; outputs have order_id grain; Target represents published
Gold orders, not daily aggregates. Latest events are bounded by arrived batch and
fixed UTC as_of, then ranked by event_id. A diagnostic score sums rule violations;
one underlying defect can contribute to multiple rules. Instructor SQL examples
are in examples/lab_023_*.sql through examples/lab_030_*.sql. Submission rebuilds
independent clean/shifted/zero/boundary/fault fixtures (including shifted faulty
keys and alternate drifted fields) and compares against separately
specified counts; it does not use the imported file or learner workspace as truth.

## Runtime and file contracts

Every cloud session has isolated operator-owned PostgreSQL tables. Reuse the
existing generated SELECT-only query login, table allowlist, read-only transaction,
100 output rows, 2-second statement timeout, byte/cell bounds and watchdog. Only
authenticated account-owned active SANDBOX sessions may import or simulate.

Evidence is prominently SIMULATED or IMPORTED. Execution, available/incomplete
evidence and quality under the learner's latest check appear separately. An
exploration PASS is limited to that query; independent submission grading also
tests whether it detects faults. An import/reset/action invalidates old checks.
Absent provider state normalizes to UNKNOWN, missing metrics remain NULL and
incomplete evidence cannot establish quality PASS. Query execution errors are ERROR.

JSON version 1 includes provider, resource identity, selected batch_no, UTC as_of,
run/activity records, reported step/checkpoint records, four data snapshots,
reported schema, file manifest and references. Missing batch/as_of is UNKNOWN;
the importer never borrows the receiving session's batch or infers it from rows.
Supported raw
provider fields and their original state are retained alongside normalized fields.
CSV uses the exact header:

```text
dataset,order_id,customer_id,amount,updated_at,event_id,batch_no,run_id
```

Dataset names: source, bronze, silver, target. Money is an exact decimal string
(NUMERIC(14,2)); NULL required money remains observable, not zero. Timestamps need
an explicit UTC offset and normalize to UTC. Duplicate data/file rows remain
evidence. Files cannot supply expected grading contracts or change SQL permissions.

Limits: 48 KiB UTF-8/file, 100 data rows/dataset, 400 data rows total, eight retained
imports/session; 101 runs, 100 steps, 30 activities, 40 schema fields, 50 manifest rows and 20
references per JSON. The existing 64 KiB encoded HTTP request limit also applies.
An escaped JSON request can reach this cap before the file cap. Each import retains
raw content, SHA-256, run IDs, mapping version and server capture time in the owned
session schema. Invalid imports roll back; reset retains previous imports and
query/submission history while rebuilding simulator snapshots.

JSON replaces current metadata, selected batch/as_of, reported steps and all four
snapshots. CSV replaces all four snapshots and retains other metadata but clears
steps and selected batch/as_of to UNKNOWN; its quality is NOT_VERIFIED. Imported
steps are provider claims, not proof that local actions ran. Reset before returning
to simulation after import. Watermark controls are
RESET/NEXT/REPLAY; recovery controls RESET/RECOVER; other lessons RESET/RUN.
Controls perform actual session PostgreSQL publications, with a 100-step bound.
Recovery retains earlier run and step evidence, and repeated recovery is idempotent.

The UI downloads exactly the file returned by the owned `evidence-export` endpoint.
The backend uses the importer contract to validate all rows and bounds, including
the 64 KiB escaped request envelope. No run or row is silently omitted. If a
snapshot cannot fit the file/request bounds, export reports a localized error and
does not produce a file; retained session evidence remains intact.

QA results are bound to a local mutation revision (the monotonic local
`captured_at` token), captured while holding a shared context lock for the SQL
snapshot. Import, Reset and every action advance the token; provider run timestamps
never determine query age. Existing historical checks without a revision are
retained but must be rerun to establish current QA. This uses the existing context
column and query-result JSON; no learner data/schema migration is needed.
UTC conversion overflow becomes a localized EVIDENCE_INVALID validation error.

Use examples/cloud-evidence-v1.json and examples/cloud-snapshots-v1.csv, or download
the current JSON from the evidence viewer. A resource_id identifies the selected
workspace/factory/item in this local contract; it is not a live-provider API schema.
Import uses ordinary file content; it never accepts server paths, retrieves links,
extracts archives or executes code. No credentials, cloud provisioning, Microsoft
emulator, Spark, Delta/Iceberg engine or real shortcut resolution is provided.
Live-cloud stage 11.5 remains unimplemented and requires separate approval.

## Windows review on D

```powershell
Set-Location D:\Data-QA-Lab
git fetch origin
git switch feature/task-11-cloud-qa
git pull --ff-only
docker compose up -d --build --wait --wait-timeout 180
docker compose ps
```

Keep the existing PostgreSQL bind mount and accounts. Do not delete data/postgres.
Open http://localhost:8000 and use your current local login.

1. Fabric lineage: choose clean SANDBOX, inspect runs, dependencies and snapshots.
2. Download/import JSON, inspect IMPORTED and retained SHA-256; try an invalid
   version, then CSV. Reset and verify import history remains.
3. Schema drift: compare reported schema against the independent contract.
4. ADF watermark: RESET, NEXT twice, REPLAY; inspect late and exact-boundary events.
5. ADF recovery: failed dependency or partial publication → RECOVER twice; inspect
   latest SUCCESS/checkpoint and four unique Target orders.
6. OneLake: try missing/duplicate partitions and stale/NULL/future references;
   compare with the clean 60-minute SLA boundary.
7. Submit your checks, switch ENG/VIE, reload and resume through History.
8. Restart the app and verify retained personal evidence and course progress.

## Verification

Commands and observed results are recorded in TASK_11_PROGRESS.md and final PR
description. Dedicated PostgreSQL test databases are separate from learner data.
Logs, browser screenshots, package ZIP and pip/npm/Chromium caches remain on D.

```powershell
python -m unittest discover -s tests/unit -v
# Set DATA_QA_TEST_DATABASE_URL to the dedicated test database, never learner data:
python -m unittest discover -s tests/integration -v
npm run build --prefix frontend
python -m unittest discover -s tests/e2e -v
python scripts/container_smoke.py
docker compose restart app
python scripts/container_smoke.py resume
```

Learning explanation: metadata tells you what a job reported. Keyed reconciliation,
independent contracts and fixed-clock boundaries tell you whether the evidence
supports correct data. Unknown evidence, errors and unrun checks are distinct
from data defects and must never be silently converted into success.

## Course introductions (approved follow-up)

Engineering objective: expose distinct ENG/VIE beginner introductions on all nine
course detail pages, including planned courses, before the curriculum. Learning
objective: understand what each subject is, what problem it solves, and how Data
QA applies before opening a lab.

`backend/app/course_introductions.py` holds separately authored content for SQL,
ETL/ELT, API, Fabric, ADF, OneLake, Azure Data Platform, Databricks and Synapse.
Each entry includes a definition, three explained concepts, a practical example,
uses, the QA role and a connection to current or intended course lessons. Planned
courses explicitly describe future learning; no enrollment/lab availability is
changed. Only course-detail responses include the introduction.

The two independent accordions use full-width native buttons, Enter/Space/Tab,
visible focus and translated expand/collapse labels, plus/minus indicators,
`aria-expanded`, `aria-controls` and labelled panel regions. The first defaults
open, the second closed. Content wraps within the existing mobile layout.

Editorial references checked against primary documentation:
[Fabric](https://learn.microsoft.com/en-us/fabric/fundamentals/microsoft-fabric-overview),
[ADF](https://learn.microsoft.com/en-us/azure/data-factory/introduction),
[OneLake](https://learn.microsoft.com/en-us/fabric/onelake/onelake-overview),
[ETL/ELT](https://learn.microsoft.com/en-us/azure/architecture/data-guide/relational-data/etl),
[Databricks](https://learn.microsoft.com/en-us/azure/databricks/introduction/),
[Synapse](https://learn.microsoft.com/en-us/azure/synapse-analytics/overview-what-is).
Examples and course/QA explanations are specific to this curriculum.
