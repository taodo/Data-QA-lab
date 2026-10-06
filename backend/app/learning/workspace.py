"""Admin-owned snapshots. Identifiers are generated, never supplied as learner SQL."""
import re
from decimal import Decimal

from backend.app.learning.contracts import LabStateError
from backend.app.learning.advanced_profiles import ADVANCED_TABLES, ADVANCED_VARIANTS, SPECS


FOUNDATION_TABLES = ("source_orders", "target_orders", "gold_daily_sales", "target_daily_sales")
from backend.app.learning import etl, http_exercises, cloud, foundations
TABLES = FOUNDATION_TABLES + ADVANCED_TABLES + etl.TABLES + http_exercises.TABLES + cloud.TABLES + foundations.TABLES
VARIANTS = {"current", "clean", "clean_subset", "clean_zero", "missing", "swapped", "invalid_customer", "invalid_customer_last", "invalid_customer_two", "null_net_amount", "null_last", "null_two", "duplicate_order", "duplicate_last", "duplicate_twice", "duplicate_triple", "wrong_net_amount", "wrong_last", "wrong_two", "daily_wrong", "daily_missing", "mixed_order_faults"}
VARIANTS |= ADVANCED_VARIANTS | etl.VARIANTS | {"api_clean","api_shifted"} | {v for values in http_exercises.SCENARIOS.values() for v in values}
VARIANTS |= cloud.VARIANTS
VARIANTS |= foundations.VARIANTS


def require_schema(schema: str):
    if not re.fullmatch(r"learner_(?:session|query)_[0-9a-f]{32}", schema):
        raise ValueError("Not an owned learner workspace identifier")


def create_session_snapshot(connection, schema, run_id, scenario, lab_id="lab_001_record_count"):
    from psycopg import sql
    require_schema(schema)
    if lab_id in foundations.IDS:
        return foundations.create(connection, schema, lab_id, scenario)
    if lab_id in cloud.IDS:
        return cloud.create(connection, schema, lab_id, scenario)
    if lab_id in etl.SPECS:
        return etl.create(connection,schema,lab_id,scenario)
    if lab_id in http_exercises.IDS:
        return http_exercises.create(connection,schema,lab_id)
    if lab_id in SPECS:
        from backend.app.learning.advanced_workspace import create_snapshot
        return create_snapshot(connection, schema, lab_id, scenario)
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
    mutate_fixture(connection, schema, scenario)


def mutate_fixture(connection, schema, scenario):
    from psycopg import sql
    require_schema(schema)
    identifier = sql.Identifier(schema)
    if scenario == "clean":
        return
    if scenario in {"missing_order", "equal_count_swap", "missing", "swapped"}:
        return mutate_keys(connection, schema, "missing_order" if scenario in {"missing_order", "missing"} else "equal_count_swap")
    if scenario == "mixed_order_faults":
        for defect in ("missing_order", "null_last", "duplicate_order", "wrong_net_amount", "daily_wrong"):
            mutate_fixture(connection, schema, defect)
        return
    if scenario in {"daily_wrong", "daily_missing"}:
        statement = ("UPDATE {}.target_daily_sales SET net_revenue=net_revenue+0.01 WHERE order_date=(SELECT MIN(order_date) FROM {}.target_daily_sales)" if scenario == "daily_wrong" else "DELETE FROM {}.target_daily_sales WHERE order_date=(SELECT MIN(order_date) FROM {}.target_daily_sales)")
        connection.execute(sql.SQL(statement).format(identifier, identifier))
        return
    if scenario not in VARIANTS:
        raise ValueError("Unknown learning fixture")
    last = scenario.endswith("last")
    aggregate = sql.SQL("MAX" if last else "MIN")
    key = connection.execute(sql.SQL("SELECT {}(order_id) FROM {}.target_orders").format(aggregate, identifier)).fetchone()[0]
    if scenario.startswith("invalid_customer"):
        connection.execute(sql.SQL("UPDATE {}.target_orders SET customer_id=%s WHERE order_id=%s").format(identifier), (0 if last else -1, key))
    elif scenario.startswith("null"):
        connection.execute(sql.SQL("UPDATE {}.target_orders SET net_amount=NULL WHERE order_id=%s").format(identifier), (key,))
    elif scenario.startswith("wrong"):
        connection.execute(sql.SQL("UPDATE {}.target_orders SET net_amount=net_amount+%s WHERE order_id=%s").format(identifier), (Decimal("-0.01" if last else "0.01"), key))
    elif scenario.startswith("duplicate"):
        connection.execute(sql.SQL("INSERT INTO {}.target_orders SELECT * FROM {}.target_orders WHERE order_id=%s").format(identifier, identifier), (key,))
    else:
        raise ValueError("Unknown learning fixture")
    if scenario.endswith("two"):
        mutate_fixture(connection, schema, {"invalid_customer_two": "invalid_customer_last", "null_two": "null_last", "wrong_two": "wrong_last"}[scenario])
    if scenario == "duplicate_twice":
        # Duplicate a different key; grading counts duplicate keys, not extra rows.
        mutate_fixture(connection, schema, "duplicate_last")
    if scenario == "duplicate_triple":
        mutate_fixture(connection, schema, "duplicate_order")


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


