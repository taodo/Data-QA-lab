import json
from dataclasses import replace
from datetime import datetime, timezone, timedelta
from pathlib import Path
import tempfile
import unittest
from backend.app.domain.models import (
    ExecutionStatus, Layer, PipelineRun, QualityStatus, StageResult,
    ValidationResult, aggregate_quality,
)
from backend.app.services.lab_catalog import load_labs

class DomainTests(unittest.TestCase):
    def test_successful_pipeline_can_have_failed_quality(self):
        result = ValidationResult("count", QualityStatus.FAIL, "10000", "9988")
        run = PipelineRun("run1", "lab1", "orders_v1",
                          ExecutionStatus.SUCCESS, validation_results=(result,))
        self.assertEqual(run.execution_status, ExecutionStatus.SUCCESS)
        self.assertEqual(run.data_quality_status, QualityStatus.FAIL)

    def test_unrun_quality_is_not_pass(self):
        run = PipelineRun("run1", "lab1", "orders_v1", ExecutionStatus.SUCCESS)
        self.assertEqual(run.data_quality_status, QualityStatus.NOT_RUN)

    def test_quality_aggregation(self):
        for inputs, expected in [
            ([], QualityStatus.NOT_RUN),
            ([QualityStatus.PASS], QualityStatus.PASS),
            ([QualityStatus.PASS, QualityStatus.NOT_RUN], QualityStatus.NOT_RUN),
            ([QualityStatus.FAIL, QualityStatus.PASS], QualityStatus.FAIL),
            ([QualityStatus.FAIL, QualityStatus.ERROR], QualityStatus.ERROR),
        ]:
            with self.subTest(inputs=inputs):
                results = tuple(ValidationResult(str(i), value, "", "")
                                for i, value in enumerate(inputs))
                self.assertEqual(aggregate_quality(results), expected)

    def test_negative_row_count_rejected(self):
        with self.assertRaises(ValueError):
            StageResult(Layer.BRONZE, ExecutionStatus.SUCCESS, -1)

    def test_naive_timestamp_rejected(self):
        with self.assertRaises(ValueError):
            PipelineRun("r", "l", "p", started_at=datetime(2026, 1, 1))

    def test_invalid_completion_rejected(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        for start, end in [(None, now), (now, now - timedelta(seconds=1))]:
            with self.subTest(start=start), self.assertRaises(ValueError):
                PipelineRun("r", "l", "p", started_at=start, completed_at=end)

    def test_utc_timestamps_accepted(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        run = PipelineRun("r", "l", "p", started_at=now, completed_at=now)
        self.assertEqual(run.completed_at, now)

class CatalogTests(unittest.TestCase):
    def test_supplied_lab_loads(self):
        labs = load_labs()
        self.assertEqual(len(labs), 1)
        self.assertEqual(labs[0].id, "lab_001_record_count")
        self.assertIn("Gold", labs[0].requirement)

    def test_corrupted_definitions_rejected(self):
        original = json.loads((Path(__file__).resolve().parents[2] /
            "labs/lab_001_record_count/lab.json").read_text())
        for patch in [{"schema_version": 99}, {"id": ""},
                      {"learning_objectives": []}, {"difficulty": "unknown"},
                      {"available_fault_ids": "missing_rows"}]:
            with self.subTest(patch=patch), tempfile.TemporaryDirectory() as tmp:
                folder = Path(tmp) / "lab1"
                folder.mkdir()
                (folder / "lab.json").write_text(json.dumps(original | patch))
                with self.assertRaises(ValueError):
                    load_labs(Path(tmp))

    def test_duplicate_ids_rejected(self):
        original = Path(__file__).resolve().parents[2] / "labs/lab_001_record_count/lab.json"
        with tempfile.TemporaryDirectory() as tmp:
            for name in ["a", "b"]:
                folder = Path(tmp) / name
                folder.mkdir()
                (folder / "lab.json").write_text(original.read_text())
            with self.assertRaises(ValueError):
                load_labs(Path(tmp))

if __name__ == "__main__":
    unittest.main()
