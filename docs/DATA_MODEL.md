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
