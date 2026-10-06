SELECT (SELECT COUNT(*) FROM az_required_access e FULL JOIN az_access a USING(observation_id)
        CROSS JOIN cloud_context c WHERE e.observation_id IS NULL OR a.observation_id IS NULL
        OR e.identity_id IS DISTINCT FROM a.identity_id OR e.scope IS DISTINCT FROM a.scope
        OR e.operation IS DISTINCT FROM a.operation OR a.outcome IS DISTINCT FROM 'ALLOWED'
        OR a.observed_at IS NULL OR c.as_of IS NULL OR a.observed_at>c.as_of) +
        (SELECT COUNT(*) FROM (SELECT observation_id FROM az_access GROUP BY observation_id HAVING COUNT(*)>1) d) AS violation_count;
