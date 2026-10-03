# Verification

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
