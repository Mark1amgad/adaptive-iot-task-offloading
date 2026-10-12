import json
import os
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest

from helpers import feats, hello, msg, obs, outcome, send
from rl_model.persistence import CompatibilityError
from rl_model.server import Session

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "config" / "default.json"


def mk(cfg, tmp_path, mode="train", **kw):
    return Session(cfg, mode, log_dir=str(tmp_path / "logs"), artifacts_dir=str(tmp_path / "art"), **kw)


def started(cfg, tmp_path, mode="train", phase="dev", **kw):
    s = mk(cfg, tmp_path, mode, **kw)
    ack = send(s, hello("r1", phase))[0]
    assert ack["type"] == "hello_ack", ack
    return s


def code(replies):
    assert len(replies) == 1 and replies[0]["type"] == "error", replies
    return replies[0]["code"]


# ------------------------------------------------------------------ handshake
def test_hello_ack_reports_spec_and_placeholders(cfg, tmp_path):
    ack = send(mk(cfg, tmp_path), hello())[0]
    assert ack["state_count"] == 54 and ack["actions"] == ["Local", "Edge", "Cloud"]
    assert ack["updates_enabled"] is True and set(ack["placeholder_features"]) == {"task_mi", "deadline_ms"}
    assert ack["decision_model"] == "contextual_bandit"


def test_messages_before_hello_rejected_ping_allowed(cfg, tmp_path):
    s = mk(cfg, tmp_path)
    assert code(send(s, obs())) == "handshake_required"
    assert code(send(s, outcome())) == "handshake_required"
    assert send(s, msg("ping"))[0]["type"] == "pong"


def test_duplicate_hello_and_unknown_type(cfg, tmp_path):
    s = started(cfg, tmp_path)
    assert code(send(s, hello())) == "duplicate_hello"
    assert code(send(s, msg("bogus"))) == "unknown_type"


def test_version_mismatch_fatal_sets_exit(cfg, tmp_path):
    s = mk(cfg, tmp_path)
    r = send(s, json.dumps({"protocol_version": "9.9", "type": "hello", "run_id": "x", "phase": "dev"}))
    assert r[0]["code"] == "protocol_version_mismatch" and r[0]["fatal"]
    assert s.should_exit and s.exit_code == 2


@pytest.mark.parametrize("mode,phase", [("train", "test"), ("eval", "train"), ("baseline", "train")])
def test_phase_mode_mismatch_is_fatal(cfg, tmp_path, mode, phase):
    kw = {}
    if mode == "eval":
        t = started(cfg, tmp_path / "t")
        send(t, msg("save"))
        kw["model_in"] = str(tmp_path / "t" / "art" / "model_latest.json")
    if mode == "baseline":
        kw["policy"] = "edge"
    s = mk(cfg, tmp_path / "x", mode, **kw)
    r = send(s, hello("r", phase))
    assert r[0]["code"] == "phase_mode_mismatch" and s.exit_code == 2


# --------------------------------------------------------------- train loop
def test_decision_then_outcome_updates_stored_state_action(cfg, tmp_path):
    s = started(cfg, tmp_path)
    a = send(s, obs("t1"))[0]
    assert a["type"] == "action" and a["action"] == ["Local", "Edge", "Cloud"][a["action_id"]]
    assert a["model_version"].startswith("q1-")
    state, aid = a["state_index"], a["action_id"]
    ack = send(s, outcome("t1", action=a["action"], latency=500.0, met=True,
                          rm={"bandwidth_bytes": 500000, "energy_joules": 5}))[0]
    # reward = -(1*0.5 + 2*0 + 0.5*0.5) = -0.75 ; alpha=0.1, q_init=0 -> Q = -0.075
    assert ack["type"] == "outcome_ack" and ack["updated"] and ack["reward"] == pytest.approx(-0.75)
    assert s.agent.q[state][aid] == pytest.approx(-0.075)
    assert s.agent.updates == 1 and s.pending == {}


