SELECT COUNT(*) AS violation_count FROM cloud_required_references e FULL JOIN cloud_references a USING(dataset_id,reference_id)
    CROSS JOIN cloud_context c WHERE e.dataset_id IS NULL OR a.dataset_id IS NULL OR a.observed_at IS NULL
    OR a.observed_at>c.as_of OR c.as_of-a.observed_at>e.sla_minutes * INTERVAL '1 minute';
