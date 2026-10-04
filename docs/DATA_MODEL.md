# Domain and dataset contracts

Implemented contracts: Lab, Pipeline, PipelineRun, Dataset, ValidationRule, ValidationResult, FaultScenario and StageResult.

PipelineRun references lab_id and pipeline_id; execution_status and computed data_quality_status are independent. Timestamps are timezone-aware. StageResult has layer, execution status, optional row count and error. ValidationResult has rule ID, verdict, expected/actual descriptions and evidence.

Quality aggregation priority: ERROR → FAIL → NOT_RUN → PASS. An empty suite is NOT_RUN. Individual outcomes remain visible if aggregate status is ERROR.

## PostgreSQL schema — implemented in Task 1

orders: order_id (integer key), customer_id, ordered_at (UTC timestamptz), gross_amount, discount_amount, refund_amount (NUMERIC), updated_at.
customers: customer_id (integer key), country_code.
silver.orders adds net_amount = gross_amount - discount_amount - refund_amount.
gold.daily_sales: order_date (UTC), order_count, net_revenue.
target.orders_report retains order grain; target.daily_sales_report retains day grain.

Use fixed seed and dates for repeatable results. Record dataset/run scope on evidence. Validation rule IDs reference the lab's datasets; identifiers and schema ownership will be checked during catalog registration in Task 5. Task 1 persists pipeline and stage execution evidence. The domain dataclasses remain transport-neutral; a full workflow transition state machine is outside this task.

## Validation persistence — Task 2

`metadata.validation_runs` identifies each suite execution and links it to one successful pipeline run. `metadata.validation_results` stores one immutable result per rule with dataset, check type, status, expected/actual JSON, evidence JSON and execution error. The latest completed suite status is copied to `pipeline_runs.data_quality_status`; pipeline execution status remains independent.

Task 3 adds `KEY_RECONCILIATION` and `FIELD_RECONCILIATION` result types. Pair rules persist the target dataset in `dataset_id` and include both source and target dataset IDs in expected JSON. Evidence is bounded per rule. Key evidence carries `MISSING_KEY` or `UNEXPECTED_KEY`; field evidence carries the business key, source/target columns and exact expected/actual values.

## Fault persistence — Task 4

`fault_workspace.orders_report` and `fault_workspace.daily_sales_report` are run-scoped Target copies with deliberately relaxed constraints. They exist only so missing, duplicate and null behavior can be exercised without weakening or mutating the real Target tables.

`metadata.fault_runs` links a fault UUID to one successful pipeline run, an allowlisted scenario, `APPLIED`/`RESET` lifecycle state, before/after mutation evidence and the latest fault validation run. A partial unique index enforces at most one `APPLIED` fault per pipeline run. Apply and reset are transactional; reset deletes workspace rows but retains metadata evidence.

## Learning persistence — Task 5

`metadata.lab_sessions` stores session ID, lab/pipeline linkage, mode, ACTIVE /
COMPLETED / REVEALED state, private scenario/schema, hint level and UTC timestamps.
`metadata.lab_queries` retains submitted SQL and bounded public query results.
`metadata.lab_submissions` retains SQL, conclusion, PASS/FAIL/ERROR and private
grading case results. Inspection projects only learner-visible fields.

Private `learner_session_<uuid>` schemas preserve immutable order/day snapshots.
Per-execution `learner_query_<uuid>` schemas and `learner_role_<uuid>` logins are
created and dropped around each query. Schemas are admin-owned; roles receive only
USAGE and SELECT. Results are text/null cells so money remains an exact string.
Lab 001 grades key sets; it does not replace the separate 26-rule quality suite.

V1 has six lesson-specific profiles and additional isolated fixture scenarios.
Session inspection returns the latest 20 queries/submissions plus total counts;
the API exposes older pages without private grading results. Session list pages
are limited to 50. Progress aggregates all persisted sessions, independent of
history pages. Indexes support run/session time ordering. Browser language and
unsent drafts are local browser state; completed progress/history is in PostgreSQL.
