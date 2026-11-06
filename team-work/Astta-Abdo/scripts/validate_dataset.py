#!/usr/bin/env python3
"""Validate synthetic task inputs and optional simulator-produced trace tables.

The validator never generates outcomes. Decision, outcome and calibration checks
run only when corresponding simulator/policy files are explicitly supplied.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import generate_workloads as gen  # noqa: E402

TASK_REQUIRED = set(gen.TASK_FIELDS)
MANIFEST_REQUIRED = set(gen.MANIFEST_FIELDS)
URGENCY = {"CRITICAL", "TIME_SENSITIVE", "DELAY_TOLERANT"}
SPLIT = {"INDIVISIBLE", "DATA_PARALLEL_DIVISIBLE"}
ALPHAS = (0.0, 0.25, 0.50, 0.75, 1.0)
TIERS = {"LOCAL", "EDGE", "CLOUD"}
FULL_ACTIONS = {"LOCAL", "EDGE_FULL", "CLOUD_FULL"}
PARTIAL_ACTIONS = {
    "EDGE_PARTIAL_25": ("EDGE", 0.25),
    "EDGE_PARTIAL_50": ("EDGE", 0.50),
    "EDGE_PARTIAL_75": ("EDGE", 0.75),
    "CLOUD_PARTIAL_25": ("CLOUD", 0.25),
    "CLOUD_PARTIAL_50": ("CLOUD", 0.50),
    "CLOUD_PARTIAL_75": ("CLOUD", 0.75),
}
FORBIDDEN_CONTEXT_KEYS = {
    "actual_completion_time_ms", "completion_time_ms", "actual_latency_ms",
    "deadline_met", "future_regime_id", "future_regime_label", "regime_id",
    "regime_label", "regime_timeline_json", "regime_start_time_ms",
    "regime_end_time_ms", "future_shift_boundary_ms", "test_label", "test_fold",
    "heldout_label", "outcome_status", "outcome", "task_outcome", "reward",
    "energy_joules", "actual_execution_site", "actual_execution_site_id",
    "execution_end_time_ms", "final_status", "completion_status", "deadline_success",
    "dataset_split", "scenario_id", "scenario_family", "evaluation_regime_id",
}


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _number(row: dict[str, str], field: str, errors: list[str], *,
            positive: bool = False, nonnegative: bool = False,
            integer: bool = False, nullable: bool = False) -> float | None:
    raw = row.get(field)
    if raw in (None, "") and nullable:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        errors.append(f"{row.get('task_id', '?')}: {field} is missing or non-numeric: {raw!r}")
        return None
    if not math.isfinite(value):
        errors.append(f"{row.get('task_id', '?')}: {field} must be finite")
    if positive and value <= 0:
        errors.append(f"{row.get('task_id', '?')}: {field} must be > 0")
    if nonnegative and value < 0:
        errors.append(f"{row.get('task_id', '?')}: {field} must be >= 0")
    if integer and not value.is_integer():
        errors.append(f"{row.get('task_id', '?')}: {field} must be integer-valued")
    return value


def validate_tasks(path: Path) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    fields, rows = read_csv(path)
    missing = TASK_REQUIRED - set(fields)
    errors.extend(f"tasks table missing required column: {field}" for field in sorted(missing))
    if not rows:
        errors.append("tasks table has no task records; use a header-only file only for schema-only simulator tables")
    seen: set[tuple[str, str]] = set()
    run_meta: dict[str, tuple[str, str, str]] = {}
    profile_counts: Counter[str] = Counter()
    divisibility_counts: Counter[str] = Counter()
    urgency_counts: Counter[str] = Counter()
    max_arrival = 0.0
    for row_number, row in enumerate(rows, start=2):
        key = (row.get("run_id", ""), row.get("task_id", ""))
        if not key[0] or not key[1]:
            errors.append(f"row {row_number}: run_id and task_id must be non-empty")
        if key in seen:
            errors.append(f"duplicate task_id within run: {key}")
        seen.add(key)
        if row.get("urgency_class") not in URGENCY:
            errors.append(f"{key}: unknown urgency_class {row.get('urgency_class')!r}")
        else:
            urgency_counts[row["urgency_class"]] += 1
        split = row.get("splittability")
        if split not in SPLIT:
            errors.append(f"{key}: unknown splittability {split!r}")
        else:
            divisibility_counts[split] += 1
        if row.get("application_profile"):
            profile_counts[row["application_profile"]] += 1
        arrival = _number(row, "arrival_time_ms", errors, nonnegative=True)
        input_bytes = _number(row, "input_size_bytes", errors, positive=True, integer=True)
        output_bytes = _number(row, "output_size_bytes", errors, positive=True, integer=True)
        required_mi = _number(row, "required_mi", errors, positive=True)
        relative = _number(row, "relative_deadline_ms", errors, positive=True)
        absolute = _number(row, "absolute_deadline_ms", errors, positive=True)
        seed = _number(row, "seed", errors, nonnegative=True, integer=True)
        if arrival is not None:
            max_arrival = max(max_arrival, arrival)
        if arrival is not None and relative is not None and absolute is not None:
            if not math.isclose(absolute, arrival + relative, rel_tol=0, abs_tol=1e-9):
                errors.append(f"{key}: absolute_deadline_ms != arrival_time_ms + relative_deadline_ms")
            if absolute < arrival:
                errors.append(f"{key}: absolute deadline precedes arrival")
        if row.get("units_version") != gen.UNITS_VERSION:
            errors.append(f"{key}: missing/inconsistent units_version")
        for field in ("config_hash", "generator_version", "run_id", "scenario_id",
                      "source_device_id", "workload_profile_id", "application_profile"):
            if not row.get(field):
                errors.append(f"{key}: required provenance field {field} is empty")
        if row.get("config_hash") and not re.fullmatch(r"[a-f0-9]{64}", row["config_hash"]):
            errors.append(f"{key}: config_hash must be a 64-character lowercase SHA-256")
        meta = (row.get("seed", ""), row.get("scenario_id", ""), row.get("config_hash", ""))
        previous = run_meta.setdefault(key[0], meta)
        if previous != meta:
            errors.append(f"{key}: rows in one run_id have inconsistent seed/scenario/config_hash")
        if split == "INDIVISIBLE":
            for field in ("partition_model_id", "partition_overhead_ms", "merge_overhead_ms",
                          "input_partition_model", "output_partition_model"):
                if row.get(field) not in (None, ""):
                    errors.append(f"{key}: indivisible task must have null {field}")
        elif split == "DATA_PARALLEL_DIVISIBLE":
            for field in ("partition_model_id", "input_partition_model", "output_partition_model"):
                if not row.get(field):
                    errors.append(f"{key}: divisible task missing {field}")
            for field in ("partition_overhead_ms", "merge_overhead_ms"):
                _number(row, field, errors, nonnegative=True)
            if row.get("input_partition_model") != "PROPORTIONAL_TO_COMPUTE_ALPHA":
                errors.append(f"{key}: unsupported/unrecognised input partition rule")
            if row.get("output_partition_model") != "PROPORTIONAL_TO_COMPUTE_ALPHA":
                errors.append(f"{key}: unsupported/unrecognised output partition rule")
    summary = {
        "rows": len(rows),
        "runs": len({row.get("run_id") for row in rows if row.get("run_id")}),
        "application_profile_counts": dict(sorted(profile_counts.items())),
        "urgency_counts": dict(sorted(urgency_counts.items())),
        "divisibility_counts": {k: divisibility_counts.get(k, 0) for k in sorted(SPLIT)},
        "max_arrival_time_ms": max_arrival,
        "errors": errors,
    }
    return errors, summary


def _check_json_field(row: dict[str, str], field: str, errors: list[str], expected_type: type | tuple[type, ...] | None = None):
    try:
        value = json.loads(row.get(field, ""))
        if expected_type is not None and not isinstance(value, expected_type):
            errors.append(f"manifest {field} must decode to {expected_type}")
        return value
    except Exception:
        errors.append(f"manifest {field} is not valid JSON")
        return None


def validate_manifest(path: Path, task_rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    fields, rows = read_csv(path)
    errors.extend(f"manifest missing required column: {f}" for f in sorted(MANIFEST_REQUIRED - set(fields)))
    if len(rows) != 1:
        errors.append(f"expected exactly one scenario manifest row, got {len(rows)}")
    if not rows:
        return errors
    manifest = rows[0]
    arrival_params = _check_json_field(manifest, "arrival_process_parameters_json", errors, dict)
    regimes = _check_json_field(manifest, "regime_timeline_json", errors, list)
    network = _check_json_field(manifest, "network_profile_json", errors, dict)
    edge = _check_json_field(manifest, "edge_capacity_profile_json", errors, dict)
    task_mix = _check_json_field(manifest, "task_mix_profile_json", errors, dict)
    _check_json_field(manifest, "paired_seed_plan_json", errors, dict)
    if manifest.get("arrival_process_type") not in {"poisson", "on_off"}:
        errors.append(f"unsupported arrival_process_type {manifest.get('arrival_process_type')!r}")
    try:
        if int(manifest.get("task_count", -1)) != len(task_rows):
            errors.append("manifest task_count does not equal tasks row count")
    except ValueError:
        errors.append("manifest task_count must be integer-valued")
    try:
        end = float(manifest.get("generation_window_end_ms", ""))
        if not math.isfinite(end) or end < 0:
            errors.append("generation_window_end_ms must be finite and >= 0")
        if task_rows and end < max(float(r["arrival_time_ms"]) for r in task_rows):
            errors.append("generation_window_end_ms precedes final task arrival")
    except (ValueError, KeyError):
        errors.append("generation_window_end_ms is missing or invalid")
    if isinstance(regimes, list):
        if not regimes:
            errors.append("regime_timeline_json must contain at least one regime")
        for item in regimes:
            if item.get("policy_observation") is not False or item.get("evaluation_metadata_only") is not True:
                errors.append("regime metadata must be explicitly marked evaluation-only and not a policy observation")
    if isinstance(arrival_params, dict) and arrival_params.get("type") != manifest.get("arrival_process_type"):
        errors.append("arrival process type disagrees with its parameter object")
    for obj, label in ((network, "network"), (edge, "edge capacity"), (task_mix, "task mix")):
        if isinstance(obj, dict) and not obj:
            errors.append(f"manifest {label} profile cannot be empty")
    for field in ("run_id", "seed", "scenario_id", "config_hash"):
        if any(row.get(field) != manifest.get(field) for row in task_rows):
            errors.append(f"manifest/task mismatch for {field}")
    if task_rows and any(row.get("config_hash") != manifest.get("config_hash") for row in task_rows):
        errors.append("manifest config_hash does not match task records")
    if manifest.get("dataset_split") not in {"train", "validation", "test"}:
        errors.append("dataset_split must be train, validation or test")
    return errors


def _action_semantics(action: str, offload_fraction: float, local_fraction: float,
                      remote_tier: str | None, splittability: str,
                      local_site: str | None, remote_site: str | None,
                      key: tuple[str, str], errors: list[str]) -> None:
    if not any(math.isclose(offload_fraction, allowed, rel_tol=0, abs_tol=1e-9) for allowed in ALPHAS):
        errors.append(f"invalid offload fraction {offload_fraction}: {key}")
    if not math.isclose(offload_fraction + local_fraction, 1.0, rel_tol=0, abs_tol=1e-9):
        errors.append(f"local+remote fractions != 1: {key}")
    if not (0 <= local_fraction <= 1):
        errors.append(f"local fraction outside [0,1]: {key}")
    if splittability == "INDIVISIBLE" and action not in FULL_ACTIONS:
        errors.append(f"indivisible task offered partial/invalid action {action!r}: {key}")
        return
    if action == "LOCAL":
        if not (math.isclose(offload_fraction, 0.0) and math.isclose(local_fraction, 1.0)):
            errors.append(f"LOCAL action must have offload=0/local=1: {key}")
        if remote_tier not in (None, "", "null") or remote_site not in (None, "", "null"):
            errors.append(f"LOCAL action must not select a remote tier/site: {key}")
        if not local_site:
            errors.append(f"LOCAL action requires a local site ID: {key}")
    elif action in {"EDGE_FULL", "CLOUD_FULL"}:
        expected = "EDGE" if action == "EDGE_FULL" else "CLOUD"
        if not (math.isclose(offload_fraction, 1.0) and math.isclose(local_fraction, 0.0)):
            errors.append(f"full remote action must have offload=1/local=0: {key}")
        if remote_tier != expected or not remote_site:
            errors.append(f"{action} must select exactly one {expected} remote site: {key}")
    elif action in PARTIAL_ACTIONS:
        expected_tier, expected_fraction = PARTIAL_ACTIONS[action]
        if splittability != "DATA_PARALLEL_DIVISIBLE":
            errors.append(f"partial action forbidden for indivisible task: {key}")
        if not math.isclose(offload_fraction, expected_fraction, rel_tol=0, abs_tol=1e-9):
            errors.append(f"action name/fraction mismatch: {key}")
        if not math.isclose(local_fraction, 1.0 - expected_fraction, rel_tol=0, abs_tol=1e-9):
            errors.append(f"partial local fraction must equal 1-alpha: {key}")
        if remote_tier != expected_tier:
            errors.append(f"partial action must use exactly one {expected_tier} remote tier: {key}")
        if not local_site or not remote_site:
            errors.append(f"partial action requires one local and one remote site ID: {key}")
    else:
        errors.append(f"unknown requested/candidate action {action!r}: {key}")


def validate_decisions(path: Path, task_rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    fields, rows = read_csv(path)
    by_task = {(row["run_id"], row["task_id"]): row for row in task_rows}
    required = {
        "run_id", "task_id", "policy_id", "decision_time_ms", "requested_action",
        "offload_fraction", "local_fraction", "remote_tier", "partition_model_id",
        "selected_local_site_id", "selected_remote_site_id", "feasible_action_set_json",
        "selected_action_feasible", "fallback_used", "fallback_reason",
        "decision_wall_clock_ms", "model_version",
    }
    errors.extend(f"decisions missing required column: {f}" for f in sorted(required - set(fields)))
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        key = (row.get("run_id", ""), row.get("task_id", ""))
        task = by_task.get(key)
        if task is None:
            errors.append(f"decision has no matching task: {key}")
            continue
        unique_key = (key[0], key[1], row.get("policy_id", ""))
        if unique_key in seen:
            errors.append(f"duplicate decision record: {unique_key}")
        seen.add(unique_key)
        try:
            alpha = float(row.get("offload_fraction", ""))
            local = float(row.get("local_fraction", ""))
        except ValueError:
            errors.append(f"decision fractions invalid: {unique_key}")
            continue
        tier = row.get("remote_tier") or None
        _action_semantics(row.get("requested_action", ""), alpha, local, tier,
                          task.get("splittability", ""), row.get("selected_local_site_id") or None,
                          row.get("selected_remote_site_id") or None, unique_key, errors)
        if task.get("splittability") == "INDIVISIBLE" and row.get("partition_model_id") not in (None, ""):
            errors.append(f"indivisible decision must have null partition_model_id: {unique_key}")
        if task.get("splittability") == "DATA_PARALLEL_DIVISIBLE" and row.get("partition_model_id") != task.get("partition_model_id"):
            errors.append(f"decision partition_model_id does not match task profile: {unique_key}")
        try:
            allowed_actions = json.loads(row.get("feasible_action_set_json", ""))
            if not isinstance(allowed_actions, list) or any(not isinstance(x, str) for x in allowed_actions):
                raise ValueError("not a string array")
            if row.get("requested_action") not in allowed_actions and row.get("selected_action_feasible", "").lower() == "true":
                errors.append(f"selected feasible action missing from feasible_action_set: {unique_key}")
        except Exception:
            errors.append(f"feasible_action_set_json must be a JSON string array: {unique_key}")
        if row.get("selected_action_feasible", "").lower() not in {"true", "false"}:
            errors.append(f"selected_action_feasible must be boolean: {unique_key}")
        if row.get("fallback_used", "").lower() not in {"true", "false"}:
            errors.append(f"fallback_used must be boolean: {unique_key}")
        if row.get("fallback_used", "").lower() == "true" and not row.get("fallback_reason"):
            errors.append(f"fallback_used=true requires fallback_reason: {unique_key}")
        _number(row, "decision_time_ms", errors, nonnegative=True)
        _number(row, "decision_wall_clock_ms", errors, nonnegative=True)
        if not row.get("policy_id") or not row.get("model_version"):
            errors.append(f"decision policy_id/model_version must be non-empty: {unique_key}")
    return errors


def _is_forbidden_context_key(key: str) -> bool:
    name = key.lower()
    return (name in FORBIDDEN_CONTEXT_KEYS
            or name.startswith(("future_", "actual_", "outcome_", "regime_", "test_", "heldout_"))
            or name.endswith(("_outcome", "_label_leakage")))


def _scan_context_value(value: Any, path: str, errors: list[str], row_number: int) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if _is_forbidden_context_key(str(key)):
                errors.append(f"decision-context leakage at row {row_number}: {path}{key}")
            _scan_context_value(nested, f"{path}{key}.", errors, row_number)
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _scan_context_value(nested, f"{path}[{index}].", errors, row_number)


def validate_contexts(path: Path, task_rows: list[dict[str, str]]) -> list[str]:
    fields, rows = read_csv(path)
    errors: list[str] = []
    required = {
        "run_id", "task_id", "policy_id", "decision_time_ms", "candidate_tier",
        "candidate_site_id", "candidate_action", "offload_fraction", "local_fraction",
        "remote_tier", "local_site_id", "remote_site_id", "partition_model_id",
        "cpu_capacity_mips", "cpu_utilization_fraction", "queue_length_tasks",
        "estimated_queue_wait_ms", "link_bandwidth_value", "link_bandwidth_unit",
        "link_delay_ms", "predicted_transfer_time_ms", "predicted_execution_time_ms",
        "predicted_end_to_end_time_ms", "calibration_margin_ms",
        "conservative_completion_estimate_ms", "remaining_deadline_slack_ms", "feasible_at_decision",
    }
    errors.extend(f"decision_contexts missing required column: {f}" for f in sorted(required - set(fields)))
    tasks_by_key = {(r["run_id"], r["task_id"]): r for r in task_rows}
    for row_number, row in enumerate(rows, start=2):
        for key in row:
            if _is_forbidden_context_key(key):
                errors.append(f"decision-context leakage column present: {key}")
        for key, raw in row.items():
            if raw in (None, ""):
                continue
            try:
                parsed = json.loads(raw)
            except (ValueError, TypeError):
                continue
            _scan_context_value(parsed, f"{key}.", errors, row_number)
        key = (row.get("run_id", ""), row.get("task_id", ""))
        task = tasks_by_key.get(key)
        if task is None:
            errors.append(f"decision context has no matching task: {key}")
            continue
        try:
            alpha, local = float(row["offload_fraction"]), float(row["local_fraction"])
        except (ValueError, KeyError):
            errors.append(f"context split fractions invalid: {key}")
            continue
        _action_semantics(row.get("candidate_action", ""), alpha, local,
                          row.get("remote_tier") or None, task["splittability"],
                          row.get("local_site_id") or None, row.get("remote_site_id") or None,
                          key, errors)
        expected_tier = "LOCAL" if row.get("candidate_action") == "LOCAL" else (
            row.get("remote_tier") if row.get("remote_tier") else None
        )
        if row.get("candidate_tier") != expected_tier:
            errors.append(f"candidate_tier inconsistent with candidate_action: {key}")
        if row.get("feasible_at_decision", "").lower() not in {"true", "false"}:
            errors.append(f"feasible_at_decision must be boolean: {key}")
        _number(row, "decision_time_ms", errors, nonnegative=True)
        _number(row, "cpu_capacity_mips", errors, positive=True, nullable=True)
        utilization = _number(row, "cpu_utilization_fraction", errors, nonnegative=True, nullable=True)
        if utilization is not None and utilization > 1:
            errors.append(f"cpu_utilization_fraction must be <= 1: {key}")
        _number(row, "queue_length_tasks", errors, nonnegative=True, integer=True, nullable=True)
        for field in ("estimated_queue_wait_ms", "link_delay_ms", "predicted_transfer_time_ms",
                      "predicted_execution_time_ms", "predicted_end_to_end_time_ms",
                      "conservative_completion_estimate_ms"):
            _number(row, field, errors, nonnegative=True, nullable=True)
        bandwidth = _number(row, "link_bandwidth_value", errors, positive=True, nullable=True)
        unit = row.get("link_bandwidth_unit") or ""
        if bandwidth is not None and not unit:
            errors.append(f"link bandwidth value cannot be supplied without an explicit unit: {key}")
        _number(row, "calibration_margin_ms", errors, nullable=True)
        _number(row, "remaining_deadline_slack_ms", errors, nullable=True)
    return errors


def validate_outcomes(path: Path, task_rows: list[dict[str, str]]) -> tuple[list[str], dict[str, Any]]:
    fields, rows = read_csv(path)
    errors: list[str] = []
    required = {
        "run_id", "task_id", "policy_id", "arrival_time_ms", "action_type", "offload_fraction", "local_fraction",
        "remote_tier", "full_execution_site_id", "local_execution_site_id", "remote_execution_site_id",
        "full_execution_start_ms", "full_execution_end_ms", "local_branch_start_ms", "local_branch_end_ms",
        "remote_input_transfer_start_ms", "remote_input_transfer_end_ms", "remote_branch_start_ms",
        "remote_branch_end_ms", "partition_start_ms", "partition_end_ms", "merge_start_ms",
        "merge_end_ms", "result_transfer_start_ms", "result_transfer_end_ms", "completion_time_ms",
        "observed_until_ms",
        "end_to_end_latency_ms", "deadline_met", "final_status", "unresolved_at_horizon", "failure_or_unresolved_reason",
    }
    errors.extend(f"outcomes missing required column: {f}" for f in sorted(required - set(fields)))
    task_by_key = {(row["run_id"], row["task_id"]): row for row in task_rows}
    seen: set[tuple[str, str, str]] = set()
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    policy_keys: dict[str, set[tuple[str, str]]] = defaultdict(set)
    allowed_status = {"ON_TIME", "LATE", "FAILED", "UNRESOLVED_AT_HORIZON"}
    if not rows:
        return errors, {"rows": 0, "schema_only": True, "policy_reconciliation": {}}
    for row in rows:
        task_key = (row.get("run_id", ""), row.get("task_id", ""))
        task = task_by_key.get(task_key)
        if task is None:
            errors.append(f"orphan simulator outcome: {task_key}")
            continue
        policy = row.get("policy_id", "")
        unique_key = (task_key[0], task_key[1], policy)
        if unique_key in seen:
            errors.append(f"duplicate/contradictory final status record: {unique_key}")
        seen.add(unique_key)
        policy_keys[policy].add(task_key)
        status = row.get("final_status", "")
        if status not in allowed_status:
            errors.append(f"invalid final status {status!r}: {unique_key}")
            continue
        counts[policy][status] += 1
        try:
            alpha, local = float(row["offload_fraction"]), float(row["local_fraction"])
        except (ValueError, KeyError):
            errors.append(f"outcome split fractions invalid: {unique_key}")
            continue
        remote_tier = row.get("remote_tier") or None
        action = row.get("action_type", "")
        local_site = row.get("local_execution_site_id") or (row.get("full_execution_site_id") if action == "LOCAL" else None) or None
        remote_site = row.get("remote_execution_site_id") or (row.get("full_execution_site_id") if action in {"EDGE_FULL", "CLOUD_FULL"} else None) or None
        _action_semantics(action, alpha, local, remote_tier, task["splittability"],
                          local_site, remote_site, unique_key, errors)
        deadline_flag = row.get("deadline_met", "").lower()
        unresolved_flag = row.get("unresolved_at_horizon", "").lower()
        if unresolved_flag not in {"true", "false"}:
            errors.append(f"unresolved_at_horizon must be boolean: {unique_key}")
        if status == "UNRESOLVED_AT_HORIZON":
            if unresolved_flag != "true" or deadline_flag not in {"", "null"}:
                errors.append(f"unresolved status requires unresolved=true and deadline_met=null: {unique_key}")
            if row.get("completion_time_ms") not in (None, ""):
                errors.append(f"unresolved task cannot have a final completion time: {unique_key}")
            if row.get("end_to_end_latency_ms") not in (None, ""):
                errors.append(f"unresolved task cannot have final end-to-end latency: {unique_key}")
            horizon = _number(row, "observed_until_ms", errors, nonnegative=True, nullable=True)
            if horizon is None:
                errors.append(f"unresolved task requires observed_until_ms: {unique_key}")
            elif horizon < float(task["arrival_time_ms"]):
                errors.append(f"unresolved observation horizon precedes task arrival: {unique_key}")
            if not row.get("failure_or_unresolved_reason"):
                errors.append(f"unresolved task requires a reason: {unique_key}")
        elif status == "ON_TIME":
            if unresolved_flag != "false" or deadline_flag != "true":
                errors.append(f"ON_TIME requires deadline_met=true and unresolved=false: {unique_key}")
        elif status in {"LATE", "FAILED"}:
            if unresolved_flag != "false" or deadline_flag != "false":
                errors.append(f"{status} requires deadline_met=false and unresolved=false: {unique_key}")
            if status == "FAILED" and not row.get("failure_or_unresolved_reason"):
                errors.append(f"failed task requires a failure reason: {unique_key}")
        if status != "UNRESOLVED_AT_HORIZON" and row.get("observed_until_ms") not in (None, ""):
            errors.append(f"observed_until_ms is reserved for unresolved-at-horizon status: {unique_key}")
        completed = status in {"ON_TIME", "LATE"}
        completion = _number(row, "completion_time_ms", errors, nonnegative=True, nullable=True)
        latency = _number(row, "end_to_end_latency_ms", errors, nonnegative=True, nullable=True)
        arrival = float(task["arrival_time_ms"])
        outcome_arrival = _number(row, "arrival_time_ms", errors, nonnegative=True)
        if outcome_arrival is not None and not math.isclose(outcome_arrival, arrival, rel_tol=0, abs_tol=1e-9):
            errors.append(f"outcome arrival_time_ms does not match generated task: {unique_key}")
        deadline = float(task["absolute_deadline_ms"])
        _number(row, "observed_until_ms", errors, nonnegative=True, nullable=True)
        if completed and (completion is None or latency is None):
            errors.append(f"completed task requires final completion time and end-to-end latency: {unique_key}")
        if not completed and status in {"FAILED", "UNRESOLVED_AT_HORIZON"} and latency is not None:
            errors.append(f"failed/unresolved task cannot claim completed end-to-end latency: {unique_key}")
        if completion is not None and latency is not None:
            if not math.isclose(completion - arrival, latency, rel_tol=0, abs_tol=1e-6):
                errors.append(f"outcome latency mismatch against task input arrival: {unique_key}")
        if status == "ON_TIME" and completion is not None and completion > deadline:
            errors.append(f"ON_TIME completion exceeds task absolute deadline: {unique_key}")
        if status == "LATE" and completion is not None and completion <= deadline:
            errors.append(f"LATE completion does not exceed task absolute deadline: {unique_key}")

        # Event trace checks: a mixed branch requires one Local and one remote branch.
        if action in PARTIAL_ACTIONS:
            event_fields = ("local_branch_start_ms", "local_branch_end_ms",
                            "remote_input_transfer_start_ms", "remote_input_transfer_end_ms",
                            "remote_branch_start_ms", "remote_branch_end_ms",
                            "partition_start_ms", "partition_end_ms", "merge_start_ms", "merge_end_ms",
                            "result_transfer_start_ms", "result_transfer_end_ms")
            if completed:
                for field in event_fields:
                    if row.get(field) in (None, ""):
                        errors.append(f"completed partial task missing branch/partition/merge/transfer event {field}: {unique_key}")
            if not row.get("local_execution_site_id") or not row.get("remote_execution_site_id"):
                errors.append(f"partial task must record one local and one remote execution site: {unique_key}")
        else:
            if not row.get("full_execution_site_id"):
                errors.append(f"full action must record full_execution_site_id: {unique_key}")
            if action in {"EDGE_FULL", "CLOUD_FULL"}:
                if completed:
                    for field in ("remote_input_transfer_start_ms", "remote_input_transfer_end_ms",
                                  "result_transfer_start_ms", "result_transfer_end_ms",
                                  "full_execution_start_ms", "full_execution_end_ms"):
                        if row.get(field) in (None, ""):
                            errors.append(f"completed remote full task missing event {field}: {unique_key}")
            elif action == "LOCAL":
                if completed:
                    for field in ("full_execution_start_ms", "full_execution_end_ms"):
                        if row.get(field) in (None, ""):
                            errors.append(f"completed local full task missing event {field}: {unique_key}")
        # Event-pair monotonicity is checked independently of final completion.
        def event_time(field: str) -> float | None:
            raw = row.get(field)
            if raw in (None, ""):
                return None
            try:
                value = float(raw)
            except ValueError:
                errors.append(f"invalid event timestamp {field}: {unique_key}")
                return None
            if not math.isfinite(value) or value < 0:
                errors.append(f"invalid event timestamp {field}: {unique_key}")
                return None
            return value

        event_pairs = [
            ("full_execution_start_ms", "full_execution_end_ms"),
            ("local_branch_start_ms", "local_branch_end_ms"),
            ("remote_input_transfer_start_ms", "remote_input_transfer_end_ms"),
            ("remote_branch_start_ms", "remote_branch_end_ms"),
            ("partition_start_ms", "partition_end_ms"),
            ("merge_start_ms", "merge_end_ms"),
            ("result_transfer_start_ms", "result_transfer_end_ms"),
        ]
        for start_field, end_field in event_pairs:
            start_time, end_time = event_time(start_field), event_time(end_field)
            if start_time is not None and end_time is not None and end_time + 1e-9 < start_time:
                errors.append(f"event end precedes start for {start_field}/{end_field}: {unique_key}")

        if completed and action in PARTIAL_ACTIONS:
            p0, p1 = event_time("partition_start_ms"), event_time("partition_end_ms")
            l0, l1 = event_time("local_branch_start_ms"), event_time("local_branch_end_ms")
            x0, x1 = event_time("remote_input_transfer_start_ms"), event_time("remote_input_transfer_end_ms")
            r0, r1 = event_time("remote_branch_start_ms"), event_time("remote_branch_end_ms")
            m0, m1 = event_time("merge_start_ms"), event_time("merge_end_ms")
            t0, t1 = event_time("result_transfer_start_ms"), event_time("result_transfer_end_ms")
            if None not in (p1, l0) and l0 + 1e-9 < p1:
                errors.append(f"local branch starts before partition completes: {unique_key}")
            if None not in (p1, x0) and x0 + 1e-9 < p1:
                errors.append(f"remote input transfer starts before partition completes: {unique_key}")
            if None not in (x1, r0) and r0 + 1e-9 < x1:
                errors.append(f"remote branch starts before input transfer completes: {unique_key}")
            if None not in (r1, t0) and t0 + 1e-9 < r1:
                errors.append(f"result transfer starts before remote branch completes: {unique_key}")
            if None not in (l1, m0, t1) and m0 + 1e-9 < max(l1, t1):
                errors.append(f"merge starts before Local branch and remote result transfer complete: {unique_key}")
        if completed and action in {"EDGE_FULL", "CLOUD_FULL"}:
            x1, e0 = event_time("remote_input_transfer_end_ms"), event_time("full_execution_start_ms")
            e1, t0 = event_time("full_execution_end_ms"), event_time("result_transfer_start_ms")
            if None not in (x1, e0) and e0 + 1e-9 < x1:
                errors.append(f"remote execution starts before input transfer completes: {unique_key}")
            if None not in (e1, t0) and t0 + 1e-9 < e1:
                errors.append(f"result transfer starts before full execution completes: {unique_key}")
        if completed:
            completion_candidates = []
            for field in ("full_execution_end_ms", "local_branch_end_ms", "remote_branch_end_ms",
                          "merge_end_ms", "result_transfer_end_ms"):
                if row.get(field) not in (None, ""):
                    try:
                        completion_candidates.append(float(row[field]))
                    except ValueError:
                        errors.append(f"invalid event timestamp {field}: {unique_key}")
            if completion_candidates and completion is not None and completion + 1e-6 < max(completion_candidates):
                errors.append(f"final completion precedes a required branch/merge/transfer event: {unique_key}")

    expected_keys = set(task_by_key)
    policy_reconciliation: dict[str, Any] = {}
    for policy, observed in sorted(policy_keys.items()):
        missing = expected_keys - observed
        extra = observed - expected_keys
        if missing:
            errors.append(f"generated tasks silently missing from outcomes for policy {policy}: {len(missing)}")
        if extra:
            errors.append(f"outcome reconciliation has extra tasks for policy {policy}: {len(extra)}")
        category_counts = counts[policy]
        total = sum(category_counts.values())
        policy_reconciliation[policy] = {
            "generated_tasks_expected": len(expected_keys),
            "on_time": category_counts["ON_TIME"],
            "late": category_counts["LATE"],
            "failed": category_counts["FAILED"],
            "unresolved_at_horizon": category_counts["UNRESOLVED_AT_HORIZON"],
            "reconciled_total": total,
            "reconciles": total == len(expected_keys) and not missing and not extra,
        }
    return errors, {"rows": len(rows), "schema_only": False, "policy_reconciliation": policy_reconciliation}


def validate_calibration(path: Path, task_rows: list[dict[str, str]]) -> list[str]:
    fields, rows = read_csv(path)
    errors: list[str] = []
    required = {
        "run_id", "task_id", "policy_id", "candidate_site_id", "candidate_action",
        "offload_fraction", "partition_model_id", "predicted_completion_time_ms",
        "actual_completion_time_ms", "prediction_residual_ms", "residual_window_size",
        "quantile_level", "calibrated_margin_ms", "conservative_completion_estimate_ms",
        "remaining_deadline_slack_ms", "feasible_at_decision", "evaluation_regime_id",
    }
    errors.extend(f"calibration_log missing required column: {f}" for f in sorted(required - set(fields)))
    task_by_key = {(r["run_id"], r["task_id"]): r for r in task_rows}
    for row in rows:
        key = (row.get("run_id", ""), row.get("task_id", ""))
        task = task_by_key.get(key)
        if task is None:
            errors.append(f"calibration record has no matching task: {key}")
            continue
        predicted = _number(row, "predicted_completion_time_ms", errors, nonnegative=True)
        actual = _number(row, "actual_completion_time_ms", errors, nonnegative=True, nullable=True)
        residual = _number(row, "prediction_residual_ms", errors, nullable=True)
        if actual is None and residual is not None:
            errors.append(f"calibration residual cannot exist without actual completion: {key}")
        if actual is not None and predicted is not None and residual is not None:
            if not math.isclose(residual, actual - predicted, rel_tol=0, abs_tol=1e-6):
                errors.append(f"prediction_residual_ms must equal actual-predicted: {key}")
        _number(row, "residual_window_size", errors, nonnegative=True, integer=True)
        quantile = _number(row, "quantile_level", errors, positive=True)
        if quantile is not None and quantile >= 1:
            errors.append(f"quantile_level must be in (0,1): {key}")
        _number(row, "calibrated_margin_ms", errors)
        _number(row, "conservative_completion_estimate_ms", errors, nonnegative=True)
        _number(row, "remaining_deadline_slack_ms", errors)
        if row.get("feasible_at_decision", "").lower() not in {"true", "false"}:
            errors.append(f"feasible_at_decision must be boolean: {key}")
        if not row.get("candidate_site_id") or not row.get("candidate_action"):
            errors.append(f"calibration candidate site/action is required: {key}")
        if task["splittability"] == "INDIVISIBLE" and "PARTIAL" in row.get("candidate_action", ""):
            errors.append(f"indivisible task cannot have a partial calibration candidate: {key}")
    return errors


def validate_paired_inputs(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    if len(paths) < 2:
        return errors
    def signature(path: Path) -> str:
        fields, rows = read_csv(path)
        data = [{key: row.get(key) for key in sorted(fields) if key != "policy_id"} for row in rows]
        return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    hashes = {str(path): signature(path) for path in paths}
    if len(set(hashes.values())) != 1:
        errors.append(f"paired policy input mismatch: {hashes}")
    return errors


def validate_replay(tasks_path: Path, manifest_path: Path,
                    workload_config: Path, scenario_config: Path) -> list[str]:
    errors: list[str] = []
    _, task_rows = read_csv(tasks_path)
    _, manifest_rows = read_csv(manifest_path)
    if not task_rows or len(manifest_rows) != 1:
        return ["replay check requires non-empty task table and exactly one manifest row"]
    manifest = manifest_rows[0]
    try:
        workload_cfg = gen.load_yaml(workload_config)
        scenario_cfg = gen.load_yaml(scenario_config)
        with tempfile.TemporaryDirectory(prefix="abdo-replay-") as tmp:
            replay_tasks, replay_manifest, _ = gen.generate_one(
                manifest["scenario_id"], int(manifest["seed"]), len(task_rows),
                manifest["run_id"], workload_cfg, scenario_cfg, Path(tmp)
            )
            expected_tasks = hashlib.sha256(tasks_path.read_bytes()).hexdigest()
            expected_manifest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            actual_tasks = gen.sha256_file(replay_tasks)
            actual_manifest = gen.sha256_file(replay_manifest)
            if expected_tasks != actual_tasks:
                errors.append(f"non-deterministic task replay: original={expected_tasks} replay={actual_tasks}")
            if expected_manifest != actual_manifest:
                errors.append(f"non-deterministic manifest replay: original={expected_manifest} replay={actual_manifest}")
    except Exception as exc:  # Report actionable error rather than swallowing validation failure.
        errors.append(f"replay check failed to execute: {type(exc).__name__}: {exc}")
    return errors


def validate_schemas(schema_dir: Path) -> list[str]:
    errors: list[str] = []
    expected = {
        "tasks.schema.json", "scenario_manifest.schema.json", "decision_contexts.schema.json",
        "decisions.schema.json", "task_outcomes.schema.json", "calibration_log.schema.json",
    }
    for name in sorted(expected):
        path = schema_dir / name
        if not path.exists():
            errors.append(f"missing schema file: {path}")
            continue
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
            if schema.get("type") != "object" or not isinstance(schema.get("properties"), dict):
                errors.append(f"schema is not a JSON object contract: {path}")
        except Exception as exc:
            errors.append(f"invalid JSON schema {path}: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--decisions", type=Path)
    parser.add_argument("--decision-contexts", type=Path)
    parser.add_argument("--outcomes", type=Path)
    parser.add_argument("--calibration-log", type=Path)
    parser.add_argument("--paired-inputs", nargs="*", type=Path, default=[])
    parser.add_argument("--check-replay", action="store_true")
    parser.add_argument("--workload-config", type=Path, default=ROOT / "configs" / "workload_profiles.yaml")
    parser.add_argument("--scenario-config", type=Path, default=ROOT / "configs" / "scenario_profiles.yaml")
    parser.add_argument("--schema-dir", type=Path, default=ROOT / "schemas")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    errors, summary = validate_tasks(args.tasks)
    _, task_rows = read_csv(args.tasks)
    errors += validate_manifest(args.manifest, task_rows)
    outcome_summary: dict[str, Any] | None = None
    if args.decisions:
        errors += validate_decisions(args.decisions, task_rows)
    if args.decision_contexts:
        errors += validate_contexts(args.decision_contexts, task_rows)
    if args.outcomes:
        outcome_errors, outcome_summary = validate_outcomes(args.outcomes, task_rows)
        errors += outcome_errors
    if args.calibration_log:
        errors += validate_calibration(args.calibration_log, task_rows)
    if args.paired_inputs:
        errors += validate_paired_inputs(args.paired_inputs)
    if args.check_replay:
        errors += validate_replay(args.tasks, args.manifest, args.workload_config, args.scenario_config)
    errors += validate_schemas(args.schema_dir)

    report = {
        "validation_status": "PASS" if not errors else "FAIL",
        "task_summary": summary,
        "outcome_reconciliation": outcome_summary,
        "errors": errors,
        "scope_note": (
            "Generated files contain synthetic task inputs and scenario metadata only. "
            "Decision contexts, decisions, task outcomes and calibration logs must be "
            "produced by the simulator/policy integration; no such records are fabricated."
        ),
    }
    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered + "\n", encoding="utf-8")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
