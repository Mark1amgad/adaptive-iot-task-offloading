"""Validate mixed full-placement and partial-task lifecycle traces."""
import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path


class ValidationError(Exception):
    pass


def integer(value, label):
    try:
        return int(value)
    except (TypeError, ValueError) as error:
        raise ValidationError(f"invalid integer {label}: {value}") from error


def number(value, label):
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise ValidationError(f"invalid number {label}: {value}") from error
    if not (float("-inf") < result < float("inf")):
        raise ValidationError(f"non-finite number {label}: {value}")
    return result


def detail(row, key):
    for item in row.get("detail", "").split(";"):
        if "=" in item:
            name, value = item.split("=", 1)
            if name == key:
                return value
    raise ValidationError(f"missing detail field {key}: {row}")


def dint(row, key):
    return integer(detail(row, key), key)


def load_csv(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def validate(root: Path, expected_tasks: int):
    trace = load_csv(root / "mixed_trace.csv")
    summary = load_csv(root / "mixed_summary.csv")
    if not trace or not summary:
        raise ValidationError("trace or summary is empty")
    events, by_task, tuple_owners = defaultdict(list), defaultdict(list), {}
    for row in trace:
        events[row["event"]].append(row)
        tid = row.get("task_id", "")
        if tid and tid != "run":
            by_task[tid].append(row)
        raw = row.get("actual_tuple_id", "")
        if raw not in ("", "-1") and row["event"] in ("branch_created", "merge_created"):
            tuple_id = integer(raw, "tuple registration")
            if tuple_id in tuple_owners:
                raise ValidationError(f"duplicate tuple registration {tuple_id}")
            tuple_owners[tuple_id] = (tid, row["branch"])

    created, completed = events["task_created"], events["task_completed"]
    task_ids = [r["task_id"] for r in created]
    if len(task_ids) != expected_tasks or len(set(task_ids)) != expected_tasks:
        raise ValidationError("task creation count/uniqueness mismatch")
    if len(completed) != expected_tasks or len(summary) != expected_tasks:
        raise ValidationError("terminal or summary count mismatch")
    if set(task_ids) != {r["task_id"] for r in completed} or set(task_ids) != {r["task_id"] for r in summary}:
        raise ValidationError("task IDs differ across creation, terminal, and summary")
    if not max(number(r["sim_time_ms"], "creation") for r in created) < min(
            number(r["sim_time_ms"], "terminal") for r in completed):
        raise ValidationError("all tasks were not registered before the first terminal")

    full_actions = set()
    full_count = partial_count = 0
    expected_executor = {
        "Local": ("local", "local_worker", "LOCAL_RESULT"),
        "Edge": ("edge", "edge_worker", "EDGE_RESULT"),
        "Cloud": ("cloud", "cloud_worker", "CLOUD_RESULT"),
    }
    for task_id in task_ids:
        rows = by_task[task_id]
        ev = defaultdict(list)
        for row in rows:
            ev[row["event"]].append(row)
        creation = ev["task_created"]
        if len(creation) != 1 or len(ev["task_completed"]) != 1:
            raise ValidationError(f"{task_id}: duplicate/missing creation or terminal")
        mode = detail(creation[0], "mode")
        branches = {r["branch"]: r for r in ev["branch_created"]}
        executions = {r["branch"]: r for r in ev["execution_start"]}
        results = {r["branch"]: r for r in ev["branch_result"]}
        summary_row = next(r for r in summary if r["task_id"] == task_id)
        done = ev["task_completed"][0]
        if mode == "full":
            full_count += 1
            action = detail(creation[0], "full_action")
            if action not in expected_executor or action in full_actions:
                raise ValidationError(f"{task_id}: invalid or repeated full action {action}")
            full_actions.add(action)
            node, module, result_type = expected_executor[action]
            if set(branches) != {"full"} or set(executions) != {"full"} or set(results) != {"full"}:
                raise ValidationError(f"{task_id}: full task must have exactly one full branch/result")
            if ev["merge_barrier"] or ev["merge_created"]:
                raise ValidationError(f"{task_id}: full task must not enter a merge lifecycle")
            branch = branches["full"]
            tuple_id = integer(branch["actual_tuple_id"], "full tuple")
            if tuple_owners.get(tuple_id) != (task_id, "full"):
                raise ValidationError(f"{task_id}: full tuple owner mismatch")
            if integer(results["full"]["actual_tuple_id"], "full result tuple") != tuple_id:
                raise ValidationError(f"{task_id}: full result tuple mismatch")
            if integer(executions["full"]["actual_tuple_id"], "full execution tuple") != tuple_id:
                raise ValidationError(f"{task_id}: full execution tuple mismatch")
            if detail(executions["full"], "node") != node or detail(executions["full"], "module") != module:
                raise ValidationError(f"{task_id}: full action executed on wrong node/module")
            if number(results["full"]["sim_time_ms"], "full result") < number(executions["full"]["sim_time_ms"], "full execution"):
                raise ValidationError(f"{task_id}: full result precedes execution")
            if done["branch"] != "full" or integer(done["actual_tuple_id"], "full terminal tuple") != tuple_id:
                raise ValidationError(f"{task_id}: full terminal not correlated to its task tuple")
            if summary_row["mode"] != "full" or summary_row["full_action"] != action:
                raise ValidationError(f"{task_id}: full summary mode/action mismatch")
            if integer(summary_row["full_tuple_id"], "summary full tuple") != tuple_id:
                raise ValidationError(f"{task_id}: summary full tuple mismatch")
            if summary_row["merge_tuple_id"] or summary_row["local_tuple_id"] or summary_row["edge_tuple_id"]:
                raise ValidationError(f"{task_id}: full summary unexpectedly contains split/merge tuple IDs")
        elif mode == "partial":
            partial_count += 1
            if set(branches) != {"local", "edge"} or set(executions) != {"local", "edge", "merge"}:
                raise ValidationError(f"{task_id}: partial branch/execution set mismatch")
            if set(results) != {"local", "edge"} or len(ev["merge_barrier"]) != 1 or len(ev["merge_created"]) != 1:
                raise ValidationError(f"{task_id}: partial result/barrier/merge count mismatch")
            if done["branch"] != "merge":
                raise ValidationError(f"{task_id}: partial task needs one merge terminal")
            local, edge = branches["local"], branches["edge"]
            if dint(local, "mi") + dint(edge, "mi") != 10000:
                raise ValidationError(f"{task_id}: MI split not conserved")
            if dint(local, "input_bytes") + dint(edge, "input_bytes") != 12000:
                raise ValidationError(f"{task_id}: input split not conserved")
            if dint(local, "output_bytes") + dint(edge, "output_bytes") != 1000:
                raise ValidationError(f"{task_id}: output split not conserved")
            for branch_name, node, module in (("local", "local", "local_worker"), ("edge", "edge", "edge_worker")):
                branch_id = integer(branches[branch_name]["actual_tuple_id"], "branch tuple")
                if tuple_owners.get(branch_id) != (task_id, branch_name):
                    raise ValidationError(f"{task_id}/{branch_name}: branch tuple owner mismatch")
                if integer(results[branch_name]["actual_tuple_id"], "branch result") != branch_id:
                    raise ValidationError(f"{task_id}/{branch_name}: result tuple mismatch")
                if integer(executions[branch_name]["actual_tuple_id"], "branch execution") != branch_id:
                    raise ValidationError(f"{task_id}/{branch_name}: execution tuple mismatch")
                if detail(executions[branch_name], "node") != node or detail(executions[branch_name], "module") != module:
                    raise ValidationError(f"{task_id}/{branch_name}: wrong branch executor")
                if number(results[branch_name]["sim_time_ms"], "branch result") < number(executions[branch_name]["sim_time_ms"], "branch execution"):
                    raise ValidationError(f"{task_id}/{branch_name}: result before execution")
            barrier_time = number(ev["merge_barrier"][0]["sim_time_ms"], "barrier")
            latest_result = max(number(r["sim_time_ms"], "branch result") for r in results.values())
            if barrier_time < latest_result:
                raise ValidationError(f"{task_id}: merge barrier before both branch results")
            merge = ev["merge_created"][0]
            merge_id = integer(merge["actual_tuple_id"], "merge tuple")
            if tuple_owners.get(merge_id) != (task_id, "merge"):
                raise ValidationError(f"{task_id}: merge tuple owner mismatch")
            if integer(executions["merge"]["actual_tuple_id"], "merge execution") != merge_id or integer(done["actual_tuple_id"], "merge terminal") != merge_id:
                raise ValidationError(f"{task_id}: merge tuple correlation mismatch")
            if detail(executions["merge"], "node") != "local" or detail(executions["merge"], "module") != "merge_worker":
                raise ValidationError(f"{task_id}: merge did not execute on Local merge_worker")
            if dint(merge, "mi") != 1200 or dint(merge, "input_bytes") != 1000 or dint(merge, "output_bytes") != 100:
                raise ValidationError(f"{task_id}: merge Cloudlet contract mismatch")
            if number(merge["sim_time_ms"], "merge creation") < barrier_time or number(done["sim_time_ms"], "terminal") < number(executions["merge"]["sim_time_ms"], "merge execution"):
                raise ValidationError(f"{task_id}: merge order invalid")
            if summary_row["mode"] != "partial" or summary_row["full_action"]:
                raise ValidationError(f"{task_id}: partial summary mode/action mismatch")
            for field, branch_name in (("local_tuple_id", "local"), ("edge_tuple_id", "edge"), ("merge_tuple_id", "merge")):
                if integer(summary_row[field], field) != integer(
                        branches[branch_name]["actual_tuple_id"] if branch_name != "merge" else merge["actual_tuple_id"],
                        "trace tuple"):
                    raise ValidationError(f"{task_id}: summary {field} mismatch")
        else:
            raise ValidationError(f"{task_id}: unknown task mode {mode}")

        latency = number(done["sim_time_ms"], "terminal") - number(creation[0]["sim_time_ms"], "creation")
        if abs(number(summary_row["latency_ms"], "summary latency") - latency) > 1e-9:
            raise ValidationError(f"{task_id}: summary latency mismatch")
        for row in rows:
            raw = row.get("actual_tuple_id", "")
            if raw not in ("", "-1"):
                tuple_id = integer(raw, "trace tuple")
                owner = tuple_owners.get(tuple_id)
                if owner is None or owner[0] != task_id:
                    raise ValidationError(f"{task_id}: unknown or cross-task tuple {tuple_id}")

    if full_count != 3 or partial_count != 3 or full_actions != {"Local", "Edge", "Cloud"}:
        raise ValidationError(f"expected three full tasks (Local/Edge/Cloud) and three partial tasks; got {full_count}/{partial_count}")
    return {"status": "PASS", "tasks": expected_tasks, "full_tasks": full_count,
            "partial_tasks": partial_count, "full_actions": sorted(full_actions),
            "partial_merge_cloudlets": partial_count, "unique_tuple_ids": len(tuple_owners),
            "shared_run_completion_coordinator": "PASS"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--tasks", type=int, default=6)
    args = parser.parse_args()
    try:
        result = validate(args.root, args.tasks)
    except (OSError, ValidationError, KeyError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
