"""Minimal PostgreSQL boundary; psycopg is imported only when database commands run."""
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Any

SCHEMA_PATH = Path(__file__).with_name("schema.sql")

def connect(database_url: str):
    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError(
            "PostgreSQL support is not installed. Run: python -m pip install -e ."
        ) from exc
    return psycopg.connect(database_url)

@contextmanager
def transaction(database_url: str) -> Iterator[Any]:
    with connect(database_url) as connection:
        with connection.transaction():
            yield connection

def initialize_database(database_url: str) -> None:
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with transaction(database_url) as connection:
        connection.execute(sql)
