# Data QA Lab V1 — Windows / D drive

## Start the app

Prerequisite: Docker Desktop Engine running, Linux containers and Docker storage located on D. Checkout remains D:\Data-QA-Lab. The first image build needs internet for dependencies; the built application and lesson content then run locally without GitHub or an AI service.

```powershell
Set-Location D:\Data-QA-Lab
git fetch origin
git switch feature/develop
git pull --ff-only origin feature/develop
docker compose up -d --build --wait --wait-timeout 180
docker compose ps
Start-Process 'http://127.0.0.1:8000'
```

Alternatively run `powershell -ExecutionPolicy Bypass -File .\scripts\start-v1.ps1` for this process only. No global policy change. Python and Node installations on Windows are unnecessary for the packaged app.

Compose starts PostgreSQL and the app. The dedicated database schemas/learner privileges are initialized. If there is no usable successful pipeline, a deterministic 1,000-order baseline is created. Existing successful runs and learning history are preserved. The CLI's default explicit seed remains 10,000 orders. SQL is read-only through the restricted runtime; setup must target the dedicated lab database only.

## Learn

Select ENG or VIE. Open a lesson, read the concept/schema and guided steps. Challenge selects a hidden defect; Sandbox allows clean data or a named defect. Load practice SQL, Run SQL, inspect evidence, write a check returning the documented violation_count, enter a conclusion and Submit. Query SUCCESS is not grading PASS. Use progressive hints; reveal closes the attempt without credit. New attempt preserves earlier history.

Six lessons: SELECT/WHERE business rules, required-field NULLs, duplicate business keys, equal-count completeness, exact money calculations, composite order/day investigation. Every lesson has both language versions. Progress/session/queries/submissions live in PostgreSQL; language and unsent drafts are browser-local. Use the same address/browser for drafts. Do not clear browser storage if you need unsent drafts.

## D-drive storage

The default bind mount is `./data/postgres`, therefore D:\Data-QA-Lab\data\postgres. For a fresh database location, set `DATA_QA_POSTGRES_DATA=D:/DockerData/data-qa-lab-postgres` in `.env` before starting. Changing this path does not migrate an existing database: back up first and keep the current path until a planned restore. The installation directory D:\Apps\Docker is separate from Docker's image/disk storage; verify Docker Desktop's Disk image location setting points to D.

```powershell
$container = docker compose ps -q postgres
$inspection = docker inspect $container | ConvertFrom-Json
$inspection[0].Mounts | Select-Object Type, Source, Destination
```

The Source for the bind mount should point to the chosen D directory. Docker images/build cache follow Docker Desktop's disk location, not the repository path. Temporary Windows/system files may still use C.

## Stop, restart and inspect

```powershell
docker compose stop
docker compose up -d --wait
docker compose logs --tail 100 app postgres
```

Stopping retains database/history. Rebuild after updating code. App health failure: inspect logs; SQL_SECURITY_SETUP means permissions need initialization on the dedicated database. Docker pipe missing: start Docker Desktop. Port 8000 occupied: stop the conflicting app before starting. Keep one app process/worker for this single-user V1.

## Backup and deliberate reset

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\backup-v1.ps1
```

Backup uses pg_dump custom format inside the container, then copies the binary file to D:\Data-QA-Lab\backups. It avoids PowerShell binary redirection. Default credentials are for the local dedicated database.

To restore, stop app, copy the backup into postgres and run pg_restore into a **new empty dedicated database**, then configure the app to use it. Restoring into an existing lab requires an explicit migration/reset decision; no automatic overwrite is provided.

To start learning from scratch, back up, `docker compose down`, then rename the existing data/postgres directory to a dated archive on D and start Compose again. This intentionally creates a new database; do not delete the archive until the new app is verified. There is no automatic deletion of session snapshots.

## Limits

Local single-user V1; six focused lessons, not a full SQL certification course. Conclusions are retained, not AI-scored. No cloud/account integration. Trusted operators can inspect repo/DB solutions. The restricted SQL boundary is not OS isolation for hostile users. Query roles normally clean up and credentials expire after five minutes; an abrupt process crash may leave temporary query artifacts for operator cleanup. Failed API/SQL operations do not mean data quality FAIL unless a check produced that verdict.