def test_outcome_error_codes_and_pending_retained(cfg, tmp_path):
    s = started(cfg, tmp_path)
    assert code(send(s, outcome("ghost"))) == "unknown_task"
    a = send(s, obs("t1"))[0]
    assert code(send(s, obs("t1"))) == "duplicate_task"
    bad = json.loads(outcome("t1", action=a["action"]))
    del bad["resource_metrics"]["bandwidth_bytes"]                     # required cost metric missing
    assert code(send(s, json.dumps(bad))) == "invalid_outcome"
    assert "t1" in s.pending and s.agent.updates == 0                  # nothing learned from bad data
    assert send(s, outcome("t1", action=a["action"]))[0]["type"] == "outcome_ack"
    assert code(send(s, outcome("t1", action=a["action"]))) == "duplicate_outcome"


def test_failed_task_reward_and_update(cfg, tmp_path):
    s = started(cfg, tmp_path)
    a = send(s, obs("t1"))[0]
    ack = send(s, outcome("t1", action=a["action"], status="failed", latency=None, met=False,
                          rm={"bandwidth_bytes": 1000000, "energy_joules": 10},
                          failure_reason="node_down"))[0]
    assert ack["reward"] == pytest.approx(-(1 + 2 + 0.5 * 1.0))
    assert ack["updated"]


def test_action_override_trains_the_executed_action(cfg, tmp_path):
    s = started(cfg, tmp_path)
    a = send(s, obs("t1"))[0]
    other = next(n for n in ("Local", "Edge", "Cloud") if n != a["action"])
    send(s, outcome("t1", action=other))
    assert s.agent.visits[a["state_index"]][["Local", "Edge", "Cloud"].index(other)] == 1
    assert sum(map(sum, s.agent.visits)) == 1


def test_mask_respected_in_train_mode(cfg, tmp_path):
    s = started(cfg, tmp_path)
    for i in range(40):
        a = send(s, obs(f"t{i}", available_actions=["Edge"]))[0]
        assert a["action"] == "Edge"


def test_invalid_observation_leaves_no_state(cfg, tmp_path):
    s = started(cfg, tmp_path)
    assert code(send(s, obs("t1", features=feats(edge=7)))) == "invalid_observation"
    assert s.pending == {} and s.agent.decisions == 0


def test_malformed_line_does_not_kill_session(cfg, tmp_path):
    s = started(cfg, tmp_path)
    assert code(send(s, "{broken")) == "invalid_json"
    assert send(s, obs("t1"))[0]["type"] == "action"


def test_shutdown_saves_model_and_reports_orphans(cfg, tmp_path):
    s = started(cfg, tmp_path)
    send(s, obs("t1"))
    r = send(s, msg("shutdown"))[0]
    assert r["type"] == "shutdown_ack" and r["orphaned_tasks"] == 1 and s.should_exit
    assert Path(r["model_path"]).exists()


def test_eof_close_still_persists_model(cfg, tmp_path):
    s = started(cfg, tmp_path)
    a = send(s, obs("t1"))[0]
    send(s, outcome("t1", action=a["action"]))
    assert s.close() is not None and (tmp_path / "art" / "model_latest.json").exists()
    assert s.close() is None                                            # idempotent


def test_checkpointing_every_n_updates(cfg, raw_cfg, tmp_path):
    import dataclasses
    from rl_model.config import Config
    raw_cfg["agent"]["checkpoint_every"] = 2
    raw_cfg["agent"]["checkpoint_keep_last"] = 2
    c = Config.from_dict(raw_cfg)
    s = started(c, tmp_path)
    for i in range(7):
        a = send(s, obs(f"t{i}"))[0]
        send(s, outcome(f"t{i}", action=a["action"]))
    names = sorted(p.name for p in (tmp_path / "art" / "checkpoints").iterdir())
    assert names == ["checkpoint_0000000004.json", "checkpoint_0000000006.json"]


