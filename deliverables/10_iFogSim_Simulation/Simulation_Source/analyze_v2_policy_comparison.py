#!/usr/bin/env python3
"""Validate and summarize paired policy runs over one immutable workload trace."""
from __future__ import annotations
import argparse
import json
import math
import statistics
from pathlib import Path

POLICIES = ("local", "edge", "cloud", "random", "rl_eval")

def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def one(data: list[dict], kind: str) -> dict:
    found = [r for r in data if r.get("record") == kind]
    if len(found) != 1: raise AssertionError(f"expected one {kind}, got {len(found)}")
    return found[0]

def seq(task_id: str) -> int:
    return int(task_id.rsplit(":", 1)[1])

def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(p * len(ordered)) - 1)]

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--workload", type=Path, required=True)
    args = ap.parse_args()
    workload = [json.loads(x) for x in args.workload.read_text(encoding="utf-8").splitlines() if x.strip()]
    expected = {r["sequence"]: r for r in workload}
    n = len(expected)
    metrics = {}
    task_latency = {}
    action_counts = {}
    for policy in POLICIES:
        trace = rows(args.root / f"policy_{policy}" / "partial_trace.jsonl")
        cfg = one(trace, "config")
        if cfg.get("task_count") != n or Path(cfg.get("workload_file", "")).name != args.workload.name:
            raise AssertionError(f"{policy}: workload identity/config mismatch")
        decisions = [r for r in trace if r.get("record") == "decision"]
        terminals = [r for r in trace if r.get("record") == "task_terminal"]
        acks = [r for r in trace if r.get("record") == "outcome_ack"]
        if len(decisions) != n or len(terminals) != n or len(acks) != n:
            raise AssertionError(f"{policy}: not all tasks have decision, terminal, and outcome ack")
        d_by_seq = {seq(r["task_id"]): r for r in decisions}
        t_by_seq = {seq(r["task_id"]): r for r in terminals}
        if set(d_by_seq) != set(expected) or set(t_by_seq) != set(expected):
            raise AssertionError(f"{policy}: task sequence set mismatch")
        for k, task in expected.items():
            decision, terminal = d_by_seq[k], t_by_seq[k]
            for field in ("task_mi", "input_bytes", "output_bytes", "deadline_ms", "urgency_class", "splittability"):
                if decision.get(field) != task[field]:
                    raise AssertionError(f"{policy}/task{k}: {field} differs from common workload")
            action = decision["action"]
            if "_PARTIAL_" in action and task["splittability"] != "DATA_PARALLEL_DIVISIBLE":
                raise AssertionError(f"{policy}/task{k}: partial action selected for indivisible workload")
            branches = [b for b in trace if b.get("record") == "branch_created" and b.get("task_id") == decision["task_id"]]
            profile_suffix = f"_O{task['output_bytes']}"
            for branch in branches:
                expected_base = ("LOCAL_PARTIAL_INPUT" if branch["branch"] == "local" else f"{branch['tier']}_PARTIAL_INPUT") if "_PARTIAL_" in action else "TASK_INPUT"
                if branch.get("tuple_type") != expected_base + profile_suffix:
                    raise AssertionError(f"{policy}/task{k}: AppEdge output-size profile mismatch")
            if terminal["deadline_met"] != (terminal["latency_ms"] <= task["deadline_ms"]):
                raise AssertionError(f"{policy}/task{k}: deadline flag inconsistent")
        latencies = [float(t_by_seq[k]["latency_ms"]) for k in sorted(expected)]
        bandwidth = [float(t_by_seq[k]["bandwidth_bytes"]) for k in sorted(expected)]
        misses = sum(not bool(t_by_seq[k]["deadline_met"]) for k in expected)
        actions = {}
        for decision in decisions: actions[decision["action"]] = actions.get(decision["action"], 0) + 1
        action_counts[policy] = actions
        task_latency[policy] = {k: float(t_by_seq[k]["latency_ms"]) for k in expected}
        metrics[policy] = {
            "tasks": n, "mean_latency_ms": statistics.mean(latencies),
            "median_latency_ms": statistics.median(latencies), "p95_latency_ms": percentile(latencies, 0.95),
            "deadline_misses": misses, "deadline_miss_rate": misses / n,
            "mean_bandwidth_bytes": statistics.mean(bandwidth), "action_counts": actions,
        }
        shutdown = one(trace, "shutdown_ack")
        if shutdown.get("orphaned_tasks") != 0 or shutdown.get("tasks_reported") != n:
            raise AssertionError(f"{policy}: Python shutdown reconciliation failed")
        if any(r.get("record") == "task_failed" for r in trace):
            raise AssertionError(f"{policy}: failed task observed in evaluation")
        stderr = args.root / f"policy_{policy}" / "python_stderr.log"
        if stderr.exists() and stderr.read_text(encoding="utf-8").strip():
            raise AssertionError(f"{policy}: Python stderr not empty")
    paired = {}
    for baseline in ("local", "edge", "cloud", "random"):
        diffs = [task_latency["rl_eval"][k] - task_latency[baseline][k] for k in expected]
        paired[f"rl_minus_{baseline}_latency_ms"] = {
            "mean_difference": statistics.mean(diffs),
            "rl_faster_tasks": sum(x < 0 for x in diffs),
            "baseline_faster_tasks": sum(x > 0 for x in diffs),
            "ties": sum(x == 0 for x in diffs),
        }
    report = {
        "status": "PASS", "workload_seed": workload[0]["seed"],
        "workload_profile": workload[0]["profile"], "tasks": n,
        "comparison_design": "paired: identical task rows, arrival gaps, deadlines, and network settings per policy",
        "policy_metrics": metrics, "paired_rl_differences": paired,
        "interpretation": "Descriptive single-seed evaluation only; not evidence of statistical significance, convergence, or generalization.",
    }
    out = args.root / "policy_comparison_summary.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2), flush=True)
        raise
