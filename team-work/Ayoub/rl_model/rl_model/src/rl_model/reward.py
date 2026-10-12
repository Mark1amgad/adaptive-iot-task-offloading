"""Reward = -( w1*norm_latency + w2*deadline_miss + w3*resource_cost ), always <= 0.

Computed ONLY from measured simulator outcomes (never from the observation alone).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from .config import RewardConfig


class RewardError(ValueError):
    pass


@dataclass(frozen=True)
class RewardBreakdown:
    reward: float
    latency_norm: float
    deadline_miss: int
    resource_cost: float
    failed: bool

    def as_dict(self) -> dict:
        return dict(self.__dict__)


def _num(x: Any, what: str) -> float:
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or x < 0:
        raise RewardError(f"{what} must be a finite non-negative number, got {x!r}")
    return float(x)


def resource_cost(cfg: RewardConfig, metrics: Mapping[str, Any], *, lenient: bool) -> float:
    """Weighted mean of clipped, normalised metrics in [0, 1].

    lenient=True (failed tasks): a missing metric counts as 0 instead of raising.
    """
    if not cfg.cost_terms:
        return 0.0
    total_w = sum(t.weight for t in cfg.cost_terms)
    acc = 0.0
    for t in cfg.cost_terms:
        if t.metric not in metrics or metrics[t.metric] is None:
            if t.required and not lenient:
                raise RewardError(f"required resource metric missing: {t.metric}")
            continue
        acc += t.weight * min(_num(metrics[t.metric], f"resource_metrics.{t.metric}") / t.ref_value, 1.0)
    return acc / total_w


def compute_reward(cfg: RewardConfig, *, failed: bool, latency_ms: Optional[float],
                   deadline_met: bool, resource_metrics: Mapping[str, Any],
                   deadline_ms: Optional[float] = None) -> RewardBreakdown:
    """Failure handling: a failed task gets the maximum normalised latency, a deadline miss
    and ``failure_penalty``; its resource cost uses whatever metrics were reported."""
    if failed:
        lat_norm, miss = cfg.latency_clip, 1
        cost = resource_cost(cfg, resource_metrics, lenient=True)
        extra = cfg.failure_penalty
    else:
        if latency_ms is None:
            raise RewardError("latency_ms is required for a completed task")
        lat = _num(latency_ms, "latency_ms")
        if cfg.latency_norm == "deadline":
            if deadline_ms is None or deadline_ms <= 0:
                raise RewardError("latency_norm='deadline' needs the task's deadline_ms")
            ref = float(deadline_ms)
        else:
            ref = cfg.latency_ref_ms
        lat_norm = min(lat / ref, cfg.latency_clip)
        miss = 0 if deadline_met else 1
        cost = resource_cost(cfg, resource_metrics, lenient=False)
        extra = 0.0
    r = -(cfg.w_latency * lat_norm + cfg.w_deadline * miss + cfg.w_cost * cost + extra)
    return RewardBreakdown(reward=r, latency_norm=lat_norm, deadline_miss=miss,
                           resource_cost=cost, failed=failed)
