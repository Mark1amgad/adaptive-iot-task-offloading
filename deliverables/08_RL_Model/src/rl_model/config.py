"""Configuration dataclasses (loaded from JSON) with validation and fingerprints."""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


class ConfigError(ValueError):
    pass


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False)


def fingerprint(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def _finite(x: Any, what: str) -> float:
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        raise ConfigError(f"{what} must be a finite number, got {x!r}")
    return float(x)


@dataclass(frozen=True)
class FeatureConfig:
    name: str
    unit: str
    thresholds: Tuple[float, ...]
    labels: Tuple[str, ...]
    min_value: float = 0.0
    max_value: Optional[float] = None
    source: str = "TO CONFIRM"
    timing: str = "TO CONFIRM"
    enabled: bool = True
    # placeholder | from_design_doc | calibrated  (honesty flag, surfaced at runtime)
    status: str = "placeholder"

    def __post_init__(self) -> None:
        if not self.name:
            raise ConfigError("feature name is empty")
        th = tuple(_finite(t, f"{self.name}.thresholds") for t in self.thresholds)
        object.__setattr__(self, "thresholds", th)
        object.__setattr__(self, "labels", tuple(self.labels))
        if not th:
            raise ConfigError(f"{self.name}: at least one threshold required")
        if any(b <= a for a, b in zip(th, th[1:])):
            raise ConfigError(f"{self.name}: thresholds must be strictly increasing: {th}")
        if len(self.labels) != len(th) + 1:
            raise ConfigError(f"{self.name}: need {len(th) + 1} labels, got {len(self.labels)}")
        if self.status not in ("placeholder", "from_design_doc", "calibrated"):
            raise ConfigError(f"{self.name}: bad status {self.status!r}")
        _finite(self.min_value, f"{self.name}.min_value")
        if self.max_value is not None:
            _finite(self.max_value, f"{self.name}.max_value")
            if self.max_value <= self.min_value:
                raise ConfigError(f"{self.name}: max_value must exceed min_value")
        if th[0] <= self.min_value:
            raise ConfigError(f"{self.name}: first threshold must exceed min_value")
        if self.max_value is not None and th[-1] >= self.max_value:
            raise ConfigError(f"{self.name}: last threshold must be below max_value")

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "FeatureConfig":
        d = dict(d)
        d["thresholds"] = tuple(d["thresholds"])
        d["labels"] = tuple(d["labels"])
        return cls(**d)

    def spec(self) -> Dict[str, Any]:
        """Part of the feature that defines state semantics (used for compatibility)."""
        return {"name": self.name, "unit": self.unit, "thresholds": list(self.thresholds),
                "labels": list(self.labels), "min_value": self.min_value, "max_value": self.max_value}


@dataclass(frozen=True)
class CostTerm:
    metric: str            # key inside outcome.resource_metrics
    weight: float          # relative weight inside the cost term
    ref_value: float       # value that maps to normalized cost 1.0 (clipped)
    required: bool = True  # if True a completed outcome without this metric is rejected
    status: str = "placeholder"

    def __post_init__(self) -> None:
        if _finite(self.weight, "cost weight") <= 0:
            raise ConfigError("cost term weight must be > 0")
        if _finite(self.ref_value, "cost ref_value") <= 0:
            raise ConfigError("cost term ref_value must be > 0")


@dataclass(frozen=True)
class RewardConfig:
    w_latency: float = 1.0
    w_deadline: float = 2.0
    w_cost: float = 0.5
    latency_norm: str = "fixed"          # "fixed" (latency_ref_ms) | "deadline" (task deadline)
    latency_ref_ms: float = 1000.0
    latency_clip: float = 1.0            # normalized latency is clipped to [0, latency_clip]
    failure_penalty: float = 0.0         # extra penalty on failed tasks (on top of max latency + miss)
    cost_terms: Tuple[CostTerm, ...] = ()

    def __post_init__(self) -> None:
        for n in ("w_latency", "w_deadline", "w_cost", "latency_ref_ms", "latency_clip", "failure_penalty"):
            if _finite(getattr(self, n), n) < 0:
                raise ConfigError(f"{n} must be >= 0")
        if self.latency_ref_ms <= 0 or self.latency_clip <= 0:
            raise ConfigError("latency_ref_ms and latency_clip must be > 0")
        if self.latency_norm not in ("fixed", "deadline"):
            raise ConfigError("latency_norm must be 'fixed' or 'deadline'")
        if self.w_cost > 0 and not self.cost_terms:
            raise ConfigError("w_cost > 0 requires at least one cost term")

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RewardConfig":
        d = dict(d)
        d["cost_terms"] = tuple(CostTerm(**t) for t in d.get("cost_terms", ()))
        return cls(**d)

    def spec(self) -> Dict[str, Any]:
        return {
            "w_latency": self.w_latency, "w_deadline": self.w_deadline, "w_cost": self.w_cost,
            "latency_norm": self.latency_norm, "latency_ref_ms": self.latency_ref_ms,
            "latency_clip": self.latency_clip, "failure_penalty": self.failure_penalty,
            "cost_terms": [{"metric": t.metric, "weight": t.weight, "ref_value": t.ref_value,
                            "required": t.required} for t in self.cost_terms],
        }

    def fingerprint(self) -> str:
        return fingerprint(self.spec())

    @property
    def min_reward(self) -> float:
        return -(self.w_latency * self.latency_clip + self.w_deadline + self.w_cost + self.failure_penalty)


@dataclass(frozen=True)
class AgentConfig:
    alpha: float = 0.1
    gamma: float = 0.0
    epsilon_start: float = 0.3
    epsilon_end: float = 0.02
    epsilon_decay_steps: int = 16000      # training decisions over which epsilon decays linearly
    q_init: float = 0.0
    seed: int = 1
    decision_model: str = "contextual_bandit"   # or "sequential"
    # deterministic tie-break / fallback order used by frozen greedy policy
    fallback_order: Tuple[str, ...] = ("Edge", "Cloud", "Local")
    checkpoint_every: int = 0             # 0 disables; otherwise every N updates
    checkpoint_keep_last: int = 3

    def __post_init__(self) -> None:
        if not 0 < _finite(self.alpha, "alpha") <= 1:
            raise ConfigError("alpha must be in (0, 1]")
        if not 0 <= _finite(self.gamma, "gamma") <= 1:
            raise ConfigError("gamma must be in [0, 1]")
        for n in ("epsilon_start", "epsilon_end"):
            if not 0 <= _finite(getattr(self, n), n) <= 1:
                raise ConfigError(f"{n} must be in [0, 1]")
        if self.epsilon_end > self.epsilon_start:
            raise ConfigError("epsilon_end must be <= epsilon_start")
        if not isinstance(self.epsilon_decay_steps, int) or self.epsilon_decay_steps < 1:
            raise ConfigError("epsilon_decay_steps must be an integer >= 1")
        _finite(self.q_init, "q_init")
        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise ConfigError("seed must be an integer")
        if self.decision_model not in ("contextual_bandit", "sequential"):
            raise ConfigError("decision_model must be 'contextual_bandit' or 'sequential'")
        if self.decision_model == "contextual_bandit" and self.gamma != 0.0:
            raise ConfigError("gamma must be 0 for decision_model='contextual_bandit' "
                              "(no state transitions -> no future term)")
        if sorted(self.fallback_order) != ["Cloud", "Edge", "Local"]:
            raise ConfigError("fallback_order must be a permutation of Local/Edge/Cloud")
        object.__setattr__(self, "fallback_order", tuple(self.fallback_order))
        if self.checkpoint_every < 0 or self.checkpoint_keep_last < 1:
            raise ConfigError("checkpoint_every must be >= 0 and checkpoint_keep_last >= 1")

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AgentConfig":
        d = dict(d)
        if "fallback_order" in d:
            d["fallback_order"] = tuple(d["fallback_order"])
        return cls(**d)

    def to_dict(self) -> Dict[str, Any]:
        d = dict(self.__dict__)
        d["fallback_order"] = list(self.fallback_order)
        return d


@dataclass(frozen=True)
class Config:
    features: Tuple[FeatureConfig, ...]
    reward: RewardConfig
    agent: AgentConfig

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Config":
        try:
            feats = tuple(FeatureConfig.from_dict(f) for f in d["state"]["features"])
            return cls(features=feats, reward=RewardConfig.from_dict(d["reward"]),
                       agent=AgentConfig.from_dict(d["agent"]))
        except (KeyError, TypeError) as e:
            raise ConfigError(f"malformed config: {e!r}") from e

    @classmethod
    def load(cls, path: str | Path) -> "Config":
        with open(path, "r", encoding="utf-8") as fh:
            return cls.from_dict(json.load(fh))
