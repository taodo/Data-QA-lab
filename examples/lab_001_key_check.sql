-- Instructor smoke check: expected to PASS key-completeness grading.
SELECT
    (SELECT COUNT(*) FROM (
        SELECT order_id FROM source_orders
        EXCEPT SELECT order_id FROM target_orders
    ) AS missing_keys)
    +
    (SELECT COUNT(*) FROM (
        SELECT order_id FROM target_orders
        EXCEPT SELECT order_id FROM source_orders
    ) AS unexpected_keys) AS violation_count;
