"""V2 execution-time prediction and residual-calibrated feasibility filtering.

Predictions are conditional on pre-decision resource snapshots. Queue wait is an
explicit input; setting it to zero is an assumption, not a measured queue estimate.
Calibration uses only completed outcomes from earlier tasks and is empirical, not a
deterministic deadline guarantee.
"""
from __future__ import annotations

import json
import math
import os
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from .offloading import ACTION_NAMES, action_spec
from .config import fingerprint


class RiskError(ValueError):
    """Invalid prediction, calibration, or feasibility input."""


@dataclass(frozen=True)
class RiskConfig:
    enabled: bool = True
    epsilon: float = 0.10
    window_size: int = 200
    min_samples: int = 20
    uncalibrated_margin_ms: float = 0.0
    update_on_train_outcomes: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.enabled, bool) or not isinstance(self.update_on_train_outcomes, bool):
            raise RiskError("risk enabled/update flags must be booleans")
        if (isinstance(self.epsilon, bool) or not isinstance(self.epsilon, (int, float))
                or not math.isfinite(self.epsilon) or not 0 < self.epsilon < 1):
            raise RiskError("risk epsilon must be finite and in (0, 1)")
        if not isinstance(self.window_size, int) or isinstance(self.window_size, bool) or self.window_size < 2:
            raise RiskError("risk window_size must be an integer >= 2")
        if not isinstance(self.min_samples, int) or isinstance(self.min_samples, bool) or self.min_samples < 2:
            raise RiskError("risk min_samples must be an integer >= 2")
        if self.min_samples > self.window_size:
            raise RiskError("risk min_samples cannot exceed window_size")
        if (isinstance(self.uncalibrated_margin_ms, bool)
                or not isinstance(self.uncalibrated_margin_ms, (int, float))
                or not math.isfinite(self.uncalibrated_margin_ms)
                or self.uncalibrated_margin_ms < 0):
            raise RiskError("uncalibrated_margin_ms must be finite and >= 0")

    @classmethod
    def from_dict(cls, raw: Optional[Mapping[str, Any]]) -> "RiskConfig":
        if raw is None:
            return cls()
        if not isinstance(raw, Mapping):
            raise RiskError("risk config must be an object")
        allowed = {"enabled", "epsilon", "window_size", "min_samples",
                   "uncalibrated_margin_ms", "update_on_train_outcomes"}
        extra = set(raw) - allowed
        if extra:
            raise RiskError(f"unknown risk config fields: {sorted(extra)}")
        return cls(**dict(raw))

    def spec(self) -> dict:
        return {
            "enabled": self.enabled,
            "epsilon": float(self.epsilon),
            "window_size": self.window_size,
            "min_samples": self.min_samples,
            "uncalibrated_margin_ms": float(self.uncalibrated_margin_ms),
            "update_on_train_outcomes": self.update_on_train_outcomes,
        }

    def fingerprint(self) -> str:
        return fingerprint(self.spec())


def _finite_number(value: Any, name: str, *, positive: bool = False) -> float:
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value)):
        raise RiskError(f"{name} must be a finite number")
    if positive and value <= 0:
        raise RiskError(f"{name} must be > 0")
    if not positive and value < 0:
        raise RiskError(f"{name} must be >= 0")
    return float(value)


@dataclass(frozen=True)
class LinkHop:
    bandwidth_mbps: float
    latency_ms: float

    @classmethod
    def from_dict(cls, raw: Any, name: str) -> "LinkHop":
        if not isinstance(raw, Mapping) or set(raw) != {"bandwidth_mbps", "latency_ms"}:
            raise RiskError(f"{name} must contain bandwidth_mbps and latency_ms only")
        return cls(
            _finite_number(raw["bandwidth_mbps"], f"{name}.bandwidth_mbps", positive=True),
            _finite_number(raw["latency_ms"], f"{name}.latency_ms"),
        )


