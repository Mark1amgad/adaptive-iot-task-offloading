import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import analyze_v2_policy_comparison as analyzer


class PolicyOutcomeAnalysisTests(unittest.TestCase):
    def test_unresolved_tasks_remain_in_deadline_denominator(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            root.mkdir()
            workload_path = Path(tmp) / "fixture.jsonl"
            workload = [
                {"sequence": 1, "seed": 7, "profile": "fixture", "task_mi": 100,
                 "input_bytes": 10, "output_bytes": 2, "deadline_ms": 10,
                 "urgency_class": "normal", "splittability": "INDEPENDENT"},
                {"sequence": 2, "seed": 7, "profile": "fixture", "task_mi": 100,
                 "input_bytes": 10, "output_bytes": 2, "deadline_ms": 10,
                 "urgency_class": "normal", "splittability": "INDEPENDENT"},
            ]
            workload_path.write_text("".join(json.dumps(x) + "\n" for x in workload), encoding="utf-8")

            for policy in analyzer.POLICIES:
                run = root / f"policy_{policy}"
                run.mkdir()
                trace = [
                    {"record": "config", "task_count": 2, "workload_file": "fixture.jsonl"},
                    {"record": "decision", "task_id": f"{policy}:task:1", "action": "LOCAL",
                     "task_mi": 100, "input_bytes": 10, "output_bytes": 2, "deadline_ms": 10,
                     "urgency_class": "normal", "splittability": "INDEPENDENT", "mode": "test"},
                    {"record": "decision", "task_id": f"{policy}:task:2", "action": "LOCAL",
                     "task_mi": 100, "input_bytes": 10, "output_bytes": 2, "deadline_ms": 10,
                     "urgency_class": "normal", "splittability": "INDEPENDENT", "mode": "test"},
                    {"record": "task_terminal", "task_id": f"{policy}:task:1", "latency_ms": 5,
                     "deadline_met": True, "bandwidth_bytes": 4},
                    {"record": "task_failed", "task_id": f"{policy}:task:2", "reason": "execution_horizon_exceeded"},
                    {"record": "task_outcome", "task_id": f"{policy}:task:1", "outcome": "ON_TIME",
                     "latency_ms": 5, "bandwidth_bytes": 4},
                    {"record": "task_outcome", "task_id": f"{policy}:task:2",
                     "outcome": "UNRESOLVED_AT_HORIZON", "bandwidth_bytes": 0},
                    {"record": "outcome_ack", "task_id": f"{policy}:task:1"},
                    {"record": "outcome_ack", "task_id": f"{policy}:task:2"},
                    {"record": "shutdown_ack", "orphaned_tasks": 0, "tasks_reported": 2},
                ]
                (run / "partial_trace.jsonl").write_text(
                    "".join(json.dumps(x) + "\n" for x in trace), encoding="utf-8"
                )

            with patch.object(sys, "argv", ["analyzer", "--root", str(root), "--workload", str(workload_path)]):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(analyzer.main(), 0)
            report = json.loads((root / "policy_comparison_summary.json").read_text(encoding="utf-8"))
            metrics = report["policy_metrics"]["rl_eval"]
            self.assertEqual(metrics["generated_tasks"], 2)
            self.assertEqual(metrics["on_time_tasks"], 1)
            self.assertEqual(metrics["unresolved_at_horizon"], 1)
            self.assertEqual(metrics["deadline_miss_rate"], 0.5)
            self.assertEqual(metrics["completion_coverage"], 0.5)
            self.assertEqual(metrics["mean_latency_ms"], 5.0)


if __name__ == "__main__":
    unittest.main()
