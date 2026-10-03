"""PostgreSQL executors for the four Task 2 check types."""
from uuid import UUID

from backend.app.domain.models import QualityStatus
from qa.engine.contracts import (
    CheckResult, CountMode, DatasetRegistry, FieldReconciliationRule,
    KeyReconciliationRule, NotNullRule, RecordCountRule, Rule, SchemaRule,
    UniquenessRule,
)

def execute_rule(connection, pipeline_run_id: UUID, rule: Rule,
                 registry: DatasetRegistry) -> CheckResult:
    if isinstance(rule, KeyReconciliationRule):
        return _key_reconciliation(connection, pipeline_run_id, rule, registry)
    if isinstance(rule, FieldReconciliationRule):
        return _field_reconciliation(connection, pipeline_run_id, rule, registry)
    dataset = registry.get(rule.dataset_id)
    if isinstance(rule, RecordCountRule):
        return _record_count(connection, pipeline_run_id, rule, dataset)
    if isinstance(rule, UniquenessRule):
        return _uniqueness(connection, pipeline_run_id, rule, dataset)
    if isinstance(rule, NotNullRule):
        return _not_null(connection, pipeline_run_id, rule, dataset)
    if isinstance(rule, SchemaRule):
        return _schema(connection, rule, dataset)
    raise TypeError(f"Unsupported rule type: {type(rule).__name__}")

def _sql_module():
    from psycopg import sql
    return sql

def _scope(dataset, pipeline_run_id):
    if dataset.run_scoped:
        return _sql_module().SQL(" WHERE run_id = %s"), (pipeline_run_id,)
    return _sql_module().SQL(""), ()

def _record_count(connection, pipeline_run_id, rule, dataset):
    sql = _sql_module()
    expected_row = connection.execute(
        """SELECT row_count FROM metadata.stage_runs
           WHERE run_id = %s AND stage_name = %s AND execution_status = 'SUCCESS'""",
        (pipeline_run_id, rule.expected_stage_name),
    ).fetchone()
    if expected_row is None or expected_row[0] is None:
        raise RuntimeError(f"Missing successful {rule.expected_stage_name} stage evidence")
    scope, params = _scope(dataset, pipeline_run_id)
    if dataset.count_mode is CountMode.ROWS:
        expression = sql.SQL("COUNT(*)")
    else:
        expression = sql.SQL("COALESCE(SUM({}), 0)").format(sql.Identifier(dataset.count_column))
    query = sql.SQL("SELECT {} FROM {}.{}").format(
        expression, sql.Identifier(dataset.schema), sql.Identifier(dataset.table)
    ) + scope
    actual = connection.execute(query, params).fetchone()[0]
    expected = int(expected_row[0])
    actual_value = int(actual)
    status = QualityStatus.PASS if actual_value == expected else QualityStatus.FAIL
    return CheckResult(rule.id, dataset.id, rule.check_type, status,
                       {"count": expected, "source": rule.expected_stage_name},
                       {"count": actual_value},
                       ({"difference": actual_value - expected},) if status is QualityStatus.FAIL else ())

def _uniqueness(connection, pipeline_run_id, rule, dataset):
    sql = _sql_module()
    columns = sql.SQL(", ").join(sql.Identifier(column) for column in rule.columns)
    scope, params = _scope(dataset, pipeline_run_id)
    query = sql.SQL(
        "SELECT COUNT(*), COALESCE(SUM(duplicate_count - 1), 0) FROM ("
        "SELECT {}, COUNT(*) AS duplicate_count FROM {}.{}{} "
        "GROUP BY {} HAVING COUNT(*) > 1) AS duplicate_groups"
    ).format(columns, sql.Identifier(dataset.schema), sql.Identifier(dataset.table), scope, columns)
    row = connection.execute(query, params).fetchone()
    groups, duplicate_rows = int(row[0]), int(row[1])
    status = QualityStatus.PASS if groups == 0 else QualityStatus.FAIL
    return CheckResult(rule.id, dataset.id, rule.check_type, status,
                       {"duplicate_groups": 0, "duplicate_rows": 0},
                       {"duplicate_groups": groups, "duplicate_rows": duplicate_rows},
                       ({"columns": list(rule.columns)},) if status is QualityStatus.FAIL else ())

