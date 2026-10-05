"""Bounded declarative API checks against a real loopback HTTP fixture server.

No learner code, external URLs or account cookies enter the HTTP client. The
fixture is per invocation, bound to an ephemeral loopback port and closed in a
finally block. Network evidence is persisted by the learning service.
"""

from contextlib import contextmanager
from copy import deepcopy
from decimal import Decimal, InvalidOperation
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import socket
from threading import Thread
import time
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler
from psycopg import sql

IDS = (
    "lab_019_api_contract",
    "lab_020_api_pagination",
    "lab_021_api_retry",
    "lab_022_api_ingestion",
)
SCENARIOS = {
    IDS[0]: ("api_missing_field", "api_wrong_type", "api_wrong_status"),
    IDS[1]: ("api_missing_page", "api_duplicate_page"),
    IDS[2]: ("api_exhausted", "api_timeout"),
    IDS[3]: ("api_ingest_missing", "api_ingest_wrong", "api_ingest_duplicate"),
}
TABLES = ("api_context", "api_expected", "api_target")
DDL = {
    "api_context": "lab_id text",
    "api_expected": "order_id bigint, customer_id bigint, net_amount numeric(18,2)",
    "api_target": "order_id bigint, customer_id bigint, net_amount numeric(18,2)",
}
BASE = {
    "method": "GET",
    "path": "/orders",
    "page_size": 2,
    "paginate": True,
    "max_attempts": 3,
    "timeout_ms": 150,
    "ingest": False,
    "idempotent": True,
    "checks": {"status": 200},
}
RULES = {
    IDS[0]: {
        "status": 200,
        "required": ["order_id", "customer_id", "net_amount"],
        "types": {
            "order_id": "integer",
            "customer_id": "integer",
            "net_amount": "decimal",
        },
    },
    IDS[1]: {"status": 200, "complete": True, "unique": True},
    IDS[2]: {"status": 200, "complete": True},
    IDS[3]: {"status": 200, "complete": True, "unique": True, "reconcile": True},
}
SOLUTIONS = {
    key: json.dumps({**BASE, "ingest": key == IDS[3], "checks": RULES[key]}, indent=2)
    for key in IDS
}


def parse(text):
    if not isinstance(text, str) or len(text.encode()) > 16384:
        raise ValueError("API plan exceeds 16 KiB")

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON property")
            result[key] = value
        return result

    try:
        plan = json.loads(
            text,
            object_pairs_hook=pairs,
            parse_constant=lambda _: (_ for _ in ()).throw(
                ValueError("Non-finite JSON")
            ),
        )
    except (json.JSONDecodeError, RecursionError) as exc:
        raise ValueError("Use a JSON request/check plan") from exc
    if not isinstance(plan, dict) or set(plan) - set(BASE):
        raise ValueError("Unknown API plan field")
    plan = {**BASE, **plan}
    if plan["method"] != "GET" or plan["path"] != "/orders":
        raise ValueError("Use GET /orders in the local playground")
    for key, lo, hi in (
        ("page_size", 1, 5),
        ("max_attempts", 1, 3),
        ("timeout_ms", 50, 300),
    ):
        if type(plan[key]) is not int or not lo <= plan[key] <= hi:
            raise ValueError("API request limit out of range")
    for key in ("paginate", "ingest", "idempotent"):
        if type(plan[key]) is not bool:
            raise ValueError("Boolean API option required")
    checks = plan["checks"]
    if (
        not isinstance(checks, dict)
        or not checks
        or set(checks)
        - {"status", "required", "types", "complete", "unique", "reconcile"}
    ):
        raise ValueError("Unknown or empty API checks")
    if "status" in checks and (
        type(checks["status"]) is not int or not 100 <= checks["status"] <= 599
    ):
        raise ValueError("Invalid expected status")
    for key in ("complete", "unique", "reconcile"):
        if key in checks and type(checks[key]) is not bool:
            raise ValueError("Boolean check required")
    fields = {"order_id", "customer_id", "net_amount"}
    if "required" in checks and (
        not isinstance(checks["required"], list)
        or any(not isinstance(x, str) or x not in fields for x in checks["required"])
        or len(checks["required"]) > 3
        or len(set(checks["required"])) != len(checks["required"])
    ):
        raise ValueError("Invalid required fields")
    if "types" in checks and (
        not isinstance(checks["types"], dict)
        or set(checks["types"]) - fields
        or any(
            v not in ("integer", "decimal", "string") for v in checks["types"].values()
        )
    ):
        raise ValueError("Invalid field types")
    return plan


