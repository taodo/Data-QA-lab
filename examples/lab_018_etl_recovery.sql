SELECT (SELECT COUNT(*) AS violation_count FROM etl_source s FULL JOIN etl_target t USING(order_id)
WHERE s.order_id IS NULL OR t.order_id IS NULL OR t.net_amount IS DISTINCT FROM (s.gross_text::numeric-s.discount_text::numeric)) + (SELECT COUNT(*) FROM etl_steps WHERE step_no=(SELECT MAX(step_no) FROM etl_steps)
 AND (execution_status IS DISTINCT FROM 'SUCCESS' OR checkpoint IS DISTINCT FROM 1)) AS violation_count
