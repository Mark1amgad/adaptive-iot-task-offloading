#!/usr/bin/env python3
"""Validate a variable-workload v2 iFogSim training run from its JSONL trace."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

def load_trace(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def one(rows: list[dict], record: str, **filters) -> dict:
    found = [r for r in rows if r.get("record") == record and all(r.get(k) == v for k, v in filters.items())]
    if len(found) != 1:
        raise AssertionError(f"expected one {record} {filters}, got {len(found)}")
    return found[0]

def many(rows: list[dict], record: str, **filters) -> list[dict]:
    return [r for r in rows if r.get("record") == record and all(r.get(k) == v for k, v in filters.items())]

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    workload_path = next(root.glob("workload_seed*.jsonl"))
    workload = [json.loads(line) for line in workload_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    trace_path = root / "train_policy" / "partial_trace.jsonl"
    rows = load_trace(trace_path)
    cfg = one(rows, "config")
    if cfg.get("workload_file") != str(workload_path):
        # Paths may differ only by path normalization; the trace still must identify the same workload filename.
        if Path(str(cfg.get("workload_file", ""))).name != workload_path.name:
            raise AssertionError("trace config does not identify the generated workload file")
    expected_count = len(workload)
    if cfg.get("task_count") != expected_count:
        raise AssertionError("configured task count differs from workload row count")
    decisions = many(rows, "decision")
    if len(decisions) != expected_count or len({r["task_id"] for r in decisions}) != expected_count:
        raise AssertionError("decision/task cardinality mismatch")
    decision_by_seq = {int(r["task_id"].rsplit(":", 1)[1]): r for r in decisions}
    if set(decision_by_seq) != set(range(1, expected_count + 1)):
        raise AssertionError("task sequence identifiers are not contiguous")
    split_classes = set()
    urgency_classes = set()
    output_sizes = set()
    partial_count = full_count = 0
    total_merges = 0
    deadline_misses = 0
    for row in workload:
        seq = row["sequence"]
        decision = decision_by_seq[seq]
        task_id = decision["task_id"]
        for key in ("task_mi", "input_bytes", "output_bytes", "deadline_ms", "urgency_class", "splittability"):
            if decision.get(key) != row[key]:
                raise AssertionError(f"{task_id}: decision {key} differs from source workload")
        split_classes.add(row["splittability"])
        urgency_classes.add(row["urgency_class"])
        output_sizes.add(row["output_bytes"])
        action = decision["action"]
        is_partial = "_PARTIAL_" in action
        if is_partial and row["splittability"] != "DATA_PARALLEL_DIVISIBLE":
            raise AssertionError(f"{task_id}: indivisible task selected partial action")
        branches = many(rows, "branch_created", task_id=task_id)
        expected_branches = 2 if is_partial else 1
        if len(branches) != expected_branches:
            raise AssertionError(f"{task_id}: branch cardinality mismatch")
        profile_suffix = f"_O{row['output_bytes']}"
        for branch in branches:
            if is_partial:
                expected_input_type = ("LOCAL_PARTIAL_INPUT" if branch["branch"] == "local"
                                       else f"{branch['tier']}_PARTIAL_INPUT") + profile_suffix
            else:
                expected_input_type = "TASK_INPUT" + profile_suffix
            if branch.get("tuple_type") != expected_input_type:
                raise AssertionError(f"{task_id}: typed AppEdge does not match output-size profile")
        if is_partial:
            partial_count += 1
            percent = int(action.rsplit("_", 1)[1])
            remote_tier = "edge" if action.startswith("EDGE_") else "cloud"
            by_name = {b["branch"]: b for b in branches}
            if set(by_name) != {"local", remote_tier}:
                raise AssertionError(f"{task_id}: wrong partial branch pair")
            local, remote = by_name["local"], by_name[remote_tier]
            if local["module"] != f"local_partial_{percent}" or remote["module"] != f"{remote_tier}_partial_{percent}":
                raise AssertionError(f"{task_id}: wrong partial worker module")
            for key in ("mi", "input_bytes", "output_bytes"):
                expected_total = row[{"mi": "task_mi", "input_bytes": "input_bytes", "output_bytes": "output_bytes"}[key]]
                if local[key] + remote[key] != expected_total:
                    raise AssertionError(f"{task_id}: {key} conservation failed")
            if remote["mi"] != int(row["task_mi"] * percent / 100 + 0.5):
                raise AssertionError(f"{task_id}: remote MI ratio mismatch")
            if remote["input_bytes"] != int(row["input_bytes"] * percent / 100 + 0.5):
                raise AssertionError(f"{task_id}: remote input ratio mismatch")
            if remote["output_bytes"] != int(row["output_bytes"] * percent / 100 + 0.5):
                raise AssertionError(f"{task_id}: remote output ratio mismatch")
            pstart = one(rows, "partition_overhead_started", task_id=task_id)
            pdone = one(rows, "partition_overhead_completed", task_id=task_id)
            if (pdone["sim_time_ms"] - pstart["sim_time_ms"]) + 1e-9 < cfg["partition_overhead_ms"]:
                raise AssertionError(f"{task_id}: partition overhead missing")
            barrier = one(rows, "merge_barrier", task_id=task_id)
            results = many(rows, "branch_result", task_id=task_id)
            if len(results) != 2 or barrier["sim_time_ms"] < max(x["sim_time_ms"] for x in results):
                raise AssertionError(f"{task_id}: merge barrier did not wait for both branches")
            mstart = one(rows, "merge_overhead_started", task_id=task_id)
            mdone = one(rows, "merge_overhead_completed", task_id=task_id)
            merge = one(rows, "merge_created", task_id=task_id)
            if mstart["sim_time_ms"] != barrier["sim_time_ms"] or (mdone["sim_time_ms"] - mstart["sim_time_ms"]) + 1e-9 < cfg["merge_overhead_ms"]:
                raise AssertionError(f"{task_id}: merge overhead/barrier timing mismatch")
            if merge["mi"] != row["merge_mi"] or merge["input_bytes"] != row["output_bytes"] or merge["output_bytes"] != row["merge_output_bytes"]:
                raise AssertionError(f"{task_id}: merge workload mismatch")
            merge_exec = one(rows, "execution", task_id=task_id, branch="merge")
            merge_result = one(rows, "merge_result", task_id=task_id)
            if merge_exec["sim_time_ms"] < mdone["sim_time_ms"] or merge_result["sim_time_ms"] < merge_exec["sim_time_ms"]:
                raise AssertionError(f"{task_id}: merge execution lifecycle invalid")
            total_merges += 1
        else:
            full_count += 1
            expected_module = {"LOCAL": "local_executor", "EDGE_FULL": "edge_executor", "CLOUD_FULL": "cloud_executor"}.get(action)
            if expected_module is None or branches[0]["module"] != expected_module:
                raise AssertionError(f"{task_id}: invalid full-placement action/module")
            branch = branches[0]
            if branch["mi"] != row["task_mi"] or branch["input_bytes"] != row["input_bytes"] or branch["output_bytes"] != row["output_bytes"]:
                raise AssertionError(f"{task_id}: full workload changed")
        terminal = one(rows, "task_terminal", task_id=task_id)
        if terminal["deadline_ms"] != row["deadline_ms"] or terminal["urgency_class"] != row["urgency_class"]:
            raise AssertionError(f"{task_id}: deadline/urgency metadata mismatch")
        expected_deadline = terminal["latency_ms"] <= row["deadline_ms"]
        if terminal["deadline_met"] != expected_deadline:
            raise AssertionError(f"{task_id}: deadline flag inconsistent with measured latency")
        deadline_misses += int(not expected_deadline)
        one(rows, "outcome_ack", task_id=task_id)
    if "mixed" == workload[0].get("profile") and len(split_classes) != 2:
        raise AssertionError("mixed workload did not contain both divisible and indivisible tasks")
    if len(output_sizes) < 2 or len(urgency_classes) < 2:
        raise AssertionError("workload did not exercise multiple output sizes and urgency classes")
    if len({r["task_mi"] for r in workload}) < 10 or len({r["input_bytes"] for r in workload}) < 10:
        raise AssertionError("workload does not contain sufficient compute/input diversity")
    acceptance = one(rows, "acceptance")
    if acceptance.get("status") != "PASS" or acceptance.get("tasks") != expected_count:
        raise AssertionError("Java acceptance record is not PASS or task count mismatch")
    model_path = root / "train_policy" / "python_model.json"
    model = json.loads(model_path.read_text(encoding="utf-8"))
    if model.get("state_count") != 13122 or len(model.get("actions", [])) != 9:
        raise AssertionError("saved model does not match nine-feature/9-action v2 state spec")
    if model.get("counters", {}).get("updates") != expected_count:
        raise AssertionError("model update count differs from completed workload tasks")
    shutdown = one(rows, "shutdown_ack")
    if shutdown.get("orphaned_tasks") != 0 or shutdown.get("tasks_reported") != expected_count:
        raise AssertionError("Python shutdown reconciliation failed")
    stderr = root / "train_policy" / "python_stderr.log"
    if stderr.exists() and stderr.read_text(encoding="utf-8").strip():
        raise AssertionError("Python stderr is not empty")
    print(json.dumps({
        "status": "PASS", "seed": workload[0]["seed"], "profile": workload[0]["profile"],
        "tasks": expected_count, "partial_tasks": partial_count, "full_tasks": full_count,
        "merge_tasks": total_merges, "splittability_classes": sorted(split_classes),
        "urgency_classes": sorted(urgency_classes), "output_sizes_bytes": sorted(output_sizes),
        "deadline_misses": deadline_misses, "state_count": model["state_count"],
        "q_values": model["state_count"] * len(model["actions"]),
        "model_updates": model["counters"]["updates"],
    }, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2), flush=True)
        raise
