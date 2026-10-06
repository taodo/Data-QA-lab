# Task 12 — Databricks, Synapse and Azure foundations

Approved 12.1–12.4. Engineering objective: independently graded, owned, bounded
evidence exercises with retained PostgreSQL/accounts. Learning objective: reason
from explicit grain, keys, exact decimals and observed evidence; a successful
operation is not automatically correct data. No new framework or dependency.

Six runnable ENG/VIE lessons, labs 031–036, bring the catalog to 36 lessons in
nine courses. Each has an introduction/purpose, instructions, guided SELECT,
observable evidence, a defined challenge preceding the answer, submission and
explanation/resume. Written answers are retained only, never semantically graded.

| Lesson | Independent contract and observable evidence | Faults |
|---|---|---|
| 031 Databricks classification | Each record_id has one disposition and exact amount; source and publication visible | lost, wrong classification, duplicate publication |
| 032 Databricks versions | before/incoming/after plus independently authored final order snapshot; strict version increase, no delete policy | stale overwrite, replay duplicate, unintended deletion |
| 033 Synapse publication | expected sale_id/customer_key/amount/date vs staging/dimension/fact | missing/unexpected sale, wrong dimension mapping |
| 034 Synapse reporting | expected daily-region count/total vs actual fact/dimension/report | actual JOIN fanout, wrong total, wrong grain |
| 035 Azure manifest | required file_id/path/route/bytes vs observed listing | missing, unexpected, repeated, wrong-route file |
| 036 Azure access | required observation identity/scope/operation vs reported outcome/capture | denied, unknown identity/scope, missing/future observation |

RUN uses actual local classification, version guards, staging lookup and report
aggregation. REPLAY is available only in lesson 032 and uses explicit versions,
not ADF timestamp watermarks. It cannot restore a lost newer version from an older
incoming event. Azure RUN captures existing observations, never repairs files,
fetches a listing or grants access. Reset reinitializes only the owned sandbox
fixture, preserves imports and advances the local revision. There is no learner
database reset. NUMERIC(14,2), aware UTC boundaries and explicit keys remain.

Graders use independently specified acceptance counts and clean/shifted/zero
fixtures plus alternate faults with changed keys and twice the affected records.
No instructor SQL computes the expected grade. Imported rows never redefine
grading truth: each submission rebuilds private fixtures. Sandbox expected tables
are also built-in contracts, not file-supplied expected rows.

Foundation JSON uses version 1 with kind=foundations, explicit lab_id, built-in
contract_id (standard/shifted/zero), provider, resource_id, selected batch/as_of,
runs, reported steps and typed observed datasets. Contract identity selects a
documented local contract, not arbitrary truth. All required context keys must be
present; nullable batch/as_of stay unknown. The file cannot supply expected tables.
Task 11 JSON/CSV remain compatible and use their existing separate contract.
Foundation CSV is rejected because heterogeneous tables require typed context.
48KiB file, 64KiB escaped request, 101 runs, 100 steps, 100 rows/dataset, 400 rows
total and eight retained imports apply. Export validates the exact downloadable
file with the same parser and request limit; oversized evidence stays stored and
reports an error. No referenced run is silently removed. Unknown/missing run or
capture context cannot establish a QA PASS. Provider clocks never invalidate or
authorize query reuse; all mutations advance a local monotonic revision under
context locks. The shared checkpoint column named watermark records the fixed
UTC boundary here; it is not a version ordering or a provider watermark.

Access status is distinct: DENIED => observed ACCESS_ERROR/FAILED execution;
missing/unknown/future observations => INCOMPLETE/UNKNOWN, not a data defect.
A correct SQL query can run SUCCESS while evidence is NOT_VERIFIED. Clean access
check PASS means this evidence contract matches, not data correctness or future
authorization. SQL errors remain ERROR. The UI labels this metric access evidence.

## Primary references checked 2026-10-06

- [Databricks expectations](https://docs.databricks.com/aws/en/ldp/expectations):
  quality constraints can retain, drop or fail; quarantine is an explicit pattern.
  Our three-way classification is an authored exercise policy, not a default.
- [Databricks Delta MERGE](https://docs.databricks.com/aws/en/delta/merge):
  conditional updates and duplicate-match concerns motivate version/replay checks.
  We do not reproduce Delta transaction logs, time travel or runtime-specific rules.
- [Synapse table design](https://learn.microsoft.com/en-us/azure/synapse-analytics/sql-data-warehouse/sql-data-warehouse-tables-overview):
  fact/dimension design motivates lookup and grain checks. PostgreSQL does not
  reproduce dedicated/serverless engines, distributed storage or performance.
- [T-SQL GROUP BY](https://learn.microsoft.com/en-us/sql/t-sql/queries/select-group-by-transact-sql):
  grouping columns determine aggregate grain. PostgreSQL SQL is used here;
  IS DISTINCT FROM and other syntax need provider-specific translation.
- [ADLS overview](https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-introduction):
  hierarchical paths motivate per-file routing evidence; paths in this app are
  labels, never filesystem/network instructions or a real provider listing.
- [ADLS access model](https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-access-control-model):
  actual access depends on provider identity/authorization mechanisms. We inspect
  reported observations without evaluating RBAC, ABAC, ACL inheritance or masks.

These are local SIMULATED/IMPORTED exercises, not Spark, Delta, Synapse or Azure
emulators. No credentials, adapters, provisioning, paid services or live claims.
All nine course introductions remain distinct ENG/VIE accessible accordions.
See TASK_12_PROGRESS.md for executed commands/results and continuation evidence.

## Local PowerShell verification

Use the declared D-drive virtual environment and a dedicated test database; never
point fixture tests at the learner database. PostgreSQL must already be running.
Create data_qa_task12_verify once with createdb/psql if it does not exist.

```powershell
Set-Location D:\Data-QA-Lab
$env:DATA_QA_TEST_DATABASE_URL = 'postgresql://data_qa_lab:data_qa_lab@127.0.0.1:5432/data_qa_task12_verify'
$env:TEMP = 'D:\Data-QA-Lab\data\generated\task12-verify\tmp'
$env:TMP = $env:TEMP
$env:PLAYWRIGHT_BROWSERS_PATH = 'D:\Data-QA-Lab\data\generated\playwright-browsers'
New-Item -ItemType Directory -Force $env:TEMP | Out-Null
.\.venv\Scripts\python.exe -m unittest tests.unit.test_task12 -v
.\.venv\Scripts\python.exe -m unittest tests.integration.test_task12 -v
npm run build --prefix frontend
.\.venv\Scripts\python.exe -m unittest discover -s tests/e2e -v -k test_task12
```

Required full suites (normally final exact-head CI, not duplicated locally):
`python -m unittest discover -s tests/unit -v`,
`python -m unittest discover -s tests/integration -v`, and
`python -m unittest discover -s tests/e2e -v`; CI also runs packaged Docker
smoke/restart/resume. Docker startup uses `docker compose up -d --build --wait`;
never use down -v or remove the existing PostgreSQL data directory.
