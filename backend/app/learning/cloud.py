"""Deterministic local cloud evidence, actual PostgreSQL snapshots and actions."""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4
from psycopg import sql

from backend.app.learning import cloud_contracts as contracts

IDS = ("lab_023_fabric_lineage", "lab_024_fabric_schema", "lab_025_fabric_layers",
       "lab_026_adf_copy", "lab_027_adf_watermark", "lab_028_adf_recovery",
       "lab_029_onelake_partitions", "lab_030_onelake_freshness")
AS_OF = datetime(2026, 1, 3, 12, tzinfo=timezone.utc)
DEFINITIONS = {
    "cloud_context": "lab_id text,batch_no integer,as_of timestamptz,provider text,resource_id text,provenance text,captured_at timestamptz,mapping_version integer",
    "cloud_runs": "run_id text,execution_status text,started_at timestamptz,ended_at timestamptz,raw_evidence jsonb",
    "cloud_activities": "activity_id text,run_id text,dependency_id text,execution_status text,source_dataset text,target_dataset text,rows_read bigint,rows_written bigint,raw_evidence jsonb",
    **{f"cloud_{name}": "order_id bigint,customer_id bigint,amount numeric(14,2),updated_at timestamptz,event_id bigint,batch_no integer,run_id text" for name in contracts.DATASETS},
    "cloud_schema": "dataset text,column_name text,data_type text",
    "cloud_expected_schema": "dataset text,column_name text,data_type text",
    "cloud_manifest": "partition_key text,file_key text,row_count bigint,snapshot_at timestamptz,run_id text",
    "cloud_expected_partitions": "partition_key text,row_count bigint",
    "cloud_references": "dataset_id text,reference_id text,observed_at timestamptz,run_id text",
    "cloud_required_references": "dataset_id text,reference_id text,sla_minutes integer",
    "cloud_steps": "step_no integer,operation text,run_id text,execution_status text,batch_no integer,target_rows bigint,watermark timestamptz",
    "cloud_imports": "import_id text,run_ids jsonb,filename text,file_format text,sha256 text,captured_at timestamptz,mapping_version integer,raw_content text",
}
TABLES = tuple(DEFINITIONS)
SCENARIOS = {
    IDS[0]: ("cloud_orphan_run", "cloud_dependency_missing", "cloud_unknown_run"),
    IDS[1]: ("cloud_schema_type", "cloud_schema_missing", "cloud_schema_extra"),
    IDS[2]: ("cloud_layer_swap", "cloud_layer_amount", "cloud_layer_duplicate"),
    IDS[3]: ("cloud_copy_swap", "cloud_copy_missing", "cloud_copy_metrics", "cloud_copy_unknown"),
    IDS[4]: ("cloud_skip_late", "cloud_replay_duplicate", "cloud_boundary_skip"),
    IDS[5]: ("cloud_failed_dependency", "cloud_partial_publish", "cloud_checkpoint"),
    IDS[6]: ("cloud_partition_missing", "cloud_partition_extra", "cloud_file_duplicate"),
    IDS[7]: ("cloud_reference_stale", "cloud_reference_missing", "cloud_reference_null", "cloud_reference_future"),
}
VARIANTS = {"cloud_clean", "cloud_shifted", "cloud_zero", "cloud_sla_boundary", *(v for vs in SCENARIOS.values() for v in vs)}
SHIFTED_PREFIX = "shifted__"
VARIANTS |= {SHIFTED_PREFIX + v for vs in SCENARIOS.values() for v in vs}

LATEST = """SELECT DISTINCT ON (order_id) order_id,customer_id,amount,updated_at,event_id,batch_no,run_id
 FROM cloud_source WHERE batch_no<=(SELECT batch_no FROM cloud_context)
 AND updated_at<=(SELECT as_of FROM cloud_context) ORDER BY order_id,event_id DESC"""


def reconciliation(left, right):
    return f"""SELECT COUNT(*) FROM ({left}) s FULL JOIN {right} t USING(order_id)
    WHERE s.order_id IS NULL OR t.order_id IS NULL OR s.customer_id IS DISTINCT FROM t.customer_id
    OR s.amount IS DISTINCT FROM t.amount OR s.event_id IS DISTINCT FROM t.event_id
    OR s.updated_at IS DISTINCT FROM t.updated_at"""


def duplicates(table):
    return f"SELECT COUNT(*) FROM (SELECT order_id FROM {table} GROUP BY order_id HAVING COUNT(*)>1) d"


