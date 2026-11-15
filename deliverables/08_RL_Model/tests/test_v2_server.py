import json

import pytest

from rl_model.config_v2 import V2RuntimeConfig
from rl_model.protocol_v2 import PROTOCOL_VERSION_V2
from rl_model.server_v2 import V2Session

ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]


def make_session(tmp_path, mode="train", policy=None, model_in=None):
    cfg = V2RuntimeConfig.load(ROOT / "config" / "v2.json")
    return V2Session(cfg, mode, policy, model_in, str(tmp_path / "model_v2.json"))


def send(session, obj):
    return json.loads(session.handle_line(json.dumps(obj)))


def hello(phase="train"):
    return {"protocol_version": "2.0", "type": "hello", "run_id": "v2-run", "phase": phase}


def observation(task_id="task-1"):
    return {
        "protocol_version": "2.0", "type": "observation", "task_id": task_id,
        "features": {"task_mi": 900, "wan_latency_ms": 25, "local_utilization": 0.2,
                     "edge_utilization": 0.3, "cloud_utilization": 0.4,
                     "deadline_ms": 600, "splittability": 1},
        "available_actions": ["LOCAL", "EDGE_PARTIAL_25", "EDGE_PARTIAL_50",
                              "EDGE_PARTIAL_75", "EDGE_FULL"],
        "task_constraints": {"splittability": "DATA_PARALLEL_DIVISIBLE",
                             "partition_model_id": "frames-v1", "local_available": True,
                             "edge_available": True, "cloud_available": False,
                             "partition_overhead_ms": 5, "merge_overhead_ms": 5},
    }


def outcome(task_id, action):
    return {
        "protocol_version": "2.0", "type": "outcome", "task_id": task_id,
        "action_executed": action, "status": "completed", "latency_ms": 120,
        "deadline_met": True,
        "resource_metrics": {"bandwidth_bytes": 1200, "energy_joules": 1.0},
    }


def test_v2_session_handshake_action_outcome_and_persistence(tmp_path):
    s = make_session(tmp_path)
    ack = send(s, hello())
    assert ack["type"] == "hello_ack" and ack["protocol_version"] == "2.0"
    assert ack["state_count"] == 972 and len(ack["actions"]) == 9
    decision = send(s, observation())
    assert decision["type"] == "action"
    assert decision["action_id"] in (0, 1, 2, 3, 4)
    assert len(decision["q_values"]) == 9
    result = send(s, outcome("task-1", decision["action"]))
    assert result["type"] == "outcome_ack" and result["updated"]
    assert result["update_count"] == 1
    saved = send(s, {"protocol_version": "2.0", "type": "save"})
    assert saved["type"] == "saved"
    assert (tmp_path / "model_v2.json").exists()


def test_v2_server_rejects_wrong_protocol_and_illegal_executed_action(tmp_path):
    s = make_session(tmp_path)
    wrong = send(s, {"protocol_version": "1.0", "type": "hello"})
    assert wrong["code"] == "protocol_version_mismatch" and wrong["fatal"]
    s = make_session(tmp_path / "other")
    send(s, hello())
    decision = send(s, observation())
    illegal = send(s, outcome("task-1", "CLOUD_FULL"))
    assert illegal["type"] == "error" and illegal["code"] == "invalid_outcome"
    assert "task-1" in s.pending


def test_v2_baseline_never_silently_uses_unavailable_action(tmp_path):
    s = make_session(tmp_path, mode="baseline", policy="cloud")
    send(s, hello("test"))
    result = send(s, observation())
    assert result["type"] == "error" and result["code"] == "baseline_unavailable"

@pytest.mark.parametrize("action_id,action_name", [
    (0, "local"), (1, "edge_partial_25"), (2, "edge_partial_50"),
    (3, "edge_partial_75"), (4, "edge_full"),
    (5, "cloud_partial_25"), (6, "cloud_partial_50"),
    (7, "cloud_partial_75"), (8, "cloud_full"),
])
def test_v2_exact_action_baseline_selects_each_catalogue_action(tmp_path, action_id, action_name):
    s = make_session(tmp_path, mode="baseline", policy=action_name)
    send(s, hello("test"))
    obs = observation()
    obs["available_actions"] = list(range(9))
    obs["task_constraints"]["cloud_available"] = True
    decision = send(s, obs)
    assert decision["type"] == "action"
    assert decision["action_id"] == action_id
    assert decision["action"] == action_name.upper()
    ack = send(s, outcome("task-1", action_id))
    assert ack["type"] == "outcome_ack" and not ack["updated"]
    assert s.pending == {}


def test_v2_failed_outcome_reconciles_pending_task_without_success_metrics(tmp_path):
    s = make_session(tmp_path, mode="baseline", policy="edge_partial_50")
    send(s, hello("test"))
    obs = observation()
    obs["available_actions"] = list(range(9))
    obs["task_constraints"]["cloud_available"] = True
    decision = send(s, obs)
    failed = send(s, {
        "protocol_version": "2.0", "type": "outcome", "task_id": "task-1",
        "action_executed": decision["action_id"], "status": "failed",
        "deadline_met": False, "failure_reason": "missing_remote_branch",
        "resource_metrics": {"bandwidth_bytes": 6000},
    })
    assert failed["type"] == "outcome_ack"
    assert failed["updated"] is False
    assert s.pending == {}


def test_v2_train_model_reloads_in_frozen_eval_mode(tmp_path):
    s = make_session(tmp_path)
    send(s, hello())
    d = send(s, observation())
    send(s, outcome("task-1", d["action"]))
    send(s, {"protocol_version": "2.0", "type": "shutdown"})
    model = tmp_path / "model_v2.json"
    assert model.exists()

    ev = make_session(tmp_path / "eval", mode="eval", model_in=str(model))
    send(ev, hello("test"))
    d2 = send(ev, observation("eval-1"))
    ack = send(ev, outcome("eval-1", d2["action"]))
    assert ack["updated"] is False and ack["update_count"] == 1


def test_v2_server_subprocess_stdio_smoke(tmp_path):
    import os
    import subprocess
    import sys

    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    p = subprocess.Popen(
        [sys.executable, "-m", "rl_model.server_v2", "--mode", "train",
         "--config", str(ROOT / "config" / "v2.json"),
         "--model-out", str(tmp_path / "model.json")],
        cwd=tmp_path, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True,
    )
    try:
        p.stdin.write(json.dumps(hello()) + "\n")
        p.stdin.flush()
        ack = json.loads(p.stdout.readline())
        assert ack["type"] == "hello_ack"
        p.stdin.write(json.dumps({"protocol_version": "2.0", "type": "shutdown"}) + "\n")
        p.stdin.flush()
        assert json.loads(p.stdout.readline())["type"] == "shutdown_ack"
        assert p.wait(timeout=10) == 0
    finally:
        p.kill()


def test_v2_action_message_conforms_to_json_schema(tmp_path):
    import jsonschema

    s = make_session(tmp_path)
    send(s, hello())
    decision = send(s, observation())
    schema = json.loads((ROOT / "schemas" / "action.v2.schema.json").read_text())
    jsonschema.validate(decision, schema, cls=jsonschema.Draft202012Validator)
