# Task 5 — Secure learning labs

Status: approved and merged through PR #5 into feature/develop. Tasks 6–7.2 build the bilingual browser V1 on this restricted SQL/session foundation.

Engineering: provide persistent lab sessions, bounded read-only learner SQL,
progressive hints, visibility-aware responses and behavioral grading.

Learning: demonstrate that executing a query is not evidence of adequate coverage;
key identity must be tested alongside counts and grain.

## Scope

Lab 001 only; local single-user CLI. Each session copies one successful orders run.
Learner SQL must return one non-negative integer violation_count. Two clean
fixtures require zero; missing-key and equal-count-swap fixtures require positive.
SQL errors/timeouts produce ERROR; wrong detection/result shape produces FAIL.
SQL text is not compared. Conclusions are recorded, not evaluated by AI.

## Lifecycle and commands

Initialize with db-init then lab-sql-init on the dedicated Compose database.
Use lab-start, lab-show, lab-query, lab-hint, lab-submit and lab-inspect. Optional
lab-reveal ends an active attempt and exposes the solution. A PASS automatically
completes the session and exposes the solution. Repeat submission after completion
or reveal is rejected. FAILED checks can be corrected and resubmitted.

See README.md for a copy/paste Windows workflow and instructor smoke SQL examples.
Run unit tests and PostgreSQL integration tests using the existing commands.

## Security and limitations

Read SQL_SECURITY.md before use. PUBLIC privilege hardening is explicit; no learner
query runs under the admin identity. The local provisioning login is a superuser;
ephemeral learner roles are not. Query output, deadlines and private metadata are
bounded by runtime rules and database permissions. Non-allowlisted PUBLIC grants
fail closed. No SQL parser dependency, API, UI, AI grading, cloud or multi-user scope.

Session snapshots are retained for history; normal query copies/logins are removed.
An abruptly terminated process can leave query artifacts (credentials expire in
five minutes), requiring operator inspection. PostgreSQL expression memory use is
not OS-sandboxed. Local administrators/source readers can inspect instructor content.
