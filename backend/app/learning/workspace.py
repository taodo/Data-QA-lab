"""Admin-owned snapshots. Identifiers are generated, never supplied as learner SQL."""
import re

from backend.app.learning.contracts import LabStateError


TABLES = ("source_orders", "target_orders", "gold_daily_sales", "target_daily_sales")
VARIANTS = {"current", "clean", "clean_subset", "missing", "swapped"}


def require_schema(schema: str):
    if not re.fullmatch(r"learner_(?:session|query)_[0-9a-f]{32}", schema):
        raise ValueError("Not an owned learner workspace identifier")


def create_session_snapshot(connection, schema, run_id, scenario):
    from psycopg import sql
    require_schema(schema)
    connection.execute(sql.SQL("CREATE SCHEMA {};").format(sql.Identifier(schema)))
    connection.execute(sql.SQL(
        "CREATE TABLE {}.source_orders AS SELECT order_id, customer_id, ordered_at, "
        "gross_amount, discount_amount, refund_amount, updated_at FROM bronze.orders WHERE run_id = %s"
    ).format(sql.Identifier(schema)), (run_id,))
    connection.execute(sql.SQL(
        "CREATE TABLE {}.target_orders AS SELECT order_id, customer_id, ordered_at, net_amount "
        "FROM target.orders_report WHERE run_id = %s"
    ).format(sql.Identifier(schema)), (run_id,))
    for name, original in (("gold_daily_sales", "gold.daily_sales"),
                           ("target_daily_sales", "target.daily_sales_report")):
        connection.execute(sql.SQL(
            "CREATE TABLE {}.{} AS SELECT order_date, order_count, net_revenue FROM {} WHERE run_id = %s"
        ).format(sql.Identifier(schema), sql.Identifier(name),
                 sql.Identifier(*original.split("."))), (run_id,))
    count = connection.execute(sql.SQL("SELECT COUNT(*) FROM {}.source_orders").format(
        sql.Identifier(schema))).fetchone()[0]
    if count < 2:
        raise LabStateError("Lab 001 needs a successful run with at least two orders")
    mutate_keys(connection, schema, scenario)


def mutate_keys(connection, schema, scenario):
    from psycopg import sql
    require_schema(schema)
    if scenario not in {"missing_order", "equal_count_swap"}:
        raise ValueError("Unknown completeness scenario")
    connection.execute(sql.SQL(
        "DELETE FROM {}.target_orders WHERE order_id = "
        "(SELECT MIN(order_id) FROM {}.target_orders)"
    ).format(sql.Identifier(schema), sql.Identifier(schema)))
    if scenario == "equal_count_swap":
        connection.execute(sql.SQL(
            "INSERT INTO {}.target_orders SELECT "
            "(SELECT MAX(order_id) + 1 FROM {}.source_orders), customer_id, ordered_at, net_amount "
            "FROM {}.target_orders ORDER BY order_id LIMIT 1"
        ).format(sql.Identifier(schema), sql.Identifier(schema), sql.Identifier(schema)))


def populate_query_snapshot(connection, destination, snapshot, variant):
    from psycopg import sql
    require_schema(destination)
    require_schema(snapshot)
    if variant not in VARIANTS:
        raise ValueError("Unknown grading fixture")
    connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(destination)))
    for table in TABLES:
        connection.execute(sql.SQL("CREATE TABLE {}.{} AS TABLE {}.{}").format(
            sql.Identifier(destination), sql.Identifier(table),
            sql.Identifier(snapshot), sql.Identifier(table)))
    if variant == "current":
        return
    if variant == "clean_subset":
        connection.execute(sql.SQL(
            "DELETE FROM {}.source_orders WHERE order_id NOT IN "
            "(SELECT order_id FROM {}.source_orders ORDER BY order_id LIMIT "
            "(SELECT GREATEST(1, COUNT(*) / 2) FROM {}.source_orders))"
        ).format(*[sql.Identifier(destination)] * 3))
    connection.execute(sql.SQL("TRUNCATE {}.target_orders").format(sql.Identifier(destination)))
    connection.execute(sql.SQL(
        "INSERT INTO {}.target_orders SELECT order_id, customer_id, ordered_at, "
        "gross_amount - discount_amount - refund_amount FROM {}.source_orders"
    ).format(sql.Identifier(destination), sql.Identifier(destination)))
    # Recompute day-grain baselines so every clean fixture is internally consistent.
    for table in ("gold_daily_sales", "target_daily_sales"):
        connection.execute(sql.SQL("TRUNCATE {}.{}").format(
            sql.Identifier(destination), sql.Identifier(table)))
        connection.execute(sql.SQL(
            "INSERT INTO {}.{} SELECT (ordered_at AT TIME ZONE 'UTC')::date, COUNT(*), "
            "SUM(gross_amount - discount_amount - refund_amount) FROM {}.source_orders "
            "GROUP BY (ordered_at AT TIME ZONE 'UTC')::date"
        ).format(sql.Identifier(destination), sql.Identifier(table), sql.Identifier(destination)))
    if variant in {"missing", "swapped"}:
        mutate_keys(connection, destination,
                    "missing_order" if variant == "missing" else "equal_count_swap")
