CREATE SCHEMA IF NOT EXISTS source;
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
CREATE SCHEMA IF NOT EXISTS target;
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

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_started_at ON metadata.pipeline_runs(started_at DESC);
