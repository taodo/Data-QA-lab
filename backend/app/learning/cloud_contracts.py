"""Version 1 bounded file contracts. No paths, networking or executable inputs."""
import csv
import io
import json
import re
from datetime import datetime, timezone
from decimal import Decimal

MAX_BYTES = 48 * 1024
MAX_ROWS = 400
MAX_DATASET_ROWS = 100
MAX_IMPORTS = 8
DATASETS = ("source", "bronze", "silver", "target")
RECORD_FIELDS = ("order_id", "customer_id", "amount", "updated_at", "event_id", "batch_no", "run_id")
CSV_FIELDS = ("dataset", *RECORD_FIELDS)
STATES = {"SUCCESS", "FAILED", "RUNNING", "CANCELLED", "UNKNOWN"}
STATE_MAP = {"Succeeded": "SUCCESS", "Completed": "SUCCESS", "Failed": "FAILED",
             "InProgress": "RUNNING", "Cancelled": "CANCELLED", **{s: s for s in STATES}}


def localized_error(message, language):
    if language == "ENG":
        return message
    messages = {
        "Invalid evidence fields": "Field evidence thiếu hoặc không nằm trong contract được hỗ trợ.",
        "Evidence identifiers must be 1–128 printable characters": "ID evidence cần 1–128 ký tự, không chứa ký tự điều khiển.",
        "Expected a non-negative integer": "Giá trị cần là số nguyên không âm; không dùng boolean.",
        "Expected an ISO timestamp with a UTC offset": "Timestamp cần theo ISO và có UTC offset.",
        "Invalid evidence timestamp": "Timestamp evidence không hợp lệ.",
        "Naive timestamps are not evidence": "Timestamp cần có timezone/UTC offset.",
        "Money must be an exact decimal string within NUMERIC(14,2)": "Amount cần là chuỗi decimal chính xác trong giới hạn NUMERIC(14,2).",
        "Dataset exceeds 100 rows": "Dataset vượt giới hạn 100 dòng.",
        "Evidence array exceeds its limit": "Danh sách metadata vượt giới hạn số phần tử.",
        "Duplicate JSON field": "JSON có field bị lặp.",
        "Use a plain filename without a path": "Dùng tên file đơn, không chứa đường dẫn.",
        "Choose a .json or .csv evidence file": "Chọn file evidence .json hoặc .csv.",
        "Evidence file must be at most 48 KiB UTF-8": "File evidence cần tối đa 48 KiB UTF-8 và không rỗng.",
        "Invalid evidence JSON": "JSON evidence không hợp lệ.",
        "Non-finite JSON number": "JSON không được chứa NaN hoặc Infinity.",
        "Unsupported evidence version": "Version evidence không được hỗ trợ; dùng version 1.",
        "Unsupported evidence provider": "Provider không được hỗ trợ; chọn Fabric, ADF hoặc OneLake.",
        "Duplicate run ID": "Run ID bị lặp trong metadata.",
        "Unknown activity dataset": "Dataset của activity không được hỗ trợ.",
        "Evidence exceeds 400 data rows": "Evidence vượt tổng 400 dòng dữ liệu.",
        "Unknown schema dataset": "Dataset của schema không được hỗ trợ.",
        "Malformed CSV evidence": "CSV evidence sai định dạng hoặc dấu nháy.",
        "Invalid or oversized CSV row": "Dòng CSV sai số cột hoặc vượt giới hạn số dòng.",
        "Unknown CSV dataset": "Dataset CSV cần là source, bronze, silver hoặc target.",
        "Invalid CSV integer": "Cột số nguyên của CSV không hợp lệ.",
        "CSV contains no snapshot rows": "CSV không chứa dòng snapshot.",
        "At most 8 imports per session; start a new session": "Mỗi session tối đa 8 import; hãy bắt đầu session mới.",
        "Evidence provider does not match this lesson": "Provider của evidence không khớp khóa học này.",
    }
    if message.startswith("CSV header must be: "):
        return "Header CSV cần là: " + ",".join(CSV_FIELDS)
    return messages.get(message, "Evidence không hợp lệ; kiểm tra version, field, kiểu dữ liệu và giới hạn file.")


def fields(value, allowed, required=()):
    if not isinstance(value, dict) or set(value) - set(allowed) or set(required) - set(value):
        raise ValueError("Invalid evidence fields")
    return value


def text(value, nullable=False):
    if nullable and value is None:
        return None
    if not isinstance(value, str) or not 1 <= len(value) <= 128 or any(ord(c) < 32 for c in value):
        raise ValueError("Evidence identifiers must be 1–128 printable characters")
    return value


def integer(value, nullable=False):
    if nullable and value is None:
        return None
    if type(value) is not int or not 0 <= value <= 2**63 - 1:
        raise ValueError("Expected a non-negative integer")
    return value


def timestamp(value, nullable=False):
    if nullable and value is None:
        return None
    if not isinstance(value, str) or len(value) > 40:
        raise ValueError("Expected an ISO timestamp with a UTC offset")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Invalid evidence timestamp") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("Naive timestamps are not evidence")
    return result.astimezone(timezone.utc)


def amount(value):
    if value is None:
        return None  # preserve a required-value defect rather than silently fabricating zero
    if not isinstance(value, str) or not re.fullmatch(r"-?[0-9]{1,12}(?:\.[0-9]{1,2})?", value):
        raise ValueError("Money must be an exact decimal string within NUMERIC(14,2)")
    return Decimal(value)


