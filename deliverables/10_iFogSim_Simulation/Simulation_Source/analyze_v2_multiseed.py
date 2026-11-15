#!/usr/bin/env python3
"""Aggregate paired policy comparisons over multiple held-out workload seeds."""
from __future__ import annotations
import argparse
import json
import math
import statistics
from pathlib import Path

POLICIES = ("local", "edge", "cloud", "random", "rl_eval")

def load_rows(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]

def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(p * len(ordered)) - 1)]

def seq(task_id: str) -> int:
    return int(task_id.rsplit(":", 1)[1])

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--comparison-root", action="append", type=Path, required=True)
    ap.add_argument("--workload", action="append", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--training-seed", type=int, required=True)
    ap.add_argument("--training-model", type=Path, required=True)
    args = ap.parse_args()
    if len(args.comparison_root) != len(args.workload) or len(args.workload) < 2:
        raise ValueError("supply matching comparison-root/workload pairs for at least two holdout seeds")
    pooled = {p: {"latency": [], "bandwidth": [], "deadline_misses": 0, "actions": {}, "modes": {}} for p in POLICIES}
    seed_reports = []
    paired_by_baseline = {p: [] for p in ("local", "edge", "cloud", "random")}
    paired_counts = {p: {"rl_faster": 0, "baseline_faster": 0, "ties": 0} for p in paired_by_baseline}
    task_total = 0
    seeds = []
    for comparison_root, workload_path in zip(args.comparison_root, args.workload):
        workload = load_rows(workload_path)
        seed = int(workload[0]["seed"])
        if seed in seeds: raise AssertionError(f"duplicate workload seed {seed}")
        seeds.append(seed)
        expected = {int(x["sequence"]): x for x in workload}
        n = len(expected)
        seed_policy = {}
        latencies = {}
        for policy in POLICIES:
            summary = json.loads((comparison_root / "policy_comparison_summary.json").read_text(encoding="utf-8"))
            if summary.get("status") != "PASS" or summary.get("workload_seed") != seed or summary.get("tasks") != n:
                raise AssertionError(f"seed {seed}/{policy}: comparison summary mismatch")
            trace = load_rows(comparison_root / f"policy_{policy}" / "partial_trace.jsonl")
            decisions = {seq(x["task_id"]): x for x in trace if x.get("record") == "decision"}
            terminals = {seq(x["task_id"]): x for x in trace if x.get("record") == "task_terminal"}
            if set(decisions) != set(expected) or set(terminals) != set(expected):
                raise AssertionError(f"seed {seed}/{policy}: incomplete task coverage")
            values = []
            bandwidth = []
            misses = 0
            action_counts = {}
            mode_counts = {}
            for k, task in expected.items():
                d, t = decisions[k], terminals[k]
                for field in ("task_mi", "input_bytes", "output_bytes", "deadline_ms", "urgency_class", "splittability"):
                    if d.get(field) != task[field]: raise AssertionError(f"seed {seed}/{policy}/task{k}: workload mismatch {field}")
                values.append(float(t["latency_ms"]))
                bandwidth.append(float(t["bandwidth_bytes"]))
                misses += int(not bool(t["deadline_met"]))
                action_counts[d["action"]] = action_counts.get(d["action"], 0) + 1
                mode = d.get("mode", "unknown")
                mode_counts[mode] = mode_counts.get(mode, 0) + 1
            latencies[policy] = {k: float(terminals[k]["latency_ms"]) for k in expected}
            pooled[policy]["latency"].extend(values)
            pooled[policy]["bandwidth"].extend(bandwidth)
            pooled[policy]["deadline_misses"] += misses
            for action, count in action_counts.items():
                pooled[policy]["actions"][action] = pooled[policy]["actions"].get(action, 0) + count
            for mode, count in mode_counts.items():
                pooled[policy]["modes"][mode] = pooled[policy]["modes"].get(mode, 0) + count
            seed_policy[policy] = {
                "mean_latency_ms": statistics.mean(values), "median_latency_ms": statistics.median(values),
                "p95_latency_ms": percentile(values, 0.95), "deadline_misses": misses,
                "deadline_miss_rate": misses / n, "mean_bandwidth_bytes": statistics.mean(bandwidth),
                "action_counts": action_counts, "decision_modes": mode_counts,
            }
        for baseline in paired_by_baseline:
            diffs = [latencies["rl_eval"][k] - latencies[baseline][k] for k in expected]
            paired_by_baseline[baseline].append(statistics.mean(diffs))
            paired_counts[baseline]["rl_faster"] += sum(x < 0 for x in diffs)
            paired_counts[baseline]["baseline_faster"] += sum(x > 0 for x in diffs)
            paired_counts[baseline]["ties"] += sum(x == 0 for x in diffs)
        seed_reports.append({"seed": seed, "tasks": n, "policy_metrics": seed_policy})
        task_total += n
    overall = {}
    for policy, data in pooled.items():
        values, bandwidth = data["latency"], data["bandwidth"]
        overall[policy] = {
            "tasks": len(values), "mean_latency_ms": statistics.mean(values),
            "median_latency_ms": statistics.median(values), "p95_latency_ms": percentile(values, 0.95),
            "deadline_misses": data["deadline_misses"], "deadline_miss_rate": data["deadline_misses"] / len(values),
            "mean_bandwidth_bytes": statistics.mean(bandwidth), "action_counts": data["actions"],
            "decision_modes": data["modes"],
        }
    paired = {}
    for baseline, per_seed in paired_by_baseline.items():
        paired["rl_minus_" + baseline] = {
            "mean_paired_latency_difference_ms": statistics.mean(per_seed),
            "sd_of_seed_mean_differences_ms": statistics.stdev(per_seed) if len(per_seed) > 1 else 0.0,
            "per_seed_mean_differences_ms": dict(zip(seeds, per_seed)),
            **paired_counts[baseline],
        }
    model = json.loads(args.training_model.read_text(encoding="utf-8"))
    visits = model["visits"]
    q_values = model["q"]
    state_count = int(model["state_count"])
    action_count = len(model["actions"])
    visited_states = sum(any(cell > 0 for cell in state_row) for state_row in visits)
    visited_state_action_cells = sum(cell > 0 for state_row in visits for cell in state_row)
    total_state_action_cells = state_count * action_count
    q_init = model.get("agent_config", {}).get("q_init", 0.0)
    training_coverage = {
        "state_count": state_count, "action_count": action_count,
        "total_state_action_cells": total_state_action_cells,
        "decisions": model.get("counters", {}).get("decisions"),
        "updates": model.get("counters", {}).get("updates"),
        "unique_visited_states": visited_states,
        "unique_visited_state_action_cells": visited_state_action_cells,
        "state_coverage_rate": visited_states / state_count,
        "state_action_coverage_rate": visited_state_action_cells / total_state_action_cells,
        "non_default_q_cells": sum(value != q_init for state_row in q_values for value in state_row),
        "max_visits_per_state_action_cell": max((cell for state_row in visits for cell in state_row), default=0),
    }
    report = {
        "status": "PASS", "training_seed": args.training_seed, "training_coverage": training_coverage,
        "heldout_seeds": seeds,
        "tasks_per_seed": [len(load_rows(w)) for w in args.workload], "total_heldout_tasks": task_total,
        "comparison_design": "paired policy replay on identical task traces within each held-out seed; one frozen model trained on one seed",
        "overall_policy_metrics": overall, "per_seed_results": seed_reports,
        "paired_rl_differences": paired,
        "limitations": [
            "Only one training seed/model was evaluated; multiple independent training seeds are still required.",
            "Three held-out workload seeds are not enough for strong statistical claims.",
            "Workloads share the same synthetic generator distribution and do not represent a held-out application regime.",
            "Energy is not measured; partition/merge and proportional data-split assumptions remain provisional.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2), flush=True)
        raise
