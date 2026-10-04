# Verification

## V1 release verification

- Task 6: 36 unit + 27 live PostgreSQL integration checks passed before merge.
- Task 7: the same checks plus two Chromium browser tests passed before merge.
- Task 7.1: six lesson profiles, every scenario and browser completion of all six
  lessons passed before merge (37 unit, 30 integration, three browser tests).
- Task 7.2 required checks: fresh database bootstrap and repeated startup without
  reseeding/history loss; bounded history pagination; reference errors classified
  ERROR; production frontend build; real browser loop; actual Docker Compose
  startup and app restart preserving completed session and query/submission history.
- CI `tests` runs PostgreSQL 16 and Chromium, and uploads browser screenshots.
  `packaged-v1` independently builds/starts the containers and verifies retention.
- Windows on the user's own machine remains unverified while GitHub is unreachable.
  Linux CI and container evidence do not substitute for that machine-specific check.

## Task 0

Python 3.12: 10 unit tests passed and Lab 001 loaded.

## Task 1 local environment

Python 3.12:

- 14 unit tests passed.
- Catalog CLI passed.
- PostgreSQL integration test was discovered and skipped because this execution environment has no Docker/PostgreSQL service.

The task branch includes GitHub Actions with PostgreSQL 16. It installs the package, runs all unit tests, then runs the live integration test. The workflow result on the pushed commit is the authoritative PostgreSQL execution evidence.

The integration test runs the clean pipeline twice and checks counts, exact revenue, run status, quality `NOT_RUN`, and retention of the first run's five stage records.

## Task 2 local environment

Python 3.12:

- 19 unit tests passed.
- Eight Task 2 PostgreSQL integration scenarios are present and skip only when `DATA_QA_TEST_DATABASE_URL` is absent.
- GitHub Actions supplies PostgreSQL 16 and is the authoritative live integration result for the task branch.

Coverage includes clean PASS, retained validation history, count FAIL with pipeline execution still SUCCESS, duplicate/null/schema failures, execution ERROR, empty-suite NOT_RUN, immutable Source baseline and cross-run isolation.

Windows Docker verification exposed a loopback mismatch: Compose publishes PostgreSQL on `127.0.0.1`, while the original application default used `localhost`. On a host that tried IPv6 first, each connection waited roughly 260 seconds before falling back to IPv4. The local default now matches the IPv4-only port binding and every connection has a five-second timeout. The corrected 10,000-row pipeline completed in 2.4 seconds; its 20-rule quality suite passed. Local verification then passed 19 unit tests and eight PostgreSQL integration tests.

## Task 3 verification

- The combined clean suite contains 26 rules: the 20 Task 2 rules plus six reconciliation rules.
- Unit coverage validates pair-dataset allowlisting, composite keys, safe identifiers, field mappings and evidence limits.
- PostgreSQL integration covers clean PASS, equal-count key swaps, exact field mismatches, composite keys, bounded evidence and existing cross-run behavior.
- The equal-count scenario proves the record-count rule can PASS while key reconciliation correctly FAILs with one missing and one unexpected key.

## Task 4 verification

- The fault catalog contains exactly four deterministic scenarios: missing row, duplicate row, null `net_amount` and `net_amount + 0.01`.
- Unit coverage validates catalog allowlisting and the 24-rule workspace suite.
- PostgreSQL integration applies every scenario, requires the expected rules to fail, and proves pipeline execution remains `SUCCESS` while quality becomes `FAIL`.
- Target fingerprints before and after each fault are identical; only the selected pipeline run's workspace is mutated.
- Forced mid-apply failure leaves neither workspace rows nor fault metadata, proving transactional rollback.
- A second active fault is rejected, reset is idempotent, and reapplying the same scenario produces identical mutation evidence.
- After reset, the normal 26-rule suite passes against the unchanged Target.

## Task 5 verification coverage

- Unit tests cover SQL input bounds, bounded limits, grading result shape/numeric
  contract, owned identifiers, challenge visibility and CLI parsing.
- Live integration tests exercise actual restricted session_user/current_user,
  denied writes/DDL/COPY/role escalation/hidden metadata access, single-statement
  protocol, cleanup, cross-session isolation and PUBLIC-grant fail-closed behavior.
- Server timeout and an independent watchdog are tested, including SQL attempting
  to disable statement_timeout. Output row/column/cell/byte bounds are exercised.
- Good key checks pass; constants, count-only checks, false positives and malformed
  result contracts fail. Syntax errors produce ERROR. Challenge visibility, hints,
  reveal, completion and persistent query/submission history are covered.
- Local integration tests skip when no database URL is configured; GitHub Actions
  runs all integration tests against PostgreSQL 16. Read the pushed commit's CI
  result before treating these coverage claims as observed passes.