def create(c, s, lab_id):
    from backend.app.learning.workspace import require_schema

    require_schema(s)
    c.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(s)))
    for table, ddl in DDL.items():
        c.execute(
            sql.SQL("CREATE TABLE {}.{} ({})").format(
                sql.Identifier(s), sql.Identifier(table), sql.SQL(ddl)
            )
        )
    c.execute(
        sql.SQL("INSERT INTO {}.api_context VALUES (%s)").format(sql.Identifier(s)),
        (lab_id,),
    )
    for key, customer, amount in (
        (101, 41, "10.00"),
        (203, 52, "0.00"),
        (307, 41, "30.44"),
        (409, 52, "100.98"),
        (511, 41, "0.01"),
    ):
        c.execute(
            sql.SQL("INSERT INTO {}.api_expected VALUES (%s,%s,%s)").format(
                sql.Identifier(s)
            ),
            (key, customer, Decimal(amount)),
        )


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


@contextmanager
def fixture(rows, lab_id, variant):
    records = deepcopy(rows)
    if variant == "api_missing_field":
        records[-1].pop("net_amount")
    if variant == "api_wrong_type":
        records[-1]["customer_id"] = str(records[-1]["customer_id"])
    if variant in ("api_missing_page", "api_ingest_missing"):
        records = records[:-1]
    if variant in ("api_duplicate_page", "api_ingest_duplicate"):
        records.append(deepcopy(records[-1]))
    if variant == "api_ingest_wrong":
        records[-1]["net_amount"] = "0.02"
    attempts = {}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            parts = urlsplit(self.path)
            if parts.path != "/orders":
                self.send_error(404)
                return
            args = parse_qs(parts.query)
            page = int(args.get("page", ["1"])[0])
            size = int(args.get("page_size", ["2"])[0])
            attempts[page] = attempts.get(page, 0) + 1
            status = 200
            if variant == "api_wrong_status":
                status = 503
            if lab_id == IDS[2] and attempts[page] < 3:
                status = 429 if attempts[page] == 1 else 503
            if variant == "api_exhausted":
                status = 503
            if variant == "api_timeout":
                time.sleep(0.35)
            start = (page - 1) * size
            payload = (
                {
                    "items": records[start : start + size],
                    "next_page": page + 1 if start + size < len(records) else None,
                    "total": len(records),
                }
                if status == 200
                else {"error": "TEMPORARILY_UNAVAILABLE"}
            )
            data = json.dumps(payload).encode()
            try:
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                if status == 429:
                    self.send_header("Retry-After", "0")
                self.end_headers()
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    thread = Thread(
        target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True
    )
    thread.start()
    try:
        yield "http://127.0.0.1:" + str(server.server_port)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)


def _decimal(value):
    try:
        return isinstance(value, str) and Decimal(value).is_finite()
    except InvalidOperation:
        return False


def count_violations(checks, records, trace, expected, target):
    count = 0
    if "status" in checks:
        count += sum(t["status"] != checks["status"] for t in trace if t["final"])
    for item in records:
        bad = any(
            name not in item or item[name] is None
            for name in checks.get("required", [])
        )
        for name, kind in checks.get("types", {}).items():
            value = item.get(name)
            good = (
                type(value) is int
                if kind == "integer"
                else isinstance(value, str)
                if kind == "string"
                else _decimal(value)
            )
            bad = bad or not good
        count += bad
    ids = [r.get("order_id") for r in records]
    expected_ids = {r["order_id"] for r in expected}
    if checks.get("complete"):
        count += len(expected_ids - set(ids)) + len(set(ids) - expected_ids)
    if checks.get("unique"):
        count += sum(ids.count(key) > 1 for key in set(ids))
    if checks.get("reconcile"):
        actual = {r["order_id"]: r for r in target}
        for key in expected_ids | set(actual):
            e = next((r for r in expected if r["order_id"] == key), None)
            a = actual.get(key)
            count += (
                e is None
                or a is None
                or e["customer_id"] != a["customer_id"]
                or Decimal(e["net_amount"]) != Decimal(a["net_amount"])
            )
        count += sum(sum(r["order_id"] == key for r in target) > 1 for key in actual)
    return int(count)


