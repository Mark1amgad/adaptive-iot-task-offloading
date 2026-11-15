"""Version-2 masked tabular learner for the nine-action offloading catalogue.

Kept separate from the v1 learner so old protocol/model semantics remain intact.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Optional, Sequence

from .offloading import ACTION_NAMES, N_OFFLOADING_ACTIONS, OffloadingModelError


@dataclass(frozen=True)
class V2AgentConfig:
    alpha: float = 0.1
    epsilon_start: float = 0.3
    epsilon_end: float = 0.02
    epsilon_decay_steps: int = 16000
    q_init: float = 0.0
    seed: int = 1
    fallback_order: tuple[str, ...] = (
        "EDGE_FULL", "CLOUD_FULL", "LOCAL",
        "EDGE_PARTIAL_50", "CLOUD_PARTIAL_50",
        "EDGE_PARTIAL_25", "EDGE_PARTIAL_75",
        "CLOUD_PARTIAL_25", "CLOUD_PARTIAL_75",
    )

    def __post_init__(self):
        for name in ("alpha", "epsilon_start", "epsilon_end"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"{name} must be finite")
        if not 0 < self.alpha <= 1:
            raise ValueError("alpha must be in (0, 1]")
        if not 0 <= self.epsilon_end <= self.epsilon_start <= 1:
            raise ValueError("epsilon must satisfy 0 <= end <= start <= 1")
        if not isinstance(self.epsilon_decay_steps, int) or self.epsilon_decay_steps < 1:
            raise ValueError("epsilon_decay_steps must be >= 1")
        if isinstance(self.q_init, bool) or not isinstance(self.q_init, (int, float)) or not math.isfinite(self.q_init):
            raise ValueError("q_init must be finite")
        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise ValueError("seed must be an integer")
        if len(self.fallback_order) != N_OFFLOADING_ACTIONS or set(self.fallback_order) != set(ACTION_NAMES):
            raise ValueError("fallback_order must be a permutation of all nine v2 actions")


@dataclass(frozen=True)
class V2Decision:
    action_id: int
    action: str
    mode: str
    epsilon: float


class V2MaskedTabularAgent:
    def __init__(self, n_states: int, config: V2AgentConfig = V2AgentConfig()):
        if not isinstance(n_states, int) or isinstance(n_states, bool) or n_states < 1:
            raise ValueError("n_states must be a positive integer")
        self.n_states = n_states
        self.config = config
        self.q = [[float(config.q_init)] * N_OFFLOADING_ACTIONS for _ in range(n_states)]
        self.visits = [[0] * N_OFFLOADING_ACTIONS for _ in range(n_states)]
        self.rng = random.Random(config.seed)
        self.decisions = 0
        self.updates = 0
        self.frozen = False

    def _validate(self, state: int, allowed: Sequence[int]) -> tuple[int, ...]:
        if isinstance(state, bool) or not isinstance(state, int) or not 0 <= state < self.n_states:
            raise ValueError(f"state index {state!r} out of range")
        ids = set()
        for a in allowed:
            if isinstance(a, bool) or not isinstance(a, int) or not 0 <= a < N_OFFLOADING_ACTIONS:
                raise OffloadingModelError(f"invalid allowed action id: {a!r}")
            ids.add(a)
        if not ids:
            raise OffloadingModelError("action mask is empty")
        return tuple(sorted(ids))

    def epsilon(self) -> float:
        if self.frozen:
            return 0.0
        fraction = min(1.0, self.decisions / self.config.epsilon_decay_steps)
        return self.config.epsilon_start + (self.config.epsilon_end - self.config.epsilon_start) * fraction

    def select_action(self, state: int, allowed: Sequence[int]) -> V2Decision:
        mask = self._validate(state, allowed)
        if self.frozen:
            order = [ACTION_NAMES.index(n) for n in self.config.fallback_order if ACTION_NAMES.index(n) in mask]
            tried = [a for a in order if self.visits[state][a] > 0]
            if not tried:
                a, mode = order[0], "fallback"
            else:
                best = max(self.q[state][a] for a in tried)
                a, mode = next((a, "greedy") for a in tried if self.q[state][a] == best)
            return V2Decision(a, ACTION_NAMES[a], mode, 0.0)

        eps = self.epsilon()
        self.decisions += 1
        if self.rng.random() < eps:
            a, mode = self.rng.choice(mask), "explore"
        else:
            best = max(self.q[state][a] for a in mask)
            ties = [a for a in mask if self.q[state][a] == best]
            a, mode = (self.rng.choice(ties), "exploit")
        return V2Decision(a, ACTION_NAMES[a], mode, eps)

    def update(self, state: int, action_id: int, reward: float) -> float:
        if self.frozen:
            raise RuntimeError("v2 agent is frozen")
        self._validate(state, (action_id,))
        if isinstance(reward, bool) or not isinstance(reward, (int, float)) or not math.isfinite(reward):
            raise ValueError("reward must be finite")
        old = self.q[state][action_id]
        self.q[state][action_id] = old + self.config.alpha * (float(reward) - old)
        self.visits[state][action_id] += 1
        self.updates += 1
        return self.q[state][action_id]

    def freeze(self):
        self.frozen = True
