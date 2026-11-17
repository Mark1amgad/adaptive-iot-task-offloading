"""Validate the v2 full-placement iFogSim/Python handshake acceptance traces."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_records(path: Path):
    if not path.is_file():
        raise AssertionError(f"missing trace: {path}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def validate_run(run: Path, expected_tasks: int, expected_action: str | None = None,
                 require_model: bool = False):
    records = read_records(run / "java_trace.jsonl")
    decisions = {r["task_id"]: r for r in records if r.get("record") == "decision" and r.get("source") == "agent"}
    executions = [r for r in records if r.get("record") == "execution"]
    terminals = [r for r in records if r.get("record") == "terminal"]
    acks = [r for r in records if r.get("record") == "outcome_ack"]
    acceptances = [r for r in records if r.get("record") == "acceptance"]
    shutdowns = [r for r in records if r.get("record") == "shutdown_ack"]
    py_messages = [r for r in records if r.get("record") == "python_receive"]

    assert len(decisions) == expected_tasks, (run, "decision count", len(decisions))
    assert len(executions) == expected_tasks, (run, "execution count", len(executions))
    assert len(terminals) == expected_tasks, (run, "terminal count", len(terminals))
    assert len(acks) == expected_tasks, (run, "outcome ack count", len(acks))
    assert len(acceptances) == 1 and acceptances[0]["status"] == "PASS"
    assert len(shutdowns) == 1
    assert shutdowns[0]["response"]["orphaned_tasks"] == 0
    assert shutdowns[0]["response"]["tasks_reported"] == expected_tasks
    assert all(r["json"]["protocol_version"] == "2.0" for r in py_messages)

    execution_by_task = {}
    for event in executions:
        tid = event["task_id"]
        assert tid not in execution_by_task, (run, "duplicate execution", tid)
        execution_by_task[tid] = event
    terminal_by_task = {}
    for event in terminals:
        tid = event["task_id"]
        assert tid not in terminal_by_task, (run, "duplicate terminal", tid)
        terminal_by_task[tid] = event

    for tid, decision in decisions.items():
        action = decision["action"]
        assert action in ("LOCAL", "EDGE_FULL", "CLOUD_FULL"), (run, tid, action)
        if expected_action is not None:
            assert action == expected_action, (run, tid, action, expected_action)
        assert execution_by_task[tid]["action_executed"] == action
        assert tid in terminal_by_task
    assert set(decisions) == {r["task_id"] for r in acks}

    model_summary = None
    if require_model:
        model_path = run / "python_model.json"
        data = json.loads(model_path.read_text(encoding="utf-8"))
        assert data["format_version"] == 2 and data["protocol_version"] == "2.0"
        assert len(data["actions"]) == 9 and data["state_count"] == 972
        assert len(data["q"]) == 972 and all(len(row) == 9 for row in data["q"])
        assert data["counters"]["updates"] == expected_tasks
        model_summary = {"updates": data["counters"]["updates"], "states": data["state_count"],
                         "actions": len(data["actions"])}

    stderr = run / "python_stderr.log"
    if stderr.exists():
        assert not stderr.read_text(encoding="utf-8").strip(), f"Python stderr is not empty: {stderr}"
    return {"run": run.name, "tasks": expected_tasks, "action_counts": {
        action: sum(1 for d in decisions.values() if d["action"] == action)
        for action in ("LOCAL", "EDGE_FULL", "CLOUD_FULL")
    }, "model": model_summary}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    root = args.root
    results = [
        validate_run(root / "train_multi_task", 4, require_model=True),
        validate_run(root / "baseline_local", 2, expected_action="LOCAL"),
        validate_run(root / "baseline_edge", 2, expected_action="EDGE_FULL"),
        validate_run(root / "baseline_cloud", 2, expected_action="CLOUD_FULL"),
    ]
    print(json.dumps({"status": "PASS", "protocol": "2.0", "results": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
