"""Prepare only the dedicated local lab database; preserve existing run/history."""
import json
from backend.app.config import Settings
from backend.app.persistence.database import connect, initialize_database
from backend.app.learning.sql_runtime import initialize_sql_security


def prepare_local(database_url):
    initialize_database(database_url)
    initialize_sql_security(database_url)
    with connect(database_url) as connection:
        row = connection.execute("""SELECT p.run_id FROM metadata.pipeline_runs p
            WHERE p.pipeline_id='orders_v1' AND p.execution_status='SUCCESS'
            AND (SELECT COUNT(*) FROM bronze.orders b WHERE b.run_id=p.run_id)>=2
            ORDER BY p.started_at DESC LIMIT 1""").fetchone()
    if row:
        return {"status":"READY", "created_baseline":False, "run_id":str(row[0])}
    from pipeline.source.seed import seed_source
    from pipeline.jobs.orders import run_orders_pipeline
    seed_source(database_url, 1000)
    run = run_orders_pipeline(database_url)
    if run.execution_status != "SUCCESS":
        raise RuntimeError("Initial pipeline failed; inspect pipeline run evidence")
    return {"status":"READY", "created_baseline":True, "run_id":str(run.run_id)}


if __name__ == "__main__":
    print(json.dumps(prepare_local(Settings.from_env().database_url)), flush=True)
