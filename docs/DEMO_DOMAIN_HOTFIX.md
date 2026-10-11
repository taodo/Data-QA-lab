# Demo custom-domain hotfix checkpoint

Engineering objective: allow one approved Named Tunnel hostname through the
existing demo configuration without weakening host/proxy/auth boundaries.
Learning objective: distinguish exact host allowlisting and trusted HTTPS scheme
evidence from manual verification of Cloudflare's public edge.

Base: origin/feature/develop 2edc112 (Task 18 PR #25 merged).
Branch: feature/hotfix-demo-custom-domain. Initial working tree clean; no merge.

## Scope and changes

- scripts/demo.ps1: allow exactly data-qa-lab.store plus existing lowercase,
  single-label Quick Tunnel names. Absolute regex anchors also reject trailing
  newlines. Rejected input never writes the env or calls Docker.
- scripts/demo_verify.py: same hostname policy; verify malformed forwarded schemes,
  localhost HTTP and public-signup restriction through the real proxy as well.
- Unit regression executes the actual PowerShell action against temporary env
  fixtures on D with Docker/filesystem routing mocked. Covers four valid names
  and 25 invalid cases, credential/other-setting preservation and app/proxy-only
  recreation. Separate application tests cover Named host/scheme/origin rejection.
- Integration adds Named HTTPS login, cookies, SQL, submission, history after
  app recreation and demo restrictions, using disposable test databases only.
- Existing packaged CI now verifies Quick then Named via actual Nginx/app with
  its private CI database. Switching the CI host recreates app/proxy only and
  never opens a public tunnel. Production Compose and Nginx remain unchanged.
- DEMO_ONLINE.md documents the exact command, constraints, proxy trust and manual
  checklist. No Cloudflare credentials/tokens/secrets or existing demo data read,
  modified, reset or deleted. No dependencies or curriculum changes.

## Observed verification

`python -m unittest tests.unit.test_demo_hostname tests.unit.test_demo_security -v`
PASS: six tests, 1.270s, including actual Windows PowerShell; no skips.

`DATA_QA_TEST_DATABASE_URL=...:55418/data_qa_task18` with
`python -m unittest tests.integration.test_demo -v`: infrastructure failure in
setup for four tests (20.067s): Docker daemon unavailable; PostgreSQL connection
timeout. No test-body assertion failed and no learner/demo DB was accessed.
Do not treat this attempt as PASS. Final-head CI will provide PostgreSQL and
real proxy verification; PR records its final results and tested SHA.

Final appropriate suite is automatic exact-head CI; no duplicate local full run.
Manual public-domain/external-device verification remains PENDING. No public
tunnel started, existing tunnel config modified or live hostname applied by agent.

## Commands after review

```powershell
Set-Location D:\Data-QA-Lab
git fetch origin
git switch feature/hotfix-demo-custom-domain
git pull --ff-only
.\scripts\demo.ps1 -Action SetHostname -Hostname data-qa-lab.store
.\.venv\Scripts\python.exe -m scripts.demo_verify --hostname data-qa-lab.store --username demo_learner --restart
```

Use the already prepared demo env; do not run Prepare to reconfigure an existing
Named Tunnel. SetHostname restarts app/proxy, preserves PostgreSQL. The verifier
prompts for the existing demo password and consumes one lab/write budget. This
is local simulated-origin verification; then perform DEMO_ONLINE.md's external
checklist against https://data-qa-lab.store. Never merge as part of this hotfix.
