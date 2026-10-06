"""Environment configuration for the local PostgreSQL adapter."""
from dataclasses import dataclass
import os

DEFAULT_DATABASE_URL = "postgresql://data_qa_lab:data_qa_lab@127.0.0.1:5432/data_qa_lab"

@dataclass(frozen=True)
class Settings:
    database_url: str

    @classmethod
    def from_env(cls) -> "Settings":
        if os.getenv("DATA_QA_DATABASE_HOST"):
            from psycopg.conninfo import make_conninfo
            return cls(make_conninfo(host=os.environ["DATA_QA_DATABASE_HOST"], port="5432",
                                     dbname=os.getenv("POSTGRES_DB", "data_qa_lab"),
                                     user=os.getenv("POSTGRES_USER", "data_qa_lab"),
                                     password=os.getenv("POSTGRES_PASSWORD", "data_qa_lab")))
        return cls(database_url=os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL))
