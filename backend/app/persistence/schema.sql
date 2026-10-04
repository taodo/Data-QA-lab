CREATE SCHEMA IF NOT EXISTS source;
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
CREATE SCHEMA IF NOT EXISTS target;
CREATE SCHEMA IF NOT EXISTS fault_workspace;
CREATE SCHEMA IF NOT EXISTS metadata;

CREATE TABLE IF NOT EXISTS source.customers (
    customer_id BIGINT PRIMARY KEY,
    country_code CHAR(2) NOT NULL
);

CREATE TABLE IF NOT EXISTS source.orders (
    order_id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES source.customers(customer_id),
    ordered_at TIMESTAMPTZ NOT NULL,
    gross_amount NUMERIC(14,2) NOT NULL CHECK (gross_amount >= 0),
    discount_amount NUMERIC(14,2) NOT NULL CHECK (discount_amount >= 0),
    refund_amount NUMERIC(14,2) NOT NULL CHECK (refund_amount >= 0),
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS metadata.pipeline_runs (
    run_id UUID PRIMARY KEY,
    pipeline_id TEXT NOT NULL,
    execution_status TEXT NOT NULL CHECK (execution_status IN ('PENDING','RUNNING','SUCCESS','FAILED')),
    data_quality_status TEXT NOT NULL DEFAULT 'NOT_RUN' CHECK (data_quality_status IN ('NOT_RUN','PASS','FAIL','ERROR')),
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    error TEXT
);

CREATE TABLE IF NOT EXISTS metadata.stage_runs (
    run_id UUID NOT NULL REFERENCES metadata.pipeline_runs(run_id),
    stage_name TEXT NOT NULL CHECK (stage_name IN ('SOURCE','BRONZE','SILVER','GOLD','TARGET')),
    execution_status TEXT NOT NULL CHECK (execution_status IN ('SUCCESS','FAILED')),
    row_count BIGINT CHECK (row_count >= 0),
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ NOT NULL,
    error TEXT,
    PRIMARY KEY (run_id, stage_name)
);

CREATE TABLE IF NOT EXISTS bronze.orders (
    run_id UUID NOT NULL REFERENCES metadata.pipeline_runs(run_id),
    order_id BIGINT NOT NULL,
    customer_id BIGINT NOT NULL,
    ordered_at TIMESTAMPTZ NOT NULL,
    gross_amount NUMERIC(14,2) NOT NULL,
    discount_amount NUMERIC(14,2) NOT NULL,
    refund_amount NUMERIC(14,2) NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (run_id, order_id)
);

CREATE TABLE IF NOT EXISTS silver.orders (
    run_id UUID NOT NULL REFERENCES metadata.pipeline_runs(run_id),
    order_id BIGINT NOT NULL,
    customer_id BIGINT NOT NULL,
    ordered_at TIMESTAMPTZ NOT NULL,
    gross_amount NUMERIC(14,2) NOT NULL,
    discount_amount NUMERIC(14,2) NOT NULL,
    refund_amount NUMERIC(14,2) NOT NULL,
    net_amount NUMERIC(14,2) NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (run_id, order_id)
);

CREATE TABLE IF NOT EXISTS gold.daily_sales (
    run_id UUID NOT NULL REFERENCES metadata.pipeline_runs(run_id),
    order_date DATE NOT NULL,
    order_count BIGINT NOT NULL CHECK (order_count >= 0),
    gross_revenue NUMERIC(18,2) NOT NULL,
    net_revenue NUMERIC(18,2) NOT NULL,
    PRIMARY KEY (run_id, order_date)
);

CREATE TABLE IF NOT EXISTS target.orders_report (
    run_id UUID NOT NULL REFERENCES metadata.pipeline_runs(run_id),
    order_id BIGINT NOT NULL,
    customer_id BIGINT NOT NULL,
    ordered_at TIMESTAMPTZ NOT NULL,
    net_amount NUMERIC(14,2) NOT NULL,
    PRIMARY KEY (run_id, order_id)
);

CREATE TABLE IF NOT EXISTS target.daily_sales_report (
    run_id UUID NOT NULL REFERENCES metadata.pipeline_runs(run_id),
    order_date DATE NOT NULL,
    order_count BIGINT NOT NULL,
    net_revenue NUMERIC(18,2) NOT NULL,
    PRIMARY KEY (run_id, order_date)
);

-- Deliberately relaxed copies used only by allowlisted fault scenarios.
-- Core target tables retain their production-like constraints and are never mutated.
CREATE TABLE IF NOT EXISTS fault_workspace.orders_report (
    run_id UUID NOT NULL REFERENCES metadata.pipeline_runs(run_id),
    order_id BIGINT,
    customer_id BIGINT,
    ordered_at TIMESTAMPTZ,
    net_amount NUMERIC(14,2)
);

CREATE INDEX IF NOT EXISTS idx_fault_orders_run
    ON fault_workspace.orders_report(run_id);

CREATE TABLE IF NOT EXISTS fault_workspace.daily_sales_report (
    run_id UUID NOT NULL REFERENCES metadata.pipeline_runs(run_id),
    order_date DATE,
    order_count BIGINT,
    net_revenue NUMERIC(18,2)
);

CREATE INDEX IF NOT EXISTS idx_fault_daily_run
    ON fault_workspace.daily_sales_report(run_id);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_started_at ON metadata.pipeline_runs(started_at DESC);

CREATE TABLE IF NOT EXISTS metadata.validation_runs (
    validation_run_id UUID PRIMARY KEY,
    pipeline_run_id UUID NOT NULL REFERENCES metadata.pipeline_runs(run_id),
    suite_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('RUNNING','NOT_RUN','PASS','FAIL','ERROR')),
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS metadata.validation_results (
    validation_run_id UUID NOT NULL REFERENCES metadata.validation_runs(validation_run_id),
    rule_id TEXT NOT NULL,
    dataset_id TEXT NOT NULL,
    check_type TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('PASS','FAIL','ERROR')),
    expected JSONB NOT NULL,
    actual JSONB NOT NULL,
    evidence JSONB NOT NULL,
    error TEXT,
    PRIMARY KEY (validation_run_id, rule_id)
);

