# Data QA Lab

Interactive Data Pipeline Testing & Learning Platform. The local V1 runs a real PostgreSQL pipeline and preserves evidence for every run.

**Current branch checkpoint: Task 4 — deterministic fault injection.**

Core principle: **Pipeline SUCCESS ≠ Data Quality PASS.** The quality engine evaluates basic checks plus source-to-target reconciliation independently as `PASS`, `FAIL`, `ERROR` or `NOT_RUN`.

## Pipeline

```text
source.orders (order grain)
        ↓
bronze.orders (run-scoped raw snapshot)
        ↓
silver.orders (clean values + net_amount)
        ↓
gold.daily_sales (UTC-day grain)
        ↓
target.orders_report + target.daily_sales_report
```

The clean seed contains 1,000 customers and 10,000 deterministic orders. Exact expected net revenue is `25,245,493.29`.

## Run on Windows from D:\Data-QA-Lab

Requirements: Python 3.11+ and Docker Desktop with Docker Compose.

```powershell
Set-Location D:\Data-QA-Lab
git switch feature/task-4-fault-injection
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
docker compose up -d postgres
.\.venv\Scripts\python.exe -m backend.app.main db-init
.\.venv\Scripts\python.exe -m backend.app.main seed
.\.venv\Scripts\python.exe -m backend.app.main pipeline-run
.\.venv\Scripts\python.exe -m backend.app.main inspect
.\.venv\Scripts\python.exe -m backend.app.main quality-run
.\.venv\Scripts\python.exe -m backend.app.main quality-inspect
.\.venv\Scripts\python.exe -m backend.app.main fault-list
```

Expected clean-run facts:

- Source, Bronze, Silver and `target.orders_report`: 10,000 order rows.
- Gold `SUM(order_count)`: 10,000. Gold row count is the number of UTC dates.
- Net revenue at Source, Silver, Gold and Target: `25,245,493.29`.
- Pipeline execution: `SUCCESS`.
- Data quality after the built-in clean suite: `PASS` across 26 rules.
- Reconciliation uses immutable run-scoped datasets and reports missing keys, unexpected keys and field mismatches with bounded evidence.

Task 4 faults are applied only to relaxed copies in `fault_workspace`; the original Target remains unchanged. A typical investigation is:

```powershell
$fault = .\.venv\Scripts\python.exe -m backend.app.main fault-apply wrong_net_amount | ConvertFrom-Json
.\.venv\Scripts\python.exe -m backend.app.main fault-quality-run --fault-run-id $fault.fault_run_id
.\.venv\Scripts\python.exe -m backend.app.main fault-inspect --fault-run-id $fault.fault_run_id
.\.venv\Scripts\python.exe -m backend.app.main fault-reset --fault-run-id $fault.fault_run_id
.\.venv\Scripts\python.exe -m backend.app.main quality-run --run-id $fault.pipeline_run_id
```

The fault quality run should report `FAIL` while pipeline execution remains `SUCCESS`; the final clean quality run should report `PASS`.

Stop PostgreSQL without deleting its D-drive data:

```powershell
docker compose down
```

## Verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests/unit -v
$env:DATA_QA_TEST_DATABASE_URL = 'postgresql://data_qa_lab:data_qa_lab@127.0.0.1:5432/data_qa_lab'
.\.venv\Scripts\python.exe -m unittest discover -s tests/integration -v
```

The integration test initializes only Data QA Lab schemas, reseeds its source tables, runs the pipeline twice, and verifies that evidence from the first run remains available.

The Windows connection uses `127.0.0.1` because Compose publishes PostgreSQL on the IPv4 loopback interface. The database adapter also applies a five-second connection timeout so an unreachable host fails promptly instead of leaving a pipeline command waiting indefinitely.

See `docs/TASK_1.md`, `docs/TASK_2.md`, `docs/TASK_3.md`, `docs/TASK_4.md`, `docs/ARCHITECTURE.md`, `docs/DATA_MODEL.md`, `docs/BRANCHING.md` and `docs/WINDOWS_D_DRIVE.md`.
