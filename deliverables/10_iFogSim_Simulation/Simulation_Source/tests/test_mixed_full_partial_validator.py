import csv
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE_DIR))
import validate_mixed_full_partial as validator

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "mixed_full_partial_6"


class MixedFullPartialValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "fixture"
        shutil.copytree(FIXTURE, self.root)

    def tearDown(self):
        self.temp.cleanup()

    def read_trace(self):
        with (self.root / "mixed_trace.csv").open(newline="", encoding="utf-8") as stream:
            return list(csv.DictReader(stream))

    def write_trace(self, rows):
        with (self.root / "mixed_trace.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=[
                "event", "task_id", "branch", "actual_tuple_id", "sim_time_ms", "detail"
            ])
            writer.writeheader()
            writer.writerows(rows)

    def assert_rejected(self):
        with self.assertRaises(validator.ValidationError):
            validator.validate(self.root, 6)

    def test_valid_mixed_fixture_passes(self):
        result = validator.validate(self.root, 6)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["full_tasks"], 3)
        self.assertEqual(result["partial_tasks"], 3)
        self.assertEqual(result["unique_tuple_ids"], 12)

    def test_full_task_terminal_tuple_mismatch_is_rejected(self):
        rows = self.read_trace()
        terminal = next(r for r in rows if r["event"] == "task_completed"
                        and r["task_id"] == "mixed-task-001")
        terminal["actual_tuple_id"] = "99999"
        self.write_trace(rows)
        self.assert_rejected()

    def test_cross_task_partial_tuple_is_rejected(self):
        rows = self.read_trace()
        task1 = next(r for r in rows if r["event"] == "branch_created"
                     and r["task_id"] == "mixed-task-002" and r["branch"] == "local")
        task2 = next(r for r in rows if r["event"] == "branch_result"
                     and r["task_id"] == "mixed-task-004" and r["branch"] == "local")
        task2["actual_tuple_id"] = task1["actual_tuple_id"]
        self.write_trace(rows)
        self.assert_rejected()

    def test_partial_merge_barrier_before_second_result_is_rejected(self):
        rows = self.read_trace()
        task = "mixed-task-002"
        edge_result = next(r for r in rows if r["event"] == "branch_result"
                           and r["task_id"] == task and r["branch"] == "edge")
        barrier = next(r for r in rows if r["event"] == "merge_barrier" and r["task_id"] == task)
        barrier["sim_time_ms"] = str(float(edge_result["sim_time_ms"]) - 0.01)
        self.write_trace(rows)
        self.assert_rejected()

    def test_full_task_with_merge_lifecycle_is_rejected(self):
        rows = self.read_trace()
        rows.append({
            "event": "merge_created", "task_id": "mixed-task-001", "branch": "merge",
            "actual_tuple_id": "88888", "sim_time_ms": "40.0",
            "detail": "mi=1200;input_bytes=1000;output_bytes=100"
        })
        self.write_trace(rows)
        self.assert_rejected()


if __name__ == "__main__":
    unittest.main(verbosity=2)