CREATE INDEX IF NOT EXISTS idx_validation_runs_pipeline
    ON metadata.validation_runs(pipeline_run_id, started_at DESC);

ALTER TABLE metadata.validation_results
    DROP CONSTRAINT IF EXISTS validation_results_check_type_check;
ALTER TABLE metadata.validation_results
    ADD CONSTRAINT validation_results_check_type_check CHECK (
        check_type IN (
            'RECORD_COUNT','UNIQUENESS','NOT_NULL','SCHEMA',
            'KEY_RECONCILIATION','FIELD_RECONCILIATION'
        )
    );

CREATE TABLE IF NOT EXISTS metadata.fault_runs (
    fault_run_id UUID PRIMARY KEY,
    pipeline_run_id UUID NOT NULL REFERENCES metadata.pipeline_runs(run_id),
    scenario_id TEXT NOT NULL CHECK (
        scenario_id IN ('missing_order','duplicate_order','null_net_amount','wrong_net_amount')
    ),
    status TEXT NOT NULL CHECK (status IN ('APPLIED','RESET')),
    mutation_evidence JSONB NOT NULL,
    validation_run_id UUID REFERENCES metadata.validation_runs(validation_run_id),
    applied_at TIMESTAMPTZ NOT NULL,
    reset_at TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_one_active_fault_per_pipeline
    ON metadata.fault_runs(pipeline_run_id) WHERE status = 'APPLIED';

CREATE INDEX IF NOT EXISTS idx_fault_runs_applied_at
    ON metadata.fault_runs(applied_at DESC);

CREATE TABLE IF NOT EXISTS metadata.lab_sessions (
    session_id UUID PRIMARY KEY,
    lab_id TEXT NOT NULL,
    pipeline_run_id UUID NOT NULL REFERENCES metadata.pipeline_runs(run_id),
    mode TEXT NOT NULL CHECK (mode IN ('CHALLENGE','SANDBOX')),
    status TEXT NOT NULL CHECK (status IN ('ACTIVE','COMPLETED','REVEALED')),
    scenario_id TEXT NOT NULL CHECK (scenario_id IN ('missing_order','equal_count_swap')),
    snapshot_schema TEXT NOT NULL UNIQUE,
    hints_used INTEGER NOT NULL DEFAULT 0 CHECK (hints_used BETWEEN 0 AND 3),
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS metadata.lab_submissions (
    submission_id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES metadata.lab_sessions(session_id),
    sql_text TEXT NOT NULL,
    conclusion TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('PASS','FAIL','ERROR')),
    private_results JSONB NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS metadata.lab_queries (
    query_id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES metadata.lab_sessions(session_id),
    sql_text TEXT NOT NULL,
    result JSONB NOT NULL,
    executed_at TIMESTAMPTZ NOT NULL
);
