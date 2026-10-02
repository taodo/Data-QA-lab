# Data QA Lab

Interactive Data Pipeline Testing & Learning Platform. The local V1 runs a real PostgreSQL pipeline and preserves evidence for every run.

**Current branch checkpoint: Task 1 — first working pipeline.**

Core principle: **Pipeline SUCCESS ≠ Data Quality PASS.** Task 1 records a successful pipeline with quality `NOT_RUN`; executable data-quality checks start in Task 2.

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
git switch feature/task-1-postgresql-pipeline
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
docker compose up -d postgres
.\.venv\Scripts\python.exe -m backend.app.main db-init
.\.venv\Scripts\python.exe -m backend.app.main seed
.\.venv\Scripts\python.exe -m backend.app.main pipeline-run
.\.venv\Scripts\python.exe -m backend.app.main inspect
```

Expected clean-run facts:

- Source, Bronze, Silver and `target.orders_report`: 10,000 order rows.
- Gold `SUM(order_count)`: 10,000. Gold row count is the number of UTC dates.
- Net revenue at Source, Silver, Gold and Target: `25,245,493.29`.
- Pipeline execution: `SUCCESS`.
- Data quality: `NOT_RUN` until Task 2.

Stop PostgreSQL without deleting its D-drive data:

```powershell
docker compose down
```

## Verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests/unit -v
$env:DATA_QA_TEST_DATABASE_URL = 'postgresql://data_qa_lab:data_qa_lab@localhost:5432/data_qa_lab'
.\.venv\Scripts\python.exe -m unittest discover -s tests/integration -v
```

The integration test initializes only Data QA Lab schemas, reseeds its source tables, runs the pipeline twice, and verifies that evidence from the first run remains available.

See `docs/TASK_1.md`, `docs/ARCHITECTURE.md`, `docs/DATA_MODEL.md`, `docs/BRANCHING.md` and `docs/WINDOWS_D_DRIVE.md`.