def snapshot_tables(connection, schema):
    """Discover only operator-owned allowlisted tables; old four-table sessions remain valid."""
    from backend.app.learning.contracts import SqlSecurityError
    require_schema(schema)
    names = tuple(row[0] for row in connection.execute(
        "SELECT tablename FROM pg_tables WHERE schemaname=%s ORDER BY tablename", (schema,)).fetchall())
    if not names or not set(names) <= set(TABLES):
        raise SqlSecurityError("Workspace table allowlist does not match")
    if "cloud_context" in names:
        rows=cloud.execute(connection,schema,"SELECT lab_id FROM {s}.cloud_context").fetchall()
        expected = foundations.table_names(rows[0][0]) if len(rows)==1 and rows[0][0] in foundations.IDS else cloud.TABLES
        if len(rows)!=1 or rows[0][0] not in (*cloud.IDS,*foundations.IDS) or set(names)!=set(expected):
            raise SqlSecurityError("Cloud workspace does not match")
    elif "etl_context" in names:
        lab_id=etl.execute(connection,schema,"SELECT lab_id FROM {s}.etl_context").fetchall()
        if len(lab_id)!=1 or lab_id[0][0] not in etl.SPECS or set(names)!=set(etl.TABLES):
            raise SqlSecurityError("ETL workspace does not match")
    elif "api_context" in names:
        from psycopg import sql
        rows=connection.execute(sql.SQL("SELECT lab_id FROM {}.api_context").format(sql.Identifier(schema))).fetchall()
        if len(rows)!=1 or rows[0][0] not in http_exercises.IDS or set(names)!=set(http_exercises.TABLES):
            raise SqlSecurityError("API workspace does not match")
    elif "lab_context" in names:
        from psycopg import sql
        rows = connection.execute(sql.SQL("SELECT lab_id FROM {}.lab_context").format(sql.Identifier(schema))).fetchall()
        if len(rows)!=1 or rows[0][0] not in SPECS or set(names)!=set(SPECS[rows[0][0]][3]):
            raise SqlSecurityError("Advanced workspace does not match its lesson")
    elif set(names)!=set(FOUNDATION_TABLES):
        raise SqlSecurityError("Foundation workspace does not match")
    return names


def populate_query_snapshot(connection, destination, snapshot, variant):
    from psycopg import sql
    require_schema(destination)
    require_schema(snapshot)
    if variant not in VARIANTS:
        raise ValueError("Unknown grading fixture")
    connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(destination)))
    for table in snapshot_tables(connection, snapshot):
        connection.execute(sql.SQL("CREATE TABLE {}.{} AS TABLE {}.{}").format(
            sql.Identifier(destination), sql.Identifier(table),
            sql.Identifier(snapshot), sql.Identifier(table)))
    if variant == "current":
        return
    tables = snapshot_tables(connection, destination)
    if "cloud_context" in tables:
        lab_id=cloud.execute(connection,destination,"SELECT lab_id FROM {s}.cloud_context").fetchone()[0]
        if lab_id in foundations.IDS:
            return foundations.populate(connection,destination,lab_id,variant)
        return cloud.populate(connection,destination,lab_id,variant)
    if "etl_context" in tables:
        lab_id=etl.execute(connection,destination,"SELECT lab_id FROM {s}.etl_context").fetchone()[0]
        return etl.populate(connection,destination,lab_id,variant)
    if "api_context" in tables:
        raise ValueError("Use the HTTP grader for API exercises")
    if "lab_context" in tables:
        from backend.app.learning.advanced_workspace import populate
        lab_id=connection.execute(sql.SQL("SELECT lab_id FROM {}.lab_context").format(sql.Identifier(destination))).fetchone()[0]
        return populate(connection,destination,lab_id,variant)
    if variant == "clean_subset":
        connection.execute(sql.SQL(
            "DELETE FROM {}.source_orders WHERE order_id NOT IN "
            "(SELECT order_id FROM {}.source_orders ORDER BY order_id LIMIT "
            "(SELECT GREATEST(1, COUNT(*) / 2) FROM {}.source_orders))"
        ).format(*[sql.Identifier(destination)] * 3))
    if variant == "clean_zero":
        connection.execute(sql.SQL("UPDATE {}.source_orders SET gross_amount=0,discount_amount=0,refund_amount=0 WHERE order_id=(SELECT MIN(order_id) FROM {}.source_orders)").format(sql.Identifier(destination), sql.Identifier(destination)))
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
    if variant not in {"clean", "clean_subset", "clean_zero"}:
        mutate_fixture(connection, destination, variant)
