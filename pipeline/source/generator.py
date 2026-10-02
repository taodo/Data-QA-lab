"""Deterministic source fixtures. Values are business data, not random mocks."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

BASE_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)
COUNTRIES = ("VN", "US", "GB", "SG", "AU")
CENT = Decimal("0.01")

@dataclass(frozen=True)
class CustomerRow:
    customer_id: int
    country_code: str

@dataclass(frozen=True)
class OrderRow:
    order_id: int
    customer_id: int
    ordered_at: datetime
    gross_amount: Decimal
    discount_amount: Decimal
    refund_amount: Decimal
    updated_at: datetime

    @property
    def net_amount(self) -> Decimal:
        return (self.gross_amount - self.discount_amount - self.refund_amount).quantize(CENT)

def generate_customers(count: int = 1_000) -> tuple[CustomerRow, ...]:
    if count <= 0:
        raise ValueError("customer count must be positive")
    return tuple(CustomerRow(i, COUNTRIES[(i - 1) % len(COUNTRIES)]) for i in range(1, count + 1))

def generate_orders(count: int = 10_000, customer_count: int = 1_000) -> tuple[OrderRow, ...]:
    if count <= 0 or customer_count <= 0:
        raise ValueError("counts must be positive")
    rows = []
    window_minutes = 30 * 24 * 60
    for order_id in range(1, count + 1):
        gross = (Decimal(5_000 + (order_id * 7_919) % 500_000) / 100).quantize(CENT)
        discount = (Decimal((order_id * 37) % 1_500) / 100).quantize(CENT)
        refund = (gross * Decimal("0.10")).quantize(CENT, rounding=ROUND_HALF_UP) if order_id % 17 == 0 else Decimal("0.00")
        ordered_at = BASE_TIME + timedelta(minutes=(order_id * 37) % window_minutes)
        rows.append(OrderRow(
            order_id=order_id,
            customer_id=((order_id * 73) % customer_count) + 1,
            ordered_at=ordered_at,
            gross_amount=gross,
            discount_amount=discount,
            refund_amount=refund,
            updated_at=ordered_at + timedelta(hours=order_id % 48),
        ))
    return tuple(rows)

def expected_net_revenue(rows: tuple[OrderRow, ...]) -> Decimal:
    return sum((row.net_amount for row in rows), start=Decimal("0.00")).quantize(CENT)
