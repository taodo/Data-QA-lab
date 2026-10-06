"""Orders pipeline with run-scoped evidence across each data layer."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable
from uuid import UUID, uuid4
import json

from backend.app.persistence.database import connect, transaction

PIPELINE_ID = "orders_v1"
STAGES = ("SOURCE", "BRONZE", "SILVER", "GOLD", "TARGET")

@dataclass(frozen=True)
class StageOutcome:
    name: str
    row_count: int
    metrics: dict[str, object]

@dataclass(frozen=True)
class RunSummary:
    run_id: UUID
    execution_status: str
    data_quality_status: str
    stages: tuple[StageOutcome, ...]
    error: str | None = None

class PipelineStageError(RuntimeError):
    pass

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

def _record_run_start(database_url: str, run_id: UUID, owner_id=None) -> None:
    with transaction(database_url) as connection:
        connection.execute(
            """INSERT INTO metadata.pipeline_runs
               (run_id, pipeline_id, execution_status, data_quality_status, started_at, owner_id)
               VALUES (%s, %s, 'RUNNING', 'NOT_RUN', %s, %s)""",
            (run_id, PIPELINE_ID, _utcnow(), owner_id),
        )

def _record_stage(database_url: str, run_id: UUID, name: str, status: str,
                  started_at: datetime, row_count: int | None = None,
                  metrics: dict[str, object] | None = None, error: str | None = None) -> None:
    with transaction(database_url) as connection:
        connection.execute(
            """INSERT INTO metadata.stage_runs
               (run_id, stage_name, execution_status, row_count, metrics, started_at, completed_at, error)
               VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, %s)""",
            (run_id, name, status, row_count, json.dumps(metrics or {}, default=str),
             started_at, _utcnow(), error),
        )

def _record_run_end(database_url: str, run_id: UUID, status: str, error: str | None = None) -> None:
    with transaction(database_url) as connection:
        connection.execute(
            """UPDATE metadata.pipeline_runs
               SET execution_status = %s, completed_at = %s, error = %s
               WHERE run_id = %s""",
            (status, _utcnow(), error, run_id),
        )

def _source(connection, run_id: UUID) -> StageOutcome:
    row = connection.execute(
        "SELECT COUNT(*) AS count, COALESCE(SUM(gross_amount - discount_amount - refund_amount), 0) AS net FROM source.orders"
    ).fetchone()
    return StageOutcome("SOURCE", row[0], {"net_revenue": str(row[1])})

def _bronze(connection, run_id: UUID) -> StageOutcome:
    connection.execute(
        """INSERT INTO bronze.orders
           (run_id, order_id, customer_id, ordered_at, gross_amount, discount_amount, refund_amount, updated_at)
           SELECT %s, order_id, customer_id, ordered_at, gross_amount, discount_amount, refund_amount, updated_at
           FROM source.orders ORDER BY order_id""", (run_id,))
    count = connection.execute("SELECT COUNT(*) FROM bronze.orders WHERE run_id = %s", (run_id,)).fetchone()[0]
    return StageOutcome("BRONZE", count, {})

def _silver(connection, run_id: UUID) -> StageOutcome:
    connection.execute(
        """INSERT INTO silver.orders
           (run_id, order_id, customer_id, ordered_at, gross_amount, discount_amount, refund_amount, net_amount, updated_at)
           SELECT run_id, order_id, customer_id, ordered_at, gross_amount, discount_amount, refund_amount,
                  gross_amount - discount_amount - refund_amount, updated_at
           FROM bronze.orders WHERE run_id = %s ORDER BY order_id""", (run_id,))
    row = connection.execute(
        "SELECT COUNT(*), COALESCE(SUM(net_amount), 0) FROM silver.orders WHERE run_id = %s", (run_id,)
    ).fetchone()
    return StageOutcome("SILVER", row[0], {"net_revenue": str(row[1])})

def _gold(connection, run_id: UUID) -> StageOutcome:
    connection.execute(
        """INSERT INTO gold.daily_sales
           (run_id, order_date, order_count, gross_revenue, net_revenue)
           SELECT run_id, (ordered_at AT TIME ZONE 'UTC')::date, COUNT(*), SUM(gross_amount), SUM(net_amount)
           FROM silver.orders WHERE run_id = %s
           GROUP BY run_id, (ordered_at AT TIME ZONE 'UTC')::date
           ORDER BY (ordered_at AT TIME ZONE 'UTC')::date""", (run_id,))
    row = connection.execute(
        """SELECT COUNT(*), COALESCE(SUM(order_count), 0), COALESCE(SUM(net_revenue), 0)
           FROM gold.daily_sales WHERE run_id = %s""", (run_id,)
    ).fetchone()
    return StageOutcome("GOLD", row[0], {"order_count": int(row[1]), "net_revenue": str(row[2]), "grain": "UTC day"})

def _target(connection, run_id: UUID) -> StageOutcome:
    connection.execute(
        """INSERT INTO target.orders_report (run_id, order_id, customer_id, ordered_at, net_amount)
           SELECT run_id, order_id, customer_id, ordered_at, net_amount
           FROM silver.orders WHERE run_id = %s ORDER BY order_id""", (run_id,))
    connection.execute(
        """INSERT INTO target.daily_sales_report (run_id, order_date, order_count, net_revenue)
           SELECT run_id, order_date, order_count, net_revenue
           FROM gold.daily_sales WHERE run_id = %s ORDER BY order_date""", (run_id,))
    row = connection.execute(
        """SELECT COUNT(*), COALESCE(SUM(net_amount), 0)
           FROM target.orders_report WHERE run_id = %s""", (run_id,)
    ).fetchone()
    daily_rows = connection.execute(
        "SELECT COUNT(*) FROM target.daily_sales_report WHERE run_id = %s", (run_id,)
    ).fetchone()[0]
    return StageOutcome("TARGET", row[0], {"daily_rows": daily_rows, "net_revenue": str(row[1])})

STAGE_FUNCTIONS: tuple[tuple[str, Callable], ...] = (
    ("SOURCE", _source), ("BRONZE", _bronze), ("SILVER", _silver),
    ("GOLD", _gold), ("TARGET", _target),
)

def run_orders_pipeline(database_url: str, run_id: UUID | None = None, owner_id=None) -> RunSummary:
    current_run_id = run_id or uuid4()
    _record_run_start(database_url, current_run_id, owner_id)
    outcomes = []
    for name, stage in STAGE_FUNCTIONS:
        started_at = _utcnow()
        try:
            with transaction(database_url) as connection:
                outcome = stage(connection, current_run_id)
            _record_stage(database_url, current_run_id, name, "SUCCESS", started_at,
                          outcome.row_count, outcome.metrics)
            outcomes.append(outcome)
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            _record_stage(database_url, current_run_id, name, "FAILED", started_at, error=message)
            _record_run_end(database_url, current_run_id, "FAILED", message)
            raise PipelineStageError(f"Pipeline {current_run_id} failed at {name}: {message}") from exc
    _record_run_end(database_url, current_run_id, "SUCCESS")
    return RunSummary(current_run_id, "SUCCESS", "NOT_RUN", tuple(outcomes))

def inspect_run(database_url: str, run_id: UUID | None = None) -> dict[str, object] | None:
    with connect(database_url) as connection:
        if run_id is None:
            run = connection.execute(
                """SELECT run_id, pipeline_id, execution_status, data_quality_status,
                          started_at, completed_at, error
                   FROM metadata.pipeline_runs ORDER BY started_at DESC LIMIT 1"""
            ).fetchone()
        else:
            run = connection.execute(
                """SELECT run_id, pipeline_id, execution_status, data_quality_status,
                          started_at, completed_at, error
                   FROM metadata.pipeline_runs WHERE run_id = %s""", (run_id,)
            ).fetchone()
        if run is None:
            return None
        stages = connection.execute(
            """SELECT stage_name, execution_status, row_count, metrics, started_at, completed_at, error
               FROM metadata.stage_runs WHERE run_id = %s ORDER BY started_at""", (run[0],)
        ).fetchall()
    return {
        "run_id": str(run[0]), "pipeline_id": run[1], "execution_status": run[2],
        "data_quality_status": run[3], "started_at": run[4], "completed_at": run[5],
        "error": run[6],
        "stages": [{"name": row[0], "execution_status": row[1], "row_count": row[2],
                    "metrics": row[3], "started_at": row[4], "completed_at": row[5],
                    "error": row[6]} for row in stages],
    }