@dataclass(frozen=True)
class TierProfile:
    compute_mips: float
    utilization: float
    queue_wait_ms: float
    uplink_path: tuple[LinkHop, ...] = ()
    downlink_path: tuple[LinkHop, ...] = ()

    @classmethod
    def from_dict(cls, raw: Any, tier: str, *, remote: bool) -> "TierProfile":
        required = {"compute_mips", "utilization", "queue_wait_ms"}
        optional = {"uplink_path", "downlink_path"}
        if not isinstance(raw, Mapping):
            raise RiskError(f"risk_context.resources.{tier} must be an object")
        if required - set(raw) or set(raw) - (required | optional):
            raise RiskError(f"risk_context.resources.{tier}: missing={sorted(required-set(raw))}, "
                            f"unexpected={sorted(set(raw)-(required|optional))}")
        mips = _finite_number(raw["compute_mips"], f"{tier}.compute_mips", positive=True)
        util = _finite_number(raw["utilization"], f"{tier}.utilization")
        if util > 1:
            raise RiskError(f"{tier}.utilization must be in [0, 1]")
        queue = _finite_number(raw["queue_wait_ms"], f"{tier}.queue_wait_ms")
        up_raw, down_raw = raw.get("uplink_path", []), raw.get("downlink_path", [])
        if not isinstance(up_raw, list) or not isinstance(down_raw, list):
            raise RiskError(f"{tier} paths must be arrays")
        up = tuple(LinkHop.from_dict(v, f"{tier}.uplink_path[{i}]") for i, v in enumerate(up_raw))
        down = tuple(LinkHop.from_dict(v, f"{tier}.downlink_path[{i}]") for i, v in enumerate(down_raw))
        if remote and (not up or not down):
            raise RiskError(f"{tier} requires non-empty uplink_path and downlink_path")
        if not remote and (up or down):
            raise RiskError("LOCAL must not declare network paths")
        return cls(mips, util, queue, up, down)

    @property
    def effective_mips(self) -> float:
        return self.compute_mips * (1.0 - self.utilization)


@dataclass(frozen=True)
class RiskContext:
    remaining_deadline_ms: float
    resources: dict[str, TierProfile]
    partition_overhead_ms: float
    merge_overhead_ms: float
    merge_compute_mi: float
    merge_queue_wait_ms: float
    queue_wait_basis: str = "provided_predecision_estimate"

    @classmethod
    def from_dict(cls, raw: Any, features: Mapping[str, Any],
                  constraints: Mapping[str, Any]) -> "RiskContext":
        if not isinstance(raw, Mapping):
            raise RiskError("risk_context must be an object")
        required = {"remaining_deadline_ms", "resources", "partition_overhead_ms", "merge_overhead_ms",
                    "merge_compute_mi", "merge_queue_wait_ms"}
        optional = {"queue_wait_basis"}
        if required - set(raw) or set(raw) - (required | optional):
            raise RiskError(f"risk_context: missing={sorted(required-set(raw))}, "
                            f"unexpected={sorted(set(raw)-(required|optional))}")
        slack = _finite_number(raw["remaining_deadline_ms"], "remaining_deadline_ms")
        if slack > float(features["deadline_ms"]) + 1e-9:
            raise RiskError("remaining_deadline_ms cannot exceed task deadline_ms")
        resources_raw = raw["resources"]
        if not isinstance(resources_raw, Mapping):
            raise RiskError("risk_context.resources must be an object")
        names = {"LOCAL", "EDGE", "CLOUD"}
        if set(resources_raw) - names:
            raise RiskError("risk_context.resources contains an unknown tier")
        expected_tiers = set()
        if constraints["local_available"]:
            expected_tiers.add("LOCAL")
        if constraints["edge_available"]:
            expected_tiers.add("EDGE")
        if constraints["cloud_available"]:
            expected_tiers.add("CLOUD")
        missing_tiers = expected_tiers - set(resources_raw)
        if missing_tiers:
            raise RiskError(f"risk_context.resources missing available tier(s): {sorted(missing_tiers)}")
        profiles: dict[str, TierProfile] = {}
        for tier, profile in resources_raw.items():
            profiles[tier] = TierProfile.from_dict(profile, tier, remote=tier != "LOCAL")
        feature_keys = {"LOCAL": "local_utilization", "EDGE": "edge_utilization",
                        "CLOUD": "cloud_utilization"}
        for tier, profile in profiles.items():
            if not math.isclose(profile.utilization, float(features[feature_keys[tier]]),
                                rel_tol=0.0, abs_tol=1e-9):
                raise RiskError(f"risk_context {tier} utilization disagrees with features")
        partition = _finite_number(raw["partition_overhead_ms"], "partition_overhead_ms")
        merge = _finite_number(raw["merge_overhead_ms"], "merge_overhead_ms")
        if constraints["splittability"] == "DATA_PARALLEL_DIVISIBLE":
            if not math.isclose(partition, float(constraints["partition_overhead_ms"]), abs_tol=1e-9):
                raise RiskError("risk_context partition overhead disagrees with task_constraints")
            if not math.isclose(merge, float(constraints["merge_overhead_ms"]), abs_tol=1e-9):
                raise RiskError("risk_context merge overhead disagrees with task_constraints")
        merge_mi = _finite_number(raw["merge_compute_mi"], "merge_compute_mi")
        merge_queue = _finite_number(raw["merge_queue_wait_ms"], "merge_queue_wait_ms")
        if constraints["splittability"] == "DATA_PARALLEL_DIVISIBLE" and merge_mi <= 0:
            raise RiskError("divisible tasks require positive merge_compute_mi")
        if constraints["splittability"] == "INDIVISIBLE" and merge_mi != 0:
            raise RiskError("indivisible tasks must have merge_compute_mi=0")
        basis = raw.get("queue_wait_basis", "provided_predecision_estimate")
        if not isinstance(basis, str) or not basis:
            raise RiskError("queue_wait_basis must be a non-empty string")
        return cls(slack, profiles, partition, merge, merge_mi, merge_queue, basis)


