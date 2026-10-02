"""Environment configuration for the local PostgreSQL adapter."""
from dataclasses import dataclass
import os

DEFAULT_DATABASE_URL = "postgresql://data_qa_lab:data_qa_lab@localhost:5432/data_qa_lab"

@dataclass(frozen=True)
class Settings:
    database_url: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(database_url=os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL))
