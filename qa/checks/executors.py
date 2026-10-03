"""PostgreSQL executors for the four Task 2 check types."""
from uuid import UUID

from backend.app.domain.models import QualityStatus
from qa.engine.contracts import (
    CheckResult, CountMode, DatasetRegistry, NotNullRule, RecordCountRule,
    Rule, SchemaRule, UniquenessRule,
)

def execute_rule(connection, pipeline_run_id: UUID, rule: Rule,
                 registry: DatasetRegistry) -> CheckResult:
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
