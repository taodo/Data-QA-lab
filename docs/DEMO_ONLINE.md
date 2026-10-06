# Temporary online showcase (Windows / D drive)

Engineering objective: serve the existing learning app through an exact temporary
HTTPS hostname, with a private demo database, trusted proxy and durable quotas.
Learning objective: distinguish edge HTTPS from the local HTTP origin leg, and
verify authenticated learning evidence without exposing learner data.

Approved demo preparation only. Task 12 merged as PR #14 at
`b0863f8798c8bba2c0ed0f8fc5d37c5e1e158fab`. No curriculum changes or merges.

## Isolation and security

`docker-compose.demo.yml` is a **standalone** Compose project `data-qa-demo`.
Do not combine it with `docker-compose.yml`. Original learner app/DB can continue
on ports 8000/5432. Demo proxy is bound only to `127.0.0.1:8001`; demo app and
PostgreSQL have no published ports. The separate PostgreSQL cluster uses
`data_qa_demo` credentials and `data/generated/demo/postgres`, never `data/postgres`.
Bootstrap is additive, never a reset. Docker Desktop's existing engine disk/image
cache location is unchanged; configure its disk image on D in Docker Desktop
settings if it is not already there before building. This runbook does not move it.

App defaults allow `localhost`, `127.0.0.1`, `testserver`; public hosts require
`DATA_QA_PUBLIC_HOSTS` as exact comma-separated hostnames (no URL/port/wildcard).
Public hosts require HTTPS. `DATA_QA_TRUSTED_PROXIES` accepts exact IP literals,
defaults empty, and trusts only the demo proxy `172.29.246.2` in demo Compose.
Network `172.29.246.0/24` must be free; if Docker reports an overlap, stop and choose
a free subnet, updating Compose, nginx upstream and trusted peer together.

Uvicorn's automatic forwarded-header trust is disabled in demo Compose. The
proxy overwrites protocol, clears forwarded host/IP headers, preserves actual
Host, limits body/rate/time, and exposes only a loopback listener. The app trusts
protocol only from that peer; client IP headers never alter rate-limit identity.
Host validation runs before same-origin checks. Existing CSRF tokens, auth intent,
ownership, restricted SQL roles and execution bounds remain active. HTTPS login
produces Secure/HttpOnly/SameSite=Lax cookies. Local processes with access to the
loopback listener remain inside the trusted operator boundary.

Public signup is disabled in demo mode. Hidden-prompt `demo-account` reuses
Argon2 signup and removes its unused login token. Limits: 5 accounts, 5 live auth
tokens per account (oldest tokens revoked), 12 retained labs per account, 500
mutation attempts globally, 128 MiB database pre-write threshold. Failed operations,
resets and replays consume the budget; all write endpoints share it. Budgets survive
restart. Auth budgets have fixed key cardinality and normal 15-minute throttling;
visitors share proxy/auth rate limits. History stays readable when writes stop.
No automatic evidence deletion or quota reset. Expired/replaced auth tokens alone
are pruned. Database size is a preflight threshold, **not a hard disk quota**: one
bounded operation can exceed it; PostgreSQL WAL/temporary space and cloudflared
logs need disk headroom. Compose rotates container logs (2 × 5 MiB/service), bounds
memory/CPU/connections and sets a 256 MiB WAL target (also not a hard disk quota).
Keep the showcase short, monitor D free space and stop if storage pressure rises.

## Prepare and start only the local demo

Docker Desktop (Linux containers), Windows PowerShell and network access to
official release/container registries are needed. Python in the repo `.venv` is
needed only for the optional verification script. All generated files below are
ignored by Git, including the random DB password. Never print/commit `.env.demo`.

```powershell
Set-Location D:\Data-QA-Lab
.\scripts\demo.ps1 -Action Prepare
.\scripts\demo.ps1 -Action Start
.\scripts\demo.ps1 -Action Account -Username demo_learner
.\scripts\demo.ps1 -Action Status
Invoke-RestMethod http://127.0.0.1:8001/api/health
```

Account prompts hide the password; use a unique demo-only password, 12–128
characters. Up to five separate visitor accounts can be created. Do not reuse a
learner password or share one account when demonstrating personal ownership.
`Prepare` never overwrites existing credentials. To recover a demo password:

```powershell
docker compose -p data-qa-demo --env-file D:\Data-QA-Lab\data\generated\demo\.env.demo -f docker-compose.demo.yml exec app python -m backend.app.main account-reset --username demo_learner
```

## Official cloudflared download and user-started tunnel

