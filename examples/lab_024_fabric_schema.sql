SELECT (SELECT COUNT(*) FROM cloud_expected_schema e FULL JOIN cloud_schema a USING(dataset,column_name)
    WHERE e.column_name IS NULL OR a.column_name IS NULL OR e.data_type IS DISTINCT FROM a.data_type) +
    (SELECT COUNT(*) FROM (SELECT dataset,column_name FROM cloud_schema GROUP BY dataset,column_name HAVING COUNT(*)>1) d)
    AS violation_count;
