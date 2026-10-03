"""Built-in Task 2 quality suite for the orders pipeline."""
from qa.engine.contracts import (
    ColumnExpectation as C, CountMode, DatasetRegistry, DatasetSpec,
    NotNullRule, RecordCountRule, SchemaRule, UniquenessRule, ValidationSuite,
)

ORDERS_DATASETS = DatasetRegistry((
    DatasetSpec("bronze_orders", "bronze", "orders"),
    DatasetSpec("silver_orders", "silver", "orders"),
    DatasetSpec("gold_daily_sales", "gold", "daily_sales", count_mode=CountMode.SUM, count_column="order_count"),
    DatasetSpec("target_orders", "target", "orders_report"),
    DatasetSpec("target_daily_sales", "target", "daily_sales_report", count_mode=CountMode.SUM, count_column="order_count"),
))

_COMMON_RAW = (
    C("run_id", "uuid", False), C("order_id", "bigint", False),
    C("customer_id", "bigint", False), C("ordered_at", "timestamp with time zone", False),
    C("gross_amount", "numeric", False), C("discount_amount", "numeric", False),
    C("refund_amount", "numeric", False), C("updated_at", "timestamp with time zone", False),
)

ORDERS_SUITE = ValidationSuite("orders_basic_v1", (
    *(RecordCountRule(f"count_{dataset}", dataset) for dataset in ORDERS_DATASETS.ids),
    UniquenessRule("unique_bronze_order_id", "bronze_orders", ("order_id",)),
    UniquenessRule("unique_silver_order_id", "silver_orders", ("order_id",)),
    UniquenessRule("unique_gold_order_date", "gold_daily_sales", ("order_date",)),
    UniquenessRule("unique_target_order_id", "target_orders", ("order_id",)),
    UniquenessRule("unique_target_order_date", "target_daily_sales", ("order_date",)),
    NotNullRule("required_bronze", "bronze_orders", ("order_id", "customer_id", "ordered_at", "gross_amount", "discount_amount", "refund_amount", "updated_at")),
    NotNullRule("required_silver", "silver_orders", ("order_id", "customer_id", "ordered_at", "net_amount")),
    NotNullRule("required_gold", "gold_daily_sales", ("order_date", "order_count", "net_revenue")),
    NotNullRule("required_target_orders", "target_orders", ("order_id", "customer_id", "ordered_at", "net_amount")),
    NotNullRule("required_target_daily", "target_daily_sales", ("order_date", "order_count", "net_revenue")),
    SchemaRule("schema_bronze_orders", "bronze_orders", _COMMON_RAW + (C("ingested_at", "timestamp with time zone", False),)),
    SchemaRule("schema_silver_orders", "silver_orders", _COMMON_RAW[:-1] + (C("net_amount", "numeric", False), C("updated_at", "timestamp with time zone", False))),
    SchemaRule("schema_gold_daily_sales", "gold_daily_sales", (
        C("run_id", "uuid", False), C("order_date", "date", False), C("order_count", "bigint", False),
        C("gross_revenue", "numeric", False), C("net_revenue", "numeric", False))),
    SchemaRule("schema_target_orders", "target_orders", (
        C("run_id", "uuid", False), C("order_id", "bigint", False), C("customer_id", "bigint", False),
        C("ordered_at", "timestamp with time zone", False), C("net_amount", "numeric", False))),
    SchemaRule("schema_target_daily", "target_daily_sales", (
        C("run_id", "uuid", False), C("order_date", "date", False), C("order_count", "bigint", False),
        C("net_revenue", "numeric", False))),
))
