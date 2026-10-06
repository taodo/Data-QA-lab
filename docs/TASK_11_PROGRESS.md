# Task 11 implementation checkpoint

Final status (2026-10-06, supersedes pending/approval notes below): PR #13 approved
and merged into feature/develop at 34064470c681816e5ea72e03a82cecabb57dbfb8.
Reviewed source head 81d06a3 passed exact-head CI run 37300698537: 60 unit,
62 PostgreSQL integration, 12 browser tests plus build and Docker smoke/restart.
Task 12.1–12.4 is now separately approved; use TASK_12_PROGRESS.md to resume.
Live stage 11.5 remains unimplemented/unapproved. Historical checkpoints follow.

Engineering objective: session-owned cloud evidence, bounded imports, eight local
lessons and retained account progress, using the existing PostgreSQL security boundary.
Learning objective: reconcile run/activity metadata with actual data, partitions,
freshness and recovery; execution SUCCESS never proves data-quality PASS.

Scope 11.1–11.4 approved by the user on 2026-10-05. Plan and review occur in a
separate ChatGPT chat. Implementation/verification happen here. Push and open a
PR into feature/develop when ready. Do not merge or start the next task.

Branch: feature/task-11-cloud-qa, already created for this task from Task 10 merge.
Local feature/develop advanced to origin/feature/develop (6799950); task branch
already contains that base. Existing learner PostgreSQL data and accounts remain.

## Security decisions before workspace implementation

- Reuse short-lived SELECT-only PostgreSQL query roles, generated per-query schemas,
  table allowlists, 100 output rows, 2-second statement timeout and independent
  watchdog cancellation. Imported SQL/code never runs; trusted actions are scoped
  to the authenticated account's active SANDBOX session.
- JSON envelope version 1; CSV has a fixed record header. Maximum 48 KiB UTF-8 per
  file, 400 data rows total, 100 rows per dataset, 8 retained imports per session.
  Existing API body cap remains 64 KiB. Import metadata arrays are bounded too.
- Ordinary file content only; no paths, URL retrieval or archive extraction.
  Strict metadata fields retain original supported provider fields in raw evidence;
  absent fields normalize to UNKNOWN/NULL, not SUCCESS/zero.
- Exact NUMERIC money, UTC-aware timestamps and explicit event/order/file grains.
  Grading builds independent fixtures; imports cannot redefine grading truth.
- Simulator is local PostgreSQL, not a Microsoft emulator. No live cloud adapter,
  credentials, provisioning, Spark or Delta/Iceberg engine is in this task.

## Progress

- Repository/branch/runtime checked; declared project test/e2e dependencies installed
  in D:\Data-QA-Lab\.venv. Pip cache and test temp directories are on D.
- 11.1–11.3 runtime/contracts, eight bilingual lessons and independent graders
  implemented. 11.4 evidence/import UI and release regression are implemented;
  final verification continues.
- Observed: 53 unit tests PASS; six real PostgreSQL cloud integration tests PASS
  (356 seconds); production frontend build PASS. Logs under the pre-approval
  evidence directory below. Later fixture/NULL/Windows reload changes are covered
  by the ongoing full regression run, not assumed verified by the earlier run.
- Browser flow completed all eight lessons including JSON/CSV imports, ENG/VIE,
  drafts, mobile and correct-course resume. Separate challenge/reveal test failed
  only on expected label (UI says 'Solution revealed'); correcting assertion.
- Native Windows deep-link fallback fixed by normalizing path separators. Test
  dependencies were missing locally and have now been installed from declarations.
- Docker build/start/restart smoke PASS. Read-only hashes prove the existing
  account, 11 sessions, 16 queries, 2 submissions and 66,246 Target rows were
  retained exactly through the upgrade, before smoke-test data was added.
- Added shifted faulty keys/alternate schema fields/copy metrics so hardcoded
  checks cannot pass using only unshifted faults. Re-running cloud tests.
- Quality guard now rejects truncated/non-integer/out-of-range result contracts;
  import validation messages are ENG/VIE, and simulator actions require reset
  after import. These final changes are under verification.
- Reveal test corrected to check the actual backend completion flag: zero
  progress intentionally has no progress bar. Full browser suite is re-running.
- Pending: complete final PostgreSQL/browser regression, final Docker smoke,
  source ZIP verification, push final code and open PR. Do not merge.
- Full regression identified an obsolete enrollment assertion: Fabric is now
  executable, so the planned-course rejection test uses Synapse instead.
- Metadata-only imports now attach run IDs from runs/activities/manifests/references,
  even when no data snapshot rows exist. A regression assertion covers this case.
