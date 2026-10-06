# Demo preparation progress

2026-10-06. Engineering objective: exact-host HTTPS showcase, bounded ownership
and private demo storage. Learning objective: prove the authenticated learning
flow across the proxy boundary and distinguish local simulation from edge proof.

Read AGENTS, branching/roadmap/current progress; fetched origin. Working tree was
clean. Task 12 merge confirmed at b0863f8798c8bba2c0ed0f8fc5d37c5e1e158fab.
Created requested `feature/demo-online` from current `origin/feature/develop`.
No merge, curriculum task, automatic tunnel startup or learner DB reset.

## Implemented checkpoint

- Exact configurable public hosts; empty/default retains strict local hosts.
- Explicit IP-only trusted proxy protocol, public HTTPS requirement; automatic
  Uvicorn proxy trust disabled; existing CSRF, origin, auth intent and ownership.
- Independent Compose app/proxy/PostgreSQL project, demo-only random credentials
  and D bind mount. No PostgreSQL or app published port; nginx only 127.0.0.1:8001.
- Demo public signup disabled, hidden-password account CLI reuses existing signup;
  5 accounts, 5 tokens/account, 12 labs/account, 500 durable mutation attempts,
  128 MiB pre-write guard, fixed-cardinality auth budgets and resource/log limits.
- ENG/VIE quota messages; D-drive PowerShell runbook and physical proxy verifier.
- Official Cloudflare Quick Tunnel/download/CLI config references verified.
- Unit, PostgreSQL and mobile HTTPS-origin browser regressions; packaged CI now
  also verifies the real nginx proxy and demo app restart (never cloudflared).

## Observed targeted verification

```powershell
.\.venv\Scripts\python.exe -m unittest tests.unit.test_api tests.unit.test_database_config -v
.\.venv\Scripts\python.exe -m unittest tests.unit.test_demo_security tests.unit.test_api -v
$env:DATA_QA_TEST_DATABASE_URL='postgresql://data_qa_lab:data_qa_lab@127.0.0.1:5432/data_qa_task12_test'
.\.venv\Scripts\python.exe -m unittest tests.integration.test_demo tests.integration.test_accounts -v
$env:PLAYWRIGHT_BROWSERS_PATH='D:\Data-QA-Lab\data\generated\playwright-browsers'
.\.venv\Scripts\python.exe -m unittest tests.e2e.test_demo_browser -v
npm --prefix frontend run build
.\scripts\demo.ps1 -Action Prepare
.\scripts\demo.ps1 -Action Start
.\scripts\demo.ps1 -Action SetHostname -Hostname local-demo.trycloudflare.com
.\.venv\Scripts\python.exe -m scripts.demo_verify --hostname local-demo.trycloudflare.com --self-test --restart
```

Observed PASS: 8 existing API/config tests; 7 new host/proxy + API tests;
11 demo/account PostgreSQL integration tests; 1 mobile browser test; TypeScript
and Vite build; real nginx HTTPS-origin login/course/SQL/submission/history,
host/origin/CSRF rejection, logout and app restart retention. Test databases are
disposable and separately named. The browser screenshot is
`e2e-artifacts/demo-https-origin-mobile.png` (inspected, no horizontal overflow).

Verification caught and fixed: auto-assigned PostgreSQL IP collided with proxy
IP; all internal service IPs are now explicit. Docker Desktop did not publish a
port on an internal-only network; nginx alone now also has an edge network.
The verifier now accepts TrustedHostMiddleware's expected plain-text 400 response.

Original learner app still bound 127.0.0.1:8000; original PostgreSQL still bound
127.0.0.1:5432 with D:\Data-QA-Lab\data\postgres mount. No commands write/delete
learner data. Demo uses D:\Data-QA-Lab\data\generated\demo\postgres.

## Handoff gate and limitations

Final exact-head CI is pending at this checkpoint. Do not duplicate full suites
locally; record final commit, CI run and results in the PR and ignored
`data/generated/demo/logs/HANDOFF.md` when green. Rerun affected tests after fixes.
Final inspection strengthened fail-closed startup: demo mode now refuses a
learner database before schema/bootstrap writes and before creating the API.
Regression checks assert bootstrap initialization is not called on refusal.
Affected tests rerun: `python -m unittest tests.integration.test_demo
tests.integration.test_bootstrap -v` — 4 tests PASS (36.046s).
Docker backing VHD files observed under D:\DockerData\wsl\disk and
D:\DockerData\wsl\main; the engine location was not moved. Local demo was
returned to an empty public-host allowlist and stopped; its data is retained.
No external-device or Cloudflare edge checks were executed; explicitly PENDING
until user runs the public tunnel/checklist in DEMO_ONLINE.md. Quick Tunnel has no
uptime guarantee, stable hostname or SSE support. Shared demo throttle/budget may
limit simultaneous visitors. DB size/WAL settings are preflight/target bounds,
not filesystem quotas; operator monitors D disk headroom. Preserve budgets and
history, no automatic pruning/reset. Stop only at review-ready PR; never merge.
