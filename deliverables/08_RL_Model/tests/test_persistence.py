import copy
import json

import pytest

from conftest import make_agent_cfg
from rl_model.agent import QLearningAgent
from rl_model.config import Config, CostTerm, RewardConfig
from rl_model.persistence import (CompatibilityError, latest_checkpoint, load_model, save_checkpoint,
                                  save_model)
from rl_model.state import StateSpace


def trained(space, n=50, seed=3):
    ag = QLearningAgent(space, make_agent_cfg(seed=seed))
    for i in range(n):
        s = i % space.n_states
        d = ag.select_action(s)
        ag.update(s, d.action, -((i * 7) % 5) / 5)
    return ag


def test_roundtrip_is_exact(space, cfg, tmp_path):
    ag = trained(space)
    p = save_model(ag, cfg.reward, tmp_path / "m.json")
    ag2 = load_model(p, space, ag.cfg, cfg.reward)
    assert ag2.q == ag.q and ag2.visits == ag.visits
    assert (ag2.decisions, ag2.updates) == (ag.decisions, ag.updates)
    assert ag2.rng.getstate() == ag.rng.getstate()


def test_resume_equals_uninterrupted_run(space, cfg, tmp_path):
    def steps(ag, lo, hi):
        for i in range(lo, hi):
            s = i % space.n_states
            d = ag.select_action(s)
            ag.update(s, d.action, -((i * 7) % 5) / 5)
    full = QLearningAgent(space, make_agent_cfg(seed=9))
    steps(full, 0, 200)
    part = QLearningAgent(space, make_agent_cfg(seed=9))
    steps(part, 0, 100)
    p = save_model(part, cfg.reward, tmp_path / "m.json")
    resumed = load_model(p, space, part.cfg, cfg.reward)
    steps(resumed, 100, 200)
    assert resumed.q == full.q and resumed.visits == full.visits


def _edit(path, fn):
    d = json.loads(path.read_text())
    fn(d)
    path.write_text(json.dumps(d))


@pytest.mark.parametrize("edit,match", [
    (lambda d: d.update(format_version=99), "format_version"),
    (lambda d: d.update(kind="other"), "not a tabular"),
    (lambda d: d.update(actions=["Local", "Edge"]), "action set"),
    (lambda d: d.update(state_fingerprint="deadbeef"), "state specification"),
    (lambda d: d.update(q=d["q"][:-1]), "wrong shape"),
    (lambda d: d["q"][0].pop(), "wrong shape"),
    (lambda d: d["visits"][0].__setitem__(0, "x"), "non-finite/non-numeric"),
    (lambda d: d.pop("counters"), "corrupt"),
])
def test_incompatible_files_rejected(space, cfg, tmp_path, edit, match):
    p = save_model(trained(space), cfg.reward, tmp_path / "m.json")
    _edit(p, edit)
    with pytest.raises(CompatibilityError, match=match):
        load_model(p, space, make_agent_cfg(), cfg.reward)


def test_nan_in_file_rejected(space, cfg, tmp_path):
    p = save_model(trained(space), cfg.reward, tmp_path / "m.json")
    d = json.loads(p.read_text())
    d["q"][0][0] = float("nan")
    p.write_text(json.dumps(d))                                        # writes the token NaN; json.load accepts it
    with pytest.raises(CompatibilityError):
        load_model(p, space, make_agent_cfg(), cfg.reward)


def test_unreadable_file(space, cfg, tmp_path):
    (tmp_path / "bad.json").write_text("{not json")
    with pytest.raises(CompatibilityError):
        load_model(tmp_path / "bad.json", space, make_agent_cfg(), cfg.reward)
    with pytest.raises(CompatibilityError):
        load_model(tmp_path / "missing.json", space, make_agent_cfg(), cfg.reward)


def test_different_state_space_rejected(space, cfg, raw_cfg, tmp_path):
    p = save_model(trained(space), cfg.reward, tmp_path / "m.json")
    raw_cfg["state"]["features"][2]["thresholds"] = [0.5, 0.9]
    other = Config.from_dict(raw_cfg)
    with pytest.raises(CompatibilityError, match="state specification"):
        load_model(p, StateSpace(other.features), other.agent, other.reward)


def test_reward_mismatch_requires_explicit_opt_in(space, cfg, tmp_path):
    p = save_model(trained(space), cfg.reward, tmp_path / "m.json")
    other = RewardConfig(w_latency=3.0, cost_terms=cfg.reward.cost_terms)
    with pytest.raises(CompatibilityError, match="reward"):
        load_model(p, space, make_agent_cfg(), other)
    assert load_model(p, space, make_agent_cfg(), other, allow_reward_mismatch=True).q


def test_json_has_no_nonstandard_tokens(space, cfg, tmp_path):
    p = save_model(trained(space), cfg.reward, tmp_path / "m.json")
    json.loads(p.read_text(), parse_constant=lambda c: pytest.fail(f"non-standard token {c}"))
    assert not list(tmp_path.glob("*.tmp"))


def test_checkpoint_naming_pruning_and_latest(space, cfg, tmp_path):
    ag = QLearningAgent(space, make_agent_cfg())
    for i in range(5):
        ag.update(0, 0, -1.0)
        save_checkpoint(ag, cfg.reward, tmp_path, keep_last=2)
    names = sorted(p.name for p in tmp_path.iterdir())
    assert names == ["checkpoint_0000000004.json", "checkpoint_0000000005.json"]
    assert latest_checkpoint(tmp_path).name == "checkpoint_0000000005.json"
    assert latest_checkpoint(tmp_path / "nope") is None
