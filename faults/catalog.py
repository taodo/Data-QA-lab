"""Allowlisted Task 4 fault scenarios."""
from types import MappingProxyType
from typing import Mapping

from faults.contracts import FaultScenario


FAULT_SCENARIOS = (
    FaultScenario(
        "missing_order",
        "Delete the lowest order_id from the isolated target workspace.",
        ("count_target_orders", "keys_silver_to_target_orders"),
    ),
    FaultScenario(
        "duplicate_order",
        "Duplicate the lowest order_id in the isolated target workspace.",
        ("count_target_orders", "unique_target_order_id"),
    ),
    FaultScenario(
        "null_net_amount",
        "Set net_amount to NULL for the lowest order_id in the isolated target workspace.",
        ("required_target_orders", "fields_silver_to_target_orders"),
    ),
    FaultScenario(
        "wrong_net_amount",
        "Add 0.01 to net_amount for the lowest order_id in the isolated target workspace.",
        ("fields_silver_to_target_orders",),
    ),
)

_BY_ID: Mapping[str, FaultScenario] = MappingProxyType(
    {scenario.id: scenario for scenario in FAULT_SCENARIOS}
)


def list_fault_scenarios() -> tuple[FaultScenario, ...]:
    return FAULT_SCENARIOS


def get_fault_scenario(scenario_id: str) -> FaultScenario:
    try:
        return _BY_ID[scenario_id]
    except KeyError as exc:
        raise ValueError(f"Unknown fault scenario: {scenario_id}") from exc
