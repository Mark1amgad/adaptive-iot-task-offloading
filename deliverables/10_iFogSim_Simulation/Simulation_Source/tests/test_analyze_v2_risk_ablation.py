import json
from pathlib import Path

import pytest

from analyze_v2_risk_ablation import AnalysisError, analyze


def write_summary(path: Path, seed: int, mode: str, workload_hash: str,
                  miss: float, latency: float, bandwidth: float) -> Path:
    risk_hash = {
        "none": None,
        "analytical": "empty-risk-state-sha",
        "calibrated": "trained-risk-state-sha",
    }[mode]
    provenance = {
        "source_git_commit": "abc123",
        "source_inventory": [{"path": "src.py", "sha256": "source-sha"}],
        "model_sha256": "frozen-model-sha",
        "risk_state_sha256": risk_hash,
        "risk_filter_mode": mode,
        "workload_sha256": workload_hash,
        "java_version": "JAVA_VERSION=25",
        "simulator_jar_inventory": [{"name": "sim.jar", "sha256": "jar-sha"}],
        "parameters": {"deadline_ms": 15000},
        "policies": ["local", "edge", "cloud", "random", "rl_eval"],
        "evaluation_split": "test",
    }
    data = {
        "status": "PASS",
        "workload_seed": seed,
        "workload_profile": "test_profile_v1",
        "evaluation_split": "test",
        "provenance": provenance,
        "provenance_fingerprint": f"fingerprint-{seed}-{mode}",
        "policy_metrics": {
            "rl_eval": {
                "deadline_miss_rate": miss,
                "mean_latency_ms": latency,
                "mean_bandwidth_bytes": bandwidth,
                "completion_coverage": 1.0 - miss,
            }
        },
    }
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def make_groups(tmp_path: Path):
    groups = {"none": [], "analytical": [], "calibrated": []}
    values = {
        "none": [(0.20, 120.0, 1000.0), (0.25, 130.0, 1100.0)],
        "analytical": [(0.15, 115.0, 950.0), (0.20, 125.0, 1050.0)],
        "calibrated": [(0.10, 110.0, 900.0), (0.15, 120.0, 1000.0)],
    }
    for mode, rows in values.items():
        for index, (miss, latency, bandwidth) in enumerate(rows):
            seed = 2001 + index
            path = tmp_path / f"{mode}_{seed}.json"
            groups[mode].append(write_summary(
                path, seed, mode, f"workload-{seed}", miss, latency, bandwidth
            ))
    return groups


def test_matched_risk_ablation_accepts_same_seed_workload_and_model(tmp_path):
    groups = make_groups(tmp_path)
    result = analyze(groups["none"], groups["analytical"], groups["calibrated"])
    assert result["status"] == "PASS"
    assert result["n_paired_seeds"] == 2
    assert result["comparisons"]["P3_minus_P2__deadline_miss_rate"]["mean_difference"] == pytest.approx(-0.05)


def test_risk_ablation_rejects_mismatched_seed_sets(tmp_path):
    groups = make_groups(tmp_path)
    groups["calibrated"].pop()
    with pytest.raises(AnalysisError, match="same workload seed set"):
        analyze(groups["none"], groups["analytical"], groups["calibrated"])


def test_risk_ablation_rejects_different_workload_bytes_within_seed(tmp_path):
    groups = make_groups(tmp_path)
    # Replace the analytical summary for the first seed with a different workload hash.
    path = groups["analytical"][0]
    data = json.loads(path.read_text(encoding="utf-8"))
    data["provenance"]["workload_sha256"] = "different-workload"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(AnalysisError, match="workload provenance differs"):
        analyze(groups["none"], groups["analytical"], groups["calibrated"])


def test_risk_ablation_rejects_identical_analytical_and_calibrated_states(tmp_path):
    groups = make_groups(tmp_path)
    path = groups["calibrated"][0]
    data = json.loads(path.read_text(encoding="utf-8"))
    data["provenance"]["risk_state_sha256"] = "empty-risk-state-sha"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(AnalysisError, match="hashes are identical"):
        analyze(groups["none"], groups["analytical"], groups["calibrated"])
