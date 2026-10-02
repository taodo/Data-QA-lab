"""Small, dependency-free contracts. No database or execution side effects."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class Layer(str, Enum):
    SOURCE = "source"
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    TARGET = "target"

class ExecutionStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class QualityStatus(str, Enum):
    NOT_RUN = "NOT_RUN"
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"

@dataclass(frozen=True)
class Dataset:
    id: str
    layer: Layer
    name: str
    primary_key: tuple[str, ...]

@dataclass(frozen=True)
class Pipeline:
    id: str
    title: str
    datasets: tuple[Dataset, ...]

@dataclass(frozen=True)
class ValidationRule:
    id: str
    kind: str
    description: str
    dataset_id: str

@dataclass(frozen=True)
class ValidationResult:
    rule_id: str
    status: QualityStatus
    expected: str
    actual: str
    evidence: tuple[str, ...] = ()

@dataclass(frozen=True)
class FaultScenario:
    id: str
    title: str
    injection_layer: Layer
    description: str
    seed: int = 42

@dataclass(frozen=True)
class Lab:
    id: str
    title: str
    requirement: str
    difficulty: str
    pipeline_id: str
    available_fault_ids: tuple[str, ...]
    learning_objectives: tuple[str, ...]

@dataclass(frozen=True)
class StageResult:
    layer: Layer
    execution_status: ExecutionStatus
    row_count: int | None = None
    error: str | None = None

    def __post_init__(self):
        if self.row_count is not None and self.row_count < 0:
            raise ValueError("row_count must be non-negative")

@dataclass(frozen=True)
class PipelineRun:
    run_id: str
    lab_id: str
    pipeline_id: str
    execution_status: ExecutionStatus = ExecutionStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    stages: tuple[StageResult, ...] = ()
    injected_fault_ids: tuple[str, ...] = ()
    validation_results: tuple[ValidationResult, ...] = field(default_factory=tuple)

    def __post_init__(self):
        for timestamp in (self.started_at, self.completed_at):
            if timestamp is not None and timestamp.utcoffset() is None:
                raise ValueError("timestamps must be timezone-aware")
        if self.completed_at is not None:
            if self.started_at is None or self.completed_at < self.started_at:
                raise ValueError("completed_at must follow started_at")

    @property
    def data_quality_status(self) -> QualityStatus:
        return aggregate_quality(self.validation_results)

def aggregate_quality(results: tuple[ValidationResult, ...]) -> QualityStatus:
    """ERROR has priority: at least one check could not produce a verdict."""
    statuses = {result.status for result in results}
    if QualityStatus.ERROR in statuses:
        return QualityStatus.ERROR
    if QualityStatus.FAIL in statuses:
        return QualityStatus.FAIL
    if not statuses or QualityStatus.NOT_RUN in statuses:
        return QualityStatus.NOT_RUN
    return QualityStatus.PASS
