from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


class LabStateError(ValueError):
    pass


class SqlSecurityError(RuntimeError):
    pass


@dataclass(frozen=True)
class QueryLimits:
    timeout_ms: int = 2000
    watchdog_ms: int = 3000
    max_rows: int = 100
    max_columns: int = 20
    max_bytes: int = 65536
    cell_chars: int = 2048

    def __post_init__(self):
        values = (self.timeout_ms, self.watchdog_ms, self.max_rows,
                  self.max_columns, self.max_bytes, self.cell_chars)
        if any(type(value) is not int or value <= 0 for value in values):
            raise ValueError("Query limits must be positive integers")
        if not 50 <= self.timeout_ms <= 10000 or not self.timeout_ms < self.watchdog_ms <= 15000:
            raise ValueError("Query deadline is outside the supported bounds")
        if self.max_rows > 100 or self.max_columns > 20 or self.max_bytes > 65536 or self.cell_chars > 2048:
            raise ValueError("Query output limits cannot exceed the safety defaults")


@dataclass(frozen=True)
class QueryResult:
    status: str
    columns: tuple[str, ...] = ()
    rows: tuple[tuple[str | None, ...], ...] = ()
    truncated: bool = False
    error: str | None = None


def normalize_sql(query: str) -> str:
    if not isinstance(query, str) or not query.strip():
        raise ValueError("SQL must not be empty")
    if len(query.encode("utf-8")) > 16384 or "\x00" in query:
        raise ValueError("SQL must be UTF-8 text of at most 16 KiB without NUL")
    # PostgreSQL's extended cursor protocol enforces a single SELECT statement.
    # This only accommodates the conventional final statement terminator.
    return query.strip().removesuffix(";").rstrip()


def violation_count(result: QueryResult) -> int:
    if result.status != "SUCCESS" or result.truncated:
        raise ValueError("A complete, successful result is required")
    if result.columns != ("violation_count",) or len(result.rows) != 1 or len(result.rows[0]) != 1:
        raise ValueError("Return one row and one column named violation_count")
    value = result.rows[0][0]
    try:
        number = Decimal(value) if value is not None else Decimal("NaN")
    except InvalidOperation as exc:
        raise ValueError("violation_count must be a non-negative integer") from exc
    if not number.is_finite() or number < 0 or number != number.to_integral_value() or number > 2**63 - 1:
        raise ValueError("violation_count must be a non-negative 64-bit integer")
    return int(number)
