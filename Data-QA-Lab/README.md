# Data QA Lab

Interactive Data Pipeline Testing & Learning Platform. Independent project with its own repository and context.

**Current checkpoint: Task 0 — Foundation.** Domain contracts, lab catalog, CLI and tests work. PostgreSQL pipeline, QA execution, fault injection, API and UI are scheduled next.

Core principle: **Pipeline SUCCESS ≠ Data Quality PASS.**

## Quick start — Windows, on D:

Extract the archive into `D:\Data-QA-Lab`. The project file must be at `D:\Data-QA-Lab\pyproject.toml`. Open PowerShell:

```powershell
Set-Location D:\Data-QA-Lab
py -3 --version  # Python 3.11 or newer
py -3 -m backend.app.main check
py -3 -m backend.app.main labs
py -3 -m unittest discover -s tests/unit -v
```

Task 0 needs no package download, virtual environment or Docker. All commands run from the project root.

## Optional isolated environment for later tasks

```powershell
Set-Location D:\Data-QA-Lab
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m backend.app.main check
```

The virtual environment stays on D. Instructions for caches and Docker data are in `docs/WINDOWS_D_DRIVE.md`.

## Linux/macOS

```bash
python3 -m backend.app.main check
python3 -m unittest discover -s tests/unit -v
```

See `docs/ARCHITECTURE.md`, `docs/DATA_MODEL.md`, `docs/LEARNING_MODEL.md`, `docs/ROADMAP.md` and `docs/TASK_1.md` before implementation.

Gold aggregates daily data; it does not preserve the number of order rows. Target is an order-detail reporting table plus a daily-sales reporting table in Task 1. Bronze/Silver/Gold are PostgreSQL schemas for V1. This models layered processing; it is not a full lakehouse storage implementation.
