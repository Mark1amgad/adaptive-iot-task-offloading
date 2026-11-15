"""Validate one-task regressions and multi-task lifecycle traces."""

import argparse
import json
import sys
from pathlib import Path


EXPECTED_BYTES = {"Local": 0, "Edge": 14000, "Cloud": 28000}
EXPECTED_TRANSFERS = {"Local": 0, "Edge": 2, "Cloud": 4}


class ValidationError(Exception):
    pass


def load_jsonl(path):
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            raise ValidationError(f"{path}: blank line {line_number}")
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValidationError(f"{path}: invalid JSON at line {line_number}: {error}") from error
        if not isinstance(row, dict) or not isinstance(row.get("record"), str):
            raise ValidationError(f"{path}: line {line_number} is not a trace record object")
        rows.append(row)
    if not rows:
        raise ValidationError(f"{path}: empty trace")
    return rows


def only(rows, record):
    matches = [row for row in rows if row["record"] == record]
    if len(matches) != 1:
        raise ValidationError(f"expected exactly one {record}, found {len(matches)}")
    return matches[0]


def validate_trace(path, expected_action, training, expected_tasks=1, require_overlap=False):
    rows = load_jsonl(path)
    decisions = [row for row in rows if row["record"] == "decision"]
    created = [row for row in rows if row["record"] == "task_created"]
    executions = [row for row in rows if row["record"] == "execution"]
    terminals = [row for row in rows if row["record"] == "terminal"]
    outcome_sends = [row for row in rows if row["record"] == "python_send"
                     and row.get("json", {}).get("type") == "outcome"]
    outcome_acks = [row for row in rows if row["record"] == "outcome_ack"]
    acceptance = only(rows, "acceptance")
    shutdown = only(rows, "shutdown_ack")
    process_exit = only(rows, "python_process_exit")

    expected_counts = (expected_tasks, expected_tasks, expected_tasks, expected_tasks,
                       expected_tasks, expected_tasks)
    actual_counts = (len(decisions), len(created), len(executions), len(terminals),
                     len(outcome_sends), len(outcome_acks))
    if actual_counts != expected_counts:
        raise ValidationError(f"expected {expected_tasks} decisions/creations/executions/terminals/outcomes/acks; got {actual_counts}")

    task_ids = [row.get("task_id") for row in decisions]
    if None in task_ids or len(set(task_ids)) != expected_tasks:
        raise ValidationError("task IDs are missing or not unique")
    by_record = {}
    for label, collection in (("decision", decisions), ("created", created),
                              ("execution", executions), ("terminal", terminals),
                              ("outcome_send", [row["json"] for row in outcome_sends]),
                              ("outcome_ack", outcome_acks)):
        mapping = {}
        for row in collection:
            task_id = row.get("task_id")
            if not task_id or task_id in mapping:
                raise ValidationError(f"{label} contains missing or duplicate task_id {task_id}")
            mapping[task_id] = row
        if set(mapping) != set(task_ids):
            raise ValidationError(f"{label} task IDs do not match decision task IDs")
        by_record[label] = mapping

    tuple_ids = [row.get("actual_tuple_id") for row in created]
    if None in tuple_ids or len(set(tuple_ids)) != expected_tasks:
        raise ValidationError("actualTupleId values are missing or not unique")

    for task_id in task_ids:
        decision = by_record["decision"][task_id]
        creation = by_record["created"][task_id]
        execution = by_record["execution"][task_id]
        terminal = by_record["terminal"][task_id]
        outcome = by_record["outcome_send"][task_id]
        ack = by_record["outcome_ack"][task_id]
        if decision.get("source") != "agent":
            raise ValidationError(f"{task_id}: decision did not come from the agent")
        task_action = decision.get("action")
        if task_action not in EXPECTED_BYTES:
            raise ValidationError(f"{task_id}: decision contains an unknown action {task_action}")
        if expected_action is not None and task_action != expected_action:
            raise ValidationError(f"{task_id}: requested route differs from expected {expected_action}")
        if execution.get("action_executed") != task_action:
            raise ValidationError(f"{task_id}: requested and executed routes differ")

        if creation.get("actual_tuple_id") != execution.get("actual_tuple_id") or creation.get("actual_tuple_id") != terminal.get("actual_tuple_id"):
            raise ValidationError(f"{task_id}: tuple correlation changed during lifecycle")
        if outcome.get("status") != "completed" or outcome.get("terminal") is not True:
            raise ValidationError(f"{task_id}: outcome is not terminal/completed")
        if outcome.get("task_id") != task_id or ack.get("response", {}).get("task_id") != task_id:
            raise ValidationError(f"{task_id}: outcome send/ack correlation mismatch")
        if not isinstance(outcome.get("deadline_met"), bool):
            raise ValidationError(f"{task_id}: deadline_met is not boolean")
        transfers = [row for row in rows if row["record"] == "transfer" and row.get("task_id") == task_id]
        byte_total = sum(row.get("bytes", -1) for row in transfers)
        if any(row.get("bytes", -1) < 0 for row in transfers):
            raise ValidationError(f"{task_id}: invalid transfer bytes")
        if byte_total != terminal.get("bandwidth_bytes") or byte_total != EXPECTED_BYTES[task_action]:
            raise ValidationError(f"{task_id}: byte total mismatch ({byte_total})")
        if len(transfers) != terminal.get("transfer_count") or len(transfers) != EXPECTED_TRANSFERS[task_action]:
            raise ValidationError(f"{task_id}: transfer count mismatch")
        if training and ack.get("response", {}).get("updated") is not True:
            raise ValidationError(f"{task_id}: Python did not acknowledge applying the training outcome")

    if acceptance.get("status") != "PASS" or acceptance.get("task_count") != expected_tasks:
        raise ValidationError("run-level acceptance record does not match configured task count")
    if acceptance.get("completed_count") != expected_tasks or acceptance.get("accepted_decision_count") != expected_tasks:
        raise ValidationError("run-level completion/decision counts are inconsistent")
    if shutdown.get("response", {}).get("type") != "shutdown_ack" or shutdown.get("response", {}).get("orphaned_tasks") != 0:
        raise ValidationError("Python shutdown was not clean")
    if process_exit.get("shutdown_ack_received") is not True or process_exit.get("exit_code") != 0:
        raise ValidationError("Python process did not exit cleanly after shutdown")

    shutdown_index = rows.index(shutdown)
    last_ack_index = max(rows.index(row) for row in outcome_acks)
    if shutdown_index <= last_ack_index:
        raise ValidationError("shutdown occurred before every outcome acknowledgement")

    if training:
        saved = only(rows, "saved")
        if saved.get("response", {}).get("type") != "saved":
            raise ValidationError("training run did not save the model")
        if rows.index(saved) <= last_ack_index or rows.index(saved) >= shutdown_index:
            raise ValidationError("model save was not performed after outcomes and before shutdown")
    elif any(row["record"] == "saved" for row in rows):
        raise ValidationError("baseline run unexpectedly saved a model")

    if require_overlap:
        last_created_time = max(row.get("creation_sim_time_ms", -1) for row in created)
        first_terminal_time = min(row.get("terminal_sim_time_ms", float("inf")) for row in terminals)
        if not last_created_time < first_terminal_time:
            raise ValidationError("tasks did not overlap: not all tasks were registered before the first terminal")
    actual_action = by_record["decision"][task_ids[0]].get("action") if expected_action is None else expected_action
    return {"trace": str(path), "task_count": expected_tasks, "action": actual_action,
            "training": training, "overlap": require_overlap, "status": "PASS"}


