"""Reset only Data QA Lab source tables and load a deterministic clean baseline."""
from backend.app.persistence.database import transaction
from pipeline.source.generator import generate_customers, generate_orders, expected_net_revenue

def seed_source(database_url: str, order_count: int = 10_000) -> dict[str, object]:
    customers = generate_customers()
    orders = generate_orders(order_count, len(customers))
    with transaction(database_url) as connection:
        connection.execute("TRUNCATE source.orders, source.customers")
        with connection.cursor() as cursor:
            cursor.executemany(
                "INSERT INTO source.customers (customer_id, country_code) VALUES (%s, %s)",
                [(row.customer_id, row.country_code) for row in customers],
            )
            cursor.executemany(
                """INSERT INTO source.orders
                   (order_id, customer_id, ordered_at, gross_amount, discount_amount, refund_amount, updated_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                [(row.order_id, row.customer_id, row.ordered_at, row.gross_amount,
                  row.discount_amount, row.refund_amount, row.updated_at) for row in orders],
            )
    return {
        "customers": len(customers),
        "orders": len(orders),
        "expected_net_revenue": str(expected_net_revenue(orders)),
    }
