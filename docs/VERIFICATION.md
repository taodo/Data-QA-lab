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