- Pre-approval evidence: data/generated/task11-review-20261005/REVIEW.md.

## Resume

Read this file and TASK_11_PLAN.md, inspect git status/log, then continue Task 11
only. Use a dedicated PostgreSQL test database; never run integration fixtures
against the learner database. Record observed commands/results and pending work
at each milestone. Merge requires the user's explicit review approval.

## Verification checkpoint after the interrupted session (2026-10-05)

Implementation checkpoint: bee78f4. This section supersedes intermediate test
counts and pending verification notes above; those notes retain the audit trail.
Core 11.1–11.4 is implemented. Review in the separate ChatGPT chat has not been
reported here. No merge or next-task work is authorized.

Observed commands and results (logs on D under
`data/generated/task11-review-20261005`):

- `python -m unittest discover -s tests/unit -v`: 55 PASS on Windows and Linux
  (`unit-final.log`, `linux-final/linux-unit.log`).
- `npm run build --prefix frontend`: PASS (`frontend-build.log`).
- `python -m unittest discover -s tests/integration -v` with a dedicated test DB:
  latest Linux full run reported 57 PASS and one cleanup failure out of 58
  (`linux-final/linux-integration.log`). All six cloud methods passed, including
  final metadata-only import coverage. The cleanup assertion counts cluster-wide
  temporary roles. A deliberately stopped earlier verification container left
  one expired role in `data_qa_task11_linux_test`; it had no active connections
  and no dependencies in the learner database. Only its exact matching temporary
  query schema and role were removed. The failing method then PASS on rerun:
  `PYTHONPATH=/app/tests/integration:$PYTHONPATH python -m unittest
  test_learning_labs.LearningLabTests.test_read_queries_ctes_and_cleanup -v`
  (`linux-final/linux-cleanup-rerun.log`). The full suite was not rerun after that
  environmental cleanup; report the full result and targeted rerun separately.
- The earlier Windows full integration run had one obsolete planned-course
  assertion (Fabric became available). That assertion now targets Synapse and
  passed with metadata import retention in the two-test final-fixes rerun
  (`final-fixes.log`).
- `python -m unittest discover -s tests/e2e -v`: 10 PASS in native Chromium
  (`browser-final.log`), covering all 30 lessons, eight cloud lessons, imports,
  ENG/VIE, challenge/reveal, mobile, course resume and account isolation. Linux
  browser tests were not reached by the interrupted full verification script.
- Docker build, startup, smoke and restart/resume: PASS, including imported
  cloud evidence and personal progress (`container-head-resume.log` and other
  container logs). Existing PostgreSQL bind mount stays on D.
- Read-only retention hashes before/after upgrade: existing account, 11 sessions,
  16 queries, two submissions and 66,246 Target rows preserved exactly. Smoke
  tests subsequently added their own accounts/evidence.
- Source ZIP at bee78f4: CRC validation PASS; 30 lab definitions and runtime
  included; PostgreSQL data, environment secrets and virtualenv excluded.

Limitations: all cloud evidence is local SIMULATED or file IMPORTED. Live cloud
stage 11.5 is unimplemented. No Spark/Delta engine or live shortcut resolution.
Written explanations are retained rather than semantically graded. A hard-killed
process can leave expired temporary SQL roles requiring scoped administrator
cleanup; normal SQL cleanup and timeout/watchdog tests pass.

Learning explanation: run/activity success is a provider claim. Independent
key-based reconciliation, explicit schema/partition contracts, exact decimals and
UTC boundaries establish whether the data is correct. Unknown evidence and
unexecuted checks cannot imply PASS.

Task branch pushed; PR #13 is open into feature/develop:
https://github.com/taodo/Data-QA-lab/pull/13. CI is running; final CI diagnostics
are retained under the D-drive evidence directory and in the PR. Do not merge;
user review/approval remains the gate. No next-task work.

## Course introduction follow-up

Approved in this chat: add two ENG/VIE beginner accordions to every course on the
existing Task 11 branch. Nine distinct introduction datasets and accessible,
responsive UI are implemented; planned courses keep their existing lab lock.
56 unit tests PASS; production frontend build PASS after Windows sandbox denied
Vite's realpath operation and the build was rerun outside the sandbox. Browser
verification PASS (one E2E method, 18 course/language subcases, 13.232 seconds):
all nine courses in both languages, mouse/full-header clicks, Enter/Space/Tab,
visible focus, panel ARIA relationships, language switching and 390px layout.
Planned pages have no curriculum or start/enroll buttons. Logs:
`introduction-unit.log`, `introduction-build.log`, `introduction-browser-final.log`.
Mobile screenshots for all 18 variants and a desktop screenshot are under
`e2e-artifacts` on D; inspected SQL desktop and Databricks VIE mobile visually.

