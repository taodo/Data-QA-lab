# Task 10 — ETL and API testing courses

Engineering objective: make ETL and HTTP exercises executable in the local
account-scoped learning platform, with retained evidence and independent grading.
Learning objective: design checks that prove data contracts using actual source,
HTTP and PostgreSQL target evidence, rather than trusting SUCCESS or HTTP 200.

Branch: `feature/task-10-etl-api-curriculum`, based on approved Task 9 merge
`12171da2047e76fbd10c084c61ee3c0ab381c158`. Version 1.3.0.

## Curriculum

Three executable courses contain 22 ENG/VIE lessons: original SQL (13), ETL (5)
and API (4). Each course has its own chapters, enrollment, progress and resume
routes. Existing session IDs, answers, restricted SQL and account data remain.

| Lesson | Practice and graded contract |
|---|---|
| 014 Mapping | Join customer-code reference data; reconcile keys and mapped IDs |
| 015 Transformation | Parse amount strings into exact NUMERIC; preserve cents, zeros and NULL evidence |
| 016 Quarantine | Prove valid keys reach Target and invalid keys reach unique rejects with the correct reason |
| 017 Replay | Run/reset/advance/replay three persisted batches; validate latest visible events and unique keys |
| 018 Recovery | Recover an interrupted publication; check the latest execution/checkpoint plus Target completeness |
| 019 HTTP contract | Actual GET response status, required JSON fields and integer/decimal-string types |
| 020 Pagination | Follow all pages, compare expected keys and detect duplicate response keys |
| 021 Retry | Actual 429/503 followed by success; bounded retry, exhausted attempts and real socket timeouts |
| 022 API ingestion | Load actual HTTP records into PostgreSQL twice; reconcile keys, exact amounts and idempotency |

Instructions precede practice and the challenge precedes the written answer.
Queries, HTTP response/attempt evidence and submissions are retained. Written
answers are saved but not semantically graded. Reveal does not award completion.

## Runtime and boundaries

ETL has dedicated allowlisted Source, customer reference, Target, rejects,
context and step tables in each session schema. The existing restricted SQL login
retains SELECT-only access and output/time bounds. Trusted SANDBOX actions change
only that session's data. Grading rebuilds independent fixtures, including shifted
keys; it does not change the learner's current workspace.

API exercises use JSON request/check plans, not arbitrary executable code. The
runner starts a per-invocation stdlib HTTP server on an ephemeral loopback port,
sends actual TCP HTTP requests, closes it after the run and does not send learner
cookies. No external service, separate manual setup or additional dependency is
required. Plans allow only GET /orders: up to 10 pages, 3 attempts per page,
50–300 ms/request and 64 KiB per response. HTTP bodies include exact decimal
strings. Retry evidence preserves headers, attempts, elapsed time and final
status; intermediate transient errors do not alone make quality FAIL.

For ingestion, each of two replays performs real session PostgreSQL writes.
Grading executes its own target changes inside rolled-back transactions, retaining
the learner's actual Target. Fixture failure produces grading ERROR; a data defect
produces FAIL. Transport execution and configured-check quality are displayed
separately. A status-only check can show PASS during exploration and still fail the
independent submission grader because it misses data defects.

ETL actions: RESET clears output and evidence. RUN rebuilds a valid mapping,
transformation or quarantine load from Source. The selected defective starting
snapshot remains evidence in query history. Incremental append/skip policies
remain reproducible on NEXT/REPLAY; RECOVER resumes interrupted publication,
while the partial-publication policy continues to expose an incorrect SUCCESS.
Original SQL simulation is unchanged. Controls require an active SANDBOX.

The API playground is intentionally deterministic and local. It teaches fixed
request/check contracts, not unrestricted HTTP scripting or a cloud SDK. Fabric,
ADF, OneLake, Azure, Databricks and Synapse remain planned for Task 11.

## Windows review

Open Docker Desktop first, then PowerShell:

```powershell
Set-Location D:\Data-QA-Lab
git fetch origin
git switch feature/task-10-etl-api-curriculum
git pull --ff-only
docker compose up -d --build --wait --wait-timeout 180
docker compose ps
Start-Process 'http://localhost:8000'
```

On the first checkout, if Git says the local branch does not exist, use:

```powershell
git switch --track origin/feature/task-10-etl-api-curriculum
```

Preserve `.env` and `data/postgres` on D; do not delete the database. Bootstrap
applies the additive course/scenario upgrade. Your current local account works.

1. Explore courses: SQL 13, ETL 5, API 4; switch ENG/VIE.
2. ETL Recovery: SANDBOX / interrupted publication → run example → RECOVER →
   verify Target and latest SUCCESS/checkpoint 1. Repeat recovery: no duplicates.
3. ETL Replay: clean SANDBOX → RESET/NEXT/REPLAY; compare row counts and events.
4. API contract: wrong JSON type → Send HTTP → inspect a 200 response with an
   invalid customer_id type. Extend required/types checks before submitting.
5. API retry: clean → inspect 429/503/200 attempts per page. Compare exhausted
   retry and timeout scenarios; execution FAILED is observable.
6. API ingestion: clean → enable ingest/reconcile → inspect PostgreSQL Target
   after two replays. Status-only example must not pass the submission grader.
7. My Learning: course-specific progress; History links resume the correct course.
   Reload, switch language and restart app: retain your drafts and evidence.

Instructor reference plans are in `examples/lab_014_*.sql` through
`examples/lab_022_*.json`; use them only after trying the challenge.

## Verification commands

```bash
python -m unittest discover -s tests/unit -v
# Dedicated test PostgreSQL, never the learner database:
DATA_QA_TEST_DATABASE_URL=postgresql://... python -m unittest discover -s tests/integration -v
npm run build --prefix frontend
python -m playwright install --with-deps chromium
DATA_QA_TEST_DATABASE_URL=postgresql://... python -m unittest discover -s tests/e2e -v
# Packaged Compose review database:
python scripts/container_smoke.py
docker compose restart app
python scripts/container_smoke.py resume
```

The integration suite checks independently specified defect counts, read-only
permissions, real HTTP attempts, actual Target writes, replay/recovery, hidden
solutions, two-account access, CSRF, migration retention and course progress.
Browser tests complete all nine new lessons and exercise language, reload,
responsive layout and correct-course history routes. PR evidence records observed
results; these commands alone are not a claim that a check passed.
