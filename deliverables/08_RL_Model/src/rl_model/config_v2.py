"""Loader for the isolated v2 state, reward, and nine-action learner configuration."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .agent_v2 import V2AgentConfig
from .config import FeatureConfig, RewardConfig
from .state import StateSpace
from .risk import RiskConfig


@dataclass(frozen=True)
class V2RuntimeConfig:
    space: StateSpace
    agent: V2AgentConfig
    reward: RewardConfig
    risk: RiskConfig

    @classmethod
    def load(cls, path: str | Path) -> "V2RuntimeConfig":
        try:
            with open(path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
            features = tuple(FeatureConfig.from_dict(item) for item in raw["state"]["features"])
            agent_raw = dict(raw["agent"])
            if "fallback_order" in agent_raw:
                agent_raw["fallback_order"] = tuple(agent_raw["fallback_order"])
            return cls(StateSpace(features), V2AgentConfig(**agent_raw),
                       RewardConfig.from_dict(raw["reward"]),
                       RiskConfig.from_dict(raw.get("risk", {})))
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"invalid v2 configuration: {exc}") from exc