Native browser startup initially timed out because PostgreSQL `localhost`
connections took about five seconds while health probes allow one second.
Explicit `127.0.0.1` reduced connection time to 0.057 seconds. The browser command
uses that address and the dedicated `data_qa_task11_e2e` database. An early test
attempt also raced initial account hydration (which remounts the owned course
page); the final test waits for the signed-in page before keyboard interaction.
No runtime dependency, SQL permission, account or availability changes.

Local Docker rebuild/start PASS (`introduction-docker-build.log`). Read-only
packaged API smoke PASS: READY, 18 distinct introductions and six planned
course/language variants with empty curriculum (`introduction-packaged-api.log`).
The existing PostgreSQL container/bind mount and accounts are retained.
Targeted PostgreSQL/API account/CSRF/bounds test PASS (7.408 seconds), including
planned-course enrollment rejection (`introduction-planned-lock.log`).

Previous checkpoint bd7e64e now has successful GitHub CI for both test and
packaged-v1 jobs, including full integration and Linux browser runs:
https://github.com/taodo/Data-QA-lab/actions/runs/37281206389.
That success precedes the introduction follow-up and does not verify these edits.
Next: push this follow-up to existing PR #13, inspect updated-head CI and report
results. No merge or next task.

## PR #13 review fixes (authorized follow-up)

Engineering objective: preserve the meaning of exported snapshots and invalidate
QA only by local mutations. Learning objective: distinguish selected-batch and
checkpoint evidence from provider clocks and local execution.

Root causes and changes:
- Batch/as-of filtering depended on receiving-session state, and import discarded
  recovery checkpoints. V1 files now carry explicit batch_no and reported steps;
  imports replace that context. Legacy missing context remains NULL/NOT_VERIFIED.
  CSV has no selected-batch/as-of contract and clears those values, not guesses.
- Import allowed 20 runs while the simulator can retain 101; state export also
  truncated at 100. Backend export reads all bounded evidence, applies the shared
  importer contract (101 runs/100 steps), preserves every run and checks both
  48 KiB file and escaped 64 KiB request limits. Oversize is an explicit error.
- QA compared query times with provider ended_at. Queries now bind to a monotonic
  local captured_at revision under a shared context lock. All mutations advance
  it; provider dates never affect QA age. Legacy results lacking a token remain
  in history but are NOT_RUN until a fresh check.
- UTC normalization could OverflowError at years 1/9999. It now raises the same
  ENG/VIE timestamp validation error before any import mutation.

Targeted verification (D-drive evidence: data/generated/task11-reviewfix-20261005):
- `python -m unittest tests.unit.test_cloud -v`: 10 PASS, including explicit
  batch/steps, 101-run export, file/request envelope bounds and UTC overflow.
- `python -m unittest tests.unit.test_api.ApiContractTests.test_input_origin_host_and_body_limits -v`:
  1 PASS after sharing the request-size constant.
- `python -m unittest tests.integration.test_cloud -v`: 10 PASS (539.210 seconds)
  on dedicated data_qa_task11_reviewfix with IPv4 loopback, never the learner DB.
  Covers round-trip batches 0–3, faulty watermark/checkpoint snapshots, recovery,
  98 replays/101 runs, future provider clocks and atomic ENG/VIE overflow errors,
  plus all existing cloud grading/isolation/import regressions.
- `npm run build --prefix frontend`: PASS.
- `python -m unittest discover -s tests/e2e -v -k test_cloud_download_round_trip`:
  1 PASS (24.225 seconds), actual browser download after 21 replays, Reset, upload
  and unchanged batch/check PASS. Dedicated data_qa_task11_reviewfix_browser.

No local full-suite run: final exact-head GitHub CI will run required unit,
PostgreSQL integration, Linux browser and packaged smoke/restart checks per the
user's policy. Targeted checks are complete; pushing this checkpoint to PR #13.
Final CI diagnostics and handoff are retained in the D-drive evidence directory
and PR description. Handoff requires green CI on this final commit. No merge or
new task.

Limits retained: 48 KiB file / 64 KiB request, 100 rows/dataset, 400 rows total,
eight imports/session and 100 simulator steps. Missing context is not inferred;
oversized evidence remains stored but cannot be downloaded as an importable file.
Imported checkpoint claims retain IMPORTED provenance; no live provider execution
is verified. Existing accounts, PostgreSQL mount/data and history are preserved.
