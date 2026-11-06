"""Validate one-task Java JSONL traces without changing experiment artifacts."""

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


def validate(path, expected_action, training):
    rows = load_jsonl(path)
    decisions = [row for row in rows if row["record"] == "decision"]
    outcomes = [row for row in rows
                if row["record"] == "python_send" and row.get("json", {}).get("type") == "outcome"]
    if len(decisions) != 1 or len(outcomes) != 1:
        raise ValidationError(f"expected one decision and one outcome send, found {len(decisions)} and {len(outcomes)}")
    decision = only(rows, "decision")
    created = only(rows, "task_created")
    execution = only(rows, "execution")
    terminal = only(rows, "terminal")
    acceptance = only(rows, "acceptance")
    shutdown = only(rows, "shutdown_ack")
    process_exit = only(rows, "python_process_exit")
    outcome_ack = only(rows, "outcome_ack")

    task_id = decision.get("task_id")
    if not task_id or any(row.get("task_id") != task_id for row in (created, execution, terminal, acceptance, outcome_ack)):
        raise ValidationError("task correlation is not identical across lifecycle records")
    if decision.get("source") != "agent":
        raise ValidationError(f"expected an accepted agent decision, got {decision.get('source')}")
    if outcomes[0].get("json", {}).get("task_id") != task_id:
        raise ValidationError("outcome send is not correlated to the task")
    if outcomes[0].get("json", {}).get("status") != "completed" or outcomes[0].get("json", {}).get("terminal") is not True:
        raise ValidationError("normal outcome is not a terminal completed outcome")
    if not isinstance(outcomes[0].get("json", {}).get("deadline_met"), bool):
        raise ValidationError("normal outcome deadline_met is not boolean")
    if decision.get("action") != expected_action or acceptance.get("requested_action") != expected_action:
        raise ValidationError("requested action does not match the expected route")
    if execution.get("action_executed") != expected_action or acceptance.get("action_executed") != expected_action:
        raise ValidationError("executed action does not match the expected route")
    if acceptance.get("status") != "PASS":
        raise ValidationError("acceptance record is not PASS")

    transfers = [row for row in rows if row["record"] == "transfer"]
    byte_total = sum(row.get("bytes", -1) for row in transfers)
    if any(row.get("task_id") != task_id or row.get("bytes", -1) < 0 for row in transfers):
        raise ValidationError("transfer row is uncorrelated or has invalid bytes")
    if byte_total != terminal.get("bandwidth_bytes") or byte_total != EXPECTED_BYTES[expected_action]:
        raise ValidationError(f"byte total mismatch: rows={byte_total}, terminal={terminal.get('bandwidth_bytes')}")
    if len(transfers) != terminal.get("transfer_count") or len(transfers) != EXPECTED_TRANSFERS[expected_action]:
        raise ValidationError("transfer count mismatch")
    if expected_action == "Local" and transfers:
        raise ValidationError("Local route must have zero counted link transfers")

    if shutdown.get("response", {}).get("orphaned_tasks") != 0:
        raise ValidationError("shutdown reported orphaned tasks")
    if shutdown.get("response", {}).get("type") != "shutdown_ack":
        raise ValidationError("missing shutdown acknowledgement")
    if process_exit.get("shutdown_ack_received") is not True or process_exit.get("exit_code") != 0:
        raise ValidationError("Python process did not exit cleanly after shutdown")
    if training:
        saved = only(rows, "saved")
        if saved.get("response", {}).get("type") != "saved":
            raise ValidationError("training run did not save the model")
        if outcome_ack.get("response", {}).get("updated") is not True:
            raise ValidationError("training outcome was not applied")
    elif any(row["record"] == "saved" for row in rows):
        raise ValidationError("baseline run unexpectedly saved a model")
    return {"trace": str(path), "task_id": task_id, "action": expected_action,
            "bandwidth_bytes": byte_total, "transfer_count": len(transfers),
            "training": training, "status": "PASS"}


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
    if shutdown.get("response", {}).get("orphaned_tasks") != 0:
        raise ValidationError("fallback shutdown reported orphaned tasks")
    if process_exit.get("shutdown_ack_received") is not True or process_exit.get("exit_code") != 0:
        raise ValidationError("fallback Python process did not exit cleanly")
    return {"trace": str(path), "fault": fault_mode, "action": "Edge",
            "outcome_sent": False, "status": "PASS"}


def validate_deadline(path):
    result = validate(path, "Local", False)
    rows = load_jsonl(path)
    terminal = only(rows, "terminal")
    config = only(rows, "config")
    if terminal.get("deadline_met") is not False or terminal.get("latency_ms", 0) <= config.get("deadline_ms", -1):
        raise ValidationError("deadline test did not produce a truthful deadline miss")
    outcome = [row["json"] for row in rows
               if row["record"] == "python_send" and row.get("json", {}).get("type") == "outcome"]
    if len(outcome) != 1 or outcome[0].get("deadline_met") is not False:
        raise ValidationError("deadline miss outcome is missing or has the wrong deadline flag")
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
            cases = [("one_task_train_pass", "Local", True),
                     ("regression_local", "Local", False),
                     ("regression_edge", "Edge", False),
                     ("regression_cloud", "Cloud", False)]
            results = [validate(args.root / name / "java_trace.jsonl", action, training)
                       for name, action, training in cases]
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