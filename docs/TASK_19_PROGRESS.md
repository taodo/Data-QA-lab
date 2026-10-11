# Task 19 — public demo access checkpoint

Engineering objective: opt-in, bounded shared demo identities and accessible login
autofill without public registration/admin APIs or damage to existing accounts.
Learning objective: visitors can start a SQL lesson and resume evidence while
understanding that one shared identity exposes its learning history to other users.

Branch: `feature/task-19-public-demo-access`, base `origin/feature/develop` at
`9a4361e` (custom-domain hotfix PR #27 merged; Task 18 PR #25 merged).
Initial working tree was clean on main; no unrelated changes overwritten.
Live read-only inventory: five active ordinary accounts. No credential hashes or
passwords inspected; no live provisioning, migration, env update or deployment.

Completed: additive public-designation schema; opt-in read-only no-store catalog;
server password lock/login/session disable boundary; local provision/status/rotate/
disable CLI; bounded cap 10–50, recommend 15 only to accommodate the observed five;
ENG/VIE Coming Soon and collapsed disclosure with reveal/copy/explicit-login autofill.
All existing security, ownership and budgets retained, except justified account cap.
See [deployment/rollback commands](TASK_19_DEPLOYMENT.md).

Observed local checks (disposable PostgreSQL on 127.0.0.1:55419; D-drive files):
- `python -m unittest tests.unit.test_public_demo tests.integration.test_public_demo -v`:
  8 PASS, 46.839s, no skips. Cap, conflicts/idempotency, Argon2/randomness, private
  credential exclusion, password locks/recovery, rotation/disable/expiry/logout,
  ownership/history and rate/session boundaries.
- `python -m unittest tests.integration.test_demo tests.integration.test_accounts
  tests.unit.test_demo_hostname tests.unit.test_demo_security -v`: 18 PASS, 76.965s.
- `npm run build`: PASS after rerunning with filesystem permission. Initial Vite
  sandbox realpath EPERM prevented build; no source change required.
- Affected demo browser test: PASS, 22.203s. Initial browser run used wrong D cache
  path and failed before browser launch; corrected to existing `playwright-browsers`.
  375 ENG / 390 VIE screenshots inspected: no overflow; passwords remain masked.

Final affected checks, desktop screenshot and final-head full CI results are recorded
in the PR. CI also exercises public credentials/login/password lock/history/restart
through real Nginx in its own disposable demo. Never starts a public tunnel.
Final backend focused check: 9 PASS, 48.923s, including sanitized CLI error output
and valid-public-password denial while delivery is disabled/outside demo mode.
One parallel browser rerun timed out waiting for completion; submission-response
validation was added without weakening its PASS requirement. Serial rerun passed
in 18.672s. Final UI alignment after screenshot inspection is rechecked in the PR.
All five PowerShell runbook blocks parse successfully; operational deployment,
backup and rollback commands were NOT executed against live data.
Final demo browser run after UI alignment: 1 PASS, 18.789s; desktop 1440px and
mobile 375 ENG / 390 VIE screenshots inspected. Final CLI units plus normal
signup/login browser regression: 4 PASS, 9.386s. Final frontend build and
`git diff --check` passed. No tests skipped in these observed local runs.
No repeated full suite locally. Test credentials are random ephemeral values,
never printed or captured in screenshots. Backend dependency warning about
Starlette/httpx is pre-existing; no new dependency introduced.

Live domain/Cloudflare edge/device verification, operator backup/provision/deployment
and rollback execution remain pending. Shared history is deliberately not private;
five concurrent login sessions and combined auth budget limit showcase concurrency.
No semantic grading of written answers. No automatic progress/budget reset.
