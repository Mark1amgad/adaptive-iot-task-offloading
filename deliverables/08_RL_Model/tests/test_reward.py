import random

import pytest

from rl_model.config import ConfigError, CostTerm, RewardConfig
from rl_model.reward import RewardError, compute_reward


def rc(**kw):
    base = dict(w_latency=1.0, w_deadline=2.0, w_cost=0.5, latency_norm="fixed", latency_ref_ms=1000.0,
                latency_clip=1.0, failure_penalty=0.0,
                cost_terms=(CostTerm("bandwidth_bytes", 0.5, 1e6), CostTerm("energy_joules", 0.5, 10, required=False)))
    base.update(kw)
    return RewardConfig(**base)


def test_completed_met_exact_value():
    rb = compute_reward(rc(), failed=False, latency_ms=500, deadline_met=True,
                        resource_metrics={"bandwidth_bytes": 500000, "energy_joules": 5})
    # latency .5 ; miss 0 ; cost = (.5*.5 + .5*.5)/1 = .5  ->  -(0.5 + 0 + 0.25)
    assert rb.reward == pytest.approx(-0.75)
    assert (rb.latency_norm, rb.deadline_miss, rb.resource_cost) == (0.5, 0, 0.5)


def test_deadline_miss_and_clipping():
    rb = compute_reward(rc(), failed=False, latency_ms=5000, deadline_met=False,
                        resource_metrics={"bandwidth_bytes": 9e9, "energy_joules": 99})
    assert rb.latency_norm == 1.0 and rb.resource_cost == 1.0
    assert rb.reward == pytest.approx(-(1 + 2 + 0.5))


def test_failure_handling_and_penalty():
    rb = compute_reward(rc(failure_penalty=1.5), failed=True, latency_ms=None, deadline_met=False,
                        resource_metrics={})
    assert rb.failed and rb.deadline_miss == 1 and rb.latency_norm == 1.0
    assert rb.reward == pytest.approx(-(1 + 2 + 0 + 1.5))


def test_required_metric_missing_raises_for_completed_only():
    with pytest.raises(RewardError):
        compute_reward(rc(), failed=False, latency_ms=10, deadline_met=True, resource_metrics={})
    compute_reward(rc(), failed=True, latency_ms=None, deadline_met=False, resource_metrics={})


def test_optional_metric_missing_contributes_zero():
    rb = compute_reward(rc(), failed=False, latency_ms=0, deadline_met=True,
                        resource_metrics={"bandwidth_bytes": 1e6})
    assert rb.resource_cost == pytest.approx(0.5)


def test_deadline_normalisation_mode():
    rb = compute_reward(rc(latency_norm="deadline", latency_clip=2.0), failed=False, latency_ms=300,
                        deadline_met=True, resource_metrics={"bandwidth_bytes": 0}, deadline_ms=400)
    assert rb.latency_norm == pytest.approx(0.75)
    with pytest.raises(RewardError):
        compute_reward(rc(latency_norm="deadline"), failed=False, latency_ms=300, deadline_met=True,
                       resource_metrics={"bandwidth_bytes": 0})


@pytest.mark.parametrize("bad", [-1, float("nan"), float("inf"), True, "5"])
def test_invalid_latency(bad):
    with pytest.raises(RewardError):
        compute_reward(rc(), failed=False, latency_ms=bad, deadline_met=True,
                       resource_metrics={"bandwidth_bytes": 0})


def test_reward_always_within_documented_bounds():
    cfg, rng = rc(failure_penalty=0.7), random.Random(0)
    for _ in range(500):
        failed = rng.random() < 0.3
        rb = compute_reward(cfg, failed=failed, latency_ms=None if failed else rng.uniform(0, 5000),
                            deadline_met=False if failed else rng.random() < 0.5,
                            resource_metrics={"bandwidth_bytes": rng.uniform(0, 3e6),
                                              "energy_joules": rng.uniform(0, 30)})
        assert cfg.min_reward <= rb.reward <= 0.0


def test_config_validation():
    with pytest.raises(ConfigError):
        RewardConfig(w_cost=0.5, cost_terms=())
    with pytest.raises(ConfigError):
        RewardConfig(w_latency=-1, w_cost=0)
    with pytest.raises(ConfigError):
        RewardConfig(latency_norm="weird", w_cost=0)
