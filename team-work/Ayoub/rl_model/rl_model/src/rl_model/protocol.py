"""JSON-lines protocol v1.0 : parsing, strict validation and message builders.

Framing: one UTF-8 JSON object per line, terminated by "\\n", no embedded newlines.
Observations (before the decision) and outcomes (after execution) are separate message types.
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Tuple

from . import PROTOCOL_VERSION
from .actions import action_id, normalize_mask
from .state import ObservationError, StateSpace

MAX_LINE_BYTES = 1_000_000
RUN_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
PHASES = ("train", "test", "dev")


class ProtocolError(Exception):
    def __init__(self, code: str, message: str, task_id: Optional[str] = None, fatal: bool = False):
        super().__init__(message)
        self.code, self.message, self.task_id, self.fatal = code, message, task_id, fatal


def dumps(msg: Mapping[str, Any]) -> str:
    return json.dumps(msg, separators=(",", ":"), allow_nan=False)


def parse_line(line: str) -> Dict[str, Any]:
    if len(line.encode("utf-8")) > MAX_LINE_BYTES:
        raise ProtocolError("line_too_long", f"line exceeds {MAX_LINE_BYTES} bytes")
    try:
        msg = json.loads(line, parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))
    except ValueError as e:
        raise ProtocolError("invalid_json", f"not valid JSON: {e}") from e
    if not isinstance(msg, dict):
        raise ProtocolError("invalid_message", "message must be a JSON object")
    return msg


def _keys(obj: Mapping, required: set, optional: set, where: str, task_id: Optional[str] = None) -> None:
    missing = required - set(obj)
    if missing:
        raise ProtocolError("invalid_message", f"{where}: missing field(s) {sorted(missing)}", task_id)
    extra = set(obj) - required - optional
    if extra:
        raise ProtocolError("invalid_message", f"{where}: unexpected field(s) {sorted(extra)}", task_id)


def _number(x: Any, what: str, tid: Optional[str], *, minimum: Optional[float] = 0.0) -> float:
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        raise ProtocolError("invalid_message", f"{what} must be a finite number", tid)
    if minimum is not None and x < minimum:
        raise ProtocolError("invalid_message", f"{what} must be >= {minimum}", tid)
    return float(x)


def check_version(msg: Mapping[str, Any]) -> None:
    v = msg.get("protocol_version")
    if v != PROTOCOL_VERSION:
        raise ProtocolError("protocol_version_mismatch",
                            f"server speaks {PROTOCOL_VERSION!r}, got {v!r}", fatal=True)


def _task_id(msg: Mapping[str, Any]) -> str:
    t = msg.get("task_id")
    if not isinstance(t, str) or not t or len(t) > 128:
        raise ProtocolError("invalid_message", "task_id must be a non-empty string (<=128 chars)")
    return t


# ---------------------------------------------------------------- hello
@dataclass(frozen=True)
class Hello:
    run_id: str
    phase: str
    sim_seed: Optional[int]
    simulator: Optional[Dict[str, Any]]


def parse_hello(msg: Mapping[str, Any]) -> Hello:
    check_version(msg)
    _keys(msg, {"protocol_version", "type", "run_id", "phase"}, {"sim_seed", "simulator"}, "hello")
    if not isinstance(msg["run_id"], str) or not RUN_ID_RE.match(msg["run_id"]):
        raise ProtocolError("invalid_message", "run_id must match [A-Za-z0-9._-]{1,64}")
    if msg["phase"] not in PHASES:
        raise ProtocolError("invalid_message", f"phase must be one of {PHASES}")
    seed = msg.get("sim_seed")
    if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int)):
        raise ProtocolError("invalid_message", "sim_seed must be an integer or null")
    sim = msg.get("simulator")
    if sim is not None and not isinstance(sim, dict):
        raise ProtocolError("invalid_message", "simulator must be an object")
    return Hello(msg["run_id"], msg["phase"], seed, sim)


# ---------------------------------------------------------- observation
@dataclass(frozen=True)
class Observation:
    task_id: str
    features: Dict[str, Any]          # as sent (validated)
    state_index: int
    available: Tuple[int, ...]
    sim_time_ms: Optional[float]


def _parse_features_block(features: Any, available: Any, space: StateSpace, tid: Optional[str]):
    try:
        idx = space.encode(features)
    except ObservationError as e:
        raise ProtocolError("invalid_observation", str(e), tid) from e
    try:
        mask = normalize_mask(available)
    except (ValueError, TypeError) as e:
        raise ProtocolError("invalid_observation", f"available_actions: {e}", tid) from e
    return idx, mask


def parse_observation(msg: Mapping[str, Any], space: StateSpace) -> Observation:
    check_version(msg)
    tid = _task_id(msg)
    _keys(msg, {"protocol_version", "type", "task_id", "features"},
          {"available_actions", "sim_time_ms"}, "observation", tid)
    st = msg.get("sim_time_ms")
    if st is not None:
        st = _number(st, "sim_time_ms", tid)
    idx, mask = _parse_features_block(msg["features"], msg.get("available_actions"), space, tid)
    return Observation(tid, dict(msg["features"]), idx, mask, st)


# -------------------------------------------------------------- outcome
@dataclass(frozen=True)
class Outcome:
    task_id: str
    action_executed: int
    failed: bool
    failure_reason: Optional[str]
    latency_ms: Optional[float]
    deadline_met: bool
    resource_metrics: Dict[str, float]
    terminal: bool
    next_state_index: Optional[int]
    next_available: Optional[Tuple[int, ...]]


def parse_outcome(msg: Mapping[str, Any], space: StateSpace) -> Outcome:
    check_version(msg)
    tid = _task_id(msg)
    _keys(msg, {"protocol_version", "type", "task_id", "action_executed", "status",
                "deadline_met", "resource_metrics"},
          {"latency_ms", "failure_reason", "terminal", "next_observation", "sim_time_ms"},
          "outcome", tid)
    try:
        a = action_id(msg["action_executed"])
    except ValueError as e:
        raise ProtocolError("invalid_outcome", str(e), tid) from e
    if msg["status"] not in ("completed", "failed"):
        raise ProtocolError("invalid_outcome", "status must be 'completed' or 'failed'", tid)
    failed = msg["status"] == "failed"
    if not isinstance(msg["deadline_met"], bool):
        raise ProtocolError("invalid_outcome", "deadline_met must be a boolean", tid)
    if failed and msg["deadline_met"]:
        raise ProtocolError("invalid_outcome", "a failed task cannot have deadline_met=true", tid)
    lat = msg.get("latency_ms")
    if lat is None:
        if not failed:
            raise ProtocolError("invalid_outcome", "latency_ms is required for completed tasks", tid)
    else:
        lat = _number(lat, "latency_ms", tid)
    reason = msg.get("failure_reason")
    if reason is not None and not isinstance(reason, str):
        raise ProtocolError("invalid_outcome", "failure_reason must be a string", tid)
    if reason is not None and not failed:
        raise ProtocolError("invalid_outcome", "failure_reason only allowed when status='failed'", tid)
    rm = msg["resource_metrics"]
    if not isinstance(rm, dict):
        raise ProtocolError("invalid_outcome", "resource_metrics must be an object", tid)
    metrics: Dict[str, float] = {}
    for k, v in rm.items():
        if v is None:
            continue
        metrics[k] = _number(v, f"resource_metrics.{k}", tid)
    u = metrics.get("executing_node_utilization")
    if u is not None and u > 1.0:
        raise ProtocolError("invalid_outcome", "executing_node_utilization must be in [0,1]", tid)
    terminal = msg.get("terminal", True)
    if not isinstance(terminal, bool):
        raise ProtocolError("invalid_outcome", "terminal must be a boolean", tid)
    nxt = msg.get("next_observation")
    nidx = nmask = None
    if nxt is not None:
        if terminal:
            raise ProtocolError("invalid_outcome", "next_observation not allowed when terminal=true", tid)
        if not isinstance(nxt, dict):
            raise ProtocolError("invalid_outcome", "next_observation must be an object", tid)
        _keys(nxt, {"features"}, {"available_actions"}, "next_observation", tid)
        nidx, nmask = _parse_features_block(nxt["features"], nxt.get("available_actions"), space, tid)
    return Outcome(tid, a, failed, reason, lat, msg["deadline_met"], metrics, terminal, nidx, nmask)


# ------------------------------------------------------------- builders
def _base(type_: str, **kw: Any) -> Dict[str, Any]:
    return {"protocol_version": PROTOCOL_VERSION, "type": type_, **kw}


def hello_ack(**kw: Any) -> Dict[str, Any]:
    return _base("hello_ack", **kw)


def action_msg(task_id: str, action_id_: int, action_name_: str, model_version: str,
               state_index: int, mode: str, epsilon: float, q_values) -> Dict[str, Any]:
    return _base("action", task_id=task_id, action_id=action_id_, action=action_name_,
                 model_version=model_version, state_index=state_index, mode=mode,
                 epsilon=round(epsilon, 6), q_values=[round(x, 6) for x in q_values])


def outcome_ack(task_id: str, updated: bool, reward: float, model_version: str,
                update_count: int) -> Dict[str, Any]:
    return _base("outcome_ack", task_id=task_id, updated=updated, reward=round(reward, 6),
                 model_version=model_version, update_count=update_count)


def error_msg(code: str, message: str, task_id: Optional[str] = None, fatal: bool = False) -> Dict[str, Any]:
    m = _base("error", code=code, message=message, fatal=fatal)
    if task_id is not None:
        m["task_id"] = task_id
    return m
