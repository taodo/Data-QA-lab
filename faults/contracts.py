"""Typed contracts for deterministic, run-scoped fault injection."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import re
from uuid import UUID


_SCENARIO_ID = re.compile(r"^[a-z_][a-z0-9_]*$")


class FaultStatus(str, Enum):
    APPLIED = "APPLIED"
    RESET = "RESET"


class FaultStateError(ValueError):
    """Raised when a fault lifecycle transition is not allowed."""


@dataclass(frozen=True)
class FaultScenario:
    id: str
    description: str
    expected_rule_ids: tuple[str, ...]

    def __post_init__(self):
        if not _SCENARIO_ID.fullmatch(self.id):
            raise ValueError(f"Invalid fault scenario id: {self.id!r}")
        if not self.description.strip():
            raise ValueError("Fault scenario description must not be empty")
        if not self.expected_rule_ids or len(set(self.expected_rule_ids)) != len(
            self.expected_rule_ids
        ):
            raise ValueError("Expected rule ids must be non-empty and unique")


@dataclass(frozen=True)
class FaultRunSummary:
    fault_run_id: UUID
    pipeline_run_id: UUID
    scenario_id: str
    status: FaultStatus
    mutation_evidence: dict[str, object]
    validation_run_id: UUID | None
    applied_at: datetime
    reset_at: datetime | None