def logical_summary(path):
    rows = load_jsonl(path)
    decisions = sorted((row for row in rows if row["record"] == "decision"),
                       key=lambda row: row.get("sim_time_ms", -1))
    summary = []
    for decision in decisions:
        task_id = decision["task_id"]
        execution = only([row for row in rows if row.get("task_id") == task_id], "execution")
        terminal = only([row for row in rows if row.get("task_id") == task_id], "terminal")
        summary.append((decision.get("action"), execution.get("device"), execution.get("module"),
                        execution.get("sim_time_ms"), terminal.get("latency_ms"),
                        terminal.get("bandwidth_bytes"), terminal.get("transfer_count"),
                        terminal.get("deadline_met")))
    return summary


def validate_fallback(path, fault_mode):
    rows = load_jsonl(path)
    decision = only(rows, "decision")
    execution = only(rows, "execution")
    terminal = only(rows, "terminal")
    acceptance = only(rows, "acceptance")
    shutdown = only(rows, "shutdown_ack")
    process_exit = only(rows, "python_process_exit")
    injection = only(rows, "fault_injection")
    no_outcome = only(rows, "fallback_no_outcome")
    if decision.get("source") != "fallback_error" or decision.get("action") != "Edge":
        raise ValidationError("fallback did not select Edge with fallback_error source")
    if injection.get("mode") != fault_mode or injection.get("sent_to_python") is not False:
        raise ValidationError("fault injection record does not prove a pre-send response boundary fault")
    if execution.get("action_executed") != "Edge" or acceptance.get("decision_source") != "fallback_error":
        raise ValidationError("fallback did not execute on Edge or preserve its source")
    if no_outcome.get("reason") != decision.get("reason"):
        raise ValidationError("fallback reason was not retained")
    if any(row["record"] == "outcome_ack" or
           (row["record"] == "python_send" and row.get("json", {}).get("type") == "outcome") for row in rows):
        raise ValidationError("fallback sent or acknowledged an RL outcome")
    if terminal.get("deadline_met") is not True:
        raise ValidationError("fallback terminal result did not complete")
    if acceptance.get("status") != "PASS" or acceptance.get("completed_count") != 1:
        raise ValidationError("fallback run did not complete")
    if shutdown.get("response", {}).get("orphaned_tasks") != 0:
        raise ValidationError("fallback shutdown reported orphaned tasks")
    if process_exit.get("shutdown_ack_received") is not True or process_exit.get("exit_code") != 0:
        raise ValidationError("fallback Python process did not exit cleanly")
    return {"trace": str(path), "fault": fault_mode, "action": "Edge",
            "outcome_sent": False, "status": "PASS"}


