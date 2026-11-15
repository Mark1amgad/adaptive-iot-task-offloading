"""Research-grade offloading action catalogue, feasibility masks, and analytical cost estimates.

This module is deliberately isolated from protocol v1 and the legacy 3-action Q-table.
It defines the proposed v2 action semantics without silently changing persisted models.
The estimator is a transparent analytical model, not a substitute for CloudSim results.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import IntEnum
from typing import Iterable, Optional, Tuple


class OffloadingAction(IntEnum):
    LOCAL = 0
    EDGE_PARTIAL_25 = 1
    EDGE_PARTIAL_50 = 2
    EDGE_PARTIAL_75 = 3
    EDGE_FULL = 4
    CLOUD_PARTIAL_25 = 5
    CLOUD_PARTIAL_50 = 6
    CLOUD_PARTIAL_75 = 7
    CLOUD_FULL = 8


@dataclass(frozen=True)
class ActionSpec:
    action: OffloadingAction
    name: str
    remote_tier: Optional[str]
    remote_fraction: float

    @property
    def local_fraction(self) -> float:
        return 1.0 - self.remote_fraction

    @property
    def is_partial(self) -> bool:
        return 0.0 < self.remote_fraction < 1.0


ACTION_SPECS: Tuple[ActionSpec, ...] = (
    ActionSpec(OffloadingAction.LOCAL, "LOCAL", None, 0.0),
    ActionSpec(OffloadingAction.EDGE_PARTIAL_25, "EDGE_PARTIAL_25", "EDGE", 0.25),
    ActionSpec(OffloadingAction.EDGE_PARTIAL_50, "EDGE_PARTIAL_50", "EDGE", 0.50),
    ActionSpec(OffloadingAction.EDGE_PARTIAL_75, "EDGE_PARTIAL_75", "EDGE", 0.75),
    ActionSpec(OffloadingAction.EDGE_FULL, "EDGE_FULL", "EDGE", 1.0),
    ActionSpec(OffloadingAction.CLOUD_PARTIAL_25, "CLOUD_PARTIAL_25", "CLOUD", 0.25),
    ActionSpec(OffloadingAction.CLOUD_PARTIAL_50, "CLOUD_PARTIAL_50", "CLOUD", 0.50),
    ActionSpec(OffloadingAction.CLOUD_PARTIAL_75, "CLOUD_PARTIAL_75", "CLOUD", 0.75),
    ActionSpec(OffloadingAction.CLOUD_FULL, "CLOUD_FULL", "CLOUD", 1.0),
)
ACTION_NAMES: Tuple[str, ...] = tuple(s.name for s in ACTION_SPECS)
N_OFFLOADING_ACTIONS = len(ACTION_SPECS)
_SPEC_BY_ID = {int(s.action): s for s in ACTION_SPECS}
_SPEC_BY_NAME = {s.name: s for s in ACTION_SPECS}


class OffloadingModelError(ValueError):
    """Invalid task/resource input for action feasibility or cost estimation."""


def action_spec(action: int | str | OffloadingAction) -> ActionSpec:
    if isinstance(action, str):
        spec = _SPEC_BY_NAME.get(action)
    elif isinstance(action, OffloadingAction):
        spec = _SPEC_BY_ID.get(int(action))
    elif isinstance(action, int) and not isinstance(action, bool):
        spec = _SPEC_BY_ID.get(action)
    else:
        spec = None
    if spec is None:
        raise OffloadingModelError(f"unknown offloading action: {action!r}")
    return spec


def legal_actions(*, splittability: str, partition_model_id: Optional[str],
                  local_available: bool = True, edge_available: bool = True,
                  cloud_available: bool = True) -> Tuple[int, ...]:
    """Return legal v2 action IDs for the current task and feasible tiers.

    Partial actions require an explicit divisible-task declaration and a non-empty
    partition model identifier. Full placement never requires partition metadata.
    """
    if splittability not in ("INDIVISIBLE", "DATA_PARALLEL_DIVISIBLE"):
        raise OffloadingModelError(f"unsupported splittability: {splittability!r}")
    for name, value in (("local_available", local_available),
                        ("edge_available", edge_available),
                        ("cloud_available", cloud_available)):
        if not isinstance(value, bool):
            raise OffloadingModelError(f"{name} must be a boolean")
    allowed = []
    if local_available:
        allowed.append(int(OffloadingAction.LOCAL))
    divisible = (splittability == "DATA_PARALLEL_DIVISIBLE"
                 and local_available)
    if divisible and (not isinstance(partition_model_id, str) or not partition_model_id.strip()):
        divisible = False
    if edge_available:
        if divisible:
            allowed.extend((1, 2, 3))
        allowed.append(int(OffloadingAction.EDGE_FULL))
    if cloud_available:
        if divisible:
            allowed.extend((5, 6, 7))
        allowed.append(int(OffloadingAction.CLOUD_FULL))
    if not allowed:
        raise OffloadingModelError("no feasible action: local, edge, and cloud are unavailable")
    return tuple(allowed)


def _finite_positive(value: float, name: str, *, allow_zero: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise OffloadingModelError(f"{name} must be a finite number")
    if value < 0 or (value == 0 and not allow_zero):
        op = ">= 0" if allow_zero else "> 0"
        raise OffloadingModelError(f"{name} must be {op}")
    return float(value)


@dataclass(frozen=True)
class CostInputs:
    required_mi: float
    input_bytes: float
    output_bytes: float
    local_mips: float
    remote_mips: float
    uplink_mbps: float
    downlink_mbps: float
    uplink_latency_ms: float = 0.0
    downlink_latency_ms: float = 0.0
    partition_overhead_ms: float = 0.0
    merge_overhead_ms: float = 0.0

    def validate(self) -> None:
        for name in ("required_mi", "local_mips", "remote_mips", "uplink_mbps", "downlink_mbps"):
            _finite_positive(getattr(self, name), name)
        for name in ("input_bytes", "output_bytes", "uplink_latency_ms", "downlink_latency_ms",
                     "partition_overhead_ms", "merge_overhead_ms"):
            _finite_positive(getattr(self, name), name, allow_zero=True)


@dataclass(frozen=True)
class CostEstimate:
    action: str
    local_branch_ms: float
    remote_branch_ms: float
    partition_ms: float
    merge_ms: float
    predicted_completion_ms: float
    uplink_ms: float
    downlink_ms: float


def _transfer_ms(size_bytes: float, bandwidth_mbps: float) -> float:
    # Mbps means decimal megabits/second; convert bytes to bits and seconds to ms.
    return (size_bytes * 8.0 / (bandwidth_mbps * 1_000_000.0)) * 1000.0


def estimate_completion_ms(action: int | str | OffloadingAction, inputs: CostInputs,
                           *, splittability: str = "INDIVISIBLE",
                           partition_model_id: Optional[str] = None) -> CostEstimate:
    """Estimate task completion using parallel local/remote branches for partial actions.

    Partial byte volumes are assumed proportional to the remote compute fraction.
    This is valid only for workload profiles whose declared partition model guarantees
    that relationship. The estimate uses max(local branch, remote branch) + partition
    + merge; no contention, queueing, migration, or failure model is implied.
    """
    inputs.validate()
    spec = action_spec(action)
    if spec.is_partial:
        if splittability != "DATA_PARALLEL_DIVISIBLE" or not partition_model_id:
            raise OffloadingModelError("partial action requires DATA_PARALLEL_DIVISIBLE and partition_model_id")
    if spec.remote_tier is None:
        local_ms = inputs.required_mi / inputs.local_mips * 1000.0
        return CostEstimate(spec.name, local_ms, 0.0, 0.0, 0.0, local_ms, 0.0, 0.0)

    alpha = spec.remote_fraction
    if spec.is_partial:
        local_ms = (1.0 - alpha) * inputs.required_mi / inputs.local_mips * 1000.0
        uplink = _transfer_ms(alpha * inputs.input_bytes, inputs.uplink_mbps) + inputs.uplink_latency_ms
        remote_compute = alpha * inputs.required_mi / inputs.remote_mips * 1000.0
        downlink = _transfer_ms(alpha * inputs.output_bytes, inputs.downlink_mbps) + inputs.downlink_latency_ms
        remote_ms = uplink + remote_compute + downlink
        partition = inputs.partition_overhead_ms
        merge = inputs.merge_overhead_ms
        completion = max(local_ms, remote_ms) + partition + merge
    else:
        local_ms = 0.0
        uplink = _transfer_ms(inputs.input_bytes, inputs.uplink_mbps) + inputs.uplink_latency_ms
        remote_compute = inputs.required_mi / inputs.remote_mips * 1000.0
        downlink = _transfer_ms(inputs.output_bytes, inputs.downlink_mbps) + inputs.downlink_latency_ms
        remote_ms = uplink + remote_compute + downlink
        partition = merge = 0.0
        completion = remote_ms

    return CostEstimate(spec.name, local_ms, remote_ms, partition, merge,
                        completion, uplink, downlink)