def _transfer_ms(size_bytes: float, path: tuple[LinkHop, ...]) -> float:
    total = 0.0
    for hop in path:
        total += (size_bytes * 8.0 / (hop.bandwidth_mbps * 1_000_000.0)) * 1000.0
        total += hop.latency_ms
    return total


def predict_action_ms(action: int | str, features: Mapping[str, Any],
                      constraints: Mapping[str, Any], context: RiskContext) -> Optional[float]:
    """Predict pre-decision time-to-completion; None means the required tier is saturated."""
    spec = action_spec(action)
    local = context.resources.get("LOCAL")
    remote = context.resources.get(spec.remote_tier) if spec.remote_tier else None
    mi = float(features["task_mi"])
    input_bytes = float(features["input_bytes"])
    output_bytes = float(features["output_bytes"])

    def compute(profile: Optional[TierProfile], work_mi: float, name: str) -> Optional[float]:
        if profile is None or profile.effective_mips <= 0:
            return None
        return profile.queue_wait_ms + work_mi / profile.effective_mips * 1000.0

    if spec.remote_tier is None:
        return compute(local, mi, "LOCAL")

    assert remote is not None
    alpha = spec.remote_fraction
    remote_input = input_bytes * alpha
    remote_output = output_bytes * alpha
    remote_queue_compute = compute(remote, mi * alpha, spec.remote_tier)
    if remote_queue_compute is None:
        return None
    remote_time = (
        _transfer_ms(remote_input, remote.uplink_path)
        + remote_queue_compute
        + _transfer_ms(remote_output, remote.downlink_path)
    )
    if not spec.is_partial:
        return remote_time
    local_time = compute(local, mi * (1.0 - alpha), "LOCAL")
    if local_time is None:
        return None
    if constraints["splittability"] != "DATA_PARALLEL_DIVISIBLE" or not constraints.get("partition_model_id"):
        raise RiskError("partial prediction requires DATA_PARALLEL_DIVISIBLE and partition_model_id")
    merge_compute_time = compute(local, context.merge_compute_mi, "LOCAL")
    if merge_compute_time is None:
        return None
    merge_compute_time = context.merge_queue_wait_ms + (
        context.merge_compute_mi / local.effective_mips * 1000.0
    )
    return (max(local_time, remote_time) + context.partition_overhead_ms
            + context.merge_overhead_ms + merge_compute_time)


