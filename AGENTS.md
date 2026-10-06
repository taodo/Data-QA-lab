# Data QA Lab engineering instructions

This project is independent. Work only in this repository; do not import QA Sentinel agents, workflows or instructions.

Use `feature/develop` as the integration branch. Create each task on `feature/task-<number>-<slug>` from the latest `feature/develop`. Merge only after review/approval. See `docs/BRANCHING.md`.

Implement the active task from `docs/ROADMAP.md`. Keep source and target evidence observable. Execution status and quality status are separate; an unrun check never implies PASS. DQ execution errors are ERROR, not data defects.

Use deterministic seed data, exact decimal money (database NUMERIC), UTC-aware timestamps, explicit data grain and key-based reconciliation. Isolate run artifacts and attach evidence to run IDs. Fault injection is explicit, scoped and reproducible; never mutate unrelated data.

Begin each task with engineering and learning objectives. Finish with commands, observed results, limitations and a learning explanation.

New dependencies require a concrete use in the active task. Prefer small modules and meaningful behavior tests. Never claim unexecuted checks passed. V1 Tasks 0–7.2 exclude AI, cloud, authentication and multi-user scope. Task 9 approved local accounts and ownership. Task 11.1–11.4 is merged; Task 12.1–12.4 approves local Databricks/Synapse/Azure evidence foundations. Live adapters, cloud authorization emulation, credentials, provisioning, paid services and AI remain out of scope.

Task 12 is merged as PR #14 at b0863f8798c8bba2c0ed0f8fc5d37c5e1e158fab; demo preparation is merged as PR #15. Task 13 is merged as PR #18 at 2588f03. Task 14 is merged as PR #19 at 221e1b4. Active approved scope: Task 15 beginner guidance for all four API lessons in ENG/VIE on feature/task-15-api-learning-guidance. See docs/TASK_15_PROGRESS.md. Follow existing-field guidance and extend GuidanceText only for API. Preserve original challenge contracts and reveal/completion rules. Do not change HTTP execution, graders, fixtures, retries, simulation, permissions, scoring, schemas, APIs or SQL/ETL/cloud content. Preserve accounts/history/Docker data; keep artifacts/caches on D. Use targeted local tests and exact final-head full CI without duplicate full runs. No merge or next task without user instruction. Never open a public tunnel automatically; external-device demo verification remains user-operated.

Before SQL workspace implementation, design database read-only permissions, allowlisted lab schemas, row/time limits and cancellation. Do not rely on SQL text filtering alone.

Run unit tests with `python -m unittest discover -s tests/unit -v`. Run PostgreSQL integration tests with `DATA_QA_TEST_DATABASE_URL` set.
