# Task 19 — operator deployment and rollback (Windows / D drive)

Implementation is not a deployment. Review the PR first. The agent has not
deployed, provisioned live accounts, changed DNS/tunnels or changed live env files.
Use the existing prepared Named Tunnel demo, never demo `Prepare` or `down -v`.

## Architecture and boundaries

`metadata.public_demo_accounts` is an additive table linked to existing accounts.
Only newly created identities enter it through the trusted local `public-demo`
CLI. An ordinary account with a matching username is reported as a conflict;
it is never promoted or overwritten. Ten public identities maximum: `demo_01`
through `demo_10`. Each receives an independent 192-bit random password and an
Argon2 hash in the existing authentication table. Passwords in the public table
are intentionally plaintext for public display, not private secrets. They are
separate from operator/DB/Cloudflare credentials. Never reuse them elsewhere.

`GET /api/auth/config` reports demo mode without credentials.
`GET /api/auth/demo` is bounded to ten active, explicitly designated accounts,
read-only and `Cache-Control: no-store`. Delivery and shared-account login/session
access require BOTH demo mode and `DATA_QA_PUBLIC_DEMO_ENABLED=1`. Compose maps
`DEMO_PUBLIC_ACCOUNTS_ENABLED`, default **0**, to that switch. Other accounts
remain usable. Closing the Login disclosure discards fetched credentials;
reopening fetches current credentials. Nothing is saved in browser storage.
There is no public provisioning, rotation, disable or admin endpoint.

Shared accounts cannot change passwords via the API, even if their password is
known. Local operator rotation/recovery updates hash and displayed credential
atomically and revokes sessions. Disable clears public plaintext, marks the
account inactive and revokes sessions; progress/history stay intact. Provision
never silently rotates or enables an existing disabled account.

Global account cap: `DEMO_MAX_ACCOUNTS` / `DATA_QA_DEMO_MAX_ACCOUNTS`, default 10,
validated range 10–50. Set only the capacity actually needed. The read-only live
inventory on 2026-10-11 found five active ordinary accounts, so ten additional
public accounts require **15**, not 10. Recheck status at deployment; concurrent
changes/conflicts may change the required capacity. Provision locks the accounts
table, checks capacity before creating any missing accounts, and reports missing
names/required cap/conflicts without deleting data. Disabled accounts still count.

The actual existing limit is **5 login sessions/account**, not 12; 12 is the lab
limit. The sixth login evicts the oldest session. Shared users also share progress,
answers, drafts/history for that identity; distinct identities retain ownership
isolation. Existing auth rates (60 global IP / 10 combined demo username attempts
per 15 minutes), 12 labs/account, 500 global writes, 128 MiB DB cap, SQL restrictions,
Docker resource/log limits and security controls remain. Ten identities improve
distribution but do not support unlimited simultaneous visitors. Failed logins
consume auth attempts; never retry a rate-limited login in a loop. No automatic
history reset or budget increase. This is a convenience showcase, not private
multi-user hosting. Do not enter personal data.

## 1. Preflight and backup

After review/approval, check out the reviewed code. Keep the existing hostname,
DB password, connector and other env settings. Commands below do not start a tunnel.
Run in PowerShell with Docker Desktop available:

```powershell
Set-Location D:\Data-QA-Lab
git status --short
# Stop if there are unrelated changes; do not overwrite them.
$demoEnv = 'D:\Data-QA-Lab\data\generated\demo\.env.demo'
$demo = @('compose','-p','data-qa-demo','--env-file',$demoEnv,'-f','docker-compose.demo.yml')
docker @demo ps
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backupDir = "D:\Data-QA-Lab\backups\task19-$stamp"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
& icacls $backupDir /inheritance:r /grant:r "$([Security.Principal.WindowsIdentity]::GetCurrent().Name):(OI)(CI)(F)" | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Backup ACL failed' }
$pgId = docker @demo ps -q postgres
$appId = docker @demo ps -q app
if (!$pgId -or !$appId) { throw 'Existing demo containers not found' }
$oldImage = docker inspect --format '{{.Image}}' $appId
$rollbackImage = "data-qa-lab-demo:before-task19-$stamp"
docker image tag $oldImage $rollbackImage
if ($LASTEXITCODE -ne 0) { throw 'Image backup failed' }
[IO.File]::WriteAllText("$backupDir\rollback-image.txt", $rollbackImage)
docker @demo exec -T postgres pg_dump -U data_qa_demo -d data_qa_demo -Fc -f /tmp/task19-before.dump
if ($LASTEXITCODE -ne 0) { throw 'Database backup failed' }
docker cp "${pgId}:/tmp/task19-before.dump" "$backupDir\demo-before.dump"
if ($LASTEXITCODE -ne 0) { throw 'Backup copy failed' }
docker @demo exec -T postgres pg_restore --list /tmp/task19-before.dump | Out-File "$backupDir\backup-index.txt"
if ($LASTEXITCODE -ne 0) { throw 'Backup verification failed' }
Copy-Item -LiteralPath $demoEnv -Destination "$backupDir\.env.demo.before"
git rev-parse HEAD | Out-File "$backupDir\reviewed-source.txt"
```

