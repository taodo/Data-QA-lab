# Task 12 progress

2026-10-06: read AGENTS, branching, roadmap and Task 11 progress. Fetched origin;
reviewed merge 3406447 confirmed, clean working tree. Created approved branch
feature/task-12-cloud-foundations from current origin/feature/develop.
Read TASK_12_PLAN.md for engineering/learning objectives and contract decisions.
Implementation and verification pending. Preserve learner DB and Docker mount.
Use dedicated Task 12 test databases. No full suite has been run for Task 12.

## Implementation checkpoint

Six local typed-evidence runtimes/ENG-VIE lessons and three available courses are
implemented, with independent built-in expected tables and fixed acceptance
counts. Source drives classification/version/fact/report operators. Azure captures
observations only. Foundation JSON round-trips explicit context, references and
all bounded rows; expected tables cannot be imported. Existing cloud contracts,
ownership/read-only SQL and local mutation revisions are reused.

Observed targeted verification under data/generated/task12-20261006:
- Unit: `python -m unittest tests.unit.test_task12 tests.unit.test_courses
  tests.unit.test_curriculum tests.unit.test_cloud tests.unit.test_foundation -v`:
  27 PASS, 0.497s. Old 30-lesson assertion changed to 36.
- PostgreSQL: four Task 12 methods initially found enrollment/scenario constraints
  only allowed old values. Both constraints are expanded non-destructively.
  Independent clean/fault/alternate grading and version replay methods passed;
  the two scenario-dependent methods initially errored. Affected three-method
  rerun: 3 PASS, 51.806s. Data QA learner DB never used for fixtures.
- `npm run build --prefix frontend`: PASS. Windows sandbox realpath limitation
  required running the existing build outside the sandbox; no dependency change.
- `python -m unittest discover -s tests/e2e -v -k test_task12_six_lessons`:
  1 PASS, 88.048s. Six actual CHALLENGE submissions; ENG/VIE/draft/reload,
  challenge before answer, mobile screenshots, progress/history and real
  foundation JSON download/import. Database data_qa_task12_browser (127.0.0.1).

## Final local verification checkpoint

Release 1.5.0 includes explicit Introduction/Purpose before guided instructions;
versioned source docs and examples cover all six lessons. No new dependency.
Affected refinement regressions completed:
- Access + existing account ownership/CSRF/enrollment/history/security: 9 PASS,
  67.361s (`access-accounts.log`). Command: `python -m unittest
  tests.integration.test_task12.Task12IntegrationTests.test_access_execution_incomplete_evidence_not_data_defects_and_restricted_sql
  tests.integration.test_accounts -v`.
- Existing Task 11 watermark/recovery round-trip across Reset and other sessions:
  1 PASS, 56.048s (`cloud-regression.log`), targeted method
  `tests.integration.test_cloud.CloudIntegrationTests.test_watermark_and_recovery_round_trip_keep_batch_and_checkpoint_context`.
- Introduction accordions across nine courses, both languages, Enter/Space/Tab,
  ARIA and mobile: 1 PASS, 15.262s (`introduction-browser.log`),
  `python -m unittest discover -s tests/e2e -v -k test_course_introductions_all_courses`.
- Final explicit learning sequence for six lessons in ENG/VIE and mobile:
  1 PASS, 10.764s (`flow-browser.log`),
  `python -m unittest discover -s tests/e2e -v -k test_task12_learning_sequence`.
  Inspected Synapse ENG mobile screenshot; readable layout with no overflow.
- Final affected contract/curriculum units: 5 PASS, 0.024s (`unit-final.log`),
  `python -m unittest tests.unit.test_task12 tests.unit.test_curriculum -v`.
- Final frontend production build PASS (`build-final.log`).
- Docker app-only upgrade/start, actual packaged query/grading/import for all six
  lessons, restart and history/evidence/revision resume PASS (`docker-upgrade.log`,
  `container-smoke.log`, `container-restart.log`, `container-resume.log`). Commands:
  `docker compose up -d --build --no-deps --wait --wait-timeout 180 app`,
  `python scripts/container_smoke.py`, `docker compose restart app`,
  `docker compose up -d --no-deps --wait --wait-timeout 180 app`,
  `python scripts/container_smoke.py resume`.
- Read-only hashes before/after upgrade retained exactly: three original accounts,
  15 enrollments, 31 sessions, 60 queries, 15 submissions, 66,746 Target rows and
  all 194 original snapshot tables (`retention.json`, `retention-*.log`). Smoke
  subsequently adds only its own account/sessions. PostgreSQL mount stays on D.

No local full-suite duplication; final exact-head CI must validate full unit,
PostgreSQL integration, Linux browser and packaged smoke/restart before handoff.
CI link/counts, exact tested commit and ZIP hash are recorded in the PR and the
ignored D-drive HANDOFF.md/ci-final.json, avoiding a post-CI source commit that
would invalidate the exact-head result. Commit/push/PR/CI completion follows this
checkpoint. Do not merge or start another task.

Limits: local PostgreSQL only, no live cloud/Spark/Delta/Synapse engine or Azure
authorization emulation. Imported expected rows are forbidden; built-in contract
identity selects an explicit fixture, while grading always rebuilds independent
truth. JSON-only foundation evidence retains existing size/row/history bounds.
Unbounded cloud snapshots and arbitrary provider contracts are unsupported.
Written answers are retained only. The learning outcome is evidence-based
classification/version/grain/routing investigation, not provider certification.
