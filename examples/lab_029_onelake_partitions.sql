SELECT (SELECT COUNT(*) FROM cloud_expected_partitions e FULL JOIN
    (SELECT partition_key,SUM(row_count) AS row_count FROM cloud_manifest GROUP BY partition_key) a USING(partition_key)
    WHERE e.partition_key IS NULL OR a.partition_key IS NULL OR e.row_count IS DISTINCT FROM a.row_count) +
    (SELECT COUNT(*) FROM (SELECT file_key FROM cloud_manifest GROUP BY file_key HAVING COUNT(*)>1) d)
    AS violation_count;
