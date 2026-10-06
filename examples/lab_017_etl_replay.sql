WITH ranked AS (SELECT s.*,ROW_NUMBER() OVER(PARTITION BY order_id ORDER BY event_id DESC) rn
 FROM etl_source s CROSS JOIN etl_context c WHERE arrived_batch<=c.batch_no),
expected AS (SELECT * FROM ranked WHERE rn=1), mismatches AS (
 SELECT 1 FROM expected e FULL JOIN etl_target t USING(order_id)
 WHERE e.order_id IS NULL OR t.order_id IS NULL OR e.event_id IS DISTINCT FROM t.event_id
 OR t.net_amount IS DISTINCT FROM (e.gross_text::numeric-e.discount_text::numeric)),
duplicates AS (SELECT order_id FROM etl_target GROUP BY order_id HAVING COUNT(*)>1)
SELECT (SELECT COUNT(*) FROM mismatches)+(SELECT COUNT(*) FROM duplicates) AS violation_count
