import contextlib
import io
import json
import hashlib
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
            manifest = {
                "schema_version": "v1", "evaluation_split": "test",
                "workload_seed": 7, "workload_profile": "fixture",
                "workload_file": workload_path.name,
                "workload_sha256": hashlib.sha256(workload_path.read_bytes()).hexdigest(),
                "model_sha256": "a" * 64, "risk_state_sha256": "b" * 64,
                "source_git_commit": "abc123", "java_version": "Java 25",
                "simulator_jar_inventory": [{"name": "sim.jar", "sha256": "c" * 64}],
                "parameters": {"partition_overhead_ms": 3.0, "merge_overhead_ms": 2.0,
                               "wan_latency_ms": 45.0, "watchdog_ms": 60000.0},
                "policies": list(analyzer.POLICIES),
            }
            manifest_path = root / "experiment_manifest.json"
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

            for policy in analyzer.POLICIES:
                run = root / f"policy_{policy}"
                run.mkdir()
                (run / "experiment_manifest.json").write_bytes(manifest_path.read_bytes())
                trace = [
                    {"record": "config", "task_count": 2, "workload_file": "fixture.jsonl",
                     "partition_overhead_ms": 3.0, "merge_overhead_ms": 2.0,
                     "wan_latency_ms": 45.0, "watchdog_ms": 60000.0},
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

            with patch.object(sys, "argv", ["analyzer", "--root", str(root), "--workload", str(workload_path),
                                                   "--manifest", str(manifest_path)]):
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
