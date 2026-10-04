"""Atomic lifecycle operations for run-scoped fault workspaces."""
from datetime import datetime, timezone
from decimal import Decimal
import json
from uuid import UUID, uuid4

from backend.app.persistence.database import connect, transaction
from faults.catalog import get_fault_scenario
from faults.contracts import FaultRunSummary, FaultStateError, FaultStatus


_ORDER_COLUMNS = ("order_id", "customer_id", "ordered_at", "net_amount")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _json(value: object) -> str:
    return json.dumps(value, default=str, sort_keys=True)


def _order_snapshot(row) -> dict[str, object]:
    return dict(zip(_ORDER_COLUMNS, row, strict=True))


def _resolve_pipeline_run(connection, pipeline_run_id: UUID | None) -> UUID:
    if pipeline_run_id is None:
        row = connection.execute(
            """SELECT run_id FROM metadata.pipeline_runs
               WHERE execution_status = 'SUCCESS' ORDER BY started_at DESC LIMIT 1"""
        ).fetchone()
    else:
        row = connection.execute(
            """SELECT run_id FROM metadata.pipeline_runs
               WHERE run_id = %s AND execution_status = 'SUCCESS'""",
            (pipeline_run_id,),
        ).fetchone()
    if row is None:
        raise FaultStateError("No matching successful pipeline run found")
    return row[0]


def _select_first_order(connection, pipeline_run_id: UUID):
    row = connection.execute(
        """SELECT order_id, customer_id, ordered_at, net_amount
           FROM fault_workspace.orders_report
           WHERE run_id = %s ORDER BY order_id LIMIT 1""",
        (pipeline_run_id,),
    ).fetchone()
    if row is None:
        raise FaultStateError("The fault workspace contains no target orders")
    return row


def _apply_mutation(connection, pipeline_run_id: UUID, scenario_id: str) -> dict[str, object]:
    before_row = _select_first_order(connection, pipeline_run_id)
    before = _order_snapshot(before_row)
    order_id = before["order_id"]

    if scenario_id == "missing_order":
        connection.execute(
            "DELETE FROM fault_workspace.orders_report WHERE run_id = %s AND order_id = %s",
            (pipeline_run_id, order_id),
        )
        action = "DELETE"
        after = None
    elif scenario_id == "duplicate_order":
        connection.execute(
            """INSERT INTO fault_workspace.orders_report
               (run_id, order_id, customer_id, ordered_at, net_amount)
               VALUES (%s, %s, %s, %s, %s)""",
            (pipeline_run_id, *before_row),
        )
        action = "INSERT_DUPLICATE"
        after = [before, before]
    elif scenario_id == "null_net_amount":
        connection.execute(
            """UPDATE fault_workspace.orders_report SET net_amount = NULL
               WHERE run_id = %s AND order_id = %s""",
            (pipeline_run_id, order_id),
        )
        action = "SET_NULL"
        after = {**before, "net_amount": None}
    elif scenario_id == "wrong_net_amount":
        wrong_amount = before["net_amount"] + Decimal("0.01")
        connection.execute(
            """UPDATE fault_workspace.orders_report SET net_amount = %s
               WHERE run_id = %s AND order_id = %s""",
            (wrong_amount, pipeline_run_id, order_id),
        )
        action = "ADD_0_01"
        after = {**before, "net_amount": wrong_amount}
    else:  # protected by the allowlisted catalog
        raise ValueError(f"Unsupported fault scenario: {scenario_id}")

    return {
        "dataset": "target_orders",
        "action": action,
        "key": {"order_id": order_id},
        "before": before,
        "after": after,
    }


def _row_to_summary(row) -> FaultRunSummary:
    return FaultRunSummary(
        fault_run_id=row[0],
        pipeline_run_id=row[1],
        scenario_id=row[2],
        status=FaultStatus(row[3]),
        mutation_evidence=row[4],
        validation_run_id=row[5],
        applied_at=row[6],
        reset_at=row[7],
    )


def _fetch_fault(connection, fault_run_id: UUID):
    return connection.execute(
        """SELECT fault_run_id, pipeline_run_id, scenario_id, status,
                  mutation_evidence, validation_run_id, applied_at, reset_at
           FROM metadata.fault_runs WHERE fault_run_id = %s""",
        (fault_run_id,),
    ).fetchone()


