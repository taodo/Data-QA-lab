# Learner SQL boundary — Task 5

Engineering objective: execute learner SELECT queries without granting access to
pipeline data, private grading metadata, other sessions, or write privileges.
Learning objective: distinguish query execution success from a check that detects
real defects without false positives.

## Design before implementation

- This is a dedicated local Data QA Lab database, not a shared production database.
- Session snapshots are admin-owned opaque schemas. Every execution copies only
  four allowlisted tables into a new opaque schema: source_orders, target_orders,
  gold_daily_sales, target_daily_sales. Source means immutable Bronze order keys.
- A separate, short-lived LOGIN role with a generated password receives schema
  USAGE and table SELECT only. It is NOSUPERUSER, NOCREATEDB, NOCREATEROLE,
  NOINHERIT, NOREPLICATION, NOBYPASSRLS and has no memberships. Learner SQL never
  runs on the admin connection or via SET ROLE on an admin login.
- PUBLIC CREATE/TEMP rights on this dedicated database and PUBLIC rights on the
  public schema are revoked by an explicit lab-sql-init command. Core lab schemas
  and hidden metadata must not be PUBLIC-accessible. Runtime privilege audits fail
  closed if unrelated user objects become readable/writable or callable.
- Only a single SELECT/CTE query is accepted by PostgreSQL's server cursor protocol.
  Transactions are READ ONLY and always rolled back. Database privileges remain
  authoritative even if a query attempts to alter session configuration.
- Default statement timeout: 2 seconds. An independent 3-second watchdog terminates
  only the execution's PID/role if SQL tries to disable timeouts. Lock/idle timeouts
  and a temporary-file limit are also configured. This is not OS-level isolation
  against a hostile local administrator or memory-intensive PostgreSQL expressions.
- Results are streamed, capped at 100 rows, 20 columns, 64 KiB total and 8 KiB per
  cell, including server-side bounded text projection. Truncation is explicit and
  invalidates grading. Input SQL is capped at 16 KiB. Results use text/null cells.
- Close learner connection before dropping only its generated workspace and role;
  cleanup also occurs on errors and timeout. Process crashes may leave opaque
  artifacts; no automatic broad cleanup of unrelated schemas/roles is performed.
- Challenge responses exclude scenario IDs, fault evidence, grading case values,
  private schema names and solution SQL. Hints are progressive. Explicit reveal
  ends a session; revealed solutions remain visible on resume. Local users who
  control source files or the database administrator can inspect solutions.

## Grading contract

A submission returns exactly one non-negative integer cell named violation_count.
It must return zero for two clean snapshots and a positive count for missing-key
and equal-count-swapped-key snapshots. Grading executes behavior, never compares
SQL text. SQL errors/timeouts are ERROR, inadequate detection is FAIL. Conclusions
are required and retained, not semantically graded by an LLM.
