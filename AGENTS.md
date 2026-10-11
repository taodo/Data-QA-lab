# Data QA Lab engineering instructions

This project is independent. Work only in this repository; do not import QA Sentinel agents, workflows or instructions.

Use `feature/develop` as the integration branch. Create each task on `feature/task-<number>-<slug>` from the latest `feature/develop`. Merge only after review/approval. See `docs/BRANCHING.md`.

Implement the active task from `docs/ROADMAP.md`. Keep source and target evidence observable. Execution status and quality status are separate; an unrun check never implies PASS. DQ execution errors are ERROR, not data defects.

Use deterministic seed data, exact decimal money (database NUMERIC), UTC-aware timestamps, explicit data grain and key-based reconciliation. Isolate run artifacts and attach evidence to run IDs. Fault injection is explicit, scoped and reproducible; never mutate unrelated data.

Begin each task with engineering and learning objectives. Finish with commands, observed results, limitations and a learning explanation.

New dependencies require a concrete use in the active task. Prefer small modules and meaningful behavior tests. Never claim unexecuted checks passed. V1 Tasks 0–7.2 exclude AI, cloud, authentication and multi-user scope. Task 9 approved local accounts and ownership. Task 11.1–11.4 is merged; Task 12.1–12.4 approves local Databricks/Synapse/Azure evidence foundations. Live adapters, cloud authorization emulation, cloud credentials/provisioning, paid services and AI remain out of scope.

Task 12 is merged as PR #14 at b0863f8798c8bba2c0ed0f8fc5d37c5e1e158fab; demo preparation is merged as PR #15. Task 13 is merged as PR #18 at 2588f03. Task 14 is merged as PR #19 at 221e1b4. Task 15 is merged as PR #20 at deab838. Task 16 is merged as PR #21 at e0be176. Task 17 is merged as PR #22. Task 18 is merged as PR #25; custom-domain hotfix is merged as PR #27 at 9a4361e. See docs/TASK_18_PROGRESS.md and design-system/data-qa-lab/MASTER.md for accepted frontend design.

Task 19 is merged as PR #29 at 9e47ede. Its public shared-account disclosure,
explicit-login autofill, Coming Soon signup and restrictions remain mandatory.
Active approved scope: Task 20 global frontend UI and persistent Dark/Light on
feature/task-20-global-ui-redesign. See docs/TASK_20_PROGRESS.md and the design
system MASTER.md. Use document-level semantic tokens on every route; default
Dark and independently preserve explicit theme/language preferences. Keep learning
content, nine authored visuals, editor state/history and Task 19 behavior. No
backend, schema, grader, auth policy, provisioning, Docker, tunnel or live environment
changes. No new dependencies. Keep tooling/artifacts/caches on D. Run targeted
browser/theme regressions and frontend build; no full local suite unless required
to investigate an actual failure. Stop at review-ready PR: no merge, deployment,
public tunnel or next task without user instruction. External-device demo
verification remains user-operated.

Before SQL workspace implementation, design database read-only permissions, allowlisted lab schemas, row/time limits and cancellation. Do not rely on SQL text filtering alone.

Run unit tests with `python -m unittest discover -s tests/unit -v`. Run PostgreSQL integration tests with `DATA_QA_TEST_DATABASE_URL` set.
