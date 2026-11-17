"""Strict JSON-lines contract for protocol v2.0 (nine-action offloading)."""
from __future__ import annotations

import math
from typing import Any, Mapping

from .offloading import ACTION_NAMES, N_OFFLOADING_ACTIONS, action_spec, legal_actions

PROTOCOL_VERSION_V2 = "2.0"


class V2ProtocolError(ValueError):
    pass


def _check_version(msg: Mapping[str, Any]) -> None:
    if msg.get("protocol_version") != PROTOCOL_VERSION_V2:
        raise V2ProtocolError(
            f"protocol v2.0 required; received {msg.get('protocol_version')!r}"
        )


def _check_keys(msg: Mapping[str, Any], required: set[str], optional: set[str], where: str) -> None:
    missing, extra = required - set(msg), set(msg) - required - optional
    if missing or extra:
        raise V2ProtocolError(f"{where}: missing={sorted(missing)}, unexpected={sorted(extra)}")


def parse_observation_v2(msg: Mapping[str, Any]) -> dict:
    _check_version(msg)
    _check_keys(msg, {"protocol_version", "type", "task_id", "features", "available_actions",
                      "task_constraints"}, {"sim_time_ms"}, "observation")
    if msg["type"] != "observation":
        raise V2ProtocolError("type must be observation")
    tid = msg["task_id"]
    if not isinstance(tid, str) or not tid or len(tid) > 128:
        raise V2ProtocolError("task_id must be a non-empty string (<=128 chars)")
    features = msg["features"]
    if not isinstance(features, dict) or not features:
        raise V2ProtocolError("features must be a non-empty object")
    for name, value in features.items():
        if not isinstance(name, str) or isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise V2ProtocolError(f"feature {name!r} must be a finite number")
    raw_mask = msg["available_actions"]
    if not isinstance(raw_mask, list) or not raw_mask:
        raise V2ProtocolError("available_actions must be a non-empty array")
    ids = []
    for value in raw_mask:
        if isinstance(value, bool):
            raise V2ProtocolError("boolean is not a valid action id")
        try:
            spec = action_spec(value)
        except ValueError as exc:
            raise V2ProtocolError(str(exc)) from exc
        ids.append(int(spec.action))
    if len(set(ids)) != len(ids):
        raise V2ProtocolError("available_actions must not contain duplicates")
    constraints = msg["task_constraints"]
    if not isinstance(constraints, dict):
        raise V2ProtocolError("task_constraints must be an object")
    required_constraints = {"splittability", "local_available", "edge_available", "cloud_available"}
    optional_constraints = {"partition_model_id", "partition_overhead_ms", "merge_overhead_ms", "urgency_class"}
    missing = required_constraints - set(constraints)
    extra = set(constraints) - required_constraints - optional_constraints
    if missing or extra:
        raise V2ProtocolError(f"task_constraints: missing={sorted(missing)}, unexpected={sorted(extra)}")
    for name in ("local_available", "edge_available", "cloud_available"):
        if not isinstance(constraints[name], bool):
            raise V2ProtocolError(f"task_constraints.{name} must be boolean")
    split = constraints["splittability"]
    partition = constraints.get("partition_model_id")
    if split not in ("INDIVISIBLE", "DATA_PARALLEL_DIVISIBLE"):
        raise V2ProtocolError("unsupported task_constraints.splittability")
    if "splittability" in features:
        expected_split_feature = 1.0 if split == "DATA_PARALLEL_DIVISIBLE" else 0.0
        if features["splittability"] != expected_split_feature:
            raise V2ProtocolError("features.splittability disagrees with task_constraints")
    urgency = constraints.get("urgency_class")
    if urgency is not None and urgency not in ("critical", "high", "normal"):
        raise V2ProtocolError("task_constraints.urgency_class must be critical, high, or normal")
    if split == "DATA_PARALLEL_DIVISIBLE":
        if not isinstance(partition, str) or not partition.strip():
            raise V2ProtocolError("divisible task requires partition_model_id")
        for name in ("partition_overhead_ms", "merge_overhead_ms"):
            if name not in constraints:
                raise V2ProtocolError(f"divisible task requires {name}")
    try:
        expected = legal_actions(
            splittability=split, partition_model_id=partition,
            local_available=constraints["local_available"],
            edge_available=constraints["edge_available"],
            cloud_available=constraints["cloud_available"],
        )
    except ValueError as exc:
        raise V2ProtocolError(f"invalid task feasibility constraints: {exc}") from exc
    if tuple(sorted(ids)) != expected:
        raise V2ProtocolError(
            f"available_actions do not match task feasibility; expected {expected}, got {tuple(sorted(ids))}"
        )
    for name in ("partition_overhead_ms", "merge_overhead_ms"):
        if name in constraints:
            value = constraints[name]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise V2ProtocolError(f"task_constraints.{name} must be finite and >= 0")
    if msg.get("sim_time_ms") is not None:
        value = msg["sim_time_ms"]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise V2ProtocolError("sim_time_ms must be finite and >= 0")
    return {"task_id": tid, "features": dict(features), "available_actions": tuple(ids),
            "task_constraints": dict(constraints)}


