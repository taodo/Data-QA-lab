"""Restricted login per query; PostgreSQL permissions are the security boundary."""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import json
import secrets
from threading import Event, Timer
from uuid import uuid4

from backend.app.persistence.database import connect, transaction
from backend.app.learning.contracts import QueryLimits, QueryResult, SqlSecurityError, normalize_sql
from backend.app.learning.workspace import TABLES, populate_query_snapshot


def initialize_sql_security(database_url):
    """Explicit hardening for the dedicated local lab database."""
    from psycopg import sql
    with transaction(database_url) as connection:
        if not connection.execute("SELECT rolsuper FROM pg_roles WHERE rolname=current_user").fetchone()[0]:
            raise SqlSecurityError("The dedicated local lab provisioning connection requires a superuser")
        db = connection.execute("SELECT current_database()").fetchone()[0]
        # Do not change PUBLIC privileges on an unrelated populated public schema.
        count = connection.execute(
            """SELECT (SELECT COUNT(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                       WHERE n.nspname='public') +
                      (SELECT COUNT(*) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
                       WHERE n.nspname='public')"""
        ).fetchone()[0]
        if count:
            raise SqlSecurityError("Use a dedicated lab database with an empty public schema")
        connection.execute(sql.SQL("REVOKE CREATE, TEMPORARY ON DATABASE {} FROM PUBLIC").format(
            sql.Identifier(db)))
        connection.execute("REVOKE ALL ON SCHEMA public FROM PUBLIC")


def _audit_permissions(connection, schema):
    # PUBLIC grants apply even to a NOINHERIT role. Fail closed on misconfiguration.
    db_rights = connection.execute(
        "SELECT has_database_privilege(current_database(), 'CREATE'), "
        "has_database_privilege(current_database(), 'TEMP')"
    ).fetchone()
    if any(db_rights):
        raise SqlSecurityError("Run lab-sql-init: learner inherits PUBLIC CREATE/TEMP rights")
    row = connection.execute(
        "SELECT rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls "
        "FROM pg_roles WHERE rolname=current_user"
    ).fetchone()
    if any(row):
        raise SqlSecurityError("Learner login has elevated privileges")
    memberships = connection.execute(
        "SELECT COUNT(*) FROM pg_auth_members WHERE member = "
        "(SELECT oid FROM pg_roles WHERE rolname=current_user)"
    ).fetchone()[0]
    if memberships:
        raise SqlSecurityError("Learner login must not have role memberships")
    accessible = connection.execute(
        """SELECT nspname FROM pg_namespace
           WHERE nspname NOT LIKE 'pg_%%' AND nspname <> 'information_schema'
           AND has_schema_privilege(oid, 'USAGE')"""
    ).fetchall()
    if {row[0] for row in accessible} != {schema}:
        raise SqlSecurityError("Learner can access a non-allowlisted schema")
    objects = connection.execute(
        """SELECT n.nspname, c.relname,
                  has_table_privilege(c.oid, 'SELECT'),
                  has_table_privilege(c.oid, 'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
           FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
           WHERE n.nspname NOT LIKE 'pg_%%' AND n.nspname <> 'information_schema'
           AND c.relkind IN ('r','v','m','p','f')"""
    ).fetchall()
    if any(write or (read and (ns != schema or table not in TABLES))
           for ns, table, read, write in objects):
        raise SqlSecurityError("Learner object privileges exceed the SELECT allowlist")
    if connection.execute(
        """SELECT COUNT(*) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
           WHERE n.nspname NOT LIKE 'pg_%%' AND n.nspname <> 'information_schema'
           AND has_function_privilege(p.oid, 'EXECUTE')"""
    ).fetchone()[0]:
        raise SqlSecurityError("Learner can execute a non-system routine")


