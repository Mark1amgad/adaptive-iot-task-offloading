import json
import random

import pytest

from conftest import make_agent_cfg
from rl_model.agent import FrozenAgentError, QLearningAgent
from rl_model.config import AgentConfig, ConfigError


def new_agent(space, **kw):
    return QLearningAgent(space, make_agent_cfg(**kw))


# ---------------------------------------------------------------- update arithmetic
def test_update_arithmetic_terminal(space):
    ag = new_agent(space, alpha=0.5)
    info = ag.update(3, 1, -2.0)                       # Q = 0 + .5*(-2-0)
    assert ag.q[3][1] == pytest.approx(-1.0)
    assert (info.old_q, info.target, info.td_error) == (0.0, -2.0, -2.0)
    ag.update(3, 1, -2.0)                              # Q = -1 + .5*(-2+1)
    assert ag.q[3][1] == pytest.approx(-1.5)
    assert ag.visits[3][1] == 2 and ag.updates == 2
    assert ag.q[3][0] == 0.0 and ag.q[4][1] == 0.0     # nothing else touched


def test_update_with_future_term(space):
    ag = new_agent(space, alpha=0.5, gamma=0.9, decision_model="sequential")
    ag.q[10] = [-1.0, -0.2, -3.0]
    ag.q[5][2] = -1.0
    info = ag.update(5, 2, -0.4, s_next=10, terminal=False)
    # target = -0.4 + 0.9*max(-1,-0.2,-3) = -0.58 ; Q = -1 + .5*(-0.58+1) = -0.79
    assert info.target == pytest.approx(-0.58) and info.bootstrapped
    assert ag.q[5][2] == pytest.approx(-0.79)


def test_future_term_respects_next_state_mask(space):
    ag = new_agent(space, alpha=1.0, gamma=0.5, decision_model="sequential")
    ag.q[10] = [-1.0, -0.2, -3.0]
    info = ag.update(5, 0, 0.0, s_next=10, terminal=False, next_available=["Local", "Cloud"])
    assert info.target == pytest.approx(0.5 * -1.0)       # Edge (-0.2) is masked out


def test_terminal_transition_omits_future_term(space):
    ag = new_agent(space, alpha=1.0, gamma=0.9, decision_model="sequential")
    ag.q[10] = [100.0, 100.0, 100.0]
    info = ag.update(5, 0, -1.0, s_next=10, terminal=True)
    assert info.target == -1.0 and not info.bootstrapped and ag.q[5][0] == -1.0


def test_nonterminal_requires_next_state(space):
    ag = new_agent(space, gamma=0.9, decision_model="sequential")
    with pytest.raises(ValueError):
        ag.update(0, 0, -1.0, terminal=False)


def test_contextual_bandit_never_bootstraps(space):
    ag = new_agent(space, alpha=1.0)
    ag.q[10] = [100.0] * 3
    ag.update(5, 0, -1.0, s_next=10, terminal=False)
    assert ag.q[5][0] == -1.0


def test_gamma_must_be_zero_for_bandit():
    with pytest.raises(ConfigError):
        AgentConfig(gamma=0.9, decision_model="contextual_bandit")


@pytest.mark.parametrize("args", [(-1, 0, -1.0), (54, 0, -1.0), (0, 3, -1.0), (0, -1, -1.0),
                                  (0, 0, float("nan")), (0, 0, float("inf")), (0, 0, True), (True, 0, -1.0)])
def test_update_validation(space, args):
    with pytest.raises(ValueError):
        new_agent(space).update(*args)


# -------------------------------------------------------------- exploration / greedy
def test_epsilon_schedule(space):
    ag = new_agent(space, epsilon_start=0.4, epsilon_end=0.1, epsilon_decay_steps=100)
    assert ag.epsilon() == pytest.approx(0.4)
    ag.decisions = 50
    assert ag.epsilon() == pytest.approx(0.25)
    ag.decisions = 10_000
    assert ag.epsilon() == pytest.approx(0.1)


