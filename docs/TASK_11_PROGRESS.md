# Task 11 implementation checkpoint

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

Remaining: push the task branch, open the PR into feature/develop, inspect CI and
record its result. Do not merge; user review/approval remains the gate.
