"""Run validation suites, retain evidence, and update only quality status."""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4
import json

from backend.app.domain.models import QualityStatus
from backend.app.persistence.database import connect, transaction
from qa.checks.executors import execute_rule
from qa.checks.orders_suite import ORDERS_DATASETS, ORDERS_SUITE
from qa.engine.contracts import (
    CheckResult, DatasetRegistry, ValidationSuite, aggregate_statuses, validate_suite,
)

@dataclass(frozen=True)
class QualityRunSummary:
    validation_run_id: UUID
    pipeline_run_id: UUID
    suite_id: str
    status: QualityStatus
    results: tuple[CheckResult, ...]

class PipelineRunNotReady(ValueError):
    pass

def _utcnow():
    return datetime.now(timezone.utc)

def _resolve_pipeline_run(database_url: str, pipeline_run_id: UUID | None) -> UUID:
    with connect(database_url) as connection:
        if pipeline_run_id is None:
            row = connection.execute(
                """SELECT run_id FROM metadata.pipeline_runs
                   WHERE execution_status = 'SUCCESS' ORDER BY started_at DESC LIMIT 1"""
            ).fetchone()
        else:
            row = connection.execute(
                "SELECT run_id FROM metadata.pipeline_runs WHERE run_id = %s AND execution_status = 'SUCCESS'",
                (pipeline_run_id,),
            ).fetchone()
    if row is None:
        raise PipelineRunNotReady("No matching successful pipeline run found")
    return row[0]

def _json(value) -> str:
    return json.dumps(value, default=str, sort_keys=True)

def run_quality_suite(database_url: str, pipeline_run_id: UUID | None = None,
                      suite: ValidationSuite = ORDERS_SUITE,
                      registry: DatasetRegistry = ORDERS_DATASETS) -> QualityRunSummary:
    validate_suite(suite, registry)
    resolved_run_id = _resolve_pipeline_run(database_url, pipeline_run_id)
    validation_run_id = uuid4()
    started_at = _utcnow()
    with transaction(database_url) as connection:
        connection.execute(
            """INSERT INTO metadata.validation_runs
               (validation_run_id, pipeline_run_id, suite_id, status, started_at)
               VALUES (%s, %s, %s, 'RUNNING', %s)""",
            (validation_run_id, resolved_run_id, suite.id, started_at),
        )

    results = []
    for rule in suite.rules:
        try:
            with connect(database_url) as connection:
                with connection.transaction():
                    connection.execute("SET TRANSACTION READ ONLY")
                    result = execute_rule(connection, resolved_run_id, rule, registry)
        except Exception as exc:
            result = CheckResult(
                rule.id, rule.dataset_id, rule.check_type, QualityStatus.ERROR,
                {}, {}, (), f"{type(exc).__name__}: {exc}",
            )
        results.append(result)

    status = aggregate_statuses(result.status for result in results)
    completed_at = _utcnow()
    with transaction(database_url) as connection:
        for result in results:
            connection.execute(
                """INSERT INTO metadata.validation_results
                   (validation_run_id, rule_id, dataset_id, check_type, status,
                    expected, actual, evidence, error)
                   VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s)""",
                (validation_run_id, result.rule_id, result.dataset_id, result.check_type.value,
                 result.status.value, _json(result.expected), _json(result.actual),
                 _json(result.evidence), result.error),
            )
        connection.execute(
            """UPDATE metadata.validation_runs SET status = %s, completed_at = %s
               WHERE validation_run_id = %s""",
            (status.value, completed_at, validation_run_id),
        )
        connection.execute(
            "UPDATE metadata.pipeline_runs SET data_quality_status = %s WHERE run_id = %s",
            (status.value, resolved_run_id),
        )
    return QualityRunSummary(validation_run_id, resolved_run_id, suite.id, status, tuple(results))

def inspect_quality_run(database_url: str, pipeline_run_id: UUID | None = None) -> dict[str, object] | None:
    with connect(database_url) as connection:
        if pipeline_run_id is None:
            run = connection.execute(
                """SELECT validation_run_id, pipeline_run_id, suite_id, status, started_at, completed_at
                   FROM metadata.validation_runs ORDER BY started_at DESC LIMIT 1"""
            ).fetchone()
        else:
            run = connection.execute(
                """SELECT validation_run_id, pipeline_run_id, suite_id, status, started_at, completed_at
                   FROM metadata.validation_runs WHERE pipeline_run_id = %s
                   ORDER BY started_at DESC LIMIT 1""", (pipeline_run_id,)
            ).fetchone()
        if run is None:
            return None
        rows = connection.execute(
            """SELECT rule_id, dataset_id, check_type, status, expected, actual, evidence, error
               FROM metadata.validation_results WHERE validation_run_id = %s ORDER BY rule_id""",
            (run[0],),
        ).fetchall()
    return {
        "validation_run_id": str(run[0]), "pipeline_run_id": str(run[1]), "suite_id": run[2],
        "status": run[3], "started_at": run[4], "completed_at": run[5],
        "results": [{"rule_id": row[0], "dataset_id": row[1], "check_type": row[2],
                     "status": row[3], "expected": row[4], "actual": row[5],
                     "evidence": row[6], "error": row[7]} for row in rows],
    }
