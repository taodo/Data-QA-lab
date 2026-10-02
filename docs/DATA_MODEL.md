# Domain and dataset contracts

Implemented contracts: Lab, Pipeline, PipelineRun, Dataset, ValidationRule, ValidationResult, FaultScenario and StageResult.

PipelineRun references lab_id and pipeline_id; execution_status and computed data_quality_status are independent. Timestamps are timezone-aware. StageResult has layer, execution status, optional row count and error. ValidationResult has rule ID, verdict, expected/actual descriptions and evidence.

Quality aggregation priority: ERROR → FAIL → NOT_RUN → PASS. An empty suite is NOT_RUN. Individual outcomes remain visible if aggregate status is ERROR.

## Planned database schema — Task 1

orders: order_id (integer key), customer_id, ordered_at (UTC timestamptz), gross_amount, discount_amount, refund_amount (NUMERIC), updated_at.
customers: customer_id (integer key), country_code.
silver.orders adds net_amount = gross_amount - discount_amount - refund_amount.
gold.daily_sales: order_date (UTC), order_count, net_revenue.
target.orders_report retains order grain; target.daily_sales_report retains day grain.

Use fixed seed and dates for repeatable results. Record dataset/run scope on evidence. Validation rule IDs reference the lab's datasets; identifiers and schema ownership will be checked during catalog registration in Task 5. Current contracts do not implement persistence or a transition state machine.
