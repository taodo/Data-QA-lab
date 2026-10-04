-- Instructor smoke check: expected to FAIL grading despite valid SQL execution.
SELECT abs(
    (SELECT COUNT(*) FROM source_orders)
    - (SELECT COUNT(*) FROM target_orders)
) AS violation_count;
