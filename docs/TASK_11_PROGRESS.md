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
