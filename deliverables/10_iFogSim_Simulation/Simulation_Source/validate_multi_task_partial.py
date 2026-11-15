"""Validate task-scoped multi-task partial-offloading lifecycle traces."""
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
    raise ValidationError(f"missing detail field {key} in {row}")


def dint(row, key):
    return integer(detail(row, key), key)


def load_csv(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def validate(root: Path, expected_tasks: int):
    trace = load_csv(root / "partial_trace.csv")
    summary = load_csv(root / "partial_summary.csv")
    if not trace or not summary:
        raise ValidationError("trace or summary is empty")
    events = defaultdict(list)
    tasks = defaultdict(list)
    tuple_owners = {}
    for row in trace:
        events[row["event"]].append(row)
        task_id = row.get("task_id", "")
        if task_id and task_id != "run":
            tasks[task_id].append(row)
        raw_id = row.get("actual_tuple_id", "")
        if raw_id not in ("", "-1") and row["event"] in ("branch_created", "merge_created"):
            tuple_id = integer(raw_id, "actual_tuple_id")
            if tuple_id in tuple_owners:
                raise ValidationError(f"duplicate tuple registration {tuple_id}")
            tuple_owners[tuple_id] = (task_id, row["branch"])

    created, completed = events["task_created"], events["task_completed"]
    ids = [row["task_id"] for row in created]
    if len(ids) != expected_tasks or len(set(ids)) != expected_tasks:
        raise ValidationError("task creation count/uniqueness mismatch")
    if len(completed) != expected_tasks or len(summary) != expected_tasks:
        raise ValidationError("completion or summary count mismatch")
    if set(ids) != {row["task_id"] for row in completed}:
        raise ValidationError("created and completed task IDs differ")
    if set(ids) != {row["task_id"] for row in summary}:
        raise ValidationError("trace and summary task IDs differ")

    first_terminal = min(number(row["sim_time_ms"], "terminal time") for row in completed)
    last_creation = max(number(row["sim_time_ms"], "creation time") for row in created)
    if not last_creation < first_terminal:
        raise ValidationError("tasks were not concurrently in flight before first completion")

    for task_id in ids:
        rows = tasks[task_id]
        by = defaultdict(list)
        for row in rows:
            by[row["event"]].append(row)
        if len(by["branch_created"]) != 2 or {r["branch"] for r in by["branch_created"]} != {"local", "edge"}:
            raise ValidationError(f"{task_id}: expected one local and one edge branch")
        branches = {r["branch"]: r for r in by["branch_created"]}
        if len(by["execution_start"]) != 3 or {r["branch"] for r in by["execution_start"]} != {"local", "edge", "merge"}:
            raise ValidationError(f"{task_id}: expected exactly three branch/merge execution admissions")
        executions = {r["branch"]: r for r in by["execution_start"]}
        if len(by["branch_result"]) != 2 or {r["branch"] for r in by["branch_result"]} != {"local", "edge"}:
            raise ValidationError(f"{task_id}: expected one result per split branch")
        results = {r["branch"]: r for r in by["branch_result"]}
        for event in ("merge_barrier", "merge_created", "task_completed"):
            if len(by[event]) != 1:
                raise ValidationError(f"{task_id}: expected exactly one {event}")

        local, edge = branches["local"], branches["edge"]
        local_id = integer(local["actual_tuple_id"], "local tuple")
        edge_id = integer(edge["actual_tuple_id"], "edge tuple")
        if local_id == edge_id:
            raise ValidationError(f"{task_id}: branch tuple IDs collide")
        if dint(local, "mi") + dint(edge, "mi") != 10000:
            raise ValidationError(f"{task_id}: MI partition not conserved")
        if dint(local, "input_bytes") + dint(edge, "input_bytes") != 12000:
            raise ValidationError(f"{task_id}: input partition not conserved")
        if dint(local, "output_bytes") + dint(edge, "output_bytes") != 1000:
            raise ValidationError(f"{task_id}: output partition not conserved")

        expected_execution = {
            "local": ("local", "local_worker"),
            "edge": ("edge", "edge_worker"),
            "merge": ("local", "merge_worker"),
        }
        for branch_name in ("local", "edge", "merge"):
            execution = executions[branch_name]
            if detail(execution, "node") != expected_execution[branch_name][0] or detail(execution, "module") != expected_execution[branch_name][1]:
                raise ValidationError(f"{task_id}/{branch_name}: executed on an unexpected node/module")
        for branch_name in ("local", "edge"):
            branch_id = integer(branches[branch_name]["actual_tuple_id"], "branch tuple")
            if integer(results[branch_name]["actual_tuple_id"], "result tuple") != branch_id:
                raise ValidationError(f"{task_id}/{branch_name}: result tuple correlation mismatch")
            if integer(executions[branch_name]["actual_tuple_id"], "execution tuple") != branch_id:
                raise ValidationError(f"{task_id}/{branch_name}: execution tuple correlation mismatch")
            if tuple_owners.get(branch_id) != (task_id, branch_name):
                raise ValidationError(f"{task_id}/{branch_name}: tuple is registered to a different owner")
            if number(results[branch_name]["sim_time_ms"], "branch result") < number(executions[branch_name]["sim_time_ms"], "branch execution"):
                raise ValidationError(f"{task_id}/{branch_name}: result preceded execution")

        barrier_time = number(by["merge_barrier"][0]["sim_time_ms"], "barrier")
        latest_branch_result = max(number(r["sim_time_ms"], "branch result") for r in results.values())
        if barrier_time < latest_branch_result:
            raise ValidationError(f"{task_id}: merge barrier fired before both results")
        merge = by["merge_created"][0]
        merge_exec = executions["merge"]
        done = by["task_completed"][0]
        merge_id = integer(merge["actual_tuple_id"], "merge tuple")
        if integer(merge_exec["actual_tuple_id"], "merge execution tuple") != merge_id:
            raise ValidationError(f"{task_id}: merge execution tuple mismatch")
        if integer(done["actual_tuple_id"], "terminal tuple") != merge_id:
            raise ValidationError(f"{task_id}: terminal event not correlated to merge tuple")
        if tuple_owners.get(merge_id) != (task_id, "merge"):
            raise ValidationError(f"{task_id}: merge tuple registered to another task")
        if (detail(merge, "mi") != "1200" or detail(merge, "input_bytes") != "1000"
                or detail(merge, "output_bytes") != "100"):
            raise ValidationError(f"{task_id}: merge Cloudlet input/output contract mismatch")
        if number(merge["sim_time_ms"], "merge creation") < barrier_time:
            raise ValidationError(f"{task_id}: merge created before barrier")
        if number(merge_exec["sim_time_ms"], "merge execution") < barrier_time:
            raise ValidationError(f"{task_id}: merge execution admitted before barrier")
        if number(done["sim_time_ms"], "terminal") < number(merge_exec["sim_time_ms"], "merge execution"):
            raise ValidationError(f"{task_id}: terminal before merge execution")

        transfers = by["transfer"]
        expected_hops = {("local", "uplink", 7200), ("edge", "downlink", 600)}
        actual_hops = set()
        for row in transfers:
            if integer(row["actual_tuple_id"], "transfer tuple") != edge_id:
                raise ValidationError(f"{task_id}: transfer attributed to wrong branch")
            actual_hops.add((detail(row, "node"), detail(row, "direction"), dint(row, "bytes")))
        if len(transfers) != 2 or actual_hops != expected_hops:
            raise ValidationError(f"{task_id}: transfer hops/bytes differ from expected Local→Edge→Local path")
        summary_row = next(row for row in summary if row["task_id"] == task_id)
        for field, expected in (("local_tuple_id", local_id), ("edge_tuple_id", edge_id), ("merge_tuple_id", merge_id)):
            if integer(summary_row[field], field) != expected:
                raise ValidationError(f"{task_id}: summary {field} mismatch")
        if integer(summary_row["bandwidth_bytes"], "summary bytes") != 7800 or integer(summary_row["transfer_count"], "summary transfers") != 2:
            raise ValidationError(f"{task_id}: summary transfer metrics mismatch")
        creation_time = number(next(r for r in created if r["task_id"] == task_id)["sim_time_ms"], "creation")
        if abs(number(summary_row["latency_ms"], "summary latency") - (number(done["sim_time_ms"], "completion") - creation_time)) > 1e-9:
            raise ValidationError(f"{task_id}: end-to-end latency mismatch")

    for row in trace:
        raw = row.get("actual_tuple_id", "")
        if raw not in ("", "-1"):
            owner = tuple_owners.get(integer(raw, "trace tuple"))
            if owner is None:
                raise ValidationError(f"unregistered tuple ID in trace: {raw}")
            if owner[0] != row.get("task_id"):
                raise ValidationError(f"cross-task tuple contamination: {raw}")

    return {
        "status": "PASS",
        "task_count": expected_tasks,
        "split_branches": expected_tasks * 2,
        "merge_cloudlets": expected_tasks,
        "unique_registered_tuple_ids": len(tuple_owners),
        "all_tasks_created_before_first_terminal": True,
        "task_scoped_barriers_and_merges": "PASS",
        "partition_conservation": "PASS",
        "transfer_attribution": "PASS",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--tasks", type=int, default=4)
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
