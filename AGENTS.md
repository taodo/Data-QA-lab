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
Task 20 is merged as PR #30; Task 20.1 header polish is merged as PR #32
at 72ea6d9. Task 21.1 is merged through PR #33 at e4274a4; U1 is merged
through PR #34 at 37734f5. Active approved scope: U2 Unified Learning Tracks on
feature/u2-unified-learning-tracks; see docs/TASK_U2_PROGRESS.md and the four
UNIFIED_PLATFORM architecture/contract/roadmap/test documents. Reuse the shared
Task 20/20.1 shell/tokens and existing Data QA courses and Task 21.1 tutorials.
Banking remains bilingual informational/Planned, with no banking calls/state.
Automation uses existing platform course APIs; independent framework integration
remains future work. Backend changes are limited to exact SPA route allowlisting.
Preserve nine executable courses/36 labs, tutorial contracts, auth, Task 19 policies,
accounts/history and public demo data/configuration. No dependencies, migrations,
execution services, domain repository changes or deployment. Keep artifacts/cache
on D. Focused browser/catalog/SPA tests and frontend build; final-head CI covers
full regression. No merge, deploy, public tunnel or U3 without user instruction.

Before SQL workspace implementation, design database read-only permissions, allowlisted lab schemas, row/time limits and cancellation. Do not rely on SQL text filtering alone.

Run unit tests with `python -m unittest discover -s tests/unit -v`. Run PostgreSQL integration tests with `DATA_QA_TEST_DATABASE_URL` set.
