SELECT
    (SELECT COUNT(*) FROM cloud_activities a LEFT JOIN cloud_runs r USING(run_id)
     WHERE r.run_id IS NULL OR r.execution_status='UNKNOWN' OR a.execution_status='UNKNOWN'
     OR a.source_dataset IS NULL OR a.target_dataset IS NULL) +
    (SELECT COUNT(*) FROM cloud_activities a LEFT JOIN cloud_activities d ON a.dependency_id=d.activity_id AND a.run_id=d.run_id
     WHERE a.dependency_id IS NOT NULL AND (d.activity_id IS NULL OR d.execution_status IS DISTINCT FROM 'SUCCESS')) +
    (SELECT COUNT(*) FROM cloud_target t LEFT JOIN cloud_runs r USING(run_id) WHERE r.run_id IS NULL)
    AS violation_count;
