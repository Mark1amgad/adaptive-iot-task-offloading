"""Tabular Q-Learning agent with epsilon-greedy training and frozen greedy evaluation.

Update (standard Q-learning):
    Q(s,a) += alpha * ( r + gamma * max_{a' in allowed(s')} Q(s',a') - Q(s,a) )
and for terminal transitions the future term is omitted:
    Q(s,a) += alpha * ( r - Q(s,a) )
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from .actions import ACTION_NAMES, N_ACTIONS, action_id, normalize_mask
from .config import AgentConfig
from .state import StateSpace


class FrozenAgentError(RuntimeError):
    """Raised when an update is attempted on a frozen (evaluation) agent."""


@dataclass(frozen=True)
class Decision:
    action: int
    mode: str          # explore | exploit | greedy | fallback
    epsilon: float


@dataclass(frozen=True)
class UpdateInfo:
    old_q: float
    target: float
    td_error: float
    new_q: float
    bootstrapped: bool


class QLearningAgent:
    def __init__(self, space: StateSpace, cfg: AgentConfig):
        self.space = space
        self.cfg = cfg
        n = space.n_states
        self.q: List[List[float]] = [[cfg.q_init] * N_ACTIONS for _ in range(n)]
        self.visits: List[List[int]] = [[0] * N_ACTIONS for _ in range(n)]
        self.rng = random.Random(cfg.seed)
        self.decisions = 0     # epsilon-greedy decisions taken in training mode
        self.updates = 0
        self.frozen = False

    # ---- exploration schedule -----------------------------------------
    def epsilon(self) -> float:
        if self.frozen:
            return 0.0
        c = self.cfg
        frac = min(1.0, self.decisions / c.epsilon_decay_steps)
        return c.epsilon_start + (c.epsilon_end - c.epsilon_start) * frac

    def freeze(self) -> None:
        self.frozen = True

    def unfreeze(self) -> None:
        self.frozen = False

    # ---- action selection ---------------------------------------------
    def _check_state(self, s: int) -> None:
        if isinstance(s, bool) or not isinstance(s, int) or not 0 <= s < self.space.n_states:
            raise ValueError(f"state index {s!r} out of range")

    def greedy_deterministic(self, s: int, allowed: Sequence[int]) -> Tuple[int, str]:
        """Deterministic greedy action. Unvisited states use the configured fallback order
        (otherwise an all-equal row would silently pick action 0 = Local)."""
        order = [action_id(n) for n in self.cfg.fallback_order if action_id(n) in allowed]
        row = self.q[s]
        # Only actions with real training data are candidates: with q_init=0 and rewards <= 0 an
        # untried action's Q would look optimistically best (an artefact, not an estimate).
        tried = [a for a in order if self.visits[s][a] > 0]
        if not tried:
            return order[0], "fallback"
        best = max(row[a] for a in tried)
        for a in tried:                    # first in fallback order among the ties
            if row[a] == best:
                return a, "greedy"
        raise AssertionError("unreachable")

    def select_action(self, s: int, available=None) -> Decision:
        self._check_state(s)
        allowed = normalize_mask(available)
        if self.frozen:
            a, mode = self.greedy_deterministic(s, allowed)
            return Decision(a, mode, 0.0)
        eps = self.epsilon()
        self.decisions += 1
        if self.rng.random() < eps:
            return Decision(self.rng.choice(allowed), "explore", eps)
        row = self.q[s]
        best = max(row[a] for a in allowed)
        ties = [a for a in allowed if row[a] == best]
        return Decision(self.rng.choice(ties) if len(ties) > 1 else ties[0], "exploit", eps)

    def random_action(self, available=None) -> int:
        """Uniform random allowed action (data-collection baseline)."""
        return self.rng.choice(normalize_mask(available))

    # ---- learning -------------------------------------------------------
    def update(self, s: int, a: int, reward: float, s_next: Optional[int] = None,
               terminal: bool = True, next_available=None) -> UpdateInfo:
        if self.frozen:
            raise FrozenAgentError("agent is frozen; updates are disabled in evaluation")
        self._check_state(s)
        if isinstance(a, bool) or not isinstance(a, int) or not 0 <= a < N_ACTIONS:
            raise ValueError(f"invalid action id {a!r}")
        if isinstance(reward, bool) or not isinstance(reward, (int, float)) or not math.isfinite(reward):
            raise ValueError(f"reward must be finite, got {reward!r}")
        bootstrap = (not terminal) and self.cfg.gamma > 0.0
        future = 0.0
        if bootstrap:
            if s_next is None:
                raise ValueError("non-terminal transition requires s_next")
            self._check_state(s_next)
            allowed = normalize_mask(next_available)
            future = self.cfg.gamma * max(self.q[s_next][x] for x in allowed)
        old = self.q[s][a]
        target = reward + future
        td = target - old
        self.q[s][a] = old + self.cfg.alpha * td
        self.visits[s][a] += 1
        self.updates += 1
        return UpdateInfo(old, target, td, self.q[s][a], bootstrap)

    # ---- introspection ---------------------------------------------------
    def greedy_policy_table(self) -> List[str]:
        out = []
        for s in range(self.space.n_states):
            a, _ = self.greedy_deterministic(s, tuple(range(N_ACTIONS)))
            out.append(ACTION_NAMES[a])
        return out

    def model_version(self) -> str:
        return f"q1-{self.space.fingerprint()[:8]}-u{self.updates}"
