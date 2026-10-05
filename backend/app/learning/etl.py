"""Real, session-isolated ETL batches with independent SQL verification contracts."""

from datetime import datetime, timezone
from decimal import Decimal
import re
from psycopg import sql

DDL = {
    "etl_context": "lab_id text, as_of timestamptz, batch_no integer",
    "etl_customers": "customer_code text, customer_id bigint",
    "etl_source": "order_id bigint, customer_code text, gross_text text, discount_text text, arrived_batch integer, event_id bigint",
    "etl_target": "order_id bigint, customer_id bigint, net_amount numeric(18,2), event_id bigint",
    "etl_rejects": "order_id bigint, reason text",
    "etl_steps": "step_no integer, operation text, execution_status text, target_rows integer, rejected_rows integer, checkpoint integer",
}
TABLES = tuple(DDL)
MAPPING = """WITH expected AS (SELECT s.order_id,c.customer_id FROM etl_source s JOIN etl_customers c USING(customer_code))
SELECT COUNT(*) AS violation_count FROM expected e FULL JOIN etl_target t USING(order_id)
WHERE e.order_id IS NULL OR t.order_id IS NULL OR e.customer_id IS DISTINCT FROM t.customer_id"""
TRANSFORM = """SELECT COUNT(*) AS violation_count FROM etl_source s FULL JOIN etl_target t USING(order_id)
WHERE s.order_id IS NULL OR t.order_id IS NULL OR t.net_amount IS DISTINCT FROM (s.gross_text::numeric-s.discount_text::numeric)"""
VALID = "gross_text ~ '^[0-9]+([.][0-9]{1,2})?$' AND discount_text ~ '^[0-9]+([.][0-9]{1,2})?$'"
QUARANTINE = f"""WITH valid AS (SELECT order_id FROM etl_source WHERE {VALID}),
invalid AS (SELECT order_id FROM etl_source WHERE NOT ({VALID})),
accepted AS (SELECT 1 FROM valid v FULL JOIN etl_target t USING(order_id) WHERE v.order_id IS NULL OR t.order_id IS NULL),
rejected AS (SELECT 1 FROM invalid i FULL JOIN etl_rejects r USING(order_id) WHERE i.order_id IS NULL OR r.order_id IS NULL OR r.reason IS DISTINCT FROM 'INVALID_AMOUNT'),
duplicates AS (SELECT order_id FROM etl_rejects GROUP BY order_id HAVING COUNT(*)>1)
SELECT (SELECT COUNT(*) FROM accepted)+(SELECT COUNT(*) FROM rejected)+(SELECT COUNT(*) FROM duplicates) AS violation_count"""
REPLAY = """WITH ranked AS (SELECT s.*,ROW_NUMBER() OVER(PARTITION BY order_id ORDER BY event_id DESC) rn
 FROM etl_source s CROSS JOIN etl_context c WHERE arrived_batch<=c.batch_no),
expected AS (SELECT * FROM ranked WHERE rn=1), mismatches AS (
 SELECT 1 FROM expected e FULL JOIN etl_target t USING(order_id)
 WHERE e.order_id IS NULL OR t.order_id IS NULL OR e.event_id IS DISTINCT FROM t.event_id
 OR t.net_amount IS DISTINCT FROM (e.gross_text::numeric-e.discount_text::numeric)),
duplicates AS (SELECT order_id FROM etl_target GROUP BY order_id HAVING COUNT(*)>1)
SELECT (SELECT COUNT(*) FROM mismatches)+(SELECT COUNT(*) FROM duplicates) AS violation_count"""
RECOVERY = f"""SELECT ({TRANSFORM}) + (SELECT COUNT(*) FROM etl_steps WHERE step_no=(SELECT MAX(step_no) FROM etl_steps)
 AND (execution_status IS DISTINCT FROM 'SUCCESS' OR checkpoint IS DISTINCT FROM 1)) AS violation_count"""
SPECS = {
    "lab_014_etl_mapping": (("etl_wrong_mapping", "etl_missing"), MAPPING),
    "lab_015_etl_transform": (("etl_rounding", "etl_null_amount"), TRANSFORM),
    "lab_016_etl_quarantine": (("etl_drop_reject", "etl_accept_invalid"), QUARANTINE),
    "lab_017_etl_replay": (("etl_append", "etl_skip_late"), REPLAY),
    "lab_018_etl_recovery": (("etl_failed", "etl_partial_publish"), RECOVERY),
}
VARIANTS = {v for scenarios, _ in SPECS.values() for v in scenarios} | {
    "etl_clean",
    "etl_shifted",
}


