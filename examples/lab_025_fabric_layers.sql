SELECT (SELECT COUNT(*) FROM (SELECT DISTINCT ON (order_id) order_id,customer_id,amount,updated_at,event_id,batch_no,run_id
 FROM cloud_source WHERE batch_no<=(SELECT batch_no FROM cloud_context)
 AND updated_at<=(SELECT as_of FROM cloud_context) ORDER BY order_id,event_id DESC) s FULL JOIN cloud_bronze t USING(order_id)
    WHERE s.order_id IS NULL OR t.order_id IS NULL OR s.customer_id IS DISTINCT FROM t.customer_id
    OR s.amount IS DISTINCT FROM t.amount OR s.event_id IS DISTINCT FROM t.event_id
    OR s.updated_at IS DISTINCT FROM t.updated_at) + (SELECT COUNT(*) FROM (SELECT * FROM cloud_bronze) s FULL JOIN cloud_silver t USING(order_id)
    WHERE s.order_id IS NULL OR t.order_id IS NULL OR s.customer_id IS DISTINCT FROM t.customer_id
    OR s.amount IS DISTINCT FROM t.amount OR s.event_id IS DISTINCT FROM t.event_id
    OR s.updated_at IS DISTINCT FROM t.updated_at) + (SELECT COUNT(*) FROM (SELECT * FROM cloud_silver) s FULL JOIN cloud_target t USING(order_id)
    WHERE s.order_id IS NULL OR t.order_id IS NULL OR s.customer_id IS DISTINCT FROM t.customer_id
    OR s.amount IS DISTINCT FROM t.amount OR s.event_id IS DISTINCT FROM t.event_id
    OR s.updated_at IS DISTINCT FROM t.updated_at) + (SELECT COUNT(*) FROM (SELECT order_id FROM cloud_bronze GROUP BY order_id HAVING COUNT(*)>1) d) + (SELECT COUNT(*) FROM (SELECT order_id FROM cloud_silver GROUP BY order_id HAVING COUNT(*)>1) d) + (SELECT COUNT(*) FROM (SELECT order_id FROM cloud_target GROUP BY order_id HAVING COUNT(*)>1) d) AS violation_count;
