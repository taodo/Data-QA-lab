"""Typed contracts for built-in, read-only data quality checks."""
from dataclasses import dataclass, field
from enum import Enum
import re
from types import MappingProxyType
from typing import Mapping

from backend.app.domain.models import QualityStatus

_IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]*$")

class CheckType(str, Enum):
    RECORD_COUNT = "RECORD_COUNT"
    UNIQUENESS = "UNIQUENESS"
    NOT_NULL = "NOT_NULL"
    SCHEMA = "SCHEMA"

class CountMode(str, Enum):
    ROWS = "ROWS"
    SUM = "SUM"

@dataclass(frozen=True)
class ColumnExpectation:
    name: str
    data_type: str
    nullable: bool

    def __post_init__(self):
        _require_identifier(self.name, "column name")

@dataclass(frozen=True)
class DatasetSpec:
    id: str
    schema: str
    table: str
    run_scoped: bool = True
    count_mode: CountMode = CountMode.ROWS
    count_column: str | None = None

    def __post_init__(self):
        _require_identifier(self.id, "dataset id")
        _require_identifier(self.schema, "schema")
        _require_identifier(self.table, "table")
        if self.count_mode is CountMode.SUM:
            if not self.count_column:
                raise ValueError("SUM datasets require count_column")
            _require_identifier(self.count_column, "count column")
        elif self.count_column is not None:
            raise ValueError("ROWS datasets cannot define count_column")

@dataclass(frozen=True)
class RecordCountRule:
    id: str
    dataset_id: str
    expected_stage_name: str = "SOURCE"
    check_type: CheckType = field(default=CheckType.RECORD_COUNT, init=False)

@dataclass(frozen=True)
class UniquenessRule:
    id: str
    dataset_id: str
    columns: tuple[str, ...]
    check_type: CheckType = field(default=CheckType.UNIQUENESS, init=False)

    def __post_init__(self):
        _validate_columns(self.columns)

@dataclass(frozen=True)
class NotNullRule:
    id: str
    dataset_id: str
    columns: tuple[str, ...]
    check_type: CheckType = field(default=CheckType.NOT_NULL, init=False)

    def __post_init__(self):
        _validate_columns(self.columns)

@dataclass(frozen=True)
class SchemaRule:
    id: str
    dataset_id: str
    columns: tuple[ColumnExpectation, ...]
    allow_extra_columns: bool = False
    check_type: CheckType = field(default=CheckType.SCHEMA, init=False)

    def __post_init__(self):
        if not self.columns:
            raise ValueError("schema rule requires columns")
        names = [column.name for column in self.columns]
        if len(names) != len(set(names)):
            raise ValueError("schema rule column names must be unique")

Rule = RecordCountRule | UniquenessRule | NotNullRule | SchemaRule

@dataclass(frozen=True)
class ValidationSuite:
    id: str
    rules: tuple[Rule, ...]

    def __post_init__(self):
        _require_identifier(self.id, "suite id")
        ids = [rule.id for rule in self.rules]
        if any(not value.strip() for value in ids) or len(ids) != len(set(ids)):
            raise ValueError("rule ids must be non-empty and unique")

@dataclass(frozen=True)
class CheckResult:
    rule_id: str
    dataset_id: str
    check_type: CheckType
    status: QualityStatus
    expected: dict[str, object]
    actual: dict[str, object]
    evidence: tuple[dict[str, object], ...] = ()
    error: str | None = None

class DatasetRegistry:
    def __init__(self, datasets: tuple[DatasetSpec, ...]):
        mapping = {dataset.id: dataset for dataset in datasets}
        if len(mapping) != len(datasets):
            raise ValueError("dataset ids must be unique")
        self._datasets: Mapping[str, DatasetSpec] = MappingProxyType(mapping)

    def get(self, dataset_id: str) -> DatasetSpec:
        try:
            return self._datasets[dataset_id]
        except KeyError as exc:
            raise ValueError(f"Unknown dataset id: {dataset_id}") from exc

    @property
    def ids(self) -> tuple[str, ...]:
        return tuple(self._datasets)

def aggregate_statuses(statuses) -> QualityStatus:
    values = set(statuses)
    if QualityStatus.ERROR in values:
        return QualityStatus.ERROR
    if QualityStatus.FAIL in values:
        return QualityStatus.FAIL
    if not values or QualityStatus.NOT_RUN in values:
        return QualityStatus.NOT_RUN
    return QualityStatus.PASS

def validate_suite(suite: ValidationSuite, registry: DatasetRegistry) -> None:
    for rule in suite.rules:
        registry.get(rule.dataset_id)

def _require_identifier(value: str, label: str) -> None:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"Invalid {label}: {value!r}")

def _validate_columns(columns: tuple[str, ...]) -> None:
    if not columns:
        raise ValueError("check requires at least one column")
    for column in columns:
        _require_identifier(column, "column")
    if len(columns) != len(set(columns)):
        raise ValueError("check columns must be unique")
