"""Strict model persistence for the nine-action v2 learner."""
from __future__ import annotations

import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

from .offloading import ACTION_NAMES, N_OFFLOADING_ACTIONS
from .agent_v2 import V2AgentConfig, V2MaskedTabularAgent
from .config import fingerprint

MODEL_FORMAT_VERSION_V2 = 2


def _agent_config_spec(config: V2AgentConfig) -> dict:
    return {
        "alpha": config.alpha, "epsilon_start": config.epsilon_start,
        "epsilon_end": config.epsilon_end, "epsilon_decay_steps": config.epsilon_decay_steps,
        "q_init": config.q_init, "seed": config.seed,
        "fallback_order": list(config.fallback_order),
    }


class V2CompatibilityError(ValueError):
    pass


def save_v2_model(agent: V2MaskedTabularAgent, state_fingerprint: str, path: str | Path,
                  reward_fingerprint: str = "") -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    state = agent.rng.getstate()
    payload = {
        "format_version": MODEL_FORMAT_VERSION_V2,
        "protocol_version": "2.0",
        "kind": "masked_tabular_q_learning",
        "actions": list(ACTION_NAMES),
        "state_count": agent.n_states,
        "state_fingerprint": state_fingerprint,
        "reward_fingerprint": reward_fingerprint,
        "saved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "agent_config": _agent_config_spec(agent.config),
        "agent_config_fingerprint": fingerprint(_agent_config_spec(agent.config)),
        "counters": {"decisions": agent.decisions, "updates": agent.updates},
        "q": agent.q, "visits": agent.visits,
        "rng_state": [state[0], list(state[1]), state[2]],
    }
    tmp = p.with_suffix(p.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, allow_nan=False)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, p)
    return p


def load_v2_model(path: str | Path, n_states: int, state_fingerprint: str,
                  config: V2AgentConfig, reward_fingerprint: str = "") -> V2MaskedTabularAgent:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh, parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise V2CompatibilityError(f"cannot read v2 model: {exc}") from exc
    if not isinstance(data, dict) or data.get("kind") != "masked_tabular_q_learning":
        raise V2CompatibilityError("not a v2 masked tabular model")
    if data.get("format_version") != MODEL_FORMAT_VERSION_V2 or data.get("protocol_version") != "2.0":
        raise V2CompatibilityError("model format/protocol version mismatch; v1 models cannot be migrated implicitly")
    if data.get("actions") != list(ACTION_NAMES):
        raise V2CompatibilityError("v2 action catalogue mismatch")
    if data.get("state_count") != n_states or data.get("state_fingerprint") != state_fingerprint:
        raise V2CompatibilityError("state specification mismatch")
    if data.get("reward_fingerprint", "") != reward_fingerprint:
        raise V2CompatibilityError("reward specification mismatch")
    expected_agent_config = _agent_config_spec(config)
    if data.get("agent_config_fingerprint") != fingerprint(expected_agent_config):
        raise V2CompatibilityError("agent configuration mismatch")
    q, visits = data.get("q"), data.get("visits")
    if (not isinstance(q, list) or len(q) != n_states
            or not isinstance(visits, list) or len(visits) != n_states):
        raise V2CompatibilityError("Q/visit table has wrong state dimension")
    for grid, name in ((q, "Q"), (visits, "visit")):
        for row in grid:
            if not isinstance(row, list) or len(row) != N_OFFLOADING_ACTIONS:
                raise V2CompatibilityError(f"{name} table must have exactly nine action columns")
            for value in row:
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                    raise V2CompatibilityError(f"{name} table contains invalid value")
                if name == "visit" and (int(value) != value or value < 0):
                    raise V2CompatibilityError("visit counts must be non-negative integers")
    agent = V2MaskedTabularAgent(n_states, config)
    agent.q = [[float(x) for x in row] for row in q]
    agent.visits = [[int(x) for x in row] for row in visits]
    try:
        agent.decisions = int(data["counters"]["decisions"])
        agent.updates = int(data["counters"]["updates"])
        version, internal, gauss = data["rng_state"]
        agent.rng.setstate((version, tuple(internal), gauss))
    except (KeyError, TypeError, ValueError) as exc:
        raise V2CompatibilityError(f"corrupt counters/RNG state: {exc}") from exc
    return agent