def _not_null(connection, pipeline_run_id, rule, dataset):
    sql = _sql_module()
    expressions = sql.SQL(", ").join(
        sql.SQL("COUNT(*) FILTER (WHERE {} IS NULL)").format(sql.Identifier(column))
        for column in rule.columns
    )
    scope, params = _scope(dataset, pipeline_run_id)
    query = sql.SQL("SELECT {} FROM {}.{}").format(
        expressions, sql.Identifier(dataset.schema), sql.Identifier(dataset.table)
    ) + scope
    values = connection.execute(query, params).fetchone()
    null_counts = {column: int(value) for column, value in zip(rule.columns, values)}
    status = QualityStatus.PASS if all(value == 0 for value in null_counts.values()) else QualityStatus.FAIL
    evidence = tuple({"column": column, "null_count": value}
                     for column, value in null_counts.items() if value)
    return CheckResult(rule.id, dataset.id, rule.check_type, status,
                       {"null_count_per_column": 0}, {"null_counts": null_counts}, evidence)

def _schema(connection, rule, dataset):
    rows = connection.execute(
        """SELECT column_name, data_type, is_nullable
           FROM information_schema.columns
           WHERE table_schema = %s AND table_name = %s ORDER BY ordinal_position""",
        (dataset.schema, dataset.table),
    ).fetchall()
    actual = {row[0]: {"data_type": row[1], "nullable": row[2] == "YES"} for row in rows}
    expected = {column.name: {"data_type": column.data_type, "nullable": column.nullable}
                for column in rule.columns}
    missing = sorted(set(expected) - set(actual))
    extra = [] if rule.allow_extra_columns else sorted(set(actual) - set(expected))
    mismatched = [
        {"column": name, "expected": expected[name], "actual": actual[name]}
        for name in sorted(set(expected) & set(actual)) if expected[name] != actual[name]
    ]
    evidence = tuple(
        [{"missing_columns": missing}] if missing else []
        + ([{"extra_columns": extra}] if extra else [])
        + mismatched
    )
    status = QualityStatus.PASS if not evidence else QualityStatus.FAIL
    return CheckResult(rule.id, dataset.id, rule.check_type, status,
                       {"columns": expected, "allow_extra_columns": rule.allow_extra_columns},
                       {"columns": actual}, evidence)

def _relation(dataset, alias, pipeline_run_id):
    sql = _sql_module()
    relation = sql.SQL("{}.{} AS {}").format(
        sql.Identifier(dataset.schema), sql.Identifier(dataset.table), sql.Identifier(alias)
    )
    if dataset.run_scoped:
        return relation, sql.SQL("{}.run_id = %s").format(sql.Identifier(alias)), [pipeline_run_id]
    return relation, sql.SQL("TRUE"), []

def _difference_query(source, target, key_columns, pipeline_run_id, reverse=False):
    sql = _sql_module()
    left, right = (target, source) if reverse else (source, target)
    left_relation, left_scope, left_params = _relation(left, "left_side", pipeline_run_id)
    right_relation, right_scope, right_params = _relation(right, "right_side", pipeline_run_id)
    columns = sql.SQL(", ").join(sql.Identifier(column) for column in key_columns)
    query = sql.SQL(
        "SELECT {columns} FROM {left_relation} WHERE {left_scope} "
        "EXCEPT SELECT {columns} FROM {right_relation} WHERE {right_scope}"
    ).format(
        columns=columns,
        left_relation=left_relation,
        left_scope=left_scope,
        right_relation=right_relation,
        right_scope=right_scope,
    )
    return query, tuple(left_params + right_params)

def _difference_evidence(connection, query, params, key_columns, kind, limit):
    sql = _sql_module()
    count = connection.execute(
        sql.SQL("SELECT COUNT(*) FROM ({}) AS differences").format(query), params
    ).fetchone()[0]
    order = sql.SQL(", ").join(sql.Identifier(column) for column in key_columns)
    rows = connection.execute(
        sql.SQL("SELECT * FROM ({}) AS differences ORDER BY {} LIMIT %s").format(query, order),
        params + (limit,),
    ).fetchall()
    evidence = tuple({"kind": kind, "key": dict(zip(key_columns, row))} for row in rows)
    return int(count), evidence

