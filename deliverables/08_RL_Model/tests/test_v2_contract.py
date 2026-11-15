import json
import pytest

from rl_model.agent_v2 import V2AgentConfig, V2MaskedTabularAgent
from rl_model.offloading import ACTION_NAMES
from rl_model.persistence_v2 import V2CompatibilityError, load_v2_model, save_v2_model
from rl_model.protocol_v2 import (
    PROTOCOL_VERSION_V2, V2ProtocolError, action_message_v2,
    parse_action_v2, parse_observation_v2, parse_outcome_v2,
)
from rl_model.config import FeatureConfig
from rl_model.state import StateSpace

ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]


def v2_space():
    data = json.loads((ROOT / "config" / "v2.json").read_text())
    features = tuple(FeatureConfig.from_dict(item) for item in data["state"]["features"])
    return StateSpace(features)


def test_v2_config_has_controlled_state_cardinality():
    space = v2_space()
    assert space.n_states == 972
    assert set(space.feature_names) == {
        "task_mi", "wan_latency_ms", "local_utilization", "edge_utilization",
        "cloud_utilization", "deadline_ms", "splittability",
    }


def test_v2_agent_respects_mask_for_exploration_and_exploitation():
    agent = V2MaskedTabularAgent(4, V2AgentConfig(epsilon_start=1.0, epsilon_end=1.0, seed=9))
    for _ in range(100):
        assert agent.select_action(0, [0, 4, 8]).action_id in (0, 4, 8)
    agent.freeze()
    assert agent.select_action(0, [8, 4]).action == "EDGE_FULL"


def test_v2_action_response_roundtrips_and_carries_compound_semantics():
    msg = action_message_v2("task-7", 2, "v2-test", "exploit", 0.0)
    parsed = parse_action_v2(msg)
    assert parsed["action"] == "EDGE_PARTIAL_50"
    assert parsed["remote_tier"] == "EDGE"
    assert parsed["remote_fraction"] == 0.5
    assert parsed["local_fraction"] == 0.5


def test_v2_observation_requires_mask_and_valid_partial_constraints():
    valid = {
        "protocol_version": "2.0", "type": "observation", "task_id": "t1",
        "features": {"task_mi": 900, "splittability": 1},
        "available_actions": ["LOCAL", "EDGE_PARTIAL_25", "EDGE_PARTIAL_50", "EDGE_PARTIAL_75", "EDGE_FULL"],
        "task_constraints": {"splittability": "DATA_PARALLEL_DIVISIBLE",
                             "partition_model_id": "frames-v1", "local_available": True,
                             "edge_available": True, "cloud_available": False,
                             "partition_overhead_ms": 5, "merge_overhead_ms": 5},
    }
    assert parse_observation_v2(valid)["available_actions"] == (0, 1, 2, 3, 4)
    bad = dict(valid)
    bad["task_constraints"] = {"splittability": "INDIVISIBLE", "local_available": True,
                               "edge_available": True, "cloud_available": False}
    with pytest.raises(V2ProtocolError, match="disagrees"):
        parse_observation_v2(bad)


def test_v2_protocol_rejects_v1_and_inconsistent_action_semantics():
    with pytest.raises(V2ProtocolError, match="protocol v2.0 required"):
        parse_observation_v2({"protocol_version": "1.0"})
    msg = action_message_v2("t1", 1, "v2-test", "exploit", 0.0)
    msg["local_fraction"] = 0.9
    with pytest.raises(V2ProtocolError, match="local_fraction"):
        parse_action_v2(msg)


def test_v2_model_roundtrip_and_v1_rejection(tmp_path):
    space = v2_space()
    agent = V2MaskedTabularAgent(space.n_states, V2AgentConfig(seed=3))
    for _ in range(20):
        d = agent.select_action(0, [0, 4, 8])
        agent.update(0, d.action_id, -0.25)
    p = save_v2_model(agent, space.fingerprint(), tmp_path / "v2.json")
    loaded = load_v2_model(p, space.n_states, space.fingerprint(), V2AgentConfig(seed=3))
    assert loaded.q == agent.q and loaded.visits == agent.visits
    old = tmp_path / "v1.json"
    old.write_text(json.dumps({"format_version": 1, "kind": "tabular_q_learning",
                               "actions": ["Local", "Edge", "Cloud"]}))
    with pytest.raises(V2CompatibilityError, match="not a v2"):
        load_v2_model(old, space.n_states, space.fingerprint(), V2AgentConfig())


def test_v2_observation_rejects_mask_that_disagrees_with_availability():
    msg = {
        "protocol_version": "2.0", "type": "observation", "task_id": "t2",
        "features": {"task_mi": 1000},
        "available_actions": ["LOCAL", "EDGE_FULL", "CLOUD_FULL"],
        "task_constraints": {"splittability": "INDIVISIBLE", "local_available": True,
                              "edge_available": True, "cloud_available": False},
    }
    with pytest.raises(V2ProtocolError, match="do not match task feasibility"):
        parse_observation_v2(msg)