Verified 2026-10-06: [Cloudflare downloads](https://developers.cloudflare.com/tunnel/downloads/)
links the maintained official GitHub Windows x64 executable. Windows updates are
manual. [Quick Tunnel documentation](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/)
provides an account-free temporary URL and the `tunnel --url` command. It documents
200 in-flight requests, no SSE or uptime guarantee, and a changed hostname on each
start. Optional `--allowed-mail` requires browser email/PIN access; check installed
version support first. Anyone with an unprotected URL can visit.

Download only (does not start a tunnel):

```powershell
Set-Location D:\Data-QA-Lab
$demoDir = 'D:\Data-QA-Lab\data\generated\demo'
$env:TEMP = "$demoDir\tmp"
$env:TMP = $env:TEMP
Invoke-WebRequest 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile "$demoDir\tools\cloudflared.exe"
& "$demoDir\tools\cloudflared.exe" --version
Get-FileHash "$demoDir\tools\cloudflared.exe" -Algorithm SHA256
```

Record version/hash in your private demo log. `Prepare` writes an explicit empty
config on D, so existing profile cloudflared configuration is not changed/read as
the active config. The CLI `--config` behavior is also checked against
[Cloudflare's source](https://github.com/cloudflare/cloudflared/blob/master/cmd/cloudflared/tunnel/cmd.go).
Keep your normal learner service out of the tunnel origin URL.

**Only the user runs the following command.** In terminal A, after local startup:

```powershell
Set-Location D:\Data-QA-Lab
$demoDir = 'D:\Data-QA-Lab\data\generated\demo'
$env:TEMP = "$demoDir\tmp"
$env:TMP = $env:TEMP
& "$demoDir\tools\cloudflared.exe" tunnel --config "$demoDir\cloudflared.yml" --no-autoupdate --url http://127.0.0.1:8001 --metrics 127.0.0.1:20241 --logfile "$demoDir\logs\cloudflared.log"
```

Optional email restriction: append `--allowed-mail 'your-visitor@example.com'`
with a real chosen visitor address, using a version whose help lists this flag.
Do not run both variants simultaneously. Leave terminal A running. Until the
hostname is allowed, the app rejects public requests.

In terminal B, paste **only** the exact generated hostname (strip `https://`):

```powershell
Set-Location D:\Data-QA-Lab
$demoHostname = Read-Host 'Exact generated hostname (example: words.trycloudflare.com)'
.\scripts\demo.ps1 -Action SetHostname -Hostname $demoHostname
```

This recreates only demo app/proxy with the hostname allowlist; no wildcard,
forwarded-host override or CSRF bypass. Share `https://<exact-hostname>` only
after verification. Repeat SetHostname for each new tunnel hostname.

## Local proxy verification and external checklist

This command simulates HTTPS-origin requests across the actual local nginx/app
boundary. It does not contact Cloudflare or establish browser/edge TLS:

```powershell
Set-Location D:\Data-QA-Lab
.\.venv\Scripts\python.exe -m scripts.demo_verify --hostname $demoHostname --username demo_learner --restart
```

It prompts for the demo password, verifies Secure cookies, login/logout, ENG/VIE
courses, real read-only SQL, PASS submission, retained history after demo app
restart, hostile host/origin/CSRF rejection. It creates one retained lab and consumes
write budget. `--self-test` provisions a random test account instead of prompting;
use only for engineering verification because it consumes an account slot.

**External-device verification: PENDING until the user performs it.** From a phone
on mobile data or another computer outside this machine:

- Open exact HTTPS URL; complete email PIN if enabled; verify HTTPS and login.
- Confirm signup is rejected with the demo explanation; login to supplied account.
- Navigate all nine courses, switch ENG/VIE, expand introductions at mobile width.
- Start a SQL lesson, run SQL, submit the challenge and see the recorded result.
- Reload/relogin; confirm the SQL, written answer, submission and history remain.
- Verify another demo account cannot see the first account's attempts.
- In browser developer tools verify cookie Secure/HttpOnly/SameSite=Lax and no
  insecure mixed-content/API calls. Record device/browser/date and observed result
  in `data/generated/demo/logs/external-verification.md`; don't record passwords.

## Stop access and resume local use

Press **Ctrl+C in terminal A** first; stopping cloudflared ends public access.
Then clear the public host (defense if a tunnel was accidentally left running):

```powershell
Set-Location D:\Data-QA-Lab
.\scripts\demo.ps1 -Action LocalOnly
.\scripts\demo.ps1 -Action Stop
# Existing learner service, original data and accounts:
docker compose up -d --wait --wait-timeout 180
Start-Process 'http://127.0.0.1:8000'
```

No `down -v`, prune, delete, reset, automatic tunnel startup or Windows service
installation is used. Demo data stays on D for resume. Use `Start` again to resume
demo locally. When local-only, use a fresh localhost login; Secure public-host
cookies do not carry over to local HTTP. Storage budgets are deliberately retained.
Docker logs can be saved without exposing the DB env file:

```powershell
docker compose -p data-qa-demo --env-file D:\Data-QA-Lab\data\generated\demo\.env.demo -f docker-compose.demo.yml logs --no-color --tail 200 app proxy postgres | Out-File D:\Data-QA-Lab\data\generated\demo\logs\containers.log
```

## Verification checkpoint

Targeted security/API and disposable PostgreSQL demo/account tests are recorded
in DEMO_PROGRESS.md. Final-head CI covers required full suites and packaged proxy
verification. External-device/real-edge checks remain pending; no public tunnel is
opened during preparation or CI.
