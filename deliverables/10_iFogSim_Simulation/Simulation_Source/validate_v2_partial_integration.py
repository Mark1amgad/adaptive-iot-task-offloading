#!/usr/bin/env python3
"""Strict acceptance validator for all nine live protocol-v2 iFogSim actions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ACTIONS = {
    "LOCAL": (0, False, "LOCAL", "local_executor"),
    "EDGE_PARTIAL_25": (1, True, "EDGE", "edge_partial_25"),
    "EDGE_PARTIAL_50": (2, True, "EDGE", "edge_partial_50"),
    "EDGE_PARTIAL_75": (3, True, "EDGE", "edge_partial_75"),
    "EDGE_FULL": (4, False, "EDGE", "edge_executor"),
    "CLOUD_PARTIAL_25": (5, True, "CLOUD", "cloud_partial_25"),
    "CLOUD_PARTIAL_50": (6, True, "CLOUD", "cloud_partial_50"),
    "CLOUD_PARTIAL_75": (7, True, "CLOUD", "cloud_partial_75"),
    "CLOUD_FULL": (8, False, "CLOUD", "cloud_executor"),
}
CATALOGUE = list(ACTIONS)


def load_trace(path: Path) -> list[dict]:
    rows = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
        if not isinstance(row, dict) or "record" not in row:
            raise AssertionError(f"{path}:{line_no}: malformed trace record")
        rows.append(row)
    return rows


def one(rows: list[dict], kind: str, **filters) -> dict:
    found = [r for r in rows if r["record"] == kind and all(r.get(k) == v for k, v in filters.items())]
    if len(found) != 1:
        raise AssertionError(f"expected one {kind} {filters}, found {len(found)}")
    return found[0]


def many(rows: list[dict], kind: str, **filters) -> list[dict]:
    return [r for r in rows if r["record"] == kind and all(r.get(k) == v for k, v in filters.items())]


def validate_case(case_dir: Path, action: str, tasks_expected: int) -> dict:
    trace_path = case_dir / "partial_trace.jsonl"
    stderr_path = case_dir / "python_stderr.log"
    if not trace_path.is_file() or not stderr_path.is_file():
        raise AssertionError(f"{action}: missing trace or Python stderr artifact")
    if stderr_path.read_text(encoding="utf-8").strip():
        raise AssertionError(f"{action}: Python stderr is not empty")
    rows = load_trace(trace_path)
    action_id, partial, remote_tier, remote_module = ACTIONS[action]
    cfg = one(rows, "config")
    if cfg.get("action_policy") != action or cfg.get("task_count") != tasks_expected:
        raise AssertionError(f"{action}: run config mismatch")
    hello = one(rows, "hello_ack")
    if hello.get("mode") != "baseline" or hello.get("policy") != action.lower():
        raise AssertionError(f"{action}: wrong Python baseline policy")
    if hello.get("actions") != CATALOGUE:
        raise AssertionError(f"{action}: Python did not advertise full nine-action catalogue")

    decisions = many(rows, "decision")
    task_ids = [r["task_id"] for r in decisions]
    if len(task_ids) != tasks_expected or len(set(task_ids)) != tasks_expected:
        raise AssertionError(f"{action}: decision/task cardinality mismatch")
    if any(r.get("action") != action or r.get("action_id") != action_id for r in decisions):
        raise AssertionError(f"{action}: selected action differs from requested fixed action")

    tuple_ids = []
    for task_id in task_ids:
        task_branches = many(rows, "branch_created", task_id=task_id)
        expected_branch_count = 2 if partial else 1
        if len(task_branches) != expected_branch_count:
            raise AssertionError(f"{action}/{task_id}: wrong number of input branches")
        tuple_ids.extend(r["tuple_id"] for r in task_branches)

        if partial:
            expected_names = {"local", remote_tier.lower()}
            if {r["branch"] for r in task_branches} != expected_names:
                raise AssertionError(f"{action}/{task_id}: Local+remote branch pair mismatch")
            if {r["tier"] for r in task_branches} != {"LOCAL", remote_tier}:
                raise AssertionError(f"{action}/{task_id}: branch tier mismatch")
            by_name = {r["branch"]: r for r in task_branches}
            local, remote = by_name["local"], by_name[remote_tier.lower()]
            if local["module"] != f"local_partial_{action.rsplit('_', 1)[1]}":
                raise AssertionError(f"{action}/{task_id}: wrong Local ratio worker")
            if remote["module"] != remote_module:
                raise AssertionError(f"{action}/{task_id}: wrong remote ratio worker")
            if local["mi"] + remote["mi"] != cfg["task_mi"]:
                raise AssertionError(f"{action}/{task_id}: MI conservation failed")
            if local["input_bytes"] + remote["input_bytes"] != cfg["input_bytes"]:
                raise AssertionError(f"{action}/{task_id}: input-byte conservation failed")
            if local["output_bytes"] + remote["output_bytes"] != cfg["output_bytes"]:
                raise AssertionError(f"{action}/{task_id}: output-byte conservation failed")
            percent = int(action.rsplit("_", 1)[1])
            if remote["mi"] != int(cfg["task_mi"] * percent / 100 + 0.5):
                raise AssertionError(f"{action}/{task_id}: remote compute ratio mismatch")
            if remote["input_bytes"] != int(cfg["input_bytes"] * percent / 100 + 0.5):
                raise AssertionError(f"{action}/{task_id}: remote input partition ratio mismatch")
            if remote["output_bytes"] != int(cfg["output_bytes"] * percent / 100 + 0.5):
                raise AssertionError(f"{action}/{task_id}: remote output partition ratio mismatch")
            decision = one(rows, "decision", task_id=task_id)
            partition_start = one(rows, "partition_overhead_started", task_id=task_id)
            partition_done = one(rows, "partition_overhead_completed", task_id=task_id)
            if partition_start["sim_time_ms"] != decision["sim_time_ms"]:
                raise AssertionError(f"{action}/{task_id}: partition overhead did not start at decision")
            if partition_done["sim_time_ms"] - partition_start["sim_time_ms"] < cfg["partition_overhead_ms"]:
                raise AssertionError(f"{action}/{task_id}: partition overhead was not simulated")
            if min(r["sim_time_ms"] for r in task_branches) < partition_done["sim_time_ms"]:
                raise AssertionError(f"{action}/{task_id}: branches emitted before partition overhead")
        else:
            branch = task_branches[0]
            expected_module = {
                "LOCAL": "local_executor", "EDGE_FULL": "edge_executor",
                "CLOUD_FULL": "cloud_executor",
            }[action]
            if branch["branch"] != "full" or branch["module"] != expected_module:
                raise AssertionError(f"{action}/{task_id}: wrong full-placement worker")
            if branch["mi"] != cfg["task_mi"] or branch["input_bytes"] != cfg["input_bytes"]:
                raise AssertionError(f"{action}/{task_id}: full task workload changed")

        executions = many(rows, "execution", task_id=task_id)
        branch_results = many(rows, "branch_result", task_id=task_id)
        expected_execution_count = 3 if partial else 1
        if len(executions) != expected_execution_count or len(branch_results) != expected_branch_count:
            raise AssertionError(f"{action}/{task_id}: execution/result lifecycle cardinality mismatch")
        for created in task_branches:
            ex = one(rows, "execution", task_id=task_id, tuple_id=created["tuple_id"])
            result = one(rows, "branch_result", task_id=task_id, tuple_id=created["tuple_id"])
            if ex["module"] != created["module"] or result["sim_time_ms"] < ex["sim_time_ms"]:
                raise AssertionError(f"{action}/{task_id}: branch executed on wrong worker or result preceded execution")

        if partial:
            barrier = one(rows, "merge_barrier", task_id=task_id)
            merge_overhead_start = one(rows, "merge_overhead_started", task_id=task_id)
            merge_overhead_done = one(rows, "merge_overhead_completed", task_id=task_id)
            merge_created = one(rows, "merge_created", task_id=task_id)
            merge_exec = one(rows, "execution", task_id=task_id, branch="merge")
            merge_result = one(rows, "merge_result", task_id=task_id)
            merge_id = merge_created["tuple_id"]
            tuple_ids.append(merge_id)
            result_times = [r["sim_time_ms"] for r in branch_results]
            if barrier["sim_time_ms"] < max(result_times) or merge_created["sim_time_ms"] < max(result_times):
                raise AssertionError(f"{action}/{task_id}: merge barrier preceded a branch result")
            if merge_overhead_start["sim_time_ms"] != barrier["sim_time_ms"]:
                raise AssertionError(f"{action}/{task_id}: merge overhead did not start at barrier")
            if merge_overhead_done["sim_time_ms"] - merge_overhead_start["sim_time_ms"] < cfg["merge_overhead_ms"]:
                raise AssertionError(f"{action}/{task_id}: merge overhead was not simulated")
            if merge_created["sim_time_ms"] < merge_overhead_done["sim_time_ms"]:
                raise AssertionError(f"{action}/{task_id}: merge tuple emitted before merge overhead")
            if merge_exec["sim_time_ms"] < merge_created["sim_time_ms"]:
                raise AssertionError(f"{action}/{task_id}: merge execution preceded merge tuple")
            if merge_result["sim_time_ms"] < max(result_times) or merge_result["sim_time_ms"] < merge_exec["sim_time_ms"]:
                raise AssertionError(f"{action}/{task_id}: merge result timing invalid")
            terminal = one(rows, "task_terminal", task_id=task_id)
            if terminal["sim_time_ms"] < merge_result["sim_time_ms"]:
                raise AssertionError(f"{action}/{task_id}: task terminal preceded merge result")
        else:
            terminal = one(rows, "task_terminal", task_id=task_id)
            if terminal["sim_time_ms"] < branch_results[0]["sim_time_ms"]:
                raise AssertionError(f"{action}/{task_id}: full terminal preceded result")

        outcome_send = one(rows, "python_send", type="outcome", task_id=task_id)
        if outcome_send.get("action_executed") != action_id:
            raise AssertionError(f"{action}/{task_id}: outcome reports wrong compound action")
        one(rows, "outcome_ack", task_id=task_id)

    if len(tuple_ids) != len(set(tuple_ids)):
        raise AssertionError(f"{action}: duplicate tuple IDs across task branches")
    if many(rows, "task_failed") or many(rows, "failure_outcome_ack"):
        raise AssertionError(f"{action}: at least one task failed")
    shutdown = one(rows, "shutdown_ack")
    if shutdown.get("orphaned_tasks") != 0 or shutdown.get("tasks_reported") != tasks_expected:
        raise AssertionError(f"{action}: Python pending-task reconciliation failed")
    exit_row = one(rows, "python_exit")
    if exit_row.get("shutdown_ack") is not True or exit_row.get("exit_code") != 0:
        raise AssertionError(f"{action}: Python process did not exit cleanly")
    acceptance = one(rows, "acceptance")
    if acceptance.get("status") != "PASS" or acceptance.get("tasks") != tasks_expected:
        raise AssertionError(f"{action}: Java acceptance record mismatch")
    return {"action": action, "tasks": tasks_expected, "branches_per_task": 2 if partial else 1,
            "merge_tasks": tasks_expected if partial else 0, "tuple_ids": len(tuple_ids)}


def validate_training_case(case_dir: Path, tasks_expected: int) -> dict:
    trace_path = case_dir / "partial_trace.jsonl"
    stderr_path = case_dir / "python_stderr.log"
    if not trace_path.is_file() or not stderr_path.is_file():
        raise AssertionError("train_policy: missing trace or Python stderr artifact")
    if stderr_path.read_text(encoding="utf-8").strip():
        raise AssertionError("train_policy: Python stderr is not empty")
    rows = load_trace(trace_path)
    cfg = one(rows, "config")
    if cfg.get("mode") != "train" or cfg.get("action_policy") != "learned_train":
        raise AssertionError("train_policy: wrong mode/config")
    if cfg.get("task_count") != tasks_expected:
        raise AssertionError("train_policy: wrong task count")
    hello = one(rows, "hello_ack")
    if hello.get("mode") != "train" or hello.get("policy") != "qlearning" or hello.get("actions") != CATALOGUE:
        raise AssertionError("train_policy: wrong Python training handshake")

    decisions = many(rows, "decision")
    task_ids = [r["task_id"] for r in decisions]
    if len(task_ids) != tasks_expected or len(set(task_ids)) != tasks_expected:
        raise AssertionError("train_policy: decision/task cardinality mismatch")
    counts = {}
    tuple_ids = []
    update_counts = []
    partial_count = full_count = 0
    for decision in decisions:
        action = decision.get("action")
        if action not in ACTIONS or decision.get("action_id") != ACTIONS[action][0]:
            raise AssertionError(f"train_policy: invalid action response {decision}")
        action_id, partial, remote_tier, remote_module = ACTIONS[action]
        counts[action] = counts.get(action, 0) + 1
        partial_count += int(partial)
        full_count += int(not partial)
        task_id = decision["task_id"]
        branches = many(rows, "branch_created", task_id=task_id)
        expected_count = 2 if partial else 1
        if len(branches) != expected_count:
            raise AssertionError(f"train_policy/{task_id}: branch count mismatch")
        tuple_ids.extend(r["tuple_id"] for r in branches)
        if partial:
            by_name = {r["branch"]: r for r in branches}
            if set(by_name) != {"local", remote_tier.lower()}:
                raise AssertionError(f"train_policy/{task_id}: Local+remote branch mismatch")
            local, remote = by_name["local"], by_name[remote_tier.lower()]
            percent = int(action.rsplit("_", 1)[1])
            suffix = str(percent)
            if local["module"] != f"local_partial_{suffix}" or remote["module"] != remote_module:
                raise AssertionError(f"train_policy/{task_id}: ratio worker mismatch")
            if local["tier"] != "LOCAL" or remote["tier"] != remote_tier:
                raise AssertionError(f"train_policy/{task_id}: tier mismatch")
            if local["mi"] + remote["mi"] != cfg["task_mi"] or local["input_bytes"] + remote["input_bytes"] != cfg["input_bytes"] or local["output_bytes"] + remote["output_bytes"] != cfg["output_bytes"]:
                raise AssertionError(f"train_policy/{task_id}: workload conservation failed")
            if remote["mi"] != int(cfg["task_mi"] * percent / 100 + 0.5):
                raise AssertionError(f"train_policy/{task_id}: compute ratio mismatch")
            if remote["input_bytes"] != int(cfg["input_bytes"] * percent / 100 + 0.5):
                raise AssertionError(f"train_policy/{task_id}: input ratio mismatch")
            if remote["output_bytes"] != int(cfg["output_bytes"] * percent / 100 + 0.5):
                raise AssertionError(f"train_policy/{task_id}: output ratio mismatch")
            pstart = one(rows, "partition_overhead_started", task_id=task_id)
            pdone = one(rows, "partition_overhead_completed", task_id=task_id)
            if pdone["sim_time_ms"] - pstart["sim_time_ms"] < cfg["partition_overhead_ms"]:
                raise AssertionError(f"train_policy/{task_id}: partition delay missing")
            if min(b["sim_time_ms"] for b in branches) < pdone["sim_time_ms"]:
                raise AssertionError(f"train_policy/{task_id}: branches emitted before partition delay")
        else:
            branch = branches[0]
            expected_module = {"LOCAL": "local_executor", "EDGE_FULL": "edge_executor", "CLOUD_FULL": "cloud_executor"}[action]
            if branch["branch"] != "full" or branch["module"] != expected_module:
                raise AssertionError(f"train_policy/{task_id}: full worker mismatch")

        executions = many(rows, "execution", task_id=task_id)
        results = many(rows, "branch_result", task_id=task_id)
        if len(executions) != (3 if partial else 1) or len(results) != expected_count:
            raise AssertionError(f"train_policy/{task_id}: execution/result count mismatch")
        for branch in branches:
            ex = one(rows, "execution", task_id=task_id, tuple_id=branch["tuple_id"])
            res = one(rows, "branch_result", task_id=task_id, tuple_id=branch["tuple_id"])
            if ex["module"] != branch["module"] or res["sim_time_ms"] < ex["sim_time_ms"]:
                raise AssertionError(f"train_policy/{task_id}: branch lifecycle mismatch")
        if partial:
            barrier = one(rows, "merge_barrier", task_id=task_id)
            ms = one(rows, "merge_overhead_started", task_id=task_id)
            md = one(rows, "merge_overhead_completed", task_id=task_id)
            mc = one(rows, "merge_created", task_id=task_id)
            me = one(rows, "execution", task_id=task_id, branch="merge")
            mr = one(rows, "merge_result", task_id=task_id)
            tuple_ids.append(mc["tuple_id"])
            latest = max(r["sim_time_ms"] for r in results)
            if barrier["sim_time_ms"] < latest or ms["sim_time_ms"] != barrier["sim_time_ms"]:
                raise AssertionError(f"train_policy/{task_id}: barrier timing mismatch")
            if md["sim_time_ms"] - ms["sim_time_ms"] < cfg["merge_overhead_ms"] or mc["sim_time_ms"] < md["sim_time_ms"]:
                raise AssertionError(f"train_policy/{task_id}: merge overhead missing")
            if me["sim_time_ms"] < mc["sim_time_ms"] or mr["sim_time_ms"] < me["sim_time_ms"]:
                raise AssertionError(f"train_policy/{task_id}: merge execution/result timing mismatch")
            terminal = one(rows, "task_terminal", task_id=task_id)
            if terminal["sim_time_ms"] < mr["sim_time_ms"]:
                raise AssertionError(f"train_policy/{task_id}: terminal before merge result")
        else:
            terminal = one(rows, "task_terminal", task_id=task_id)
            if terminal["sim_time_ms"] < results[0]["sim_time_ms"]:
                raise AssertionError(f"train_policy/{task_id}: full terminal before branch result")

        sent = one(rows, "python_send", type="outcome", task_id=task_id)
        if sent.get("action_executed") != action_id:
            raise AssertionError(f"train_policy/{task_id}: wrong executed action in outcome")
        ack = one(rows, "outcome_ack", task_id=task_id)
        if ack.get("updated") is not True or not isinstance(ack.get("update_count"), int):
            raise AssertionError(f"train_policy/{task_id}: training update was not applied")
        update_counts.append(ack["update_count"])

    if sorted(update_counts) != list(range(1, tasks_expected + 1)):
        raise AssertionError("train_policy: measured-outcome update count is not a complete 1..N sequence")
    if partial_count == 0 or full_count == 0:
        raise AssertionError("train_policy: training run did not exercise both partial and full placements")
    if len(tuple_ids) != len(set(tuple_ids)):
        raise AssertionError("train_policy: duplicate tuple IDs")
    if many(rows, "task_failed"):
        raise AssertionError("train_policy: failed task present")
    saved = one(rows, "model_saved")
    model_path = Path(saved["model_path"])
    if not model_path.is_file():
        raise AssertionError("train_policy: trained model file missing")
    shutdown = one(rows, "shutdown_ack")
    if shutdown.get("orphaned_tasks") != 0 or shutdown.get("tasks_reported") != tasks_expected:
        raise AssertionError("train_policy: pending task reconciliation failed")
    exit_row = one(rows, "python_exit")
    if exit_row.get("shutdown_ack") is not True or exit_row.get("exit_code") != 0:
        raise AssertionError("train_policy: Python process did not exit cleanly")
    acceptance = one(rows, "acceptance")
    if acceptance.get("status") != "PASS" or acceptance.get("tasks") != tasks_expected or acceptance.get("action_counts") != counts:
        raise AssertionError("train_policy: Java acceptance record mismatch")
    return {"mode": "train", "tasks": tasks_expected, "partial_tasks": partial_count,
            "full_tasks": full_count, "action_counts": counts, "model": str(model_path)}


def validate_failure_case(case_dir: Path) -> dict:
    trace_path = case_dir / "partial_trace.jsonl"
    stderr_path = case_dir / "python_stderr.log"
    if not trace_path.is_file() or not stderr_path.is_file():
        raise AssertionError("failure_drop_edge: missing trace or stderr")
    if stderr_path.read_text(encoding="utf-8").strip():
        raise AssertionError("failure_drop_edge: Python stderr is not empty")
    rows = load_trace(trace_path)
    cfg = one(rows, "config")
    if cfg.get("action_policy") != "EDGE_PARTIAL_50" or cfg.get("task_count") != 1:
        raise AssertionError("failure_drop_edge: wrong fault run configuration")
    decision = one(rows, "decision")
    task_id = decision["task_id"]
    if decision.get("action") != "EDGE_PARTIAL_50" or decision.get("action_id") != 2:
        raise AssertionError("failure_drop_edge: wrong selected action")
    fault = one(rows, "fault_injection", task_id=task_id)
    if fault.get("branch") != "edge":
        raise AssertionError("failure_drop_edge: wrong dropped branch")
    one(rows, "branch_result", task_id=task_id, branch="local")
    if many(rows, "branch_result", task_id=task_id, branch="edge"):
        raise AssertionError("failure_drop_edge: dropped Edge branch unexpectedly returned")
    if many(rows, "merge_created", task_id=task_id) or many(rows, "merge_result", task_id=task_id):
        raise AssertionError("failure_drop_edge: merge was fabricated without both branches")
    failed = one(rows, "task_failed", task_id=task_id)
    if failed.get("deadline_met") is not False or "edge" not in failed.get("reason", ""):
        raise AssertionError("failure_drop_edge: task failure semantics incorrect")
    if many(rows, "task_terminal", task_id=task_id):
        raise AssertionError("failure_drop_edge: failed task was also reported successful")
    outcome = one(rows, "python_send", type="outcome", task_id=task_id)
    if outcome.get("action_executed") != 2 or outcome.get("status") != "failed":
        raise AssertionError("failure_drop_edge: Python outcome was not failed/action-correlated")
    if outcome.get("failure_reason") is None:
        raise AssertionError("failure_drop_edge: failed outcome lacks reason")
    one(rows, "failure_outcome_ack", task_id=task_id)
    shutdown = one(rows, "shutdown_ack")
    if shutdown.get("orphaned_tasks") != 0 or shutdown.get("tasks_reported") != 1:
        raise AssertionError("failure_drop_edge: Python pending task was not reconciled")
    exit_row = one(rows, "python_exit")
    if exit_row.get("shutdown_ack") is not True or exit_row.get("exit_code") != 0:
        raise AssertionError("failure_drop_edge: Python process did not exit cleanly")
    return {"status": "EXPECTED_FAIL_CLOSED", "task": task_id,
            "failed_action": "EDGE_PARTIAL_50", "orphaned_tasks": 0}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--tasks-per-action", type=int, default=2)
    args = parser.parse_args()
    results = []
    for action in ACTIONS:
        results.append(validate_case(args.root / action, action, args.tasks_per_action))
    if {r["action"] for r in results} != set(ACTIONS):
        raise AssertionError("not all nine actions were executed")
    total_tasks = sum(r["tasks"] for r in results)
    total_merges = sum(r["merge_tasks"] for r in results)
    training = validate_training_case(args.root / "train_policy", 30)
    failure = validate_failure_case(args.root / "failure_drop_edge")
    print(json.dumps({"status": "PASS", "actions": len(results), "baseline_tasks": total_tasks,
                      "partial_actions": 6, "full_actions": 3, "baseline_merge_tasks": total_merges,
                      "learned_policy_training": training, "failure_path": failure,
                      "results": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
