# Task 9 — Learning platform and local accounts

Branch: `feature/task-9-learning-platform`; base: approved Task 8 merge on
`feature/develop`. Task 9 implementation was approved on 2026-10-04; finished-task
review is required before merge. Product version: 1.2.0.

## Result and learning flow

Browse the public course library, search or select a subject, open the course
syllabus, register locally, then start a guided SQL lesson. The player keeps
chapter navigation beside instructions, SQL execution and challenge submission.
My Learning groups enrolled courses and recent attempts. ENG/VIE works throughout.

SQL has the existing 13 executable lessons in five chapters. ETL, API, Fabric,
ADF, OneLake, Azure, Databricks and Synapse each have subject/course pages with
explicit planned availability; they do not claim executable cloud labs. Original
course covers and layout use familiar course-platform conventions without fake
ratings, learner counts, video, teachers or certificates. Browser routes support
reload, Back/Forward and clickable breadcrumbs; old `/learn/lab_<id>` links redirect.

## Account and evidence boundaries

Signup/login/logout, current user, password change and operator recovery are real
PostgreSQL operations. Passwords use Argon2id through argon2-cffi, the one new runtime
dependency. No auth token or password is stored in localStorage. Random opaque
seven-day session cookies are HttpOnly, SameSite=Lax and Secure on HTTPS; local HTTP
on 127.0.0.1 remains supported. The DB stores a digest of the cookie token. CSRF
headers, same-origin checks and durable 15-minute login budgets protect writes.
Password changes rotate the current cookie and revoke other login sessions.

Every session/history/query/grade/hint/reveal/simulation and pipeline/fault API
checks the authenticated owner. Lists and progress are owner scoped. The shared
teaching baseline can be read and copied into personal lesson snapshots; learners
cannot run QA or faults against it. Run pipeline creates a private run for those
operations. Browser drafts use account + session keys; logout/account changes
remove visible private state and reject stale responses. Drafts remain on that
browser for the same learner to resume, unlike PostgreSQL history.

The local CLI and DB administrator are trusted operators; OS access and direct DB
credentials are outside the learner HTTP boundary. This release remains a local
installation, not an internet deployment. No email reset, OAuth or admin dashboard
is included. Registration never silently adopts previous single-user history.

## Update on Windows D drive

Docker Desktop must be running. Back up existing PostgreSQL first, then update
code on the review branch without replacing `data/postgres` or `.env`:

```powershell
Set-Location D:\Data-QA-Lab
powershell -ExecutionPolicy Bypass -File .\scripts\backup-v1.ps1
git fetch origin
git switch feature/task-9-learning-platform
git pull --ff-only origin feature/task-9-learning-platform
docker compose up -d --build --wait --wait-timeout 180
Start-Process 'http://127.0.0.1:8000'
```

The startup schema upgrade preserves runs, sessions, SQL, submissions and snapshots.
Create your account in the web app. To associate earlier unassigned history, stop
the app, preview the operation, then explicitly confirm the intended account:

```powershell
docker compose stop app
docker compose run --rm --no-deps app python -m backend.app.main account-import --username YOUR_USERNAME
# Review counts and target username before running the confirmation command.
docker compose run --rm --no-deps app python -m backend.app.main account-import --username YOUR_USERNAME --confirm
docker compose up -d --wait --wait-timeout 180
```

Import is transactional and audited; repeat imports move zero already-owned rows.
It imports all unassigned legacy private runs/sessions/faults into that chosen
account. The shared baseline stays read-only. It never moves another account's work.
Import requires the existing backup and deliberate operator choice.

Recovery uses a masked interactive prompt; passwords are not command arguments:

```powershell
docker compose exec app python -m backend.app.main account-reset --username YOUR_USERNAME
```

All account login sessions are revoked after operator recovery. Sign in again.
For ZIP delivery, extract to a separate D-drive folder for review. To update an
existing checkout, copy source only; preserve `.env`, `data/postgres`, backups and
`.venv`. A different Compose directory creates a different project and default DB
path, so an empty My Learning there is expected until deliberately migrating data.

## Verification

Local: `npm run build --prefix frontend`,
`python -m unittest discover -s tests/unit -v`.
Real PostgreSQL: set `DATA_QA_TEST_DATABASE_URL` to a dedicated operator-owned test
DB, then `python -m unittest discover -s tests/integration -v`.
Real Chromium: `python -m playwright install --with-deps chromium`,
`python -m unittest discover -s tests/e2e -v`.
Package: Compose build/start, `python scripts/container_smoke.py`, app restart,
`python scripts/container_smoke.py resume`.

The suite tests two-account authorization, password/cookie/CSRF/rate/expiry behavior,
explicit legacy import with retained SQL, all 13 lesson graders, simulation and
packaged restart retention. Browser evidence includes course pages, real auth,
My Learning, account-separated drafts, bilingual routes and mobile layout.
Final observed counts and CI URLs are recorded in the PR after all checks finish.