def _key_reconciliation(connection, pipeline_run_id, rule, registry):
    source = registry.get(rule.source_dataset_id)
    target = registry.get(rule.target_dataset_id)
    missing_query, missing_params = _difference_query(
        source, target, rule.key_columns, pipeline_run_id
    )
    unexpected_query, unexpected_params = _difference_query(
        source, target, rule.key_columns, pipeline_run_id, reverse=True
    )
    missing_count, missing_evidence = _difference_evidence(
        connection, missing_query, missing_params, rule.key_columns, "MISSING_KEY", rule.max_evidence
    )
    remaining = max(0, rule.max_evidence - len(missing_evidence))
    unexpected_count, unexpected_evidence = _difference_evidence(
        connection, unexpected_query, unexpected_params, rule.key_columns,
        "UNEXPECTED_KEY", max(1, remaining),
    )
    evidence = (missing_evidence + unexpected_evidence)[:rule.max_evidence]
    status = QualityStatus.PASS if missing_count == 0 and unexpected_count == 0 else QualityStatus.FAIL
    return CheckResult(
        rule.id, target.id, rule.check_type, status,
        {"missing_count": 0, "unexpected_count": 0,
         "source_dataset": source.id, "target_dataset": target.id},
        {"missing_count": missing_count, "unexpected_count": unexpected_count},
        evidence,
    )

def _field_reconciliation(connection, pipeline_run_id, rule, registry):
    sql = _sql_module()
    source = registry.get(rule.source_dataset_id)
    target = registry.get(rule.target_dataset_id)
    source_relation, source_scope, source_params = _relation(source, "source_side", pipeline_run_id)
    target_relation, target_scope, target_params = _relation(target, "target_side", pipeline_run_id)
    join = sql.SQL(" AND ").join(
        sql.SQL("source_side.{} = target_side.{}").format(
            sql.Identifier(column), sql.Identifier(column)
        ) for column in rule.key_columns
    )
    scopes = sql.SQL(" AND ").join((source_scope, target_scope))
    params = tuple(source_params + target_params)
    key_select = sql.SQL(", ").join(
        sql.SQL("source_side.{}").format(sql.Identifier(column)) for column in rule.key_columns
    )
    order = sql.SQL(", ").join(
        sql.SQL("source_side.{}").format(sql.Identifier(column)) for column in rule.key_columns
    )
    mismatch_count = 0
    evidence = []
    for mapping in rule.fields:
        mismatch = sql.SQL("source_side.{} IS DISTINCT FROM target_side.{}").format(
            sql.Identifier(mapping.source), sql.Identifier(mapping.target)
        )
        base = sql.SQL(" FROM {} JOIN {} ON {} WHERE {} AND {}").format(
            source_relation, target_relation, join, scopes, mismatch
        )
        count = int(connection.execute(sql.SQL("SELECT COUNT(*)") + base, params).fetchone()[0])
        mismatch_count += count
        remaining = rule.max_evidence - len(evidence)
        if remaining <= 0 or count == 0:
            continue
        rows = connection.execute(
            sql.SQL("SELECT {}, source_side.{}, target_side.{}").format(
                key_select, sql.Identifier(mapping.source), sql.Identifier(mapping.target)
            ) + base + sql.SQL(" ORDER BY {} LIMIT %s").format(order),
            params + (remaining,),
        ).fetchall()
        for row in rows:
            key_size = len(rule.key_columns)
            evidence.append({
                "kind": "FIELD_MISMATCH",
                "key": dict(zip(rule.key_columns, row[:key_size])),
                "source_column": mapping.source,
                "target_column": mapping.target,
                "expected": row[key_size],
                "actual": row[key_size + 1],
            })
    status = QualityStatus.PASS if mismatch_count == 0 else QualityStatus.FAIL
    return CheckResult(
        rule.id, target.id, rule.check_type, status,
        {"mismatch_count": 0, "source_dataset": source.id, "target_dataset": target.id,
         "fields": [{"source": item.source, "target": item.target} for item in rule.fields]},
        {"mismatch_count": mismatch_count}, tuple(evidence),
    )