def test_v2_outcome_validates_terminal_execution_record():
    valid = {
        "protocol_version": "2.0", "type": "outcome", "task_id": "t1",
        "action_executed": "EDGE_PARTIAL_50", "status": "completed",
        "latency_ms": 120.0, "deadline_met": True,
        "resource_metrics": {"bandwidth_bytes": 1024, "energy_joules": 2.5},
    }
    parsed = parse_outcome_v2(valid)
    assert parsed["action_executed"] == 2 and parsed["latency_ms"] == 120.0
    bad = dict(valid)
    bad["latency_ms"] = -1
    with pytest.raises(V2ProtocolError, match="latency_ms"):
        parse_outcome_v2(bad)


def test_v2_outcome_failed_branch_cannot_claim_deadline_success():
    failed = {
        "protocol_version": "2.0", "type": "outcome", "task_id": "t1",
        "action_executed": "CLOUD_PARTIAL_25", "status": "failed",
        "deadline_met": True, "resource_metrics": {},
    }
    with pytest.raises(V2ProtocolError, match="deadline_met"):
        parse_outcome_v2(failed)


def test_v2_model_rejects_reward_fingerprint_mismatch(tmp_path):
    space = v2_space()
    agent = V2MaskedTabularAgent(space.n_states, V2AgentConfig(seed=4))
    p = save_v2_model(agent, space.fingerprint(), tmp_path / "reward-v2.json", "reward-A")
    with pytest.raises(V2CompatibilityError, match="reward specification"):
        load_v2_model(p, space.n_states, space.fingerprint(), V2AgentConfig(seed=4), "reward-B")


def test_v2_observation_rejects_splittability_feature_mismatch():
    msg = {
        "protocol_version": "2.0", "type": "observation", "task_id": "t3",
        "features": {"task_mi": 1000, "splittability": 0},
        "available_actions": ["LOCAL", "EDGE_PARTIAL_25", "EDGE_PARTIAL_50",
                              "EDGE_PARTIAL_75", "EDGE_FULL"],
        "task_constraints": {"splittability": "DATA_PARALLEL_DIVISIBLE",
                              "partition_model_id": "frames-v1", "local_available": True,
                              "edge_available": True, "cloud_available": False,
                              "partition_overhead_ms": 5, "merge_overhead_ms": 5},
    }
    with pytest.raises(V2ProtocolError, match="disagrees"):
        parse_observation_v2(msg)


def test_v2_model_rejects_agent_hyperparameter_mismatch(tmp_path):
    space = v2_space()
    trained_cfg = V2AgentConfig(seed=1)
    p = save_v2_model(V2MaskedTabularAgent(space.n_states, trained_cfg),
                      space.fingerprint(), tmp_path / "agent-v2.json")
    changed_cfg = V2AgentConfig(seed=2)
    with pytest.raises(V2CompatibilityError, match="agent configuration"):
        load_v2_model(p, space.n_states, space.fingerprint(), changed_cfg)


def test_v2_observation_json_schema_accepts_full_contract():
    import jsonschema

    schema = json.loads((ROOT / "schemas" / "observation.v2.schema.json").read_text())
    msg = {
        "protocol_version": "2.0", "type": "observation", "task_id": "t-schema",
        "features": {"task_mi": 1000, "wan_latency_ms": 30, "local_utilization": 0.2,
                     "edge_utilization": 0.3, "cloud_utilization": 0.4,
                     "deadline_ms": 600, "splittability": 1},
        "available_actions": ["LOCAL", "EDGE_PARTIAL_25", "EDGE_PARTIAL_50",
                              "EDGE_PARTIAL_75", "EDGE_FULL"],
        "task_constraints": {"splittability": "DATA_PARALLEL_DIVISIBLE",
                             "partition_model_id": "frames-v1", "local_available": True,
                             "edge_available": True, "cloud_available": False,
                             "partition_overhead_ms": 5, "merge_overhead_ms": 5},
    }
    jsonschema.validate(msg, schema, cls=jsonschema.Draft202012Validator)


def test_v2_outcome_schema_and_simulator_timestamp():
    import jsonschema

    schema = json.loads((ROOT / "schemas" / "outcome.v2.schema.json").read_text())
    msg = {
        "protocol_version": "2.0", "type": "outcome", "task_id": "t-schema",
        "action_executed": "CLOUD_FULL", "status": "completed",
        "latency_ms": 22.5, "deadline_met": True, "sim_time_ms": 150.0,
        "resource_metrics": {"bandwidth_bytes": 5000, "energy_joules": None},
    }
    jsonschema.validate(msg, schema, cls=jsonschema.Draft202012Validator)
    assert parse_outcome_v2(msg)["action_executed"] == 8
    msg["sim_time_ms"] = -1
    with pytest.raises(V2ProtocolError, match="sim_time_ms"):
        parse_outcome_v2(msg)