def records(values):
    if not isinstance(values, list) or len(values) > MAX_DATASET_ROWS:
        raise ValueError("Dataset exceeds 100 rows")
    result = []
    for row in values:
        fields(row, RECORD_FIELDS, RECORD_FIELDS)
        result.append((integer(row["order_id"]), integer(row["customer_id"]), amount(row["amount"]),
                       timestamp(row["updated_at"]), integer(row["event_id"]),
                       integer(row["batch_no"]), text(row["run_id"])))
    return result


def array(value, maximum):
    if not isinstance(value, list) or len(value) > maximum:
        raise ValueError("Evidence array exceeds its limit")
    return value


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


def parse_file(filename, file_format, content):
    if not isinstance(filename, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", filename):
        raise ValueError("Use a plain filename without a path")
    if file_format not in {"json", "csv"} or not filename.lower().endswith("." + file_format):
        raise ValueError("Choose a .json or .csv evidence file")
    if not isinstance(content, str) or not content or len(content.encode("utf-8")) > MAX_BYTES:
        raise ValueError("Evidence file must be at most 48 KiB UTF-8")
    if file_format == "csv":
        try:
            return _csv(content)
        except csv.Error as exc:
            raise ValueError("Malformed CSV evidence") from exc
    try:
        data = json.loads(content, object_pairs_hook=_pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Non-finite JSON number")))
    except (json.JSONDecodeError, RecursionError) as exc:
        raise ValueError("Invalid evidence JSON") from exc
    fields(data, ("version", "provider", "resource_id", "as_of", "runs", "activities", "datasets", "schema", "manifest", "references"),
           ("version", "provider", "as_of"))
    if type(data["version"]) is not int or data["version"] != 1:
        raise ValueError("Unsupported evidence version")
    if not isinstance(data["provider"], str) or data["provider"] not in {"Fabric", "ADF", "OneLake"}:
        raise ValueError("Unsupported evidence provider")
    normalized = {"version": 1, "provider": data["provider"],
                  "resource_id": text(data.get("resource_id"), True), "as_of": timestamp(data["as_of"]),
                  "runs": [], "activities": [], "schema": [], "manifest": [], "references": []}
    run_ids = set()
    for row in array(data.get("runs", []), 20):
        fields(row, ("run_id", "execution_status", "started_at", "ended_at"), ("run_id",))
        rid = text(row["run_id"])
        if rid in run_ids:
            raise ValueError("Duplicate run ID")
        run_ids.add(rid)
        status = text(row.get("execution_status"), True)
        normalized["runs"].append((rid, STATE_MAP.get(status, "UNKNOWN"),
                                   timestamp(row.get("started_at"), True), timestamp(row.get("ended_at"), True), row))
    for row in array(data.get("activities", []), 30):
        fields(row, ("activity_id", "run_id", "dependency_id", "execution_status", "source_dataset", "target_dataset", "rows_read", "rows_written"),
               ("activity_id", "run_id"))
        source, target = row.get("source_dataset"), row.get("target_dataset")
        if source not in (*DATASETS, None) or target not in (*DATASETS, None):
            raise ValueError("Unknown activity dataset")
        normalized["activities"].append((text(row["activity_id"]), text(row["run_id"]), text(row.get("dependency_id"), True),
            STATE_MAP.get(text(row.get("execution_status"), True), "UNKNOWN"), source, target,
            integer(row.get("rows_read"), True), integer(row.get("rows_written"), True), row))
    datasets = fields(data.get("datasets", {}), DATASETS)
    normalized["datasets"] = {name: records(datasets.get(name, [])) for name in DATASETS}
    if sum(map(len, normalized["datasets"].values())) > MAX_ROWS:
        raise ValueError("Evidence exceeds 400 data rows")
    for row in array(data.get("schema", []), 40):
        fields(row, ("dataset", "column_name", "data_type"), ("dataset", "column_name", "data_type"))
        if row["dataset"] not in DATASETS:
            raise ValueError("Unknown schema dataset")
        normalized["schema"].append((row["dataset"], text(row["column_name"]), text(row["data_type"])))
    for row in array(data.get("manifest", []), 50):
        fields(row, ("partition_key", "file_key", "row_count", "snapshot_at", "run_id"), ("partition_key", "file_key", "run_id"))
        normalized["manifest"].append((text(row["partition_key"]), text(row["file_key"]), integer(row.get("row_count"), True),
                                       timestamp(row.get("snapshot_at"), True), text(row["run_id"])))
    for row in array(data.get("references", []), 20):
        fields(row, ("dataset_id", "reference_id", "observed_at", "run_id"), ("dataset_id", "reference_id", "run_id"))
        normalized["references"].append((text(row["dataset_id"]), text(row["reference_id"]),
                                         timestamp(row.get("observed_at"), True), text(row["run_id"])))
    return normalized


def _csv(content):
    reader = csv.DictReader(io.StringIO(content, newline=""), strict=True)
    if reader.fieldnames != list(CSV_FIELDS):
        raise ValueError("CSV header must be: " + ",".join(CSV_FIELDS))
    datasets = {name: [] for name in DATASETS}
    for index, row in enumerate(reader):
        if index >= MAX_ROWS or None in row or any(value is None for value in row.values()):
            raise ValueError("Invalid or oversized CSV row")
        name = row.pop("dataset")
        if name not in DATASETS:
            raise ValueError("Unknown CSV dataset")
        for field in ("order_id", "customer_id", "event_id", "batch_no"):
            if not re.fullmatch(r"[0-9]{1,19}", row[field]):
                raise ValueError("Invalid CSV integer")
            row[field] = int(row[field])
        datasets[name].append(row)
    if not any(datasets.values()):
        raise ValueError("CSV contains no snapshot rows")
    return {"datasets": {name: records(rows) for name, rows in datasets.items()}}
