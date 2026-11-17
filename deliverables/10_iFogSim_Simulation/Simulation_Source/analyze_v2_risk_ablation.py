#!/usr/bin/env python3
"""Paired-seed inference for matched frozen-learner risk-filter ablations."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

from analyze_v2_paired_seed_inference import AnalysisError, holm_adjust, paired_effect


MODES = ("none", "analytical", "calibrated")
METRICS = ("deadline_miss_rate", "mean_latency_ms", "mean_bandwidth_bytes", "completion_coverage")


def _load_group(paths: list[Path], expected_mode: str, expected_split: str) -> dict[int, dict[str, Any]]:
    if len(paths) < 2:
        raise AnalysisError(f"{expected_mode}: provide at least two paired-seed summaries")
    result: dict[int, dict[str, Any]] = {}
    for path in paths:
        try:
            summary = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise AnalysisError(f"{path}: cannot read valid JSON: {exc}") from exc
        if summary.get("status") != "PASS":
            raise AnalysisError(f"{path}: summary status is not PASS")
        if summary.get("evaluation_split") != expected_split:
            raise AnalysisError(f"{path}: expected evaluation_split={expected_split!r}")
        if not isinstance(summary.get("provenance"), dict) or summary["provenance"].get("evaluation_split") != expected_split:
            raise AnalysisError(f"{path}: provenance split does not match {expected_split!r}")
        seed = summary["workload_seed"]
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise AnalysisError(f"{path}: workload_seed must be an integer")
        if seed in result:
            raise AnalysisError(f"{expected_mode}: duplicate workload seed {seed}")
        provenance = summary["provenance"]
        if provenance.get("risk_filter_mode") != expected_mode:
            raise AnalysisError(
                f"{path}: expected risk_filter_mode={expected_mode!r}, "
                f"found {provenance.get('risk_filter_mode')!r}"
            )
        result[seed] = summary
    return result


def _common_provenance(summary: dict[str, Any]) -> dict[str, Any]:
    provenance = dict(summary["provenance"])
    provenance.pop("risk_filter_mode", None)
    provenance.pop("risk_state_sha256", None)
    return provenance


def analyze(no_filter_paths: list[Path], analytical_paths: list[Path],
            calibrated_paths: list[Path], training_risk_mode: str = "calibrated",
            expected_split: str = "test") -> dict[str, Any]:
    groups = {
        "none": _load_group(no_filter_paths, "none", expected_split),
        "analytical": _load_group(analytical_paths, "analytical", expected_split),
        "calibrated": _load_group(calibrated_paths, "calibrated", expected_split),
    }
    seed_sets = {mode: set(group) for mode, group in groups.items()}
    if len({tuple(sorted(values)) for values in seed_sets.values()}) != 1:
        raise AnalysisError("P1/P2/P3 must contain exactly the same workload seed set")
    seeds = sorted(seed_sets["none"])

    profiles = {
        mode: {s["workload_profile"] for s in group.values()}
        for mode, group in groups.items()
    }
    if any(len(value) != 1 for value in profiles.values()) or len({next(iter(v)) for v in profiles.values()}) != 1:
        raise AnalysisError("P1/P2/P3 workload profiles differ or are mixed")

    reference = groups["none"][seeds[0]]
    reference_common = _common_provenance(reference)
    reference_model = reference_common.get("model_sha256")
    reference_source = reference_common.get("source_git_commit")
    invariant_provenance = dict(reference_common)
    invariant_provenance.pop("workload_sha256", None)
    for mode, group in groups.items():
        for seed, summary in group.items():
            common = _common_provenance(summary)
            reference_for_seed = _common_provenance(groups["none"][seed])
            if common != reference_for_seed:
                raise AnalysisError(
                    f"{mode} seed {seed}: source/model/simulator/workload provenance differs "
                    "from the no-filter arm for the same seed"
                )
            invariant = dict(common)
            invariant.pop("workload_sha256", None)
            if invariant != invariant_provenance:
                raise AnalysisError(
                    f"{mode} seed {seed}: invariant source/model/simulator provenance differs "
                    "across the paired batch"
                )
            if summary.get("workload_seed") != seed:
                raise AnalysisError(f"{mode} seed identity mismatch")
            metrics = summary.get("policy_metrics", {}).get("rl_eval")
            if not isinstance(metrics, dict):
                raise AnalysisError(f"{mode} seed {seed}: missing rl_eval metrics")
            for metric in ("deadline_miss_rate", "mean_bandwidth_bytes", "completion_coverage"):
                value = metrics.get(metric)
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                    raise AnalysisError(f"{mode} seed {seed}: invalid rl_eval.{metric}")
            latency = metrics.get("mean_latency_ms")
            if latency is not None and (
                isinstance(latency, bool) or not isinstance(latency, (int, float)) or not math.isfinite(latency)
            ):
                raise AnalysisError(f"{mode} seed {seed}: invalid rl_eval.mean_latency_ms")

    # P1/P2/P3 must genuinely represent different filter states.
    for seed in seeds:
        p1 = groups["none"][seed]["provenance"]
        p2 = groups["analytical"][seed]["provenance"]
        p3 = groups["calibrated"][seed]["provenance"]
        if p1.get("risk_state_sha256") is not None:
            raise AnalysisError(f"seed {seed}: P1 no-filter manifest must not claim a risk state")
        if not p2.get("risk_state_sha256") or not p3.get("risk_state_sha256"):
            raise AnalysisError(f"seed {seed}: P2/P3 must identify their risk-state artifacts")
        if p2["risk_state_sha256"] == p3["risk_state_sha256"]:
            raise AnalysisError(f"seed {seed}: analytical and calibrated risk-state hashes are identical")

    comparisons: dict[str, Any] = {}
    raw_p: dict[str, float | None] = {}
    unavailable: dict[str, str] = {}
    metric_set = ["deadline_miss_rate", "mean_bandwidth_bytes", "completion_coverage"]
    latency_missing = any(
        groups[mode][seed]["policy_metrics"]["rl_eval"].get("mean_latency_ms") is None
        for mode in MODES for seed in seeds
    )
    if latency_missing:
        unavailable["mean_latency_ms"] = "conditional latency is undefined for at least one mode/seed"
    else:
        metric_set.append("mean_latency_ms")

    pairs = (
        ("analytical", "none", "P2_minus_P1"),
        ("calibrated", "analytical", "P3_minus_P2"),
        ("calibrated", "none", "P3_minus_P1"),
    )
    for left, right, label in pairs:
        for metric in metric_set:
            diffs = [
                float(groups[left][seed]["policy_metrics"]["rl_eval"][metric])
                - float(groups[right][seed]["policy_metrics"]["rl_eval"][metric])
                for seed in seeds
            ]
            key = f"{label}__{metric}"
            result = paired_effect(diffs)
            comparisons[key] = result
            raw_p[key] = result["wilcoxon_two_sided_p"]

    adjusted = holm_adjust(raw_p)
    for key, result in comparisons.items():
        result["wilcoxon_holm_adjusted_p"] = adjusted[key]

    return {
        "status": "PASS",
        "evaluation_split": expected_split,
        "analysis": "matched frozen-learner risk-filter ablation",
        "ablation_scope": "test-time intervention on the same frozen contextual learner",
        "arms": {
            "P1": "same frozen learner; no feasibility filter",
            "P2": "same frozen learner; analytical completion-time feasibility; zero residual margin",
            "P3": "same frozen learner; residual-calibrated feasibility",
        },
        "training_risk_mode": training_risk_mode,
        "training_interpretation_warning": (
            "The current frozen model was trained with the calibrated filter. "
            "These are test-time filter interventions, not a fully retrained end-to-end ablation."
            if training_risk_mode == "calibrated" else
            "Training filter mode was declared by the caller; verify it against the frozen training manifest."
        ),
        "independent_unit": "workload_seed / paired simulation run",
        "n_paired_seeds": len(seeds),
        "workload_seeds": seeds,
        "workload_profile": next(iter(profiles["none"])),
        "model_sha256": reference_model,
        "source_git_commit": reference_source,
        "common_provenance": reference_common,
        "unavailable_metrics": unavailable,
        "comparisons": comparisons,
        "minimum_protocol_seeds": 20,
        "meets_minimum_protocol_seeds": len(seeds) >= 20,
        "limitations": [
            "P1/P2/P3 use the same frozen model and paired workload seeds; only the test-time feasibility layer changes.",
            "Because the current model was trained with the calibrated filter, this does not establish a clean end-to-end retraining ablation.",
            "The current manifest builder still requires a separate approved seed-registry gate; its test label alone is not proof of held-out isolation.",
            "Latency is conditional on completed tasks and must be read with deadline misses and completion coverage.",
            "The empirical residual margin is not a deterministic deadline guarantee.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-filter", nargs="+", type=Path, required=True,
                        help="P1 per-seed policy_comparison_summary.json files")
    parser.add_argument("--analytical", nargs="+", type=Path, required=True,
                        help="P2 per-seed summaries using an empty zero-margin calibrator")
    parser.add_argument("--calibrated", nargs="+", type=Path, required=True,
                        help="P3 per-seed summaries using the frozen residual state")
    parser.add_argument("--training-risk-mode", choices=MODES, default="calibrated")
    parser.add_argument("--expected-split", choices=("development", "validation", "test"), default="test")
    parser.add_argument("--output", type=Path, default=Path("risk_ablation_inference.json"))
    args = parser.parse_args()
    try:
        result = analyze(args.no_filter, args.analytical, args.calibrated, args.training_risk_mode, args.expected_split)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (AnalysisError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
