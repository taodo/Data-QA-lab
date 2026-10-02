# Task 1 — First working PostgreSQL pipeline

Engineering objective: run a deterministic pipeline with retained evidence through every layer.
Learning objective: explain extraction, raw preservation, cleaning, business transformation and reporting grain.

Implement Docker Compose PostgreSQL bound only to loopback. Load 10,000 deterministic orders plus customers. Use money as NUMERIC, UTC timestamps, fixed data generation seed/date. Execute source → bronze.orders → silver.orders → gold.daily_sales → target.orders_report and target.daily_sales_report.

Add dependency/configuration management for the PostgreSQL adapter. Keep database credentials out of git. Use an app-specific database. Never reset unrelated schemas or databases. Provide CLI commands for seed/run/inspect. Preserve run_id, timestamps, stage status, counts and errors. Bind evidence to each run and protect old run snapshots from subsequent loads.

Acceptance:
- One clean run completes all stages with execution SUCCESS and quality NOT_RUN until checks exist.
- 10,000 order rows remain at order grain; Gold daily order_count sums to 10,000.
- Exact expected net revenue is verified by an independently specified fixture or calculation.
- Repeated runs remain reproducible without duplicating rows or overwriting past run evidence.
- Stage failure retains error evidence and does not claim downstream success.
- Integration tests actually connect to PostgreSQL; report a skip if unavailable.
- Document D-drive bind paths and explicitly note that Docker's own disk image needs separate configuration.

Out of scope: web UI, API, AI, fault injection, learner SQL execution, cloud. Deliver a small runnable pipeline and explain what each stage does.
