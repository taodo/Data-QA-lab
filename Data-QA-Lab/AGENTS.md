# Data QA Lab engineering instructions

This project is independent. Work only in this repository; do not import QA Sentinel agents, workflows or instructions.

Implement the active task from docs/ROADMAP.md. Keep source and target evidence observable. Execution status and quality status are separate; an unrun check never implies PASS. DQ execution errors are ERROR, not data defects.

Use deterministic seed data, exact decimal money (database NUMERIC), UTC-aware timestamps, explicit data grain and key-based reconciliation. Isolate run artifacts and attach evidence to run IDs. Fault injection is explicit, scoped and reproducible; never mutate unrelated data.

Begin each task with engineering and learning objectives. Finish with commands, observed results, limitations and a learning explanation.

Task 0 is dependency-free. New dependencies require a concrete use in the active task. Prefer small modules and meaningful behavior tests. Never claim unexecuted checks passed. No AI, cloud, authentication or multi-user scope in V1.

Before SQL workspace implementation, design database read-only permissions, allowlisted lab schemas, row/time limits and cancellation. Do not rely on SQL text filtering alone.

Run: python -m unittest discover -s tests/unit -v