Keep backup/env files private and on D. Future DB backups contain deliberately
public passwords as well as private password hashes/history. Never upload dumps,
env files, credential JSON or browser network captures to Git/PR/CI artifacts.
Record the actual pre-deployment running source revision separately if known;
the image tag above is the executable rollback reference. Do not pipe binary dumps
through Windows PowerShell text redirection.

## 2. Configure disabled state, migrate and deploy

Define a narrowly scoped env updater. It edits only the two new settings, does
not print file contents, and preserves hostname/password and existing file ACL:

```powershell
function Set-DemoAccessSetting([string]$Key, [string]$Value) {
    if ($Key -eq 'DEMO_MAX_ACCOUNTS') {
        if ($Value -cnotmatch '\A(?:1[0-9]|[2-4][0-9]|50)\z') { throw 'Cap must be 10–50' }
    } elseif ($Key -eq 'DEMO_PUBLIC_ACCOUNTS_ENABLED') {
        if ($Value -cnotmatch '\A[01]\z') { throw 'Switch must be 0 or 1' }
    } else { throw 'Setting not allowed' }
    $text = [IO.File]::ReadAllText($demoEnv)
    $pattern = '(?m)^' + [regex]::Escape($Key) + '=[^\r\n]*'
    if ([regex]::IsMatch($text, $pattern)) { $text = [regex]::Replace($text, $pattern, "$Key=$Value") }
    else { $text = $text.TrimEnd("`r", "`n") + "`n$Key=$Value`n" }
    [IO.File]::WriteAllText($demoEnv, $text)
}
Set-DemoAccessSetting 'DEMO_PUBLIC_ACCOUNTS_ENABLED' '0'
Set-DemoAccessSetting 'DEMO_MAX_ACCOUNTS' '15'
docker @demo build app
if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
# Additive, idempotent schema/bootstrap; refuses a non-demo database.
docker @demo run --rm --no-deps --entrypoint python app -m backend.app.bootstrap
if ($LASTEXITCODE -ne 0) { throw 'Migration failed; keep access disabled' }
docker @demo up -d --no-deps --force-recreate --wait --wait-timeout 180 app proxy
if ($LASTEXITCODE -ne 0) { throw 'Deployment failed; do not enable public accounts' }
docker @demo exec -T app python -m backend.app.main public-demo status
if ($LASTEXITCODE -ne 0) { throw 'Status failed' }
```

Shared login/listing remain disabled, normal existing accounts remain available,
public registration stays blocked, PostgreSQL is not recreated/published.

## 3. Provision, then enable

```powershell
docker @demo exec -T app python -m backend.app.main public-demo provision --count 10
if ($LASTEXITCODE -ne 0) { throw 'Resolve reported conflicts/cap; do not delete or promote accounts' }
docker @demo exec -T app python -m backend.app.main public-demo status
# Operator checks status: ten public identities; all existing ordinary accounts retained.
Set-DemoAccessSetting 'DEMO_PUBLIC_ACCOUNTS_ENABLED' '1'
docker @demo up -d --no-deps --force-recreate --wait --wait-timeout 180 app proxy
if ($LASTEXITCODE -ne 0) { throw 'Enable failed' }
# Verifies simulated HTTPS origin through local Nginx, not Cloudflare edge TLS.
.\.venv\Scripts\python.exe -m scripts.demo_verify --hostname data-qa-lab.store --public-account demo_01 --restart
if ($LASTEXITCODE -ne 0) { throw 'Proxy verification failed; disable shared access' }
```

