import importlib.util
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("analyze_v2_paired_seed_inference.py")
SPEC = importlib.util.spec_from_file_location("paired_inference", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def summary(seed, offset=0.0, profile="industrial_a"):
    metrics = {}
    for i, policy in enumerate(MODULE.POLICIES):
        metrics[policy] = {
            "mean_latency_ms": 100.0 + i * 10 + offset,
            "deadline_miss_rate": 0.20 - i * 0.01,
            "mean_bandwidth_bytes": 1000.0 + i * 100,
        }
    provenance = {
        "source_git_commit": "abc123",
        "source_inventory": [{"path": "src/a.py", "sha256": "f" * 64}],
        "model_sha256": "a" * 64,
        "risk_state_sha256": "b" * 64,
        "java_version": "Java 25",
        "simulator_jar_inventory": [{"name": "sim.jar", "sha256": "c" * 64}],
        "parameters": {"watchdog_ms": 60000.0},
        "policies": list(MODULE.POLICIES),
        "evaluation_split": "test",
    }
    return {
        "status": "PASS",
        "workload_seed": seed,
        "workload_profile": profile,
        "policy_metrics": metrics,
        "provenance": provenance,
        "provenance_fingerprint": hashlib.sha256(
            json.dumps(provenance, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "evaluation_split": "test",
    }


class PairedSeedInferenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, data):
        path = self.root / name
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_paired_seed_effects_and_protocol_warning(self):
        paths = [
            self.write("seed1.json", summary(1, 0)),
            self.write("seed2.json", summary(2, 5)),
            self.write("seed3.json", summary(3, -2)),
        ]
        result = MODULE.analyze(paths)
        self.assertEqual(result["n_paired_seeds"], 3)
        self.assertFalse(result["meets_minimum_protocol_seeds"])
        key = "rl_eval_minus_local__mean_latency_ms"
        self.assertAlmostEqual(result["comparisons"][key]["mean_difference"], 40.0)
        self.assertEqual(result["comparisons"][key]["positive_differences"], 3)
        self.assertEqual(len(result["comparisons"][key]["ci95_paired_bootstrap"]), 2)

    def test_duplicate_seed_is_rejected(self):
        paths = [
            self.write("a.json", summary(9)),
            self.write("b.json", summary(9, 2)),
        ]
        with self.assertRaisesRegex(MODULE.AnalysisError, "duplicate workload_seed"):
            MODULE.analyze(paths)

    def test_mixed_profiles_are_rejected(self):
        paths = [
            self.write("a.json", summary(1, profile="industrial_a")),
            self.write("b.json", summary(2, profile="industrial_b")),
        ]
        with self.assertRaisesRegex(MODULE.AnalysisError, "mixed workload profiles"):
            MODULE.analyze(paths)

    def test_mixed_model_provenance_is_rejected(self):
        first = summary(1)
        second = summary(2)
        second["provenance"]["model_sha256"] = "e" * 64
        second["provenance_fingerprint"] = hashlib.sha256(
            json.dumps(second["provenance"], sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        paths = [self.write("a.json", first), self.write("b.json", second)]
        with self.assertRaisesRegex(MODULE.AnalysisError, "mixed model/source/simulator provenance"):
            MODULE.analyze(paths)

    def test_missing_policy_metric_is_rejected(self):
        bad = summary(1)
        del bad["policy_metrics"]["rl_eval"]["deadline_miss_rate"]
        paths = [
            self.write("a.json", bad),
            self.write("b.json", summary(2)),
        ]
        with self.assertRaisesRegex(MODULE.AnalysisError, "missing/non-finite"):
            MODULE.analyze(paths)

    def test_holm_adjustment_is_monotonic_in_sorted_p_order(self):
        adjusted = MODULE.holm_adjust({"a": 0.01, "b": 0.04, "c": 0.03})
        self.assertAlmostEqual(adjusted["a"], 0.03)
        self.assertAlmostEqual(adjusted["c"], 0.06)
        self.assertAlmostEqual(adjusted["b"], 0.06)

    def test_bootstrap_requires_two_pairs(self):
        with self.assertRaisesRegex(MODULE.AnalysisError, "at least two"):
            MODULE.bootstrap_mean_ci([1.0], reps=100, seed=1)


if __name__ == "__main__":
    unittest.main()