@contextmanager
def restricted_workspace(database_url, snapshot, variant="current", limits=QueryLimits()):
    import psycopg
    from psycopg import sql
    token = uuid4().hex
    schema = "learner_query_" + token
    role = "learner_role_" + token
    password = secrets.token_urlsafe(32)
    with transaction(database_url) as admin:
        populate_query_snapshot(admin, schema, snapshot, variant)
        # Short-lived credentials are not printed or persisted in metadata.
        admin.execute(sql.SQL(
            "CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE "
            "NOINHERIT NOREPLICATION NOBYPASSRLS CONNECTION LIMIT 1 VALID UNTIL {}"
        ).format(sql.Identifier(role), sql.Literal(password),
                 sql.Literal((datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat())))
        admin.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
            sql.Identifier(schema), sql.Identifier(role)))
        for table in TABLES:
            admin.execute(sql.SQL("GRANT SELECT ON {}.{} TO {}").format(
                sql.Identifier(schema), sql.Identifier(table), sql.Identifier(role)))
        admin.execute(sql.SQL("ALTER ROLE {} SET temp_file_limit = '16MB'").format(sql.Identifier(role)))
    learner = None
    try:
        learner = psycopg.connect(
            database_url, user=role, password=password, connect_timeout=5,
            options=f"-c search_path={schema},pg_catalog -c default_transaction_read_only=on "
                    f"-c statement_timeout={limits.timeout_ms} -c lock_timeout=500 "
                    "-c idle_in_transaction_session_timeout=5000 -c work_mem=1MB",
        )
        learner.execute("SET TRANSACTION READ ONLY")
        _audit_permissions(learner, schema)
        yield learner, schema, role
    finally:
        if learner is not None:
            learner.close()  # always rollback, even for SELECT side effects
        with transaction(database_url) as admin:
            admin.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
            admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


def _terminate_execution(database_url, pid, role, timed_out):
    timed_out.set()
    with connect(database_url) as admin:
        admin.execute(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid=%s AND usename=%s",
            (pid, role),
        )


def run_sql(database_url, snapshot, query, variant="current", limits=QueryLimits()):
    from psycopg import sql
    import psycopg
    query = normalize_sql(query)
    timed_out = Event()
    try:
        with restricted_workspace(database_url, snapshot, variant, limits) as (connection, schema, role):
            watchdog = Timer(limits.watchdog_ms / 1000, _terminate_execution,
                             (database_url, connection.info.backend_pid, role, timed_out))
            watchdog.daemon = True
            watchdog.start()
            try:
                # Extended protocol + DECLARE parses exactly one SELECT. Describe
                # obtains shape without buffering an unbounded query result.
                with connection.cursor(name="learner_shape") as cursor:
                    cursor.execute(query)
                    columns = tuple(column.name for column in cursor.description)
                if len(columns) > limits.max_columns:
                    return QueryResult("ERROR", error="COLUMN_LIMIT")
                aliases = tuple(f"cell_{index}" for index in range(len(columns)))
                projection = sql.SQL(", ").join(
                    sql.SQL("left({}::text, {})").format(sql.Identifier(alias),
                                                      sql.Literal(limits.cell_chars + 1))
                    for alias in aliases
                )
                bounded = sql.SQL("SELECT {} FROM ({}\n) AS bounded({}) LIMIT {}").format(
                    projection, sql.SQL(query),
                    sql.SQL(", ").join(map(sql.Identifier, aliases)),
                    sql.Literal(limits.max_rows + 1),
                )
                rows, truncated = [], False
                size = len(json.dumps({
                    "status": "SUCCESS", "columns": columns, "rows": [],
                    "truncated": False, "error": None,
                }, ensure_ascii=False).encode("utf-8"))
                if size > limits.max_bytes:
                    return QueryResult("ERROR", error="OUTPUT_LIMIT")
                with connection.cursor(name="learner_result") as cursor:
                    cursor.execute(bounded)
                    while (row := cursor.fetchone()) is not None:
                        if len(rows) >= limits.max_rows:
                            truncated = True
                            break
                        if any(cell is not None and len(cell) > limits.cell_chars for cell in row):
                            truncated = True
                        clipped = tuple(None if cell is None else cell[:limits.cell_chars] for cell in row)
                        row_size = len(json.dumps(clipped, ensure_ascii=False).encode("utf-8")) + 2
                        if size + row_size > limits.max_bytes:
                            truncated = True
                            break
                        rows.append(clipped)
                        size += row_size
                return QueryResult("SUCCESS", columns, tuple(rows), truncated)
            finally:
                watchdog.cancel()
                watchdog.join()
    except SqlSecurityError:
        raise  # provisioning/permission blockers require operator action
    except psycopg.Error as exc:
        # Do not echo server details/private identifiers or grading fixture values.
        code = "TIMEOUT" if timed_out.is_set() or exc.sqlstate == "57014" else "SQL_ERROR"
        return QueryResult("ERROR", error=code)