def apply_fault(
    database_url: str, scenario_id: str, pipeline_run_id: UUID | None = None, owner_id=None
) -> FaultRunSummary:
    scenario = get_fault_scenario(scenario_id)
    fault_run_id = uuid4()
    applied_at = _utcnow()
    with transaction(database_url) as connection:
        resolved_run_id = _resolve_pipeline_run(connection, pipeline_run_id)
        active = connection.execute(
            """SELECT fault_run_id FROM metadata.fault_runs
               WHERE pipeline_run_id = %s AND status = 'APPLIED'""",
            (resolved_run_id,),
        ).fetchone()
        if active is not None:
            raise FaultStateError(
                f"Pipeline run {resolved_run_id} already has active fault {active[0]}"
            )

        connection.execute(
            "DELETE FROM fault_workspace.orders_report WHERE run_id = %s",
            (resolved_run_id,),
        )
        connection.execute(
            "DELETE FROM fault_workspace.daily_sales_report WHERE run_id = %s",
            (resolved_run_id,),
        )
        connection.execute(
            """INSERT INTO fault_workspace.orders_report
               (run_id, order_id, customer_id, ordered_at, net_amount)
               SELECT run_id, order_id, customer_id, ordered_at, net_amount
               FROM target.orders_report WHERE run_id = %s""",
            (resolved_run_id,),
        )
        connection.execute(
            """INSERT INTO fault_workspace.daily_sales_report
               (run_id, order_date, order_count, net_revenue)
               SELECT run_id, order_date, order_count, net_revenue
               FROM target.daily_sales_report WHERE run_id = %s""",
            (resolved_run_id,),
        )

        evidence = _apply_mutation(connection, resolved_run_id, scenario.id)
        evidence["expected_rule_ids"] = list(scenario.expected_rule_ids)
        connection.execute(
            """INSERT INTO metadata.fault_runs
               (fault_run_id, pipeline_run_id, scenario_id, status,
                mutation_evidence, applied_at,owner_id)
               VALUES (%s, %s, %s, 'APPLIED', %s::jsonb, %s,%s)""",
            (fault_run_id, resolved_run_id, scenario.id, _json(evidence), applied_at,owner_id),
        )

    return FaultRunSummary(
        fault_run_id, resolved_run_id, scenario.id, FaultStatus.APPLIED,
        json.loads(_json(evidence)), None, applied_at, None,
    )


def run_fault_quality(database_url: str, fault_run_id: UUID):
    from qa.checks.orders_suite import ORDERS_FAULT_DATASETS, ORDERS_FAULT_SUITE
    from qa.engine.runner import run_quality_suite

    with connect(database_url) as connection:
        row = _fetch_fault(connection, fault_run_id)
    if row is None:
        raise FaultStateError("No matching fault run found")
    fault = _row_to_summary(row)
    if fault.status is not FaultStatus.APPLIED:
        raise FaultStateError("Quality checks require an APPLIED fault run")

    quality = run_quality_suite(
        database_url, fault.pipeline_run_id, ORDERS_FAULT_SUITE, ORDERS_FAULT_DATASETS
    )
    with transaction(database_url) as connection:
        updated = connection.execute(
            """UPDATE metadata.fault_runs SET validation_run_id = %s
               WHERE fault_run_id = %s AND status = 'APPLIED'""",
            (quality.validation_run_id, fault_run_id),
        )
        if updated.rowcount != 1:
            raise FaultStateError("Fault state changed while quality checks were running")
    return quality


def inspect_fault(
    database_url: str, fault_run_id: UUID | None = None
) -> FaultRunSummary | None:
    with connect(database_url) as connection:
        if fault_run_id is None:
            row = connection.execute(
                """SELECT fault_run_id, pipeline_run_id, scenario_id, status,
                          mutation_evidence, validation_run_id, applied_at, reset_at
                   FROM metadata.fault_runs ORDER BY applied_at DESC LIMIT 1"""
            ).fetchone()
        else:
            row = _fetch_fault(connection, fault_run_id)
    return None if row is None else _row_to_summary(row)


def reset_fault(database_url: str, fault_run_id: UUID) -> FaultRunSummary:
    with transaction(database_url) as connection:
        row = _fetch_fault(connection, fault_run_id)
        if row is None:
            raise FaultStateError("No matching fault run found")
        fault = _row_to_summary(row)
        if fault.status is FaultStatus.RESET:
            return fault

        reset_at = _utcnow()
        connection.execute(
            "DELETE FROM fault_workspace.orders_report WHERE run_id = %s",
            (fault.pipeline_run_id,),
        )
        connection.execute(
            "DELETE FROM fault_workspace.daily_sales_report WHERE run_id = %s",
            (fault.pipeline_run_id,),
        )
        connection.execute(
            """UPDATE metadata.fault_runs SET status = 'RESET', reset_at = %s
               WHERE fault_run_id = %s AND status = 'APPLIED'""",
            (reset_at, fault_run_id),
        )
    return FaultRunSummary(
        fault.fault_run_id, fault.pipeline_run_id, fault.scenario_id,
        FaultStatus.RESET, fault.mutation_evidence, fault.validation_run_id,
        fault.applied_at, reset_at,
    )
