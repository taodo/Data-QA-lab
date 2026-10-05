WITH expected AS (SELECT s.order_id,c.customer_id FROM etl_source s JOIN etl_customers c USING(customer_code))
SELECT COUNT(*) AS violation_count FROM expected e FULL JOIN etl_target t USING(order_id)
WHERE e.order_id IS NULL OR t.order_id IS NULL OR e.customer_id IS DISTINCT FROM t.customer_id