def predict_legal_actions(features: Mapping[str, Any], constraints: Mapping[str, Any],
                          legal_action_ids: tuple[int, ...],
                          context: RiskContext) -> dict[str, Optional[float]]:
    predictions: dict[str, Optional[float]] = {}
    for action_id in legal_action_ids:
        spec = action_spec(action_id)
        predictions[spec.name] = predict_action_ms(action_id, features, constraints, context)
    return predictions


def _family_key(action_name: str) -> str:
    spec = action_spec(action_name)
    if spec.remote_tier is None:
        return "family:LOCAL"
    return f"family:{spec.remote_tier}_{'PARTIAL' if spec.is_partial else 'FULL'}"


class RiskCalibrator:
    """Bounded online residual windows with exact -> family -> pooled backoff."""

    FORMAT_VERSION = 1

    def __init__(self, config: RiskConfig):
        self.config = config
        self._windows: dict[str, deque[float]] = {}
        self.updates = 0

    def observe(self, action: int | str, predicted_ms: float, observed_ms: float) -> float:
        name = action_spec(action).name
        predicted = _finite_number(predicted_ms, "predicted_ms")
        observed = _finite_number(observed_ms, "observed_ms")
        residual = observed - predicted
        keys = (f"action:{name}", _family_key(name), "pooled")
        for key in keys:
            window = self._windows.setdefault(key, deque(maxlen=self.config.window_size))
            window.append(residual)
        self.updates += 1
        return residual

    def margin_for(self, action: int | str) -> dict:
        name = action_spec(action).name
        keys = (f"action:{name}", _family_key(name), "pooled")
        for key in keys:
            values = list(self._windows.get(key, ()))
            n = len(values)
            if n < self.config.min_samples:
                continue
            # Finite-sample one-sided empirical quantile index; no interpolation.
            rank = math.ceil((n + 1) * (1.0 - self.config.epsilon))
            if rank > n:
                continue
            raw_quantile = sorted(values)[rank - 1]
            # A negative error quantile must not shrink the analytical prediction.
            margin = max(0.0, raw_quantile)
            return {
                "margin_ms": margin,
                "raw_quantile_ms": raw_quantile,
                "source": key.split(":", 1)[0],
                "group": key,
                "sample_count": n,
                "rank": rank,
                "calibrated": True,
            }
        return {
            "margin_ms": float(self.config.uncalibrated_margin_ms),
            "raw_quantile_ms": None,
            "source": "uncalibrated",
            "group": "uncalibrated_prior",
            "sample_count": max((len(self._windows.get(k, ())) for k in keys), default=0),
            "rank": None,
            "calibrated": False,
        }

    def sample_counts(self) -> dict[str, int]:
        return {key: len(values) for key, values in sorted(self._windows.items())}

    def to_dict(self) -> dict:
        return {
            "format_version": self.FORMAT_VERSION,
            "risk_config_fingerprint": self.config.fingerprint(),
            "updates": self.updates,
            "windows": {key: list(values) for key, values in sorted(self._windows.items())},
        }

    def save(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8") as stream:
            json.dump(self.to_dict(), stream, allow_nan=False, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        return target

    @classmethod
    def load(cls, path: str | Path, config: RiskConfig) -> "RiskCalibrator":
        try:
            with Path(path).open("r", encoding="utf-8") as stream:
                raw = json.load(stream, parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            raise RiskError(f"cannot read risk calibration state: {exc}") from exc
        if not isinstance(raw, dict) or raw.get("format_version") != cls.FORMAT_VERSION:
            raise RiskError("risk calibration format version mismatch")
        if raw.get("risk_config_fingerprint") != config.fingerprint():
            raise RiskError("risk calibration configuration fingerprint mismatch")
        windows = raw.get("windows")
        if not isinstance(windows, dict):
            raise RiskError("risk calibration windows must be an object")
        result = cls(config)
        allowed_keys = {"pooled"}
        for name in ACTION_NAMES:
            allowed_keys.add(f"action:{name}")
            allowed_keys.add(_family_key(name))
        if set(windows) - allowed_keys:
            raise RiskError("risk calibration state contains unknown groups")
        for key, values in windows.items():
            if not isinstance(values, list) or len(values) > config.window_size:
                raise RiskError(f"invalid residual window {key}")
            parsed = [_finite_number(v, f"{key} residual") for v in values]
            result._windows[key] = deque(parsed, maxlen=config.window_size)
        updates = raw.get("updates")
        if isinstance(updates, bool) or not isinstance(updates, int) or updates < 0:
            raise RiskError("risk calibration updates must be a non-negative integer")
        result.updates = updates
        if len(result._windows.get("pooled", ())) > updates:
            raise RiskError("pooled residual count exceeds update count")
        return result


@dataclass(frozen=True)
class RiskDecision:
    allowed_actions: tuple[int, ...]
    feasible_actions: tuple[int, ...]
    no_feasible_action: bool
    estimates: dict[str, dict]
    fallback_reason: Optional[str]

    def metadata(self, selected_action: int, remaining_deadline_ms: float,
                 queue_wait_basis: str) -> dict:
        name = action_spec(selected_action).name
        estimate = self.estimates[name]
        return {
            "filter_applied": True,
            "status": "no_feasible_action" if self.no_feasible_action else (
                "calibrated" if estimate["calibrated"] else "uncalibrated"),
            "remaining_deadline_ms": float(remaining_deadline_ms),
            "predicted_completion_ms": estimate["predicted_completion_ms"],
            "residual_margin_ms": estimate["margin_ms"],
            "safe_completion_ms": estimate["safe_completion_ms"],
            "calibration_source": estimate["source"],
            "calibration_group": estimate["group"],
            "calibration_samples": estimate["sample_count"],
            "calibrated": estimate["calibrated"],
            "feasible_actions": [action_spec(a).name for a in self.feasible_actions],
            "no_feasible_action": self.no_feasible_action,
            "fallback_reason": self.fallback_reason,
            "queue_wait_basis": queue_wait_basis,
        }


def filter_feasible_actions(legal_action_ids: tuple[int, ...],
                            predictions: Mapping[str, Optional[float]],
                            remaining_deadline_ms: float,
                            calibrator: RiskCalibrator,
                            fallback_order: tuple[str, ...]) -> RiskDecision:
    slack = _finite_number(remaining_deadline_ms, "remaining_deadline_ms")
    estimates: dict[str, dict] = {}
    feasible = []
    rank = {name: i for i, name in enumerate(fallback_order)}
    for action_id in legal_action_ids:
        spec = action_spec(action_id)
        predicted = predictions.get(spec.name)
        calibration = calibrator.margin_for(action_id)
        if predicted is None:
            safe = None
        else:
            predicted = _finite_number(predicted, f"prediction.{spec.name}")
            safe = predicted + calibration["margin_ms"]
        estimates[spec.name] = {
            "predicted_completion_ms": predicted,
            "margin_ms": calibration["margin_ms"],
            "safe_completion_ms": safe,
            **calibration,
        }
        if safe is not None and safe <= slack + 1e-9:
            feasible.append(action_id)
    if feasible:
        return RiskDecision(tuple(sorted(feasible)), tuple(sorted(feasible)), False, estimates, None)

    def fallback_key(action_id: int):
        name = action_spec(action_id).name
        safe = estimates[name]["safe_completion_ms"]
        if safe is None:
            return (1, math.inf, math.inf, rank.get(name, len(rank)), action_id)
        return (0, max(0.0, safe - slack), safe, rank.get(name, len(rank)), action_id)

    selected = min(legal_action_ids, key=fallback_key)
    return RiskDecision(
        (selected,), (), True, estimates,
        "NO_FEASIBLE_SITE_AT_ARRIVAL",
    )
