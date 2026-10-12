"""JSON model persistence with compatibility validation and checkpointing."""
from __future__ import annotations

import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from . import MODEL_FORMAT_VERSION
from .actions import ACTION_NAMES, N_ACTIONS
from .agent import QLearningAgent
from .config import AgentConfig, RewardConfig
from .state import StateSpace

KIND = "tabular_q_learning"


class CompatibilityError(ValueError):
    """A saved model does not match the current state space / actions / reward."""


def agent_to_dict(agent: QLearningAgent, reward_cfg: RewardConfig) -> Dict[str, Any]:
    st = agent.rng.getstate()
    return {
        "format_version": MODEL_FORMAT_VERSION,
        "kind": KIND,
        "model_version": agent.model_version(),
        "saved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "actions": list(ACTION_NAMES),
        "state_spec": agent.space.spec(),
        "state_fingerprint": agent.space.fingerprint(),
        "reward_spec": reward_cfg.spec(),
        "reward_fingerprint": reward_cfg.fingerprint(),
        "agent_config": agent.cfg.to_dict(),
        "counters": {"decisions": agent.decisions, "updates": agent.updates},
        "q": agent.q,
        "visits": agent.visits,
        "rng_state": [st[0], list(st[1]), st[2]],
    }


def save_model(agent: QLearningAgent, reward_cfg: RewardConfig, path: str | Path) -> Path:
    """Atomic write (temp file + rename)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(agent_to_dict(agent, reward_cfg), fh, allow_nan=False)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, p)
    return p


def load_model(path: str | Path, space: StateSpace, agent_cfg: AgentConfig,
               reward_cfg: RewardConfig, *, allow_reward_mismatch: bool = False) -> QLearningAgent:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            d = json.load(fh)
    except (OSError, json.JSONDecodeError) as e:
        raise CompatibilityError(f"cannot read model {path}: {e}") from e
    if not isinstance(d, dict) or d.get("kind") != KIND:
        raise CompatibilityError("not a tabular_q_learning model file")
    if d.get("format_version") != MODEL_FORMAT_VERSION:
        raise CompatibilityError(f"unsupported format_version {d.get('format_version')!r}; "
                                 f"expected {MODEL_FORMAT_VERSION}")
    if d.get("actions") != list(ACTION_NAMES):
        raise CompatibilityError(f"action set mismatch: {d.get('actions')} vs {list(ACTION_NAMES)}")
    if d.get("state_fingerprint") != space.fingerprint():
        raise CompatibilityError("state specification mismatch (features/thresholds/labels differ); "
                                 "the saved Q-table has different meaning")
    if d.get("reward_fingerprint") != reward_cfg.fingerprint() and not allow_reward_mismatch:
        raise CompatibilityError("reward configuration mismatch; pass allow_reward_mismatch=True "
                                 "only if you knowingly continue under a different reward")
    q, visits = d.get("q"), d.get("visits")
    n = space.n_states

    def _grid(g, what, cast):
        if (not isinstance(g, list) or len(g) != n
                or any(not isinstance(r, list) or len(r) != N_ACTIONS for r in g)):
            raise CompatibilityError(f"{what} has wrong shape; expected {n}x{N_ACTIONS}")
        out = []
        for r in g:
            row = []
            for v in r:
                if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
                    raise CompatibilityError(f"{what} contains a non-finite/non-numeric value")
                row.append(cast(v))
            out.append(row)
        return out

    agent = QLearningAgent(space, agent_cfg)
    agent.q = _grid(q, "q", float)
    agent.visits = _grid(visits, "visits", int)
    try:
        agent.decisions = int(d["counters"]["decisions"])
        agent.updates = int(d["counters"]["updates"])
        v, internal, gauss = d["rng_state"]
        agent.rng.setstate((v, tuple(internal), gauss))
    except (KeyError, TypeError, ValueError) as e:
        raise CompatibilityError(f"corrupt counters/rng_state: {e}") from e
    return agent


_CKPT_RE = re.compile(r"^checkpoint_(\d{10})\.json$")


def save_checkpoint(agent: QLearningAgent, reward_cfg: RewardConfig, directory: str | Path,
                    keep_last: int = 3) -> Path:
    d = Path(directory)
    path = save_model(agent, reward_cfg, d / f"checkpoint_{agent.updates:010d}.json")
    ckpts = sorted(p for p in d.iterdir() if _CKPT_RE.match(p.name))
    for old in ckpts[:-keep_last]:
        old.unlink()
    return path


def latest_checkpoint(directory: str | Path) -> Optional[Path]:
    d = Path(directory)
    if not d.is_dir():
        return None
    ckpts = sorted(p for p in d.iterdir() if _CKPT_RE.match(p.name))
    return ckpts[-1] if ckpts else None