def parse_action_v2(msg: Mapping[str, Any]) -> dict:
    _check_version(msg)
    _check_keys(msg, {"protocol_version", "type", "task_id", "action_id", "action",
                      "remote_tier", "remote_fraction", "local_fraction", "model_version",
                      "mode", "epsilon"}, set(), "action")
    if msg["type"] != "action":
        raise V2ProtocolError("type must be action")
    try:
        spec = action_spec(msg["action_id"])
    except ValueError as exc:
        raise V2ProtocolError(str(exc)) from exc
    if msg["action"] != spec.name:
        raise V2ProtocolError("action name and action_id disagree")
    if msg["remote_tier"] != spec.remote_tier:
        raise V2ProtocolError("remote_tier disagrees with action catalogue")
    for key, expected in (("remote_fraction", spec.remote_fraction), ("local_fraction", spec.local_fraction)):
        value = msg[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or abs(value - expected) > 1e-9:
            raise V2ProtocolError(f"{key} disagrees with action catalogue")
    if not isinstance(msg["task_id"], str) or not msg["task_id"]:
        raise V2ProtocolError("task_id must be non-empty")
    if not isinstance(msg["model_version"], str) or not msg["model_version"]:
        raise V2ProtocolError("model_version must be non-empty")
    if msg["mode"] not in ("explore", "exploit", "greedy", "fallback", "baseline"):
        raise V2ProtocolError("invalid action decision mode")
    eps = msg["epsilon"]
    if isinstance(eps, bool) or not isinstance(eps, (int, float)) or not math.isfinite(eps) or not 0 <= eps <= 1:
        raise V2ProtocolError("epsilon must be finite and in [0,1]")
    return dict(msg)


def action_message_v2(task_id: str, action_id: int, model_version: str,
                      mode: str, epsilon: float) -> dict:
    spec = action_spec(action_id)
    return {
        "protocol_version": PROTOCOL_VERSION_V2, "type": "action", "task_id": task_id,
        "action_id": int(spec.action), "action": spec.name, "remote_tier": spec.remote_tier,
        "remote_fraction": spec.remote_fraction, "local_fraction": spec.local_fraction,
        "model_version": model_version, "mode": mode, "epsilon": float(epsilon),
    }


def parse_outcome_v2(msg: Mapping[str, Any]) -> dict:
    _check_version(msg)
    _check_keys(msg, {"protocol_version", "type", "task_id", "action_executed", "status",
                      "deadline_met", "resource_metrics"},
                {"latency_ms", "failure_reason", "sim_time_ms"}, "outcome")
    if msg["type"] != "outcome":
        raise V2ProtocolError("type must be outcome")
    tid = msg["task_id"]
    if not isinstance(tid, str) or not tid:
        raise V2ProtocolError("task_id must be non-empty")
    try:
        spec = action_spec(msg["action_executed"])
    except ValueError as exc:
        raise V2ProtocolError(str(exc)) from exc
    if msg["status"] not in ("completed", "failed"):
        raise V2ProtocolError("status must be completed or failed")
    failed = msg["status"] == "failed"
    if not isinstance(msg["deadline_met"], bool) or (failed and msg["deadline_met"]):
        raise V2ProtocolError("deadline_met must be boolean and false for failed tasks")
    latency = msg.get("latency_ms")
    if latency is None:
        if not failed:
            raise V2ProtocolError("completed task requires latency_ms")
    elif isinstance(latency, bool) or not isinstance(latency, (int, float)) or not math.isfinite(latency) or latency < 0:
        raise V2ProtocolError("latency_ms must be finite and >= 0")
    reason = msg.get("failure_reason")
    if reason is not None and (not failed or not isinstance(reason, str) or not reason):
        raise V2ProtocolError("failure_reason is allowed only as a non-empty string for failed tasks")
    if "sim_time_ms" in msg:
        sim_time = msg["sim_time_ms"]
        if isinstance(sim_time, bool) or not isinstance(sim_time, (int, float)) or not math.isfinite(sim_time) or sim_time < 0:
            raise V2ProtocolError("sim_time_ms must be finite and >= 0")
    metrics = msg["resource_metrics"]
    if not isinstance(metrics, dict):
        raise V2ProtocolError("resource_metrics must be an object")
    clean = {}
    for name, value in metrics.items():
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise V2ProtocolError(f"resource_metrics.{name} must be finite and >= 0")
        clean[name] = float(value)
    return {"task_id": tid, "action_executed": int(spec.action), "failed": failed,
            "failure_reason": reason, "latency_ms": None if latency is None else float(latency),
            "deadline_met": msg["deadline_met"], "resource_metrics": clean}