def test_run_log_records_real_fields_only(cfg, tmp_path):
    s = started(cfg, tmp_path)
    a = send(s, obs("t1"))[0]
    send(s, outcome("t1", action=a["action"]))
    s.close()
    recs = [json.loads(l) for l in (tmp_path / "logs" / "run_r1.jsonl").read_text().splitlines()]
    assert [r["record"] for r in recs] == ["run_start", "task", "run_end"]
    assert recs[0]["policy"] == "qlearning" and recs[0]["updates_enabled"] is True
    assert recs[1]["observation"] == feats() and recs[1]["outcome"]["latency_ms"] == 200.0
    assert "latency_ms" not in recs[1]["observation"]                  # no outcome leakage into observation
    events = (tmp_path / "logs" / "events_r1.jsonl").read_text()
    assert "decision" in events and "placeholder_thresholds" in events


# --------------------------------------------------------------- eval / baselines
def _trained_model(cfg, tmp_path):
    s = started(cfg, tmp_path / "train")
    for i in range(30):
        a = send(s, obs(f"t{i}"))[0]
        send(s, outcome(f"t{i}", action=a["action"], latency=100.0 + 300 * a["action_id"]))
    send(s, msg("shutdown"))
    return str(tmp_path / "train" / "art" / "model_latest.json")


def test_eval_mode_is_frozen_and_never_updates(cfg, tmp_path):
    model = _trained_model(cfg, tmp_path)
    before = Path(model).read_text()
    s = started(cfg, tmp_path / "ev", "eval", "test", model_in=model)
    q_before, upd_before = json.dumps(s.agent.q), s.agent.updates
    for i in range(10):
        a = send(s, obs(f"e{i}"))[0]
        assert a["mode"] in ("greedy", "fallback") and a["epsilon"] == 0.0
        ack = send(s, outcome(f"e{i}", action=a["action"]))[0]
        assert ack["updated"] is False
    assert json.dumps(s.agent.q) == q_before and s.agent.updates == upd_before > 0
    assert code(send(s, msg("save"))) == "not_allowed"
    send(s, msg("shutdown"))
    assert Path(model).read_text() == before                            # model file untouched


def test_eval_requires_model_and_checks_compat(cfg, raw_cfg, tmp_path):
    from rl_model.config import Config
    with pytest.raises(ValueError, match="requires --model-in"):
        mk(cfg, tmp_path, "eval")
    model = _trained_model(cfg, tmp_path)
    raw_cfg["state"]["features"][0]["thresholds"] = [10, 20]
    with pytest.raises(CompatibilityError):
        mk(Config.from_dict(raw_cfg), tmp_path / "z", "eval", model_in=model)


@pytest.mark.parametrize("policy,expected", [("local", "Local"), ("edge", "Edge"), ("cloud", "Cloud")])
def test_fixed_baselines(cfg, tmp_path, policy, expected):
    s = started(cfg, tmp_path, "baseline", "test", policy=policy)
    for i in range(5):
        a = send(s, obs(f"t{i}"))[0]
        assert a["action"] == expected and a["mode"] == "baseline"
        assert send(s, outcome(f"t{i}", action=expected))[0]["updated"] is False
    assert s.agent.updates == 0


def test_random_baseline_covers_all_actions_and_respects_mask(cfg, tmp_path):
    s = started(cfg, tmp_path, "baseline", "test", policy="random")
    got = {send(s, obs(f"t{i}"))[0]["action"] for i in range(60)}
    assert got == {"Local", "Edge", "Cloud"}
    for i in range(30):
        assert send(s, obs(f"m{i}", available_actions=["Local", "Cloud"]))[0]["action"] != "Edge"


def test_baseline_requires_policy(cfg, tmp_path):
    with pytest.raises(ValueError):
        mk(cfg, tmp_path, "baseline")


