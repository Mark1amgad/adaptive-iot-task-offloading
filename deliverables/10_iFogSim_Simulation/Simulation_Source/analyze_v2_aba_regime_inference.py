#!/usr/bin/env python3
"""Paired-seed inference for A1/B/A2 deadline misses and A2 recovery time."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_v2_paired_seed_inference import (
    AnalysisError, holm_adjust, load_summary, paired_effect,
)

POLICIES = ("local", "edge", "cloud", "random", "rl_eval")
PHASES = {"A1": "0", "B": "1", "A2": "2"}


def analyze(paths: list[Path]) -> dict[str, Any]:
    if len(paths) < 2:
        raise AnalysisError("provide at least two per-seed summary files")
    summaries = [load_summary(p) for p in paths]
    seeds = [s["workload_seed"] for s in summaries]
    if len(set(seeds)) != len(seeds):
        raise AnalysisError(f"duplicate workload seeds: {seeds}")
    profiles = {s["workload_profile"] for s in summaries}
    fingerprints = {s["provenance_fingerprint"] for s in summaries}
    canonical = {
        json.dumps(s["provenance"], sort_keys=True, separators=(",", ":"))
        for s in summaries
    }
    if len(profiles) != 1 or len(fingerprints) != 1 or len(canonical) != 1:
        raise AnalysisError("mixed workload profile or source/model/simulator provenance")
    for path, summary in zip(paths, summaries):
        results = summary.get("regime_shift_analysis", {}).get("policy_results")
        if not isinstance(results, dict):
            raise AnalysisError(f"{path}: missing regime_shift_analysis.policy_results")
        for policy in POLICIES:
            if policy not in results:
                raise AnalysisError(f"{path}: missing regime result for {policy}")
            phases = results[policy].get("phase_metrics", {})
            if any(k not in phases or not isinstance(phases[k].get("deadline_miss_rate"), (int, float))
                   for k in PHASES.values()):
                raise AnalysisError(f"{path}: incomplete phase metrics for {policy}")

    comparisons: dict[str, Any] = {}
    raw_p: dict[str, float | None] = {}
    for baseline in ("local", "edge", "cloud", "random"):
        for phase_name, phase_key in PHASES.items():
            diffs = [
                float(s["regime_shift_analysis"]["policy_results"]["rl_eval"]["phase_metrics"][phase_key]["deadline_miss_rate"])
                - float(s["regime_shift_analysis"]["policy_results"][baseline]["phase_metrics"][phase_key]["deadline_miss_rate"])
                for s in summaries
            ]
            name = f"rl_eval_minus_{baseline}__{phase_name}_deadline_miss_rate"
            result = paired_effect(diffs)
            comparisons[name] = result
            raw_p[name] = result["wilcoxon_two_sided_p"]

    recovery_rates = {}
    for policy in POLICIES:
        flags = [
            bool(s["regime_shift_analysis"]["policy_results"][policy]["return_A_recovery"].get("recovered"))
            for s in summaries
        ]
        recovery_rates[policy] = {
            "recovered_seeds": sum(flags),
            "total_seeds": len(flags),
            "recovery_rate": sum(flags) / len(flags),
        }

    for baseline in ("local", "edge", "cloud", "random"):
        paired = []
        for s in summaries:
            rl = s["regime_shift_analysis"]["policy_results"]["rl_eval"]["return_A_recovery"]
            base = s["regime_shift_analysis"]["policy_results"][baseline]["return_A_recovery"]
            if rl.get("recovered") and base.get("recovered"):
                rt_rl, rt_base = rl.get("recovery_time_ms"), base.get("recovery_time_ms")
                if isinstance(rt_rl, (int, float)) and isinstance(rt_base, (int, float)):
                    paired.append(float(rt_rl) - float(rt_base))
        name = f"rl_eval_minus_{baseline}__recovery_time_ms"
        if len(paired) >= 2:
            result = paired_effect(paired)
            result["paired_recovered_seeds"] = len(paired)
            result["interpretation"] = "positive means RL took longer to recover"
            comparisons[name] = result
            raw_p[name] = result["wilcoxon_two_sided_p"]
        else:
            comparisons[name] = {
                "paired_recovered_seeds": len(paired),
                "status": "insufficient paired recoveries for inference",
            }

    adjusted = holm_adjust(raw_p)
    for name, result in comparisons.items():
        if name in adjusted:
            result["wilcoxon_holm_adjusted_p"] = adjusted[name]

    return {
        "status": "PASS",
        "analysis": "paired A1/B/A2 and return-A recovery inference",
        "independent_unit": "workload_seed / paired simulation run",
        "n_paired_seeds": len(seeds),
        "workload_seeds": seeds,
        "workload_profile": next(iter(profiles)),
        "provenance_fingerprint": next(iter(fingerprints)),
        "recovery_rates": recovery_rates,
        "comparisons": comparisons,
        "limitations": [
            "Bootstrap intervals resample workload seeds, not tasks.",
            "Recovery-time comparisons are conditional on both policies recovering within A2.",
            "A policy that does not recover within the observed horizon is not assigned an artificial recovery time.",
            "Recovery thresholds and 10-task window size are operational definitions and require sensitivity analysis.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summaries", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, default=Path("aba_regime_inference.json"))
    args = parser.parse_args()
    try:
        result = analyze(args.summaries)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (AnalysisError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