KEY_CHECK = reconciliation(LATEST, "cloud_target")
SOLUTIONS = {
    IDS[0]: """SELECT
    (SELECT COUNT(*) FROM cloud_activities a LEFT JOIN cloud_runs r USING(run_id)
     WHERE r.run_id IS NULL OR r.execution_status='UNKNOWN' OR a.execution_status='UNKNOWN'
     OR a.source_dataset IS NULL OR a.target_dataset IS NULL) +
    (SELECT COUNT(*) FROM cloud_activities a LEFT JOIN cloud_activities d ON a.dependency_id=d.activity_id AND a.run_id=d.run_id
     WHERE a.dependency_id IS NOT NULL AND (d.activity_id IS NULL OR d.execution_status IS DISTINCT FROM 'SUCCESS')) +
    (SELECT COUNT(*) FROM cloud_target t LEFT JOIN cloud_runs r USING(run_id) WHERE r.run_id IS NULL)
    AS violation_count""",
    IDS[1]: """SELECT (SELECT COUNT(*) FROM cloud_expected_schema e FULL JOIN cloud_schema a USING(dataset,column_name)
    WHERE e.column_name IS NULL OR a.column_name IS NULL OR e.data_type IS DISTINCT FROM a.data_type) +
    (SELECT COUNT(*) FROM (SELECT dataset,column_name FROM cloud_schema GROUP BY dataset,column_name HAVING COUNT(*)>1) d)
    AS violation_count""",
    IDS[2]: "SELECT " + " + ".join(f"({q})" for q in (
        reconciliation(LATEST, "cloud_bronze"), reconciliation("SELECT * FROM cloud_bronze", "cloud_silver"),
        reconciliation("SELECT * FROM cloud_silver", "cloud_target"),
        *(duplicates(t) for t in ("cloud_bronze", "cloud_silver", "cloud_target")))) + " AS violation_count",
    IDS[3]: f"""SELECT ({KEY_CHECK}) + ({duplicates('cloud_target')}) +
    (SELECT COUNT(*) FROM cloud_activities WHERE target_dataset='target' AND
     (execution_status IS DISTINCT FROM 'SUCCESS' OR rows_read IS DISTINCT FROM (SELECT COUNT(*) FROM ({LATEST}) s)
     OR rows_written IS DISTINCT FROM (SELECT COUNT(*) FROM cloud_target))) +
    CASE WHEN EXISTS(SELECT 1 FROM cloud_activities WHERE target_dataset='target') THEN 0 ELSE 1 END AS violation_count""",
    IDS[4]: f"SELECT ({KEY_CHECK}) + ({duplicates('cloud_target')}) AS violation_count",
    IDS[5]: f"""SELECT ({KEY_CHECK}) + ({duplicates('cloud_target')}) +
    (SELECT COUNT(*) FROM cloud_activities WHERE execution_status IS DISTINCT FROM 'SUCCESS') +
    CASE WHEN (SELECT execution_status='SUCCESS' AND batch_no=(SELECT batch_no FROM cloud_context)
               FROM cloud_steps ORDER BY step_no DESC LIMIT 1) IS TRUE THEN 0 ELSE 1 END AS violation_count""",
    IDS[6]: """SELECT (SELECT COUNT(*) FROM cloud_expected_partitions e FULL JOIN
    (SELECT partition_key,SUM(row_count) AS row_count FROM cloud_manifest GROUP BY partition_key) a USING(partition_key)
    WHERE e.partition_key IS NULL OR a.partition_key IS NULL OR e.row_count IS DISTINCT FROM a.row_count) +
    (SELECT COUNT(*) FROM (SELECT file_key FROM cloud_manifest GROUP BY file_key HAVING COUNT(*)>1) d)
    AS violation_count""",
    IDS[7]: """SELECT COUNT(*) AS violation_count FROM cloud_required_references e FULL JOIN cloud_references a USING(dataset_id,reference_id)
    CROSS JOIN cloud_context c WHERE e.dataset_id IS NULL OR a.dataset_id IS NULL OR a.observed_at IS NULL
    OR a.observed_at>c.as_of OR c.as_of-a.observed_at>e.sla_minutes * INTERVAL '1 minute'""",
}
# Independent acceptance counts, specified rather than calculated by instructor SQL.
EXPECTED = dict(zip((v for vs in SCENARIOS.values() for v in vs),
                   (1, 1, 2, 1, 1, 1, 2, 1, 1, 2, 2, 1, 1, 1, 1, 1, 3, 1, 1, 1, 1, 2, 1, 1, 1, 1), strict=True))