def execute(c, s, statement, params=None):
    from backend.app.learning.workspace import require_schema

    require_schema(s)
    return c.execute(sql.SQL(statement).format(s=sql.Identifier(s)), params)


def insert(c, s, table, rows):
    if table not in DDL:
        raise ValueError("Unknown ETL table")
    for row in rows:
        c.execute(
            sql.SQL("INSERT INTO {}.{} VALUES ({})").format(
                sql.Identifier(s),
                sql.Identifier(table),
                sql.SQL(",").join(sql.Placeholder() for _ in row),
            ),
            row,
        )


def create(c, s, lab_id, variant):
    from backend.app.learning.workspace import require_schema

    require_schema(s)
    c.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(s)))
    for table, ddl in DDL.items():
        c.execute(
            sql.SQL("CREATE TABLE {}.{} ({})").format(
                sql.Identifier(s), sql.Identifier(table), sql.SQL(ddl)
            )
        )
    populate(c, s, lab_id, variant)


def populate(c, s, lab_id, variant):
    if lab_id not in SPECS or variant not in (
        "clean",
        "etl_clean",
        "etl_shifted",
        *SPECS[lab_id][0],
    ):
        raise ValueError("Wrong ETL fixture")
    for table in DDL:
        c.execute(
            sql.SQL("TRUNCATE {}.{}").format(sql.Identifier(s), sql.Identifier(table))
        )
    offset = 10000 if variant == "etl_shifted" else 0
    ids = [offset + v for v in (101, 203, 307, 409)]
    insert(
        c,
        s,
        "etl_context",
        [
            (
                lab_id,
                datetime(2026, 10, 1, tzinfo=timezone.utc),
                3 if lab_id == "lab_017_etl_replay" else 1,
            )
        ],
    )
    insert(c, s, "etl_customers", [("C-A", 41), ("C-B", 52)])
    rows = [
        (key, "C-A" if i % 2 == 0 else "C-B", amount, "0.01", 1, i + 1)
        for i, (key, amount) in enumerate(
            zip(ids, ("10.01", "0.01", "30.45", "100.99"))
        )
    ]
    if lab_id == "lab_016_etl_quarantine":
        rows[1] = (ids[1], "C-B", "oops", "0.01", 1, 2)
        rows[3] = (ids[3], "C-B", "1,23", "0.01", 1, 4)
    if lab_id == "lab_017_etl_replay":
        rows[2] = (*rows[2][:4], 2, 3)
        rows[3] = (*rows[3][:4], 3, 4)
        rows.append((ids[0], "C-A", "12.05", "0.01", 2, 5))
    insert(c, s, "etl_source", rows)
    _load(c, s, variant)
    if variant == "etl_wrong_mapping":
        execute(
            c,
            s,
            "UPDATE {s}.etl_target SET customer_id=52 WHERE order_id=%s",
            (ids[0],),
        )
    if variant == "etl_missing":
        execute(c, s, "DELETE FROM {s}.etl_target WHERE order_id=%s", (ids[-1],))
    if variant == "etl_rounding":
        execute(
            c,
            s,
            "UPDATE {s}.etl_target SET net_amount=ROUND(net_amount) WHERE order_id=%s",
            (ids[-1],),
        )
    if variant == "etl_null_amount":
        execute(
            c,
            s,
            "UPDATE {s}.etl_target SET net_amount=NULL WHERE order_id=%s",
            (ids[-1],),
        )
    if variant == "etl_drop_reject":
        execute(c, s, "DELETE FROM {s}.etl_rejects WHERE order_id=%s", (ids[-1],))
    if variant == "etl_accept_invalid":
        insert(c, s, "etl_target", [(ids[1], 52, Decimal("0.00"), 2)])
    if variant == "etl_failed":
        execute(c, s, "DELETE FROM {s}.etl_target")
        execute(c, s, "UPDATE {s}.etl_steps SET execution_status='FAILED',checkpoint=0")
    if variant == "etl_partial_publish":
        execute(c, s, "DELETE FROM {s}.etl_target WHERE order_id=%s", (ids[-1],))
    execute(
        c,
        s,
        "UPDATE {s}.etl_steps SET target_rows=(SELECT COUNT(*) FROM {s}.etl_target),rejected_rows=(SELECT COUNT(*) FROM {s}.etl_rejects)",
    )


