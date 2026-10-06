WITH valid AS (SELECT order_id FROM etl_source WHERE gross_text ~ '^[0-9]+([.][0-9]{1,2})?$' AND discount_text ~ '^[0-9]+([.][0-9]{1,2})?$'),
invalid AS (SELECT order_id FROM etl_source WHERE NOT (gross_text ~ '^[0-9]+([.][0-9]{1,2})?$' AND discount_text ~ '^[0-9]+([.][0-9]{1,2})?$')),
accepted AS (SELECT 1 FROM valid v FULL JOIN etl_target t USING(order_id) WHERE v.order_id IS NULL OR t.order_id IS NULL),
rejected AS (SELECT 1 FROM invalid i FULL JOIN etl_rejects r USING(order_id) WHERE i.order_id IS NULL OR r.order_id IS NULL OR r.reason IS DISTINCT FROM 'INVALID_AMOUNT'),
duplicates AS (SELECT order_id FROM etl_rejects GROUP BY order_id HAVING COUNT(*)>1)
SELECT (SELECT COUNT(*) FROM accepted)+(SELECT COUNT(*) FROM rejected)+(SELECT COUNT(*) FROM duplicates) AS violation_count
