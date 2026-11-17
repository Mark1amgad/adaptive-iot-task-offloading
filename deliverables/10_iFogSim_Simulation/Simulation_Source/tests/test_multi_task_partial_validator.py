import csv
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE_DIR))
import validate_multi_task_partial as validator

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "multi_task_partial_4"


class MultiTaskPartialValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "fixture"
        shutil.copytree(FIXTURE, self.root)

    def tearDown(self):
        self.temp.cleanup()

    def read_trace(self):
        with (self.root / "partial_trace.csv").open(newline="", encoding="utf-8") as stream:
            return list(csv.DictReader(stream))

    def write_trace(self, rows):
        with (self.root / "partial_trace.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=[
                "event", "task_id", "branch", "actual_tuple_id", "sim_time_ms", "detail"
            ])
            writer.writeheader()
            writer.writerows(rows)

    def assert_rejected(self):
        with self.assertRaises(validator.ValidationError):
            validator.validate(self.root, 4)

    def test_valid_fixture_passes(self):
        result = validator.validate(self.root, 4)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["unique_registered_tuple_ids"], 12)

    def test_duplicate_branch_result_is_rejected(self):
        rows = self.read_trace()
        row = next(r for r in rows if r["event"] == "branch_result")
        rows.append(dict(row))
        self.write_trace(rows)
        self.assert_rejected()

    def test_cross_task_tuple_correlation_is_rejected(self):
        rows = self.read_trace()
        task1_local = next(r for r in rows if r["event"] == "branch_created"
                           and r["task_id"] == "partial-task-001" and r["branch"] == "local")
        task2_result = next(r for r in rows if r["event"] == "branch_result"
                            and r["task_id"] == "partial-task-002" and r["branch"] == "local")
        task2_result["actual_tuple_id"] = task1_local["actual_tuple_id"]
        self.write_trace(rows)
        self.assert_rejected()

    def test_merge_barrier_before_second_branch_result_is_rejected(self):
        rows = self.read_trace()
        task = "partial-task-001"
        edge_result = next(r for r in rows if r["event"] == "branch_result"
                           and r["task_id"] == task and r["branch"] == "edge")
        barrier = next(r for r in rows if r["event"] == "merge_barrier" and r["task_id"] == task)
        barrier["sim_time_ms"] = str(float(edge_result["sim_time_ms"]) - 0.01)
        self.write_trace(rows)
        self.assert_rejected()

    def test_transfer_attributed_to_wrong_branch_is_rejected(self):
        rows = self.read_trace()
        transfer = next(r for r in rows if r["event"] == "transfer"
                        and r["task_id"] == "partial-task-001")
        transfer["actual_tuple_id"] = "99999"
        self.write_trace(rows)
        self.assert_rejected()


if __name__ == "__main__":
    unittest.main(verbosity=2)