def run(c, s, lab_id, text, variant="clean", persist=False):
    from backend.app.learning.workspace import require_schema

    require_schema(s)
    plan = parse(text)
    source = c.execute(
        sql.SQL(
            "SELECT order_id,customer_id,net_amount FROM {}.api_expected ORDER BY order_id"
        ).format(sql.Identifier(s))
    ).fetchall()
    expected = [
        {"order_id": r[0], "customer_id": r[1], "net_amount": str(r[2])} for r in source
    ]
    if variant == "api_shifted":
        expected = [
            {
                **r,
                "order_id": r["order_id"] + 10000,
                "net_amount": str(Decimal(r["net_amount"]) + Decimal("1.00")),
            }
            for r in reversed(expected)
        ]
    # Every run starts from its own empty ingestion target. Replay is within this run.
    records = []
    trace = []
    target = []
    opener = build_opener(ProxyHandler({}), NoRedirect())
    with fixture(expected, lab_id, variant) as address:
        page = 1
        for _ in range(10):
            payload = {}
            final_status = None
            for attempt in range(1, plan["max_attempts"] + 1):
                started = time.monotonic()
                headers = {}
                raw = b""
                try:
                    try:
                        reply = opener.open(
                            Request(
                                address
                                + f"/orders?page={page}&page_size={plan['page_size']}",
                                method="GET",
                            ),
                            timeout=plan["timeout_ms"] / 1000,
                        )
                    except HTTPError as exc:
                        reply = exc
                    with reply:
                        final_status = reply.code
                        headers = {
                            k: v
                            for k, v in reply.headers.items()
                            if k.lower() in ("content-type", "retry-after")
                        }
                        raw = reply.read(65537)
                    if len(raw) > 65536:
                        raise RuntimeError("Fixture exceeded response bound")
                    payload = json.loads(raw)
                except (TimeoutError, socket.timeout, URLError):
                    final_status = None
                    payload = {"error": "TIMEOUT"}
                retry = (
                    final_status in (None, 429, 503) and attempt < plan["max_attempts"]
                )
                trace.append(
                    {
                        "page": page,
                        "attempt": attempt,
                        "status": final_status,
                        "headers": headers,
                        "elapsed_ms": round((time.monotonic() - started) * 1000),
                        "final": not retry,
                        "body": payload,
                    }
                )
                if not retry:
                    break
                time.sleep(0.01)
            if final_status != 200:
                break
            records.extend(payload["items"])
            if not plan["paginate"] or payload["next_page"] is None:
                break
            page = payload["next_page"]
    if plan["ingest"]:
        if persist:
            c.execute(sql.SQL("DELETE FROM {}.api_target").format(sql.Identifier(s)))
        # Two replays of the same HTTP batch expose append-vs-upsert behavior.
        for _ in range(2):
            for row in records:
                if (
                    type(row.get("order_id")) is not int
                    or type(row.get("customer_id")) is not int
                    or not _decimal(row.get("net_amount"))
                ):
                    continue
                if plan["idempotent"]:
                    target = [r for r in target if r["order_id"] != row["order_id"]]
                target.append(row)
                if persist:
                    if plan["idempotent"]:
                        c.execute(
                            sql.SQL(
                                "DELETE FROM {}.api_target WHERE order_id=%s"
                            ).format(sql.Identifier(s)),
                            (row["order_id"],),
                        )
                    c.execute(
                        sql.SQL("INSERT INTO {}.api_target VALUES (%s,%s,%s)").format(
                            sql.Identifier(s)
                        ),
                        (
                            row["order_id"],
                            row["customer_id"],
                            Decimal(row["net_amount"]),
                        ),
                    )
        if persist:
            # Verification reads the actual persisted database Target, not a preview list.
            target = [
                {"order_id": r[0], "customer_id": r[1], "net_amount": str(r[2])}
                for r in c.execute(
                    sql.SQL(
                        "SELECT order_id,customer_id,net_amount FROM {}.api_target ORDER BY order_id"
                    ).format(sql.Identifier(s))
                ).fetchall()
            ]
    count = count_violations(plan["checks"], records, trace, expected, target)
    return {
        "status": "SUCCESS",
        "columns": ["violation_count"],
        "rows": [[str(count)]],
        "truncated": False,
        "error": None,
        "http": {
            "method": "GET",
            "path": "/orders",
            "trace": trace,
            "records": records,
            "expected": expected,
            "target": target,
            "request_count": len(trace),
            "execution_status": "SUCCESS"
            if trace and trace[-1]["status"] == 200
            else "FAILED",
            "data_quality_status": "PASS" if count == 0 else "FAIL",
            "replayed_batches": 2 if plan["ingest"] else 0,
        },
    }


def expected_count(lab_id, variant):
    """Independent fixture expectations, never derived from learner check settings."""
    if variant in ("clean", "api_clean", "api_shifted"):
        return 0
    return {
        "api_missing_field": 1,
        "api_wrong_type": 1,
        "api_wrong_status": 1,
        "api_missing_page": 1,
        "api_duplicate_page": 1,
        "api_exhausted": 6,
        "api_timeout": 6,
        "api_ingest_missing": 2,
        "api_ingest_wrong": 1,
        "api_ingest_duplicate": 1,
    }[variant]