def expected_count(variant):
    variant = variant.removeprefix(SHIFTED_PREFIX)
    return 0 if variant in {"cloud_clean", "cloud_shifted", "cloud_zero", "cloud_sla_boundary"} else EXPECTED[variant]


def execute(c, s, statement, params=None):
    from backend.app.learning.workspace import require_schema
    require_schema(s)
    return c.execute(sql.SQL(statement).format(s=sql.Identifier(s)), params)


def insert(c, s, table, rows):
    if table not in TABLES:
        raise ValueError("Unknown cloud table")
    for row in rows:
        c.execute(sql.SQL("INSERT INTO {}.{} VALUES ({})").format(sql.Identifier(s), sql.Identifier(table),
                  sql.SQL(",").join(sql.Placeholder() for _ in row)), row)


def _json(value):
    from psycopg.types.json import Jsonb
    return Jsonb(value)


def create(c, s, lab_id, scenario):
    from backend.app.learning.workspace import require_schema
    require_schema(s)
    c.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(s)))
    for table, columns in DEFINITIONS.items():
        c.execute(sql.SQL("CREATE TABLE {}.{} ({})").format(sql.Identifier(s), sql.Identifier(table), sql.SQL(columns)))
    populate(c, s, lab_id, "cloud_clean" if scenario == "clean" else scenario)


def _source(shift, zero=False):
    rows = [(shift+i, 100+i, Decimal("0.00" if zero and i == 4 else f"{i}.01"),
             datetime(2026, 1, 1 if i <= 2 else 2, 7, tzinfo=timezone.utc), shift+i, 1, "run-1") for i in range(1, 5)]
    rows.append((shift+1, 101, Decimal("9.99"), rows[0][3], shift+9, 2, "run-1"))  # late arrival behind timestamp watermark
    rows.append((shift+2, 102, Decimal("7.77"), AS_OF, shift+10, 2, "run-1"))  # inclusive as-of boundary
    rows.append((shift+3, 103, Decimal("8.88"), AS_OF+timedelta(seconds=1), shift+11, 3, "run-1"))
    return rows