def _load(c, s, policy):
    """Execute the documented batch policy against actual persisted Source rows."""
    lab_id, batch = execute(
        c, s, "SELECT lab_id,batch_no FROM {s}.etl_context"
    ).fetchone()
    rows = execute(
        c,
        s,
        "SELECT order_id,customer_code,gross_text,discount_text,arrived_batch,event_id FROM {s}.etl_source WHERE arrived_batch<=%s ORDER BY event_id",
        (batch,),
    ).fetchall()
    customers = dict(
        execute(
            c, s, "SELECT customer_code,customer_id FROM {s}.etl_customers"
        ).fetchall()
    )
    for key, code, gross, discount, arrival, event in rows:
        if not all(
            re.fullmatch(r"[0-9]+(?:\.[0-9]{1,2})?", text) for text in (gross, discount)
        ):
            if not execute(
                c, s, "SELECT 1 FROM {s}.etl_rejects WHERE order_id=%s", (key,)
            ).fetchone():
                insert(c, s, "etl_rejects", [(key, "INVALID_AMOUNT")])
            continue
        if policy == "etl_skip_late" and arrival > 1 and key == rows[0][0]:
            continue
        current = execute(
            c, s, "SELECT MAX(event_id) FROM {s}.etl_target WHERE order_id=%s", (key,)
        ).fetchone()[0]
        if policy != "etl_append" and current is not None and current >= event:
            continue
        if policy != "etl_append":
            execute(c, s, "DELETE FROM {s}.etl_target WHERE order_id=%s", (key,))
        insert(
            c,
            s,
            "etl_target",
            [(key, customers[code], Decimal(gross) - Decimal(discount), event)],
        )
    step = execute(
        c, s, "SELECT COALESCE(MAX(step_no),0)+1 FROM {s}.etl_steps"
    ).fetchone()[0]
    target = execute(c, s, "SELECT COUNT(*) FROM {s}.etl_target").fetchone()[0]
    rejects = execute(c, s, "SELECT COUNT(*) FROM {s}.etl_rejects").fetchone()[0]
    insert(c, s, "etl_steps", [(step, "RUN", "SUCCESS", target, rejects, batch)])


def advance(c, s, policy, action):
    lab_id, batch = execute(
        c, s, "SELECT lab_id,batch_no FROM {s}.etl_context"
    ).fetchone()
    count = execute(c, s, "SELECT COUNT(*) FROM {s}.etl_steps").fetchone()[0]
    if count >= 100 and action != "RESET":
        raise ValueError("Reset after 100 steps")
    if action == "RESET":
        for table in ("etl_target", "etl_rejects", "etl_steps"):
            c.execute(
                sql.SQL("TRUNCATE {}.{}").format(
                    sql.Identifier(s), sql.Identifier(table)
                )
            )
        execute(c, s, "UPDATE {s}.etl_context SET batch_no=0")
    elif action in ("NEXT", "REPLAY") and lab_id == "lab_017_etl_replay":
        if action == "NEXT":
            execute(c, s, "UPDATE {s}.etl_context SET batch_no=LEAST(batch_no+1,3)")
        _load(c, s, policy)
    elif action in ("RUN", "RECOVER"):
        execute(
            c,
            s,
            "UPDATE {s}.etl_context SET batch_no=%s",
            (3 if lab_id == "lab_017_etl_replay" else 1,),
        )
        _load(c, s, policy)
        if policy == "etl_partial_publish":
            execute(
                c,
                s,
                "DELETE FROM {s}.etl_target WHERE order_id=(SELECT MAX(order_id) FROM {s}.etl_target)",
            )
    else:
        raise ValueError("Unsupported ETL action")
    # Evidence counts reflect the actual result, including intentional defects.
    execute(
        c,
        s,
        "UPDATE {s}.etl_steps SET operation=%s,target_rows=(SELECT COUNT(*) FROM {s}.etl_target),rejected_rows=(SELECT COUNT(*) FROM {s}.etl_rejects) WHERE step_no=(SELECT MAX(step_no) FROM {s}.etl_steps)",
        (action,),
    )


def state(c, s):
    batch = execute(c, s, "SELECT batch_no FROM {s}.etl_context").fetchone()[0]
    rows = execute(
        c,
        s,
        "SELECT step_no,operation,execution_status,target_rows,rejected_rows,checkpoint FROM {s}.etl_steps ORDER BY step_no DESC LIMIT 20",
    ).fetchall()
    return {
        "batch_no": batch,
        "steps": [
            dict(
                zip(
                    (
                        "step_no",
                        "operation",
                        "execution_status",
                        "target_rows",
                        "rejected_rows",
                        "checkpoint",
                    ),
                    r,
                )
            )
            for r in reversed(rows)
        ],
    }
