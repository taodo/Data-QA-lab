# Issue #49 — Local OFF baseline and Banking integration trial preparation

**Status:** operator runbook, **not** observed local execution. Source: [Issue #49](https://github.com/taodo/Data-QA-lab/issues/49). Banking is **OFF** in U5-F. Follow [production rehearsal](RELEASE49_PRODUCTION_READINESS.md) only after this local baseline. Do not use either repo's real retained learner/domain DB.

## 1. Architecture and ownership

- Data QA Lab `feature/develop` after U5-F merge `372210246a4e1949b9ed0916f5fbb775d72a5807`: inert PostgreSQL registry, persisted ACCEPT/SUBMIT/UNKNOWN, `CAPABILITY="OFF"`; **no live signer, private client, same-origin BFF or Banking simulator**. An independent MiniBanking API at localhost is **not** an integrated Banking track.
- MiniBanking B3 accepted on its `feature/develop` at `d77ce49b6d4ba7303dd796d072f758c9f1086beb`. The live B4 producer financial-oracle PR #25 is still Draft/unmerged as checked 2026-10-16.
- Existing public demo is **not touched**: `data-qa-demo`, `docker-compose.demo.yml`, origin `127.0.0.1:8001`, private PG at `data/generated/demo/postgres`, fixed demo subnet `172.29.246.0/24`. Production tunnel stays attached only to the existing proxy; never invoke `scripts/demo.ps1 -Action Prepare` or `LocalOnly` for release-49 tests.
- Existing learner Compose may already use app port **8000** and PG **5432**. Release-49 uses `dqa-u5-local`, loopback app **18080**, **no published PG port**, a fresh ignored `data/generated/release49/postgres` directory, and default bridge networking without static demo subnet. MiniBanking isolated user-facing mock, when tested separately, uses loopback **18090** and an owned fresh SQLite file. These ports must be verified free first.

## 2. Create isolated worktrees (PowerShell)

Requires Git, Docker Desktop/Linux containers, PowerShell, free disk on D, and Python 3.12 only for the independent MiniBanking HTTP smoke. **Run from existing clean checkouts; do not switch the existing public demo's branch or rebuild it.** Stop if either target worktree directory already exists: inspect, do not overwrite.

```powershell
Set-Location D:\Data-QA-Lab
git status --short
git fetch origin
git worktree add --detach D:\Data-QA-Lab-U5-Local origin/feature/release-u5-local-banking-readiness
if ($LASTEXITCODE -ne 0) { throw 'Data QA Lab worktree failed' }
Set-Location D:\Data-QA-Lab-U5-Local
git rev-parse HEAD
# Ensure 18080 is available. If occupied, STOP; do not kill other processes.
Get-NetTCPConnection -LocalPort 18080 -State Listen -ErrorAction SilentlyContinue
```

Never run integration suites against the preserved learner/demo DB. The special `docker-compose.release49.local.yml` is a **standalone** file; do not combine it with either existing Compose. It has no Cloudflare or producer connectivity.

## 3. Generate secret locally, validate Compose, start Banking OFF

```powershell
Set-Location D:\Data-QA-Lab-U5-Local
$envFile = Join-Path $PWD '.env.release49'
if (!(Test-Path -LiteralPath $envFile)) {
    $bytes = New-Object byte[] 32
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($bytes)
    $rng.Dispose()
    $secret = -join ($bytes | ForEach-Object { $_.ToString('x2') })
    [IO.File]::WriteAllText($envFile, "U5_LOCAL_DB_PASSWORD=$secret`n")
    & icacls $envFile /inheritance:r /grant:r "$([Security.Principal.WindowsIdentity]::GetCurrent().Name):(F)" | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Could not secure local-only env file' }
}
$localCompose = @('compose','-p','dqa-u5-local','--env-file',$envFile,'-f','docker-compose.release49.local.yml')
docker @localCompose config --quiet
if ($LASTEXITCODE -ne 0) { throw 'Compose validation failed' }
docker @localCompose up -d --build --wait --wait-timeout 180
if ($LASTEXITCODE -ne 0) { throw 'Local app failed to start' }
docker @localCompose ps
Invoke-RestMethod 'http://127.0.0.1:18080/api/health'
Start-Process 'http://127.0.0.1:18080'
```

Do not print `docker compose config` (it may expand a password) or copy the env file to Git/chat. Verify frontend is served, and confirm there are **no public banking write routes/capability ON**. No direct Banking token, bank credential, tunnel or mTLS secret is used here. Database bootstrap is performed by the app's existing Dockerfile startup; it creates only the isolated `dqa_u5_local` database state.

## 4. Separate MiniBanking domain smoke — **not** platform Banking ON

Use a **second** detached worktree from accepted MiniBanking `feature/develop`, with new, ignored synthetic SQLite data. Run in a separate PowerShell terminal. Do **not** run B4 draft code as an accepted integration dependency, and do not enable B3's private listener via a fake `CAPABILITY` toggle.

```powershell
Set-Location D:\MiniBanking
git fetch origin
git worktree add --detach D:\MiniBanking-U5-Local origin/feature/develop
if ($LASTEXITCODE -ne 0) { throw 'MiniBanking worktree failed' }
Set-Location D:\MiniBanking-U5-Local
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'MiniBanking requirements failed' }
New-Item -ItemType Directory -Force -Path '.local\release49' | Out-Null
$env:MINIBANKING_DB_PATH = (Join-Path $PWD '.local\release49\minibanking.db')
$env:MINIBANKING_TOKEN_TTL_SECONDS = '1800'
.\.venv\Scripts\python.exe -m scripts.init_db
if ($LASTEXITCODE -ne 0) { throw 'MiniBanking synthetic init failed' }
# Verify port 18090 unused first.
.\.venv\Scripts\python.exe -m uvicorn backend.main:create_app --factory --host 127.0.0.1 --port 18090
```

In another terminal, `Invoke-RestMethod 'http://127.0.0.1:18090/health'` verifies only the **legacy synthetic domain API**. It does **not** prove mTLS/ES256 Q-route access, ledger oracle B4, or integrated platform Banking. Keep this service on localhost; do not add it to nginx/Cloudflare.

## 5. Local manual QA checklist — record PASS/FAIL/NOT RUN

- Data app at `http://127.0.0.1:18080`: landing, navigation, all 9 courses / 36 lessons, ENG/VIE switching, intro/subject expansion, mobile 375/390px overlay and keyboard usability.
- Local normal signup/login/logout; invalid credentials and validation; reload/resume My Learning; CSRF/origin protections and session expiry. Password-change/reset if available through actual backend UI/operator workflow; distinguish UI NOT APPLICABLE from NOT RUN.
- SQL lesson: sandbox read-only query, Challenge, submit, stored evidence/progress after browser refresh and app restart; pipeline and QA suite distinguish execution from data quality.
- Two distinct users: no access to the other user's lab/progress. Verify no public demo account/state from `data-qa-demo` appears in local database.
- Banking track remains planned/informational/OFF, no Banking write route and no attempt to call MiniBanking. A domain `/health` PASS cannot be reported as platform Banking E2E PASS.
- Record date, source HEAD, browser/device, anonymized outcomes; no cookies/passwords/DB dumps.

## 6. Status, logs, stop — preserve every volume

```powershell
Set-Location D:\Data-QA-Lab-U5-Local
$envFile = Join-Path $PWD '.env.release49'
$localCompose = @('compose','-p','dqa-u5-local','--env-file',$envFile,'-f','docker-compose.release49.local.yml')
docker @localCompose ps
# Inspect in the terminal. Logs may contain user-supplied test data: sanitize before sharing.
docker @localCompose logs --no-color --tail 100 app postgres
docker @localCompose stop
if ($LASTEXITCODE -ne 0) { throw 'Local stop failed' }
```

Stop the MiniBanking terminal with Ctrl+C. **Never** use `down -v`, `docker volume prune`, reset scripts, or delete a retained data directory. Do not change production demo Compose/env, restart its app or alter its tunnel. If cleanup is eventually needed, obtain separate explicit authorization for *only* the release49-owned resources.

## Local evidence (not executed by author)

As of this document, **worktree checkout, Compose config validation, Docker boot, database bootstrap, API health, manual browser tests, MiniBanking process and local E2E = NOT RUN**. This is a reproducible operator recipe, not a test log. U5-F previous CI success is historical evidence at its own exact HEAD, not live local Banking ON acceptance.