def populate(c, s, lab_id, variant):
    if lab_id not in IDS or variant not in VARIANTS:
        raise ValueError("Unsupported cloud fixture")
    shifted = variant == "cloud_shifted" or variant.startswith(SHIFTED_PREFIX)
    variant = variant.removeprefix(SHIFTED_PREFIX)
    for table in TABLES:
        c.execute(sql.SQL("TRUNCATE {}.{}").format(sql.Identifier(s), sql.Identifier(table)))
    provider = "Fabric" if lab_id in IDS[:3] else "ADF" if lab_id in IDS[3:6] else "OneLake"
    shift = 700 if shifted else 0
    as_of = AS_OF
    batch = 2 if lab_id == IDS[4] else 1
    insert(c, s, "cloud_context", [(lab_id, batch, as_of, provider, "local-workspace", "SIMULATED", datetime.now(timezone.utc), 1)])
    insert(c, s, "cloud_runs", [("run-1", "SUCCESS", as_of-timedelta(minutes=10), as_of,
                                _json({"run_id": "run-1", "execution_status": "Succeeded", "provider": provider}))])
    insert(c, s, "cloud_activities", [("copy-1", "run-1", None, "SUCCESS", "source", "bronze", 4, 4, _json({"execution_status": "Succeeded"})),
                                      ("publish-1", "run-1", "copy-1", "SUCCESS", "silver", "target", 4, 4, _json({"execution_status": "Succeeded"}))])
    insert(c, s, "cloud_source", _source(shift, variant == "cloud_zero"))
    expected_schema = [("target", "order_id", "bigint"), ("target", "customer_id", "bigint"),
                       ("target", "amount", "numeric(14,2)"), ("target", "updated_at", "timestamptz")]
    insert(c, s, "cloud_expected_schema", expected_schema)
    insert(c, s, "cloud_schema", expected_schema)
    insert(c, s, "cloud_expected_partitions", [("2026-01-01", 2), ("2026-01-02", 2)])
    insert(c, s, "cloud_manifest", [(date, date+"/orders.csv", 2, as_of, "run-1") for date in ("2026-01-01", "2026-01-02")])
    insert(c, s, "cloud_required_references", [("orders", "shortcut-orders", 60)])
    insert(c, s, "cloud_references", [("orders", "shortcut-orders", as_of-timedelta(minutes=60), "run-1")])
    _publish(c, s, "cloud_clean")
    insert(c, s, "cloud_steps", [(1, "INITIAL", "run-1", "SUCCESS", batch, 4, as_of)])
    # Fault mutation is explicit and confined to this fixture schema.
    mutations = {
        "cloud_orphan_run": "UPDATE {s}.cloud_target SET run_id='unlinked' WHERE order_id=(SELECT MIN(order_id) FROM {s}.cloud_target)",
        "cloud_dependency_missing": "UPDATE {s}.cloud_activities SET dependency_id='missing' WHERE activity_id='publish-1'",
        "cloud_unknown_run": "UPDATE {s}.cloud_runs SET execution_status='UNKNOWN',raw_evidence='{}'::jsonb",
        "cloud_schema_type": "UPDATE {s}.cloud_schema SET data_type='float' WHERE column_name='amount'",
        "cloud_schema_missing": "DELETE FROM {s}.cloud_schema WHERE column_name='amount'",
        "cloud_schema_extra": "INSERT INTO {s}.cloud_schema VALUES('target','debug','text')",
        "cloud_layer_amount": "UPDATE {s}.cloud_target SET amount=amount+0.01 WHERE order_id=(SELECT MIN(order_id) FROM {s}.cloud_target)",
        "cloud_layer_duplicate": "INSERT INTO {s}.cloud_target SELECT * FROM {s}.cloud_target ORDER BY order_id LIMIT 1",
        "cloud_copy_missing": "DELETE FROM {s}.cloud_target WHERE order_id=(SELECT MIN(order_id) FROM {s}.cloud_target)",
        "cloud_copy_metrics": "UPDATE {s}.cloud_activities SET rows_read=99 WHERE target_dataset='target'",
        "cloud_copy_unknown": "UPDATE {s}.cloud_activities SET rows_read=NULL WHERE target_dataset='target'",
        "cloud_partial_publish": "DELETE FROM {s}.cloud_target WHERE order_id=(SELECT MIN(order_id) FROM {s}.cloud_target)",
        "cloud_checkpoint": "UPDATE {s}.cloud_steps SET batch_no=0",
        "cloud_partition_missing": "DELETE FROM {s}.cloud_manifest WHERE partition_key='2026-01-01'",
        "cloud_partition_extra": "INSERT INTO {s}.cloud_manifest VALUES('2026-01-04','extra.csv',1,'2026-01-03T12:00:00Z','run-1')",
        "cloud_file_duplicate": "INSERT INTO {s}.cloud_manifest SELECT * FROM {s}.cloud_manifest ORDER BY file_key LIMIT 1",
        "cloud_reference_stale": "UPDATE {s}.cloud_references SET observed_at=observed_at-INTERVAL '1 microsecond'",
        "cloud_reference_missing": "TRUNCATE {s}.cloud_references",
        "cloud_reference_null": "UPDATE {s}.cloud_references SET observed_at=NULL",
        "cloud_reference_future": "UPDATE {s}.cloud_references SET observed_at=observed_at+INTERVAL '61 minutes'",
    }
    if variant in mutations:
        statement = mutations[variant]
        if shifted:
            statement = statement.replace("column_name='amount'", "column_name='customer_id'").replace("'debug'", "'new_field'").replace("rows_read=99", "rows_read=123")
        # JSON braces must be escaped for psycopg's SQL identifier formatting.
        execute(c, s, statement.replace("'{}'", "'{{}}'"))
    if variant in {"cloud_layer_swap", "cloud_copy_swap"}:
        execute(c, s, "UPDATE {s}.cloud_target SET order_id=order_id+5000 WHERE order_id=(SELECT MIN(order_id) FROM {s}.cloud_target)")
        if variant == "cloud_layer_swap":
            execute(c, s, "UPDATE {s}.cloud_silver SET order_id=order_id+5000 WHERE order_id=(SELECT MIN(order_id) FROM {s}.cloud_silver)")
    if variant in {"cloud_skip_late", "cloud_boundary_skip", "cloud_replay_duplicate"}:
        _publish(c, s, variant)
    if variant == "cloud_failed_dependency":
        execute(c, s, "UPDATE {s}.cloud_activities SET execution_status=CASE WHEN activity_id='copy-1' THEN 'FAILED' ELSE 'UNKNOWN' END")
        execute(c, s, "UPDATE {s}.cloud_runs SET execution_status='FAILED',raw_evidence='{{\"execution_status\":\"Failed\"}}'::jsonb")
        execute(c, s, "UPDATE {s}.cloud_steps SET execution_status='FAILED',batch_no=0")
    execute(c, s, "UPDATE {s}.cloud_steps SET target_rows=(SELECT COUNT(*) FROM {s}.cloud_target)")


