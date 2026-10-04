"""Small deterministic PostgreSQL teaching fixtures and a real batch/replay simulator.

Only operator-owned session/query schemas are written. Learners still receive SELECT
only. The fixed fixture clock makes freshness and late-arrival results reproducible.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from backend.app.learning.advanced_profiles import SPECS

AS_OF = datetime(2026, 1, 10, 12, tzinfo=timezone.utc)
DDL = {
 "lab_context": "lab_id text NOT NULL, as_of timestamptz NOT NULL",
 "order_lines": "order_id bigint, line_id bigint, net_amount numeric(14,2)",
 "order_payments": "order_id bigint, payment_id bigint, paid_amount numeric(14,2)",
 "target_order_totals": "order_id bigint, net_amount numeric(14,2)",
 "source_order_events": "event_id bigint, order_id bigint, updated_at timestamptz, net_amount numeric(14,2)",
 "target_current_orders": "event_id bigint, order_id bigint, updated_at timestamptz, net_amount numeric(14,2)",
 "source_time_orders": "order_id bigint, ordered_at timestamptz, net_amount numeric(14,2)",
 "target_utc_daily": "order_date date, order_count bigint, net_revenue numeric(18,2)",
 "incremental_events": "event_id bigint, order_id bigint, event_at timestamptz, arrived_at timestamptz, net_amount numeric(14,2), batch_no integer",
 "incremental_target": "event_id bigint, order_id bigint, event_at timestamptz, net_amount numeric(14,2)",
 "incremental_steps": "step_no integer, batch_no integer, operation text, execution_status text, applied_events integer, target_rows integer, watermark timestamptz",
 "freshness_requirements": "dataset_id text, as_of timestamptz, sla_minutes integer",
 "freshness_observations": "dataset_id text, last_success_at timestamptz, last_event_at timestamptz, execution_status text",
 "source_customer_changes": "event_id bigint, customer_id bigint, effective_at timestamptz, tier text",
 "target_customers_current": "event_id bigint, customer_id bigint, effective_at timestamptz, tier text",
 "target_customer_history": "version_id bigint, customer_id bigint, tier text, valid_from timestamptz, valid_to timestamptz, is_current boolean",
}


def execute(connection, schema, statement, params=None):
    from psycopg import sql
    from backend.app.learning.workspace import require_schema
    require_schema(schema)
    return connection.execute(sql.SQL(statement).format(s=sql.Identifier(schema)), params)


def insert(connection, schema, table, rows):
    from psycopg import sql
    if table not in DDL:
        raise ValueError("Unknown advanced dataset")
    if not rows:
        return
    with connection.cursor() as cursor:
        cursor.executemany(sql.SQL("INSERT INTO {}.{} VALUES ({})").format(
            sql.Identifier(schema), sql.Identifier(table),
            sql.SQL(",").join(sql.Placeholder() for _ in rows[0])), rows)


def create_snapshot(connection, schema, lab_id, scenario):
    from psycopg import sql
    from backend.app.learning.workspace import require_schema
    require_schema(schema)
    connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    for table in SPECS[lab_id][3]:
        connection.execute(sql.SQL("CREATE TABLE {}.{} ({})").format(
            sql.Identifier(schema), sql.Identifier(table), sql.SQL(DDL[table])))
    populate(connection, schema, lab_id, scenario)


def populate(connection, schema, lab_id, variant):
    """Rebuild clean independent data before applying exactly one allowlisted policy."""
    from psycopg import sql
    spec = SPECS[lab_id]
    if variant not in (*spec[1], *spec[0], "clean"):
        raise ValueError("Fixture does not belong to this lesson")
    for table in spec[3]:
        connection.execute(sql.SQL("TRUNCATE {}.{}").format(sql.Identifier(schema), sql.Identifier(table)))
    shifted = variant == "adv_shifted"
    clock = AS_OF + timedelta(days=5 if shifted else 0)
    keys = [value + (10000 if shifted else 0) for value in (101,203,307,409)]
    insert(connection,schema,"lab_context",[(lab_id,clock)])
    if lab_id == "lab_007_join_grain":
        _join(connection,schema,keys,variant)
    elif lab_id == "lab_008_latest_version":
        _latest(connection,schema,keys,clock,variant)
    elif lab_id == "lab_009_utc_dates":
        _utc(connection,schema,keys,clock,variant)
    elif lab_id == "lab_010_incremental":
        _incremental(connection,schema,keys,clock,variant)
    elif lab_id == "lab_011_freshness":
        _freshness(connection,schema,clock,variant,shifted)
    elif lab_id in {"lab_012_scd_type1","lab_013_scd_type2"}:
        _customers(connection,schema,keys,clock,variant,lab_id)
    else:
        raise ValueError("Unknown advanced lesson")


def _join(connection,schema,keys,variant):
    a,b,c,_=keys
    lines=[(a,1,Decimal("10.01")),(a,2,Decimal("20.02")),(b,1,Decimal("7.00")),(c,1,Decimal("0.00"))]
    payments=[(a,1,Decimal("15.00")),(a,2,Decimal("15.03")),(b,1,Decimal("7.00")),(c,1,Decimal("0.00"))]
    insert(connection,schema,"order_lines",lines)
    insert(connection,schema,"order_payments",payments)
    insert(connection,schema,"target_order_totals",[(a,Decimal("30.03")),(b,Decimal("7.00")),(c,Decimal("0.00"))])
    if variant in {"join_fanout","join_fanout_two"}:
        execute(connection,schema,"UPDATE {s}.target_order_totals SET net_amount=net_amount*2 WHERE order_id=%s",(a,))
        if variant=="join_fanout_two":
            execute(connection,schema,"UPDATE {s}.target_order_totals SET net_amount=net_amount+0.01 WHERE order_id=%s",(b,))
    elif variant=="join_missing":
        execute(connection,schema,"DELETE FROM {s}.target_order_totals WHERE order_id=%s",(b,))
    elif variant=="join_unexpected":
        insert(connection,schema,"target_order_totals",[(keys[3],Decimal("8.00"))])
    elif variant=="join_null":
        execute(connection,schema,"UPDATE {s}.target_order_totals SET net_amount=NULL WHERE order_id=%s",(a,))
    # join_zero is a clean regression fixture: zero and repeated line amounts are valid.
    elif variant=="join_zero":
        insert(connection,schema,"order_lines",[(b,2,Decimal("7.00"))])
        execute(connection,schema,"UPDATE {s}.target_order_totals SET net_amount=14.00 WHERE order_id=%s",(b,))


def _latest(connection,schema,keys,clock,variant):
    a,b,c,_=keys
    old=clock-timedelta(days=2);new=clock-timedelta(days=1)
    rows=[(1,a,old,Decimal("10.00")),(2,a,new,Decimal("11.01")),
          (3,b,new,Decimal("20.00")),(4,b,new,Decimal("21.01")),(5,c,old,Decimal("0.00"))]
    if keys[0]>10000:
        rows=[(event+1000,key,stamp,amount) for event,key,stamp,amount in rows]
    insert(connection,schema,"source_order_events",rows)
    insert(connection,schema,"target_current_orders",[rows[1],rows[3],rows[4]])
    if variant in {"latest_stale","latest_stale_two"}:
        execute(connection,schema,"UPDATE {s}.target_current_orders SET event_id=1,updated_at=%s,net_amount=10 WHERE order_id=%s",(old,a))
        if variant=="latest_stale_two":
            execute(connection,schema,"UPDATE {s}.target_current_orders SET event_id=3,net_amount=20 WHERE order_id=%s",(b,))
    elif variant=="latest_tie":
        execute(connection,schema,"UPDATE {s}.target_current_orders SET event_id=3,net_amount=20 WHERE order_id=%s",(b,))
    elif variant=="latest_missing":
        execute(connection,schema,"DELETE FROM {s}.target_current_orders WHERE order_id=%s",(c,))
    elif variant=="latest_null":
        execute(connection,schema,"UPDATE {s}.target_current_orders SET net_amount=NULL WHERE order_id=%s",(a,))


def _utc(connection,schema,keys,clock,variant):
    # Two rows straddle UTC midnight; another crosses year-end in +07 display time.
    shift=clock-AS_OF
    timestamps=[datetime(2025,12,31,23,30,tzinfo=timezone.utc),datetime(2026,1,1,0,30,tzinfo=timezone.utc),
                datetime(2026,1,1,23,30,tzinfo=timezone.utc),datetime(2026,1,2,0,0,tzinfo=timezone.utc)]
    insert(connection,schema,"source_time_orders",[(key,stamp+shift,Decimal(amount)) for key,stamp,amount in zip(keys,timestamps,("10.01","0.00","20.02","7.00"),strict=True)])
    zone="Asia/Bangkok" if variant=="utc_local_day" else "UTC"
    execute(connection,schema,"INSERT INTO {s}.target_utc_daily SELECT (ordered_at AT TIME ZONE %s)::date,COUNT(*),SUM(net_amount) FROM {s}.source_time_orders GROUP BY (ordered_at AT TIME ZONE %s)::date",(zone,zone))
    if variant=="utc_missing":
        execute(connection,schema,"DELETE FROM {s}.target_utc_daily WHERE order_date=(SELECT MIN(order_date) FROM {s}.target_utc_daily)")
    elif variant=="utc_null":
        execute(connection,schema,"UPDATE {s}.target_utc_daily SET net_revenue=NULL WHERE order_date=(SELECT MAX(order_date) FROM {s}.target_utc_daily)")


def merge_versions(existing, incoming):
    """Keyed upsert: greatest (event_at, event_id) wins, independent of arrival order."""
    winners={}
    for row in (*existing,*incoming):
        event_id,order_id,event_at,amount=row
        old=winners.get(order_id)
        if old is None or (event_at,event_id)>(old[2],old[0]):
            winners[order_id]=row
    return [winners[key] for key in sorted(winners)]


def _incremental(connection,schema,keys,clock,variant):
    a,b,c,d=keys
    rows=[(1,a,clock-timedelta(hours=72),clock-timedelta(hours=48),Decimal("10.00"),1),
          (2,b,clock-timedelta(hours=72),clock-timedelta(hours=48),Decimal("20.00"),1),
          (3,a,clock-timedelta(hours=36),clock-timedelta(hours=24),Decimal("11.01"),2),
          (4,c,clock-timedelta(hours=36),clock-timedelta(hours=24),Decimal("0.00"),2),
          (5,d,clock-timedelta(hours=60),clock,Decimal("40.04"),3),
          (6,b,clock-timedelta(hours=48),clock,Decimal("21.01"),3),
          (7,c,clock-timedelta(hours=36),clock,Decimal("0.01"),3),
          (8,a,clock-timedelta(hours=96),clock,Decimal("9.00"),3)]
    if keys[0]>10000:
        rows=[(event+1000,key,stamp,arrival,amount,batch) for event,key,stamp,arrival,amount,batch in rows]
    insert(connection,schema,"incremental_events",rows)
    reset_simulation(connection,schema)
    for action in ("NEXT","NEXT","REPLAY","NEXT"):
        advance_simulation(connection,schema,variant,action)


def reset_simulation(connection,schema):
    execute(connection,schema,"TRUNCATE {s}.incremental_target,{s}.incremental_steps")
    start=execute(connection,schema,"SELECT MIN(arrived_at)-INTERVAL '1 second' FROM {s}.incremental_events").fetchone()[0]
    execute(connection,schema,"UPDATE {s}.lab_context SET as_of=%s",(start,))


def advance_simulation(connection,schema,policy,action):
    """Persist each actual execution step, including replay, atomically with its target."""
    from backend.app.learning.contracts import LabStateError
    if policy not in (*SPECS["lab_010_incremental"][0],*SPECS["lab_010_incremental"][1]):
        raise ValueError("Unknown incremental policy")
    if action=="RESET":
        reset_simulation(connection,schema)
        return
    if action not in {"NEXT","REPLAY"}:
        raise ValueError("Unknown simulation action")
    previous=execute(connection,schema,"SELECT COALESCE(MAX(step_no),0),COALESCE(MAX(batch_no),0) FROM {s}.incremental_steps").fetchone()
    step,last=previous
    batch=last+1 if action=="NEXT" else last
    if not 1<=batch<=3:
        raise LabStateError("No next batch or no batch to replay")
    cutoff=execute(connection,schema,"SELECT MAX(arrived_at) FROM {s}.incremental_events WHERE batch_no=%s",(batch,)).fetchone()[0]
    current=execute(connection,schema,"SELECT event_id,order_id,event_at,net_amount FROM {s}.incremental_target ORDER BY order_id,event_id").fetchall()
    incoming=execute(connection,schema,"SELECT event_id,order_id,event_at,net_amount FROM {s}.incremental_events WHERE batch_no=%s ORDER BY event_id",(batch,)).fetchall()
    watermark=execute(connection,schema,"SELECT watermark FROM {s}.incremental_steps ORDER BY step_no DESC LIMIT 1").fetchone()
    if policy=="inc_event_watermark" and watermark:
        incoming=[row for row in incoming if row[2]>watermark[0]]
    if policy=="inc_missing" and batch==3:
        incoming=[row for row in incoming if row[0]!=5]
    if policy=="inc_append":
        result=[*current,*incoming]
    elif policy=="inc_stale":
        result=merge_versions(current,[])
        # Fault: first version of an existing key wins forever.
        seen={row[1] for row in result}
        result += [row for row in merge_versions([],incoming) if row[1] not in seen]
    else:
        result=merge_versions(current,incoming)
    execute(connection,schema,"TRUNCATE {s}.incremental_target")
    insert(connection,schema,"incremental_target",result)
    mark=max((row[2] for row in result),default=cutoff) if policy=="inc_event_watermark" else cutoff
    insert(connection,schema,"incremental_steps",[(step+1,batch,action,"SUCCESS",len(incoming),len(result),mark)])
    execute(connection,schema,"UPDATE {s}.lab_context SET as_of=%s",(cutoff,))


def _freshness(connection,schema,clock,variant,shifted):
    names=[name+("_v2" if shifted else "") for name in ("orders","payments","customers")]
    requirements=[(name,clock,sla) for name,sla in zip(names,(5,15,60),strict=True)]
    insert(connection,schema,"freshness_requirements",requirements)
    insert(connection,schema,"freshness_observations",[(name,clock-timedelta(minutes=1),clock-timedelta(minutes=2),"SUCCESS") for name in names])
    first,last=names[0],names[-1]
    if variant=="fresh_boundary":
        for name,_,sla in requirements:
            execute(connection,schema,"UPDATE {s}.freshness_observations SET last_success_at=%s,last_event_at=%s WHERE dataset_id=%s",(clock-timedelta(minutes=sla),clock-timedelta(minutes=sla),name))
    elif variant in {"fresh_stale","fresh_load_stale","fresh_multiple"}:
        field="last_success_at" if variant=="fresh_load_stale" else "last_event_at"
        execute(connection,schema,"UPDATE {s}.freshness_observations SET "+field+"=%s WHERE dataset_id=%s",(clock-timedelta(minutes=5,seconds=1),first))
        if variant=="fresh_multiple":
            execute(connection,schema,"UPDATE {s}.freshness_observations SET last_success_at=NULL,last_event_at=NULL WHERE dataset_id=%s",(last,))
    elif variant=="fresh_missing":
        execute(connection,schema,"DELETE FROM {s}.freshness_observations WHERE dataset_id=%s",(last,))
    elif variant=="fresh_null":
        execute(connection,schema,"UPDATE {s}.freshness_observations SET last_event_at=NULL WHERE dataset_id=%s",(first,))
    elif variant=="fresh_future":
        execute(connection,schema,"UPDATE {s}.freshness_observations SET last_event_at=%s WHERE dataset_id=%s",(clock+timedelta(seconds=1),first))
    elif variant=="fresh_failed":
        execute(connection,schema,"UPDATE {s}.freshness_observations SET execution_status='FAILED' WHERE dataset_id=%s",(first,))


def _customers(connection,schema,keys,clock,variant,lab_id):
    a,b,c,_=keys
    early=clock-timedelta(days=3);middle=clock-timedelta(days=2);recent=clock-timedelta(days=1)
    rows=[(1,a,early,"BRONZE"),(2,a,middle,"SILVER"),(3,a,recent,"GOLD"),
          (4,b,early,"BRONZE"),(5,b,recent,"SILVER"),(6,b,recent,"GOLD"),(7,c,early,"BRONZE")]
    if keys[0]>10000:
        rows=[(event+1000,key,stamp,tier) for event,key,stamp,tier in rows]
    insert(connection,schema,"source_customer_changes",rows)
    if lab_id=="lab_012_scd_type1":
        insert(connection,schema,"target_customers_current",[rows[2],rows[5],rows[6]])
        if variant=="scd1_stale":
            execute(connection,schema,"UPDATE {s}.target_customers_current SET event_id=2,effective_at=%s,tier='SILVER' WHERE customer_id=%s",(middle,a))
        elif variant=="scd1_tie":
            execute(connection,schema,"UPDATE {s}.target_customers_current SET event_id=5,tier='SILVER' WHERE customer_id=%s",(b,))
        elif variant=="scd1_missing":
            execute(connection,schema,"DELETE FROM {s}.target_customers_current WHERE customer_id=%s",(c,))
        elif variant=="scd1_null":
            execute(connection,schema,"UPDATE {s}.target_customers_current SET tier=NULL WHERE customer_id=%s",(a,))
        return
    insert(connection,schema,"target_customer_history",[(1,a,"BRONZE",early,middle,False),(2,a,"SILVER",middle,recent,False),(3,a,"GOLD",recent,None,True),
                                                     (4,b,"BRONZE",early,recent,False),(6,b,"GOLD",recent,None,True),(7,c,"BRONZE",early,None,True)])
    if variant=="scd2_overlap":
        execute(connection,schema,"UPDATE {s}.target_customer_history SET valid_to=valid_to+INTERVAL '1 hour' WHERE version_id=1")
    elif variant=="scd2_two_current":
        execute(connection,schema,"UPDATE {s}.target_customer_history SET is_current=TRUE WHERE version_id=2")
    elif variant=="scd2_missing":
        execute(connection,schema,"DELETE FROM {s}.target_customer_history WHERE version_id=2")
    elif variant=="scd2_invalid":
        execute(connection,schema,"UPDATE {s}.target_customer_history SET valid_to=valid_from WHERE version_id=1")
    elif variant=="scd2_duplicate":
        execute(connection,schema,"INSERT INTO {s}.target_customer_history SELECT 99,customer_id,tier,valid_from,valid_to,is_current FROM {s}.target_customer_history WHERE version_id=3")
    elif variant=="scd2_wrong_tier":
        execute(connection,schema,"UPDATE {s}.target_customer_history SET tier='SILVER' WHERE version_id=6")
    elif variant=="scd2_gap":
        execute(connection,schema,"UPDATE {s}.target_customer_history SET valid_to=valid_to-INTERVAL '1 hour' WHERE version_id=1")
