import json
import math

import pytest

from rl_model.risk import (
    RiskCalibrator,
    RiskConfig,
    RiskContext,
    RiskError,
    filter_feasible_actions,
    predict_legal_actions,
)


def features():
    return {
        "task_mi": 1000,
        "input_bytes": 8000,
        "output_bytes": 2000,
        "wan_latency_ms": 45,
        "local_utilization": 0.0,
        "edge_utilization": 0.0,
        "cloud_utilization": 0.0,
        "deadline_ms": 2000,
        "splittability": 1,
    }


def constraints():
    return {
        "splittability": "DATA_PARALLEL_DIVISIBLE",
        "partition_model_id": "data-parallel-v1",
        "local_available": True,
        "edge_available": True,
        "cloud_available": True,
        "partition_overhead_ms": 3,
        "merge_overhead_ms": 2,
    }


def context_dict(slack=2000):
    local_edge = [{"bandwidth_mbps": 10, "latency_ms": 2}]
    cloud_path = [
        {"bandwidth_mbps": 10, "latency_ms": 2},
        {"bandwidth_mbps": 10, "latency_ms": 45},
    ]
    return {
        "remaining_deadline_ms": slack,
        "partition_overhead_ms": 3,
        "merge_overhead_ms": 2,
        "merge_compute_mi": 100,
        "merge_queue_wait_ms": 0,
        "queue_wait_basis": "test_predecision_queue_estimates",
        "resources": {
            "LOCAL": {"compute_mips": 1000, "utilization": 0, "queue_wait_ms": 0},
            "EDGE": {"compute_mips": 2000, "utilization": 0, "queue_wait_ms": 0,
                     "uplink_path": local_edge, "downlink_path": local_edge},
            "CLOUD": {"compute_mips": 8000, "utilization": 0, "queue_wait_ms": 0,
                      "uplink_path": cloud_path, "downlink_path": cloud_path},
        },
    }


def make_context(slack=2000):
    return RiskContext.from_dict(context_dict(slack), features(), constraints())


def test_predicts_full_and_partial_actions_with_real_merge_compute():
    ctx = make_context()
    predictions = predict_legal_actions(features(), constraints(), tuple(range(9)), ctx)

    # Local full: 1000 MI / 1000 MIPS = 1000 ms.
    assert predictions["LOCAL"] == pytest.approx(1000.0)

    # Edge full: uplink + 1000 MI / 2000 MIPS + downlink.
    expected_edge_full = 6.4 + 500.0 + 1.6 + 2.0 + 2.0
    assert predictions["EDGE_FULL"] == pytest.approx(expected_edge_full)

    # Partial includes parallel branches, explicit partition/merge delay, and
    # the merge Cloudlet's actual 100 MI on Local.
    local_branch = 500.0
    edge_branch = 3.2 + 250.0 + 0.8 + 2.0 + 2.0
    merge_compute = 100.0
    expected_partial = max(local_branch, edge_branch) + 3.0 + 2.0 + merge_compute
    assert predictions["EDGE_PARTIAL_50"] == pytest.approx(expected_partial)
    assert predictions["CLOUD_FULL"] < predictions["EDGE_FULL"]


def test_prediction_uses_predecision_queue_wait_and_saturation():
    raw = context_dict()
    raw["resources"]["EDGE"]["queue_wait_ms"] = 40
    ctx = RiskContext.from_dict(raw, features(), constraints())
    base = predict_legal_actions(features(), constraints(), (4,), ctx)["EDGE_FULL"]
    assert base == pytest.approx(40 + 6.4 + 500 + 1.6 + 2 + 2)

    raw["resources"]["EDGE"]["utilization"] = 1.0
    f = features()
    f["edge_utilization"] = 1.0
    saturated = RiskContext.from_dict(raw, f, constraints())
    assert predict_legal_actions(f, constraints(), (4,), saturated)["EDGE_FULL"] is None