def _publish(c, s, policy):
    query = LATEST.replace("cloud_source", "{s}.cloud_source").replace("cloud_context", "{s}.cloud_context")
    if policy == "cloud_skip_late":
        query = query.replace("WHERE batch_no<=", "WHERE NOT (batch_no>1 AND updated_at<(SELECT as_of FROM {s}.cloud_context)) AND batch_no<=")
    if policy == "cloud_boundary_skip":
        query = query.replace("updated_at<=", "updated_at<")
    rows = execute(c, s, query).fetchall()
    for table in ("cloud_bronze", "cloud_silver", "cloud_target"):
        execute(c, s, "TRUNCATE {s}."+table)
        insert(c, s, table, rows)
    if policy == "cloud_replay_duplicate" and rows:
        insert(c, s, "cloud_target", [rows[0]])


def advance(c, s, scenario, action):
    lab_id, batch = execute(c, s, "SELECT lab_id,batch_no FROM {s}.cloud_context FOR UPDATE").fetchone()
    steps = execute(c, s, "SELECT COUNT(*) FROM {s}.cloud_steps").fetchone()[0]
    if steps >= 100 and action != "RESET":
        raise ValueError("Reset after 100 cloud steps")
    allowed = ("RESET", "NEXT", "REPLAY") if lab_id == IDS[4] else ("RESET", "RECOVER") if lab_id == IDS[5] else ("RESET", "RUN")
    if action not in allowed:
        raise ValueError("Unsupported cloud action for this lesson")
    if action == "RESET":
        imports = execute(c, s, "SELECT * FROM {s}.cloud_imports").fetchall()
        populate(c, s, lab_id, "cloud_clean" if scenario == "clean" else scenario)
        insert(c, s, "cloud_imports", [(*r[:1], _json(r[1]), *r[2:]) for r in imports])
        if lab_id == IDS[4]:
            execute(c, s, "UPDATE {s}.cloud_context SET batch_no=0")
            _publish(c, s, "cloud_clean")
            execute(c, s, "TRUNCATE {s}.cloud_steps")
        return
    if execute(c, s, "SELECT provenance FROM {s}.cloud_context").fetchone()[0] == "IMPORTED":
        raise ValueError("Reset to simulator fixtures before running simulation actions")
    if action == "NEXT":
        execute(c, s, "UPDATE {s}.cloud_context SET batch_no=LEAST(batch_no+1,3)")
    # Imported source rows are read as data; only predefined operations execute.
    _publish(c, s, scenario if lab_id == IDS[4] else "cloud_clean")
    run_id = "run-" + uuid4().hex
    now = datetime.now(timezone.utc)
    insert(c, s, "cloud_runs", [(run_id, "SUCCESS", now, now, _json({"operation": action, "provenance": "SIMULATED"}))])
    execute(c, s, "UPDATE {s}.cloud_context SET provenance='SIMULATED'")
    execute(c, s, "UPDATE {s}.cloud_target SET run_id=%s", (run_id,))
    execute(c, s, "UPDATE {s}.cloud_activities SET run_id=%s,execution_status='SUCCESS'", (run_id,))
    batch, as_of = execute(c, s, "SELECT batch_no,as_of FROM {s}.cloud_context").fetchone()
    count = execute(c, s, "SELECT COUNT(*) FROM {s}.cloud_target").fetchone()[0]
    execute(c, s, "UPDATE {s}.cloud_activities SET rows_read=%s,rows_written=%s", (count, count))
    insert(c, s, "cloud_steps", [(steps+1, action, run_id, "SUCCESS", batch, count, as_of)])


