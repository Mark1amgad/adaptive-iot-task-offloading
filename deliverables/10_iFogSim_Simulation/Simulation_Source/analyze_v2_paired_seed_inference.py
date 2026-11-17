#!/usr/bin/env python3
"""Paired-seed inference over per-seed policy_comparison_summary.json files.

Each input summary must come from one immutable workload/network seed and contain
policy_metrics[policy][metric]. The independent unit is the paired seed/run,
never individual tasks within a run.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
from pathlib import Path
from typing import Any

POLICIES = ("local", "edge", "cloud", "random", "rl_eval")
METRICS = ("mean_latency_ms", "deadline_miss_rate", "mean_bandwidth_bytes")


class AnalysisError(ValueError):
    pass


def load_summary(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AnalysisError(f"{path}: cannot read valid JSON: {exc}") from exc
    if data.get("status") != "PASS":
        raise AnalysisError(f"{path}: summary status is not PASS")
    for key in ("workload_seed", "workload_profile", "policy_metrics"):
        if key not in data:
            raise AnalysisError(f"{path}: missing {key}")
    if not isinstance(data["policy_metrics"], dict):
        raise AnalysisError(f"{path}: policy_metrics must be an object")
    return data


def percentile(values: list[float], p: float) -> float:
    if not values:
        raise AnalysisError("percentile requires non-empty values")
    ordered = sorted(values)
    # Linear interpolation (type-7 convention).
    h = (len(ordered) - 1) * p
    lo = math.floor(h)
    hi = math.ceil(h)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (h - lo)


def bootstrap_mean_ci(values: list[float], *, reps: int, seed: int) -> list[float]:
    if len(values) < 2:
        raise AnalysisError("at least two paired seeds are required for a CI")
    rng = random.Random(seed)
    n = len(values)
    means = [statistics.mean(values[rng.randrange(n)] for _ in range(n)) for _ in range(reps)]
    return [percentile(means, 0.025), percentile(means, 0.975)]


def wilcoxon_pvalue(diffs: list[float]) -> float | None:
    nonzero = [d for d in diffs if d != 0]
    if not nonzero:
        return 1.0
    try:
        from scipy.stats import wilcoxon
    except ImportError:
        return None
    # Explicitly request two-sided paired inference; SciPy handles zero differences.
    return float(wilcoxon(diffs, alternative="two-sided", zero_method="wilcox",
                           method="auto").pvalue)


def holm_adjust(pvalues: dict[str, float | None]) -> dict[str, float | None]:
    present = [(name, p) for name, p in pvalues.items() if p is not None]
    ordered = sorted(present, key=lambda item: item[1])
    m = len(ordered)
    adjusted: dict[str, float | None] = {name: None for name in pvalues}
    running = 0.0
    for rank, (name, p) in enumerate(ordered):
        running = max(running, min(1.0, (m - rank) * p))
        adjusted[name] = running
    return adjusted


def paired_effect(diffs: list[float]) -> dict[str, float | None]:
    mean = statistics.mean(diffs)
    sd = statistics.stdev(diffs) if len(diffs) > 1 else 0.0
    return {
        "mean_difference": mean,
        "median_difference": statistics.median(diffs),
        "sd_difference": sd,
        "paired_standardized_effect_dz": (mean / sd) if sd > 0 else None,
        "ci95_paired_bootstrap": bootstrap_mean_ci(diffs, reps=10000, seed=20261117),
        "positive_differences": sum(x > 0 for x in diffs),
        "negative_differences": sum(x < 0 for x in diffs),
        "ties": sum(x == 0 for x in diffs),
        "wilcoxon_two_sided_p": wilcoxon_pvalue(diffs),
    }


def analyze(paths: list[Path]) -> dict[str, Any]:
    if len(paths) < 2:
        raise AnalysisError("provide at least two per-seed summary files")
    summaries = [load_summary(p) for p in paths]
    seeds = [s["workload_seed"] for s in summaries]
    if len(set(seeds)) != len(seeds):
        raise AnalysisError(f"duplicate workload_seed values: {seeds}")
    profiles = {s["workload_profile"] for s in summaries}
    if len(profiles) != 1:
        raise AnalysisError(f"mixed workload profiles: {sorted(map(str, profiles))}")

    for path, summary in zip(paths, summaries):
        absent = [p for p in POLICIES if p not in summary["policy_metrics"]]
        if absent:
            raise AnalysisError(f"{path}: missing policy arms {absent}")
        for policy in POLICIES:
            for metric in METRICS:
                value = summary["policy_metrics"][policy].get(metric)
                if not isinstance(value, (int, float)) or not math.isfinite(value):
                    raise AnalysisError(f"{path}: {policy}.{metric} missing/non-finite")

    comparisons: dict[str, Any] = {}
    raw_p: dict[str, float | None] = {}
    for baseline in ("local", "edge", "cloud", "random"):
        for metric in METRICS:
            # Negative means the risk-calibrated learner has a lower metric.
            diffs = [
                float(s["policy_metrics"]["rl_eval"][metric])
                - float(s["policy_metrics"][baseline][metric])
                for s in summaries
            ]
            name = f"rl_eval_minus_{baseline}__{metric}"
            result = paired_effect(diffs)
            raw_p[name] = result["wilcoxon_two_sided_p"]
            comparisons[name] = result

    adjusted = holm_adjust(raw_p)
    for name, result in comparisons.items():
        result["wilcoxon_holm_adjusted_p"] = adjusted[name]

    return {
        "status": "PASS",
        "analysis": "paired-seed inference",
        "independent_unit": "workload_seed / paired simulation run",
        "n_paired_seeds": len(seeds),
        "workload_seeds": seeds,
        "workload_profile": next(iter(profiles)),
        "minimum_protocol_seeds": 20,
        "meets_minimum_protocol_seeds": len(seeds) >= 20,
        "limitations": [
            "Inference is only valid if each input summary used identical task and exogenous traces across policies for its seed.",
            "This script does not validate train/validation/test separation; that must be enforced by run manifests.",
            "Wilcoxon p-values are null-hypothesis tests, not evidence of practical importance.",
            "Bootstrap intervals resample paired seeds, not tasks.",
            "If SciPy is unavailable, Wilcoxon p-values are null; confidence intervals and effect sizes are still computed."
        ],
        "comparisons": comparisons,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summaries", nargs="+", type=Path,
                        help="one policy_comparison_summary.json per distinct workload seed")
    parser.add_argument("--output", type=Path, default=Path("paired_seed_inference.json"))
    args = parser.parse_args()
    try:
        result = analyze(args.summaries)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (AnalysisError, OSError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