def test_risk_context_rejects_postdecision_or_inconsistent_inputs():
    raw = context_dict()
    raw["remaining_deadline_ms"] = 2001
    with pytest.raises(RiskError, match="cannot exceed"):
        RiskContext.from_dict(raw, features(), constraints())

    raw = context_dict()
    raw["resources"]["EDGE"]["utilization"] = 0.5
    with pytest.raises(RiskError, match="disagrees"):
        RiskContext.from_dict(raw, features(), constraints())

    raw = context_dict()
    raw["merge_compute_mi"] = 0
    with pytest.raises(RiskError, match="positive merge_compute_mi"):
        RiskContext.from_dict(raw, features(), constraints())


def test_calibrator_uses_exact_then_family_then_pooled_backoff():
    config = RiskConfig(epsilon=0.2, window_size=20, min_samples=4)
    calibrator = RiskCalibrator(config)
    for residual in (1, 2, 3):
        calibrator.observe("EDGE_PARTIAL_25", 100, 100 + residual)
    # Add one sample from a different partial ratio: the EDGE_PARTIAL family
    # reaches the minimum sample count even though EDGE_PARTIAL_75 has none.
    calibrator.observe("EDGE_PARTIAL_50", 100, 104)
    margin = calibrator.margin_for("EDGE_PARTIAL_75")
    assert margin["calibrated"] is True
    assert margin["group"] == "family:EDGE_PARTIAL"
    assert margin["sample_count"] == 4
    assert margin["margin_ms"] == pytest.approx(4)


def test_calibrator_uses_finite_sample_upper_rank_and_clips_negative_margin():
    config = RiskConfig(epsilon=0.1, window_size=30, min_samples=20)
    calibrator = RiskCalibrator(config)
    for _ in range(20):
        calibrator.observe("LOCAL", 100, 90)
    margin = calibrator.margin_for("LOCAL")
    assert margin["calibrated"] is True
    assert margin["rank"] == 19
    assert margin["raw_quantile_ms"] == pytest.approx(-10)
    assert margin["margin_ms"] == 0


def test_feasibility_filter_excludes_unsafe_actions_and_uses_pooled_backoff():
    config = RiskConfig(epsilon=0.2, window_size=20, min_samples=4)
    calibrator = RiskCalibrator(config)
    predictions = {"LOCAL": 40.0, "EDGE_FULL": 70.0, "CLOUD_FULL": 120.0}
    for residual in (50, 60, 70, 80):
        calibrator.observe("EDGE_FULL", 70, 70 + residual)
    result = filter_feasible_actions(
        (0, 4, 8), predictions, 149, calibrator,
        ("EDGE_FULL", "CLOUD_FULL", "LOCAL"),
    )
    assert result.no_feasible_action is False
    # EDGE_FULL receives a 80ms empirical upper residual and is filtered out.
    assert 4 not in result.allowed_actions
    assert 0 in result.allowed_actions
    assert result.estimates["EDGE_FULL"]["calibrated"] is True
    assert 0 in result.allowed_actions
    assert result.estimates["LOCAL"]["calibrated"] is True
    assert result.estimates["LOCAL"]["group"] == "pooled"


def test_no_feasible_action_uses_minimum_conservative_violation():
    calibrator = RiskCalibrator(RiskConfig(min_samples=3))
    predictions = {"LOCAL": 200.0, "EDGE_FULL": 150.0, "CLOUD_FULL": None}
    result = filter_feasible_actions(
        (0, 4, 8), predictions, 100, calibrator,
        ("EDGE_FULL", "CLOUD_FULL", "LOCAL"),
    )
    assert result.no_feasible_action is True
    assert result.allowed_actions == (4,)
    assert result.fallback_reason == "NO_FEASIBLE_SITE_AT_ARRIVAL"


def test_residual_state_roundtrips_with_configuration_fingerprint(tmp_path):
    config = RiskConfig(min_samples=3)
    calibrator = RiskCalibrator(config)
    calibrator.observe("CLOUD_FULL", 100, 150)
    path = calibrator.save(tmp_path / "calibration.json")
    loaded = RiskCalibrator.load(path, config)
    assert loaded.updates == 1
    assert loaded.sample_counts() == calibrator.sample_counts()
    with pytest.raises(RiskError, match="fingerprint"):
        RiskCalibrator.load(path, RiskConfig(min_samples=4))