def test_same_seed_same_session_transcript(cfg, tmp_path):
    def run(d):
        s = started(cfg, tmp_path / d, seed=11)
        out = []
        for i in range(60):
            a = send(s, obs(f"t{i}", features=feats(task_mi=500 + 97 * i, edge=(i % 10) / 10)))[0]
            out.append(a["action"])
            send(s, outcome(f"t{i}", action=a["action"], latency=50.0 + 40 * a["action_id"] + i))
        return out, s.agent.q
    assert run("a") == run("b")


# ------------------------------------------- real subprocess: protocol integration test
def _spawn(args, cwd):
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    return subprocess.Popen([sys.executable, "-m", "rl_model.server", "--config", str(CFG), *args],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, cwd=cwd, env=env)


def _rpc(p, line):
    p.stdin.write(line + "\n")
    p.stdin.flush()
    out = p.stdout.readline()
    assert out.endswith("\n") and out.count("\n") == 1
    return json.loads(out)


def test_protocol_integration_over_stdio(tmp_path):
    """Persistent process, framing, schema conformance, error recovery, lifecycle, eval reload.
    Java is not involved: this uses scripted JSON lines. The iFogSim end-to-end test is separate."""
    sch = {n: json.loads((ROOT / "schemas" / f"{n}.schema.json").read_text()) for n in ("action",)}
    p = _spawn(["--mode", "train", "--log-dir", "logs", "--artifacts-dir", "art", "--seed", "3"], tmp_path)
    try:
        assert _rpc(p, hello("it1", "train"))["type"] == "hello_ack"
        assert _rpc(p, "{garbage")["code"] == "invalid_json"                   # survives bad input
        for i in range(25):
            a = _rpc(p, obs(f"t{i}", features=feats(task_mi=300 * i + 50, edge=(i % 5) / 5)))
            jsonschema.validate(a, sch["action"], cls=jsonschema.Draft202012Validator)
            assert a["task_id"] == f"t{i}"
            ack = _rpc(p, outcome(f"t{i}", action=a["action"], latency=100.0 + 200 * a["action_id"]))
            assert ack["type"] == "outcome_ack" and ack["updated"]
        assert _rpc(p, msg("save"))["type"] == "saved"
        sd = _rpc(p, msg("shutdown"))
        assert sd["type"] == "shutdown_ack" and sd["orphaned_tasks"] == 0 and sd["tasks_reported"] == 25
        assert p.wait(timeout=10) == 0
    finally:
        p.kill()
    assert (tmp_path / "art" / "model_latest.json").exists()
    assert (tmp_path / "logs" / "run_it1.jsonl").exists()

    ev = _spawn(["--mode", "eval", "--model-in", "art/model_latest.json", "--log-dir", "logs",
                 "--artifacts-dir", "art"], tmp_path)
    try:
        assert _rpc(ev, hello("it1-eval", "test", 99))["updates_enabled"] is False
        a = _rpc(ev, obs("e1"))
        assert a["mode"] in ("greedy", "fallback")
        assert _rpc(ev, outcome("e1", action=a["action"]))["updated"] is False
        _rpc(ev, msg("shutdown"))
        assert ev.wait(timeout=10) == 0
    finally:
        ev.kill()


def test_eof_without_shutdown_persists_and_exits_zero(tmp_path):
    p = _spawn(["--mode", "train", "--log-dir", "logs", "--artifacts-dir", "art"], tmp_path)
    _rpc(p, hello("eof1", "dev"))
    p.stdin.close()
    assert p.wait(timeout=10) == 0
    assert (tmp_path / "art" / "model_latest.json").exists()
    p.stdout.close(); p.stderr.close()


def test_startup_failure_reports_error_line(tmp_path):
    p = _spawn(["--mode", "eval", "--model-in", "does_not_exist.json"], tmp_path)
    out, _ = p.communicate(timeout=10)
    assert p.returncode == 2 and json.loads(out)["code"] == "startup_failed"
