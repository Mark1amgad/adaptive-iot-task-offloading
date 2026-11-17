import unittest
from pathlib import Path
from unittest.mock import patch

import analyze_v2_aba_regime_inference as module


def make_summary(seed, *, mismatch=False):
    policy_results = {}
    for policy, miss, recovery in [
        ("local", 1.0, False),
        ("edge", 0.3, True),
        ("cloud", 0.0, True),
        ("random", 0.6, False),
        ("rl_eval", 0.05, True),
    ]:
        policy_results[policy] = {
            "phase_metrics": {
                "0": {"deadline_miss_rate": miss},
                "1": {"deadline_miss_rate": 0.0 if policy in ("cloud", "rl_eval") else miss},
                "2": {"deadline_miss_rate": miss},
            },
            "return_A_recovery": {
                "recovered": recovery,
                "recovery_time_ms": (1000.0 + seed) if recovery else None,
            },
        }
    provenance = {"evaluation_split": "test", "model_sha256": "model-a"}
    if mismatch:
        provenance["model_sha256"] = "model-b"
    return {
        "status": "PASS",
        "workload_seed": seed,
        "workload_profile": "aba_network_load_v1",
        "provenance_fingerprint": "fp-a" if not mismatch else "fp-b",
        "provenance": provenance,
        "regime_shift_analysis": {"policy_results": policy_results},
    }


class AbaRegimeInferenceTests(unittest.TestCase):
    def test_phase_and_recovery_inference(self):
        summaries = {
            "seed_1.json": make_summary(1),
            "seed_2.json": make_summary(2),
        }
        with patch.object(module, "load_summary", side_effect=lambda p: summaries[p.name]):
            result = module.analyze([Path("seed_1.json"), Path("seed_2.json")])
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["recovery_rates"]["rl_eval"]["recovered_seeds"], 2)
        self.assertEqual(result["recovery_rates"]["random"]["recovered_seeds"], 0)
        cloud_recovery = result["comparisons"]["rl_eval_minus_cloud__recovery_time_ms"]
        self.assertEqual(cloud_recovery["paired_recovered_seeds"], 2)
        self.assertEqual(cloud_recovery["mean_difference"], 0.0)
        self.assertIn("rl_eval_minus_edge__B_deadline_miss_rate", result["comparisons"])

    def test_rejects_mixed_provenance(self):
        summaries = {
            "seed_1.json": make_summary(1),
            "seed_2.json": make_summary(2, mismatch=True),
        }
        with patch.object(module, "load_summary", side_effect=lambda p: summaries[p.name]):
            with self.assertRaises(module.AnalysisError):
                module.analyze([Path("seed_1.json"), Path("seed_2.json")])


if __name__ == "__main__":
    unittest.main()
