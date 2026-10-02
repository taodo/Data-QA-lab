"""Load versioned lab definitions without revealing hidden solution files."""
import json
from pathlib import Path
from backend.app.domain.models import Lab

ROOT = Path(__file__).resolve().parents[3]

def load_labs(directory: Path | None = None) -> tuple[Lab, ...]:
    labs = []
    ids = set()
    for path in sorted((directory or ROOT / "labs").glob("*/lab.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schema_version") != 1:
            raise ValueError(f"Unsupported lab schema: {path.name}")
        for key in ("id", "title", "requirement", "pipeline_id"):
            if not isinstance(data.get(key), str) or not data[key].strip():
                raise ValueError(f"Lab field {key} must be non-empty text")
        if data.get("difficulty") not in {"beginner", "intermediate", "advanced"}:
            raise ValueError("Invalid lab difficulty")
        for key in ("available_fault_ids", "learning_objectives"):
            if not isinstance(data.get(key), list) or any(
                not isinstance(value, str) or not value.strip() for value in data[key]
            ):
                raise ValueError(f"Lab field {key} must contain text values")
        if not data["learning_objectives"]:
            raise ValueError("Lab must have a learning objective")
        if data["id"] in ids:
            raise ValueError(f"Duplicate lab id: {data['id']}")
        ids.add(data["id"])
        labs.append(Lab(
            id=data["id"], title=data["title"], requirement=data["requirement"],
            difficulty=data["difficulty"], pipeline_id=data["pipeline_id"],
            available_fault_ids=tuple(data["available_fault_ids"]),
            learning_objectives=tuple(data["learning_objectives"]),
        ))
    return tuple(labs)