def validate_deadline(path):
    result = validate_trace(path, "Local", False, 1)
    rows = load_jsonl(path)
    terminal = only(rows, "terminal")
    config = only(rows, "config")
    if terminal.get("deadline_met") is not False or terminal.get("latency_ms", 0) <= config.get("deadline_ms", -1):
        raise ValidationError("deadline test did not produce a truthful deadline miss")
    result["deadline_met"] = False
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).parent / "runs")
    parser.add_argument("--suite", choices=("standard", "fallback", "deadline"), default="standard")
    parser.add_argument("--fault", choices=("timeout", "malformed"))
    args = parser.parse_args()
    try:
        if args.suite == "standard":
            cases = [("one_task_train_pass", None, True, 1, False),
                     ("regression_local", "Local", False, 1, False),
                     ("regression_edge", "Edge", False, 1, False),
                     ("regression_cloud", "Cloud", False, 1, False),
                     ("multi_task_overlap", "Edge", False, 4, True),
                     ("multi_task_train", None, True, 4, True),
                     ("multi_task_train_repeat", None, True, 4, True)]
            results = [validate_trace(args.root / name / "java_trace.jsonl", action, training, count, overlap)
                       for name, action, training, count, overlap in cases]
            first = logical_summary(args.root / "multi_task_train" / "java_trace.jsonl")
            repeated = logical_summary(args.root / "multi_task_train_repeat" / "java_trace.jsonl")
            if first != repeated:
                raise ValidationError("fixed-seed multi-task train runs produced different logical task summaries")
            results.append({"repeat_determinism": "PASS", "task_count": 4, "status": "PASS"})
        elif args.suite == "fallback":
            if args.fault is None:
                raise ValidationError("--fault is required for fallback validation")
            results = [validate_fallback(args.root / ("fallback_" + args.fault) / "java_trace.jsonl", args.fault)]
        else:
            results = [validate_deadline(args.root / "deadline_miss" / "java_trace.jsonl")]
    except (OSError, ValidationError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    for result in results:
        print(json.dumps(result, sort_keys=True))
    print(f"PASS: validated {len(results)} {args.suite} trace(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
