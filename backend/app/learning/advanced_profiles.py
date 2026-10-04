"""Trusted SQL oracles and independent fixtures for Task 8. No learner SQL here."""

JOIN_SQL = """WITH expected AS (
 SELECT order_id, SUM(net_amount) AS net_amount FROM order_lines GROUP BY order_id
)
SELECT COUNT(*) AS violation_count FROM expected e FULL JOIN target_order_totals t USING(order_id)
WHERE e.order_id IS NULL OR t.order_id IS NULL OR e.net_amount IS DISTINCT FROM t.net_amount"""

LATEST_SQL = """WITH ranked AS (
 SELECT *, ROW_NUMBER() OVER(PARTITION BY order_id ORDER BY updated_at DESC,event_id DESC) AS rn
 FROM source_order_events
)
SELECT COUNT(*) AS violation_count FROM (SELECT * FROM ranked WHERE rn=1) e
FULL JOIN target_current_orders t USING(order_id)
WHERE e.order_id IS NULL OR t.order_id IS NULL OR e.event_id IS DISTINCT FROM t.event_id
 OR e.updated_at IS DISTINCT FROM t.updated_at OR e.net_amount IS DISTINCT FROM t.net_amount"""

UTC_SQL = """WITH expected AS (
 SELECT (ordered_at AT TIME ZONE 'UTC')::date AS order_date, COUNT(*) AS order_count,
 SUM(net_amount) AS net_revenue FROM source_time_orders
 GROUP BY (ordered_at AT TIME ZONE 'UTC')::date
)
SELECT COUNT(*) AS violation_count FROM expected e FULL JOIN target_utc_daily t USING(order_date)
WHERE e.order_date IS NULL OR t.order_date IS NULL OR e.order_count IS DISTINCT FROM t.order_count
 OR e.net_revenue IS DISTINCT FROM t.net_revenue"""

INCREMENTAL_SQL = """WITH ranked AS (
 SELECT e.*, ROW_NUMBER() OVER(PARTITION BY order_id ORDER BY event_at DESC,event_id DESC) AS rn
 FROM incremental_events e CROSS JOIN lab_context c WHERE e.arrived_at <= c.as_of
), expected AS (SELECT * FROM ranked WHERE rn=1), mismatches AS (
 SELECT 1 FROM expected e FULL JOIN incremental_target t USING(order_id)
 WHERE e.order_id IS NULL OR t.order_id IS NULL OR e.event_id IS DISTINCT FROM t.event_id
 OR e.event_at IS DISTINCT FROM t.event_at OR e.net_amount IS DISTINCT FROM t.net_amount
), duplicates AS (SELECT order_id FROM incremental_target GROUP BY order_id HAVING COUNT(*)>1)
SELECT (SELECT COUNT(*) FROM mismatches)+(SELECT COUNT(*) FROM duplicates) AS violation_count"""

FRESHNESS_SQL = """SELECT COUNT(*) AS violation_count
FROM freshness_requirements r LEFT JOIN freshness_observations o USING(dataset_id)
WHERE o.dataset_id IS NULL OR o.execution_status IS DISTINCT FROM 'SUCCESS'
 OR o.last_success_at IS NULL OR o.last_event_at IS NULL
 OR o.last_success_at > r.as_of OR o.last_event_at > r.as_of
 OR r.as_of-o.last_success_at > r.sla_minutes * INTERVAL '1 minute'
 OR r.as_of-o.last_event_at > r.sla_minutes * INTERVAL '1 minute'"""

SCD1_SQL = """WITH ranked AS (
 SELECT *, ROW_NUMBER() OVER(PARTITION BY customer_id ORDER BY effective_at DESC,event_id DESC) AS rn
 FROM source_customer_changes
)
SELECT COUNT(*) AS violation_count FROM (SELECT * FROM ranked WHERE rn=1) e
FULL JOIN target_customers_current t USING(customer_id)
WHERE e.customer_id IS NULL OR t.customer_id IS NULL OR e.tier IS DISTINCT FROM t.tier
 OR e.effective_at IS DISTINCT FROM t.effective_at OR e.event_id IS DISTINCT FROM t.event_id"""