def import_file(c, s, filename, file_format, content):
    data = contracts.parse_file(filename, file_format, content)
    execute(c, s, "SELECT lab_id FROM {s}.cloud_context FOR UPDATE")
    count = execute(c, s, "SELECT COUNT(*) FROM {s}.cloud_imports").fetchone()[0]
    if count >= contracts.MAX_IMPORTS:
        raise ValueError("At most 8 imports per session; start a new session")
    now = datetime.now(timezone.utc)
    if file_format == "json":
        provider = execute(c, s, "SELECT provider FROM {s}.cloud_context").fetchone()[0]
        if data["provider"] != provider:
            raise ValueError("Evidence provider does not match this lesson")
        for table, name in (("cloud_runs", "runs"), ("cloud_activities", "activities"), ("cloud_schema", "schema"),
                            ("cloud_manifest", "manifest"), ("cloud_references", "references")):
            execute(c, s, "TRUNCATE {s}."+table)
            rows = data[name]
            if name in {"runs", "activities"}:
                rows = [(*row[:-1], _json(row[-1])) for row in rows]
            insert(c, s, table, rows)
        execute(c, s, "UPDATE {s}.cloud_context SET as_of=%s,resource_id=%s", (data["as_of"], data["resource_id"]))
    for name, rows in data["datasets"].items():
        execute(c, s, "TRUNCATE {s}.cloud_"+name)
        insert(c, s, "cloud_"+name, rows)
    # Imports are snapshots, not proof that simulator actions/checkpoints executed.
    execute(c, s, "TRUNCATE {s}.cloud_steps")
    execute(c, s, "UPDATE {s}.cloud_context SET provenance='IMPORTED',captured_at=%s", (now,))
    run_ids = {row[-1] for rows in data["datasets"].values() for row in rows}
    if file_format == "json":
        run_ids.update(row[0] for row in data["runs"])
        run_ids.update(row[1] for row in data["activities"])
        run_ids.update(row[-1] for row in (*data["manifest"], *data["references"]))
    insert(c, s, "cloud_imports", [(uuid4().hex, _json(sorted(run_ids)), filename, file_format,
                                    hashlib.sha256(content.encode()).hexdigest(), now, 1, content)])


def state(c, s, lab_id):
    cursor = execute(c, s, "SELECT * FROM {s}.cloud_context")
    result = dict(zip((col.name for col in cursor.description), cursor.fetchone(), strict=True))
    for table, order in (("cloud_runs", "started_at NULLS FIRST,run_id"), ("cloud_activities", "activity_id"),
                         ("cloud_schema", "dataset,column_name"), ("cloud_manifest", "partition_key,file_key"),
                         ("cloud_references", "dataset_id"), ("cloud_steps", "step_no")):
        cursor = execute(c, s, "SELECT * FROM {s}."+table+" ORDER BY "+order+" LIMIT 100")
        names = [col.name for col in cursor.description]
        result[table.removeprefix("cloud_")] = [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]
    result["datasets"] = {}
    for name in contracts.DATASETS:
        cursor = execute(c, s, "SELECT * FROM {s}.cloud_"+name+" ORDER BY order_id,event_id LIMIT 100")
        names = [col.name for col in cursor.description]
        result["datasets"][name] = [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]
    imports = execute(c, s, "SELECT import_id,run_ids,filename,file_format,sha256,captured_at,mapping_version FROM {s}.cloud_imports ORDER BY captured_at").fetchall()
    result["imports"] = [dict(zip(("import_id", "run_ids", "filename", "file_format", "sha256", "captured_at", "mapping_version"), row, strict=True)) for row in imports]
    gaps = []
    if not result["runs"] or any(r["execution_status"] == "UNKNOWN" or r["started_at"] is None or r["ended_at"] is None for r in result["runs"]):
        gaps.append("Run execution or timestamps are unknown")
    if not result["resource_id"]:
        gaps.append("Provider resource identity is unknown")
    if not result["datasets"]["source"] or not result["datasets"]["target"]:
        gaps.append("Source or Target snapshot is empty; completeness is not established")
    if lab_id in IDS[:6] and (not result["activities"] or any(a["execution_status"] == "UNKNOWN" or a["rows_read"] is None or a["rows_written"] is None for a in result["activities"])):
        gaps.append("Activity state or copy metrics are unknown")
    if lab_id == IDS[1] and not result["schema"]:
        gaps.append("Reported schema evidence is missing")
    if lab_id == IDS[6] and (not result["manifest"] or any(m["row_count"] is None or m["snapshot_at"] is None for m in result["manifest"])):
        gaps.append("File manifest evidence is incomplete")
    if lab_id == IDS[7] and (not result["references"] or any(r["observed_at"] is None for r in result["references"])):
        gaps.append("Reference capture time is unknown")
    result["evidence_status"] = "NOT_VERIFIED" if gaps else "AVAILABLE"
    result["evidence_gaps"] = gaps
    result["execution_status"] = result["steps"][-1]["execution_status"] if result["steps"] else result["runs"][-1]["execution_status"] if result["runs"] else "UNKNOWN"
    result["quality_status"] = "NOT_RUN"
    return result
