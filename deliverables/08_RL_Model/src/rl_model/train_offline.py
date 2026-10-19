"""Replay REAL logged transitions (run logs written by the server) into a fresh Q-table.

Use cases: re-train under a different reward weighting without re-running iFogSim; resume analysis.
Limits: Q-learning is off-policy so logs from any behaviour policy are usable, BUT a state-action pair
that never appears in the logs keeps q_init. Logs of a single fixed baseline therefore cover only one
action per state; collect exploratory data (server --mode baseline --policy random, or train mode).
"""
from __future__ import annotations

import argparse
import dataclasses
import random
import sys
from pathlib import Path
from typing import List, Optional

from .actions import action_id
from .agent import QLearningAgent
from .aggregate import AggregationError, read_run
from .config import Config
from .persistence import save_model
from .reward import RewardError, compute_reward
from .state import ObservationError, StateSpace


def train_from_logs(cfg: Config, log_paths: List[str], epochs: int = 1, shuffle_seed: int = 0,
                    phases=("train",)) -> QLearningAgent:
    space = StateSpace(cfg.features)
    agent = QLearningAgent(space, cfg.agent)
    trans = []
    for p in log_paths:
        run = read_run(p)
        if run["start"]["phase"] not in phases:
            raise AggregationError(f"{p}: phase {run['start']['phase']!r} not in {phases}; "
                                   "refusing to train on test-phase data")
        for t in run["tasks"]:
            o = t["outcome"]
            try:
                s = space.encode(t["observation"])
                rb = compute_reward(cfg.reward, failed=o["status"] == "failed", latency_ms=o.get("latency_ms"),
                                    deadline_met=o["deadline_met"], resource_metrics=o["resource_metrics"],
                                    deadline_ms=t["observation"].get("deadline_ms"))
            except (ObservationError, RewardError) as e:
                raise AggregationError(f"{p}: task {t.get('task_id')}: {e}") from e
            trans.append((s, action_id(t["action_executed"]), rb.reward))
    if not trans:
        raise AggregationError("no transitions found in logs")
    rng = random.Random(shuffle_seed)
    for _ in range(epochs):
        order = list(range(len(trans)))
        rng.shuffle(order)
        for i in order:
            s, a, r = trans[i]
            agent.update(s, a, r, terminal=True)     # contextual-bandit logs: no next state
    return agent


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_logs", nargs="+")
    ap.add_argument("--config", default="config/default.json")
    ap.add_argument("--out", default="artifacts/model_offline.json")
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args(argv)
    try:
        cfg = Config.load(a.config)
        agent = train_from_logs(cfg, a.run_logs, a.epochs, a.seed)
    except (AggregationError, ValueError, OSError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    save_model(agent, cfg.reward, a.out)
    print(f"trained on {agent.updates} updates -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