SCD2_SQL = """WITH ranked AS (
 SELECT *, ROW_NUMBER() OVER(PARTITION BY customer_id,effective_at ORDER BY event_id DESC) AS rn
 FROM source_customer_changes
), expected AS (
 SELECT customer_id,tier,effective_at AS valid_from,
 LEAD(effective_at) OVER(PARTITION BY customer_id ORDER BY effective_at) AS valid_to
 FROM ranked WHERE rn=1
), mismatches AS (
 SELECT 1 FROM expected e FULL JOIN target_customer_history t
 ON e.customer_id=t.customer_id AND e.valid_from=t.valid_from
 WHERE e.customer_id IS NULL OR t.customer_id IS NULL OR e.tier IS DISTINCT FROM t.tier
 OR e.valid_to IS DISTINCT FROM t.valid_to OR t.is_current IS DISTINCT FROM (e.valid_to IS NULL)
), overlaps AS (
 SELECT 1 FROM target_customer_history a JOIN target_customer_history b
 ON a.customer_id=b.customer_id AND a.version_id<b.version_id
 AND a.valid_from<COALESCE(b.valid_to,'infinity'::timestamptz)
 AND b.valid_from<COALESCE(a.valid_to,'infinity'::timestamptz)
), current_keys AS (
 SELECT customer_id FROM target_customer_history GROUP BY customer_id
 HAVING COUNT(*) FILTER(WHERE is_current)<>1
), bad_ranges AS (
 SELECT 1 FROM target_customer_history WHERE valid_to<=valid_from
), duplicates AS (
 SELECT customer_id,valid_from FROM target_customer_history GROUP BY customer_id,valid_from HAVING COUNT(*)>1
)
SELECT (SELECT COUNT(*) FROM mismatches)+(SELECT COUNT(*) FROM overlaps)+
 (SELECT COUNT(*) FROM current_keys)+(SELECT COUNT(*) FROM bad_ranges)+
 (SELECT COUNT(*) FROM duplicates) AS violation_count"""

# Each oracle sees only its lesson's datasets plus a non-secret fixed clock/context.
SPECS = {
 "lab_007_join_grain": (("join_fanout","join_missing"), ("clean","adv_shifted","join_fanout","join_fanout_two","join_missing","join_unexpected","join_null","join_zero"), JOIN_SQL, ("lab_context","order_lines","order_payments","target_order_totals")),
 "lab_008_latest_version": (("latest_stale","latest_tie"), ("clean","adv_shifted","latest_stale","latest_stale_two","latest_tie","latest_missing","latest_null"), LATEST_SQL, ("lab_context","source_order_events","target_current_orders")),
 "lab_009_utc_dates": (("utc_local_day","utc_missing"), ("clean","adv_shifted","utc_connection_zone","utc_local_day","utc_missing","utc_null"), UTC_SQL, ("lab_context","source_time_orders","target_utc_daily")),
 "lab_010_incremental": (("inc_append","inc_event_watermark"), ("clean","adv_shifted","inc_append","inc_event_watermark","inc_stale","inc_missing"), INCREMENTAL_SQL, ("lab_context","incremental_events","incremental_target","incremental_steps")),
 "lab_011_freshness": (("fresh_stale","fresh_missing","fresh_failed"), ("clean","adv_shifted","fresh_boundary","fresh_stale","fresh_load_stale","fresh_missing","fresh_null","fresh_future","fresh_failed","fresh_multiple"), FRESHNESS_SQL, ("lab_context","freshness_requirements","freshness_observations")),
 "lab_012_scd_type1": (("scd1_stale","scd1_tie"), ("clean","adv_shifted","scd1_stale","scd1_tie","scd1_missing","scd1_null"), SCD1_SQL, ("lab_context","source_customer_changes","target_customers_current")),
 "lab_013_scd_type2": (("scd2_overlap","scd2_two_current","scd2_missing"), ("clean","adv_shifted","scd2_overlap","scd2_two_current","scd2_missing","scd2_invalid","scd2_duplicate","scd2_wrong_tier","scd2_gap"), SCD2_SQL, ("lab_context","source_customer_changes","target_customer_history")),
}

ADVANCED_TABLES = tuple(dict.fromkeys(table for spec in SPECS.values() for table in spec[3]))
ADVANCED_VARIANTS = {variant for spec in SPECS.values() for variant in spec[1]}
