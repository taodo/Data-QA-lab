# Release #49 — Production readiness and preservation runbook

STATUS: DOCUMENTATION ONLY / NO PRODUCTION AUTHORIZATION. Read [Issue #49](https://github.com/taodo/Data-QA-lab/issues/49), [Task 19 deployment](TASK_19_DEPLOYMENT.md), [existing demo](DEMO_ONLINE.md), and [isolated local baseline](RELEASE49_LOCAL_TRIAL.md).

## Release gates

1. Latest reviewed, merged and pinned release revision, Banking OFF. Confirm tests (Data, account/session, demo, SQL/ETL, browser mobile ENG/VIE), no regression and no unexpectedly exposed Banking routes. The U5-F CI is evidence for its old exact HEAD only.
2. Independent security/schema review, production backup and successful restore rehearsal into a separate PostgreSQL instance; accepted rollback. An Issue #49 report by itself is not deploy authorization.
3. Explicit human approval for production deployment on data-qa-lab.store. Banking ON public requires an additional independent approval and real accepted B4/U5/U6 integration evidence.
4. Confirm real Cloudflare Named Tunnel remains aimed at loopback proxy 127.0.0.1:8001 and existing data-qa-demo Compose project. Never replace this with the release49 local Compose.

## Operator preflight (run only after separate release authorization)

~~~powershell
Set-Location D:\Data-QA-Lab
git status --short
git rev-parse HEAD
$demoEnv = 'D:\Data-QA-Lab\data\generated\demo\.env.demo'
if (!(Test-Path -LiteralPath $demoEnv)) { throw 'Missing original demo env file' }
$demo = @('compose','-p','data-qa-demo','--env-file',$demoEnv,'-f','docker-compose.demo.yml')
docker @demo ps
Invoke-RestMethod 'http://127.0.0.1:8001/api/health'
~~~

Check actual public demo current image, release SHA, sufficient D drive space, approved maintenance window, no uncommitted checkout changes, current demo user/account cap, tunnel/proxy/host/cookie/origin security and an available rollback operator. STOP on differences.

## Create protected PostgreSQL and executable image recovery points

Before stopping any app, capture the exact running image ID, tag it for rollback, and back up the entire *existing* demo DB in custom binary format. Password/credential material and learner records must never enter Git, chat, logs or artifacts. Use the original PG credentials only inside its container.

~~~powershell
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backupDir = "D:\Data-QA-Lab\backups\release49-$stamp"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
& icacls $backupDir /inheritance:r /grant:r "$([Security.Principal.WindowsIdentity]::GetCurrent().Name):(OI)(CI)(F)" | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Backup ACL failure' }
$pgId = docker @demo ps -q postgres
$appId = docker @demo ps -q app
if (!$pgId -or !$appId) { throw 'Existing containers missing' }
$oldImage = docker inspect --format '{{.Image}}' $appId
$rollbackImage = "data-qa-lab-demo:before-release49-$stamp"
docker image tag $oldImage $rollbackImage
if ($LASTEXITCODE -ne 0) { throw 'Image tag failure' }
[IO.File]::WriteAllText("$backupDir\rollback-image.txt", $rollbackImage)
docker @demo exec -T postgres pg_dump -U data_qa_demo -d data_qa_demo -Fc -f /tmp/release49-before.dump
if ($LASTEXITCODE -ne 0) { throw 'pg_dump failure' }
docker cp "${pgId}:/tmp/release49-before.dump" "$backupDir\before.dump"
if ($LASTEXITCODE -ne 0) { throw 'Binary copy failure' }
docker @demo exec -T postgres pg_restore --list /tmp/release49-before.dump | Out-File "$backupDir\backup-index.txt"
if ($LASTEXITCODE -ne 0) { throw 'Backup index failure' }
Get-FileHash -LiteralPath "$backupDir\before.dump" -Algorithm SHA256 | Select-Object Hash
Copy-Item -LiteralPath $demoEnv -Destination "$backupDir\.env.demo.before"
~~~

A successful dump/list is NOT verified recovery. Retain the image and DB backup independently; never pipe a binary dump through PowerShell text redirection.

## Restore rehearsal: entirely separate PostgreSQL

Start the release49 isolated local trial (distinct project and data volume) first. Restoration copies sensitive production demo data to the operator's locally isolated, non-published PostgreSQL; secure its files and delete only after separately authorized retention decisions. DO NOT restore into either active demo DB or regular learner DB.

~~~powershell
Set-Location D:\Data-QA-Lab-U5-Local
$envFile = Join-Path $PWD '.env.release49'
$trial = @('compose','-p','dqa-u5-local','--env-file',$envFile,'-f','docker-compose.release49.local.yml')
$trialPg = docker @trial ps -q postgres
if (!$trialPg) { throw 'Local trial DB missing' }
docker cp "$backupDir\before.dump" "${trialPg}:/tmp/release49-before.dump"
if ($LASTEXITCODE -ne 0) { throw 'Fixture copy failed' }
docker @trial exec -T postgres createdb -U dqa_u5_local dqa_u5_rehearsal
if ($LASTEXITCODE -ne 0) { throw 'Already exists / could not create: inspect and STOP' }
docker @trial exec -T postgres pg_restore --exit-on-error --no-owner --no-privileges -U dqa_u5_local -d dqa_u5_rehearsal /tmp/release49-before.dump
if ($LASTEXITCODE -ne 0) { throw 'Actual restored DB failure' }
docker @trial exec -T -e POSTGRES_DB=dqa_u5_rehearsal app python -m backend.app.bootstrap
if ($LASTEXITCODE -ne 0) { throw 'Migration rehearsal failed' }
docker @trial exec -T -e POSTGRES_DB=dqa_u5_rehearsal app python -m backend.app.bootstrap
if ($LASTEXITCODE -ne 0) { throw 'Idempotent migration rehearsal failed' }
docker @trial exec -T postgres psql -U dqa_u5_local -d dqa_u5_rehearsal -Atc "SELECT 'accounts',count(*) FROM metadata.accounts UNION ALL SELECT 'pipeline_runs',count(*) FROM metadata.pipeline_runs UNION ALL SELECT 'course_enrollments',count(*) FROM metadata.course_enrollments UNION ALL SELECT 'banking_bindings',count(*) FROM metadata.banking_bindings;"
if ($LASTEXITCODE -ne 0) { throw 'Data preservation verification failed' }
~~~

Reconcile before/after account IDs, courses, completed lessons/progress, lab/run ownership and Banking ACCEPT/UNKNOWN/HELD/revocation rows if any. Counts alone are insufficient for ownership integrity. Do not assert staging PASS until actual restore/compare evidence is captured. This rehearsal is on a replica; it does not change production.

## Conditional production rollout (separate release execution issue)

Freeze public writes for an approved maintenance window. Build only the reviewed release commit; keep the original demo DB bind mount, env, account restrictions, hostname and Cloudflare tunnel. Follow the *existing* [Task 19](TASK_19_DEPLOYMENT.md) operator procedure to stop only demo app, run existing additive bootstrap against the preserved demo database, then recreate app/proxy. PostgreSQL and Cloudflare connector must NOT be rebuilt/reset. Initial release keeps Banking OFF with zero private producer traffic.

Require external-device HTTPS smoke at https://data-qa-lab.store: login/logout and invalid credentials, shared demo account disclosure/explicit use, signup Coming Soon, secure cookies/origin/CSRF, nine Data courses/36 lessons, ENG/VIE and 375/390px, one SQL challenge/submission/history retention, pipeline vs QA result, cross-identity isolation, health, restart and PostgreSQL durability. Do not rate-limit the shared demo by repeated tests.

## Backout: app image first, never destructive DB restore

If migration fails, stop deployment and leave public app down or use verified original image. If runtime regressions appear, freeze writes, preserve PostgreSQL exactly as-is, retain and inspect UNKNOWN/RECOVERY_HOLD/revocation outbox, and roll back **app image only** using the original pinned image and the Task 19 service-only override (`--no-build --no-deps`), then recheck login/Data/history/Cloudflare. Never use down -v, delete Banking metadata, overwrite modern DB with old dump, reset demo public identities, or change DNS/tunnel while debugging. If the old binary is incompatible with the additive schema, escalate rather than asserting rollback success.

NO-GO triggers: failed restore/migration/idempotency; lost or cross-user learning data; altered auth security; unreviewed Banking ON/private endpoint; unexpected Cloudflare route; missing image pin/backup; unaudited UNKNOWN; failing focused or browser regression.

**Observed verification: NOT RUN.** This is a future release operator checklist, not a completed deployment.