def test_epsilon_one_always_explores_uniformly(space):
    ag = new_agent(space, epsilon_start=1.0, epsilon_end=1.0)
    ag.q[0] = [0.0, -9.0, -9.0]
    ds = [ag.select_action(0) for _ in range(3000)]
    assert all(d.mode == "explore" for d in ds)
    counts = [sum(d.action == a for d in ds) for a in range(3)]
    assert all(850 < c < 1150 for c in counts)


def test_epsilon_zero_always_exploits_best(space):
    ag = new_agent(space, epsilon_start=0.0, epsilon_end=0.0)
    ag.q[0] = [-3.0, -1.0, -2.0]
    assert {ag.select_action(0).action for _ in range(200)} == {1}


def test_exploit_ties_are_broken_randomly_in_training(space):
    ag = new_agent(space, epsilon_start=0.0, epsilon_end=0.0)
    assert {ag.select_action(0).action for _ in range(200)} == {0, 1, 2}


def test_mask_never_violated(space):
    ag = new_agent(space, epsilon_start=0.5, epsilon_end=0.5)
    ag.q[0] = [5.0, 0.0, 0.0]                              # masked Local is the best
    for _ in range(500):
        assert ag.select_action(0, ["Edge", "Cloud"]).action in (1, 2)
    ag.freeze()
    assert ag.select_action(0, ["Edge", "Cloud"]).action in (1, 2)
    with pytest.raises(ValueError):
        ag.select_action(0, [])


def test_epsilon_decays_with_training_decisions(space):
    ag = new_agent(space, epsilon_decay_steps=10)
    for _ in range(10):
        ag.select_action(0)
    assert ag.decisions == 10 and ag.epsilon() == pytest.approx(ag.cfg.epsilon_end)


# ------------------------------------------------------------------ frozen evaluation
def test_frozen_agent_is_greedy_deterministic_and_inert(space):
    ag = new_agent(space)
    ag.update(0, 2, -0.1)
    ag.update(0, 0, -5.0)
    ag.freeze()
    before = (json.dumps(ag.q), json.dumps(ag.visits), ag.decisions, ag.updates, ag.rng.getstate())
    ds = [ag.select_action(0) for _ in range(50)]
    assert {d.action for d in ds} == {2} and all(d.mode == "greedy" and d.epsilon == 0.0 for d in ds)
    assert before == (json.dumps(ag.q), json.dumps(ag.visits), ag.decisions, ag.updates, ag.rng.getstate())
    with pytest.raises(FrozenAgentError):
        ag.update(0, 1, -1.0)
    ag.unfreeze()
    ag.update(0, 1, -1.0)


def test_frozen_unvisited_state_uses_fallback_order_not_local(space):
    ag = new_agent(space, fallback_order=("Cloud", "Edge", "Local"))
    ag.freeze()
    d = ag.select_action(17)
    assert d.action == 2 and d.mode == "fallback"
    assert ag.select_action(17, ["Local", "Edge"]).action == 1


def test_frozen_tie_break_follows_fallback_order(space):
    ag = new_agent(space)                                   # default order Edge, Cloud, Local
    ag.update(4, 0, -1.0)
    ag.update(4, 1, -1.0)
    ag.freeze()
    assert ag.select_action(4).action == 1


def test_optimistic_init_forces_trying_all_actions(space):
    """All rewards are <= 0 and q_init=0, so untried actions look best until tried."""
    ag = new_agent(space, epsilon_start=0.0, epsilon_end=0.0)
    tried = set()
    for _ in range(3):
        a = ag.select_action(0).action
        tried.add(a)
        ag.update(0, a, -1.0)
    assert tried == {0, 1, 2}


# ----------------------------------------------------------------------- reproducibility
def _run(space, seed, n=300):
    ag = new_agent(space, seed=seed)
    env = random.Random(123)                               # synthetic environment (test only)
    for _ in range(n):
        s = env.randrange(space.n_states)
        d = ag.select_action(s)
        ag.update(s, d.action, -((s + 1) * (d.action + 1) % 7) / 7.0 - env.random() * 0.01)
    return ag


def test_same_seed_reproducible_different_seed_differs(space):
    a, b, c = _run(space, 5), _run(space, 5), _run(space, 6)
    assert a.q == b.q and a.visits == b.visits
    assert a.q != c.q