Provision output/status never include passwords. With name conflicts, nonconflicting
missing accounts may be created but command exits 1 with the conflict report.
With insufficient total slots, no missing account is created. Retry after an
explicitly justified capacity adjustment; never delete existing identities.
Do not use `--self-test` repeatedly on live demo: it consumes retained account slots.

## 4. Operator maintenance and emergency disable

```powershell
docker @demo exec -T app python -m backend.app.main public-demo status
docker @demo exec -T app python -m backend.app.main public-demo rotate --username demo_03
# Re-enable a previously disabled account ONLY when explicitly intended:
docker @demo exec -T app python -m backend.app.main public-demo rotate --username demo_03 --enable
docker @demo exec -T app python -m backend.app.main public-demo disable --username demo_03
# Emergency: all shared accounts, never ordinary accounts; revokes their sessions.
docker @demo exec -T app python -m backend.app.main public-demo disable --all
if ($LASTEXITCODE -ne 0) { throw 'Disable failed; stop demo app until resolved' }
Set-DemoAccessSetting 'DEMO_PUBLIC_ACCOUNTS_ENABLED' '0'
docker @demo up -d --no-deps --force-recreate --wait --wait-timeout 180 app proxy
```

Check exit status after each selected maintenance command. Existing interactive
`account-reset --username ...` recovery remains available; a public account's
display updates atomically but a disabled account is not silently enabled.
Reopen the disclosure to fetch a rotated password; old copies may remain with
visitors, but cannot authenticate. The env switch alone blocks shared access while
off, but does not revoke stored sessions: use CLI disable for abuse/revocation.

## 5. Manual public-device checklist (pending until operator performs it)

- Visit `https://data-qa-lab.store/login`: disclosure collapsed by default.
- ENG/VIE, 375/390px and desktop: readable controls, keyboard disclosure/reveal/copy.
- Use this account fills username/password, password remains masked, no auto-login.
- Explicit login; cookie Secure/HttpOnly/SameSite=Lax, no HTTP mixed content.
- Create an SQL challenge, query, submit a check and written answer; reload history.
- Another public identity cannot read that attempt. Same identity intentionally shares it.
- Shared account has no password-change form and API returns `PUBLIC_DEMO_PASSWORD_LOCKED`.
- `/signup` and navigation say Coming Soon; backend registration stays denied.
- Logout invalidates session. App restart retains accounts, credentials and history.
- Disable one identity: no listing/login/old-session access; ordinary login still works.
- Record only device/date/check outcomes, never actual credentials or secret responses.

## 6. Rollback without data loss

Do NOT restore the dump automatically: that would lose newer learning history.
Disable all shared accounts using the NEW code first. This is essential because
older code does not enforce the new shared-password restriction. Preserve the
additive table and inactive identities. Only then restore the prior app image:

```powershell
docker @demo exec -T app python -m backend.app.main public-demo disable --all
if ($LASTEXITCODE -ne 0) { throw 'Cannot safely roll back until shared accounts are inactive' }
Set-DemoAccessSetting 'DEMO_PUBLIC_ACCOUNTS_ENABLED' '0'
$rollbackFile = 'D:\Data-QA-Lab\data\generated\demo\task19-rollback.yml'
[IO.File]::WriteAllText($rollbackFile, "services:`n  app:`n    image: $rollbackImage`n    pull_policy: never`n")
docker @demo -f $rollbackFile up -d --no-build --no-deps --force-recreate --wait --wait-timeout 180 app proxy
if ($LASTEXITCODE -ne 0) { throw 'Rollback failed; keep shared access disabled' }
```

If the new app is unavailable, use its built new image in a one-off `run --rm
--no-deps --entrypoint python app -m backend.app.main public-demo disable --all`
before adding the rollback override. Never fall back to an older image with active
shared identities. Test ordinary login/history and host/proxy controls afterward.
Old cap-five code may refuse new accounts while retaining all existing ones;
normal learning continues within its original quotas. Keep the backup for separate,
explicit operator recovery, not routine rollback. No schema down-migration, database
drop, volume deletion, DNS or Cloudflare changes are required.

If resuming in a new PowerShell session, reload `$rollbackImage` from the selected
backup's `rollback-image.txt` and define `$demo`/the updater again. Retain the selected
tag; do not prune rollback images before the deployment is verified.
