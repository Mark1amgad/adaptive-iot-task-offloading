import json
from pathlib import Path

import jsonschema
import pytest

from helpers import feats, hello, msg, obs, outcome
from rl_model.protocol import (ProtocolError, parse_hello, parse_line, parse_observation, parse_outcome)

ROOT = Path(__file__).resolve().parents[1]


def schema(name):
    return json.loads((ROOT / "schemas" / f"{name}.schema.json").read_text())


def example(name):
    return json.loads((ROOT / "examples" / f"{name}.json").read_text())


# ----------------------------------------------------- schemas vs shipped examples
@pytest.mark.parametrize("sch,ex", [("observation", "observation"), ("action", "action"),
                                     ("outcome", "outcome_completed"), ("outcome", "outcome_failed")])
def test_examples_validate_against_schemas(sch, ex):
    jsonschema.validate(example(ex), schema(sch), cls=jsonschema.Draft202012Validator)


def test_examples_are_accepted_by_the_python_parsers(space):
    o = parse_observation(example("observation"), space)
    assert o.task_id == "t-000123" and 0 <= o.state_index < 54
    assert parse_outcome(example("outcome_completed"), space).latency_ms == 212.4
    f = parse_outcome(example("outcome_failed"), space)
    assert f.failed and f.latency_ms is None


def test_session_example_file_replays_without_errors(cfg, tmp_path):
    from rl_model.server import Session
    s = Session(cfg, "train", log_dir=str(tmp_path / "l"), artifacts_dir=str(tmp_path / "a"))
    for line in (ROOT / "examples" / "session.jsonl").read_text().splitlines():
        for r in s.handle_line(line):
            assert json.loads(r)["type"] != "error", r


@pytest.mark.parametrize("mutate", [
    lambda m: m.update(extra=1), lambda m: m["features"].update(edge_utilization=2),
    lambda m: m.pop("task_id"), lambda m: m.update(protocol_version="2.0"),
])
def test_observation_schema_rejects_bad(mutate):
    m = example("observation")
    mutate(m)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(m, schema("observation"), cls=jsonschema.Draft202012Validator)


def test_outcome_schema_rejects_inconsistent():
    for mutate in (lambda m: m.pop("latency_ms"), lambda m: m.update(status="failed", deadline_met=True)):
        m = example("outcome_completed")
        mutate(m)
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(m, schema("outcome"), cls=jsonschema.Draft202012Validator)


# ------------------------------------------------------------------- framing / JSON
@pytest.mark.parametrize("line,code", [("{not json", "invalid_json"), ("[1,2]", "invalid_message"),
                                       ('{"a": NaN}', "invalid_json"), ('{"a": Infinity}', "invalid_json"),
                                       ("x" * 1_000_001, "line_too_long")])
def test_parse_line_errors(line, code):
    with pytest.raises(ProtocolError) as e:
        parse_line(line)
    assert e.value.code == code


# ---------------------------------------------------------------- observation rules
def _obs(**kw):
    return json.loads(obs(**kw))


@pytest.mark.parametrize("mutate,code", [
    (lambda m: m.update(task_id=""), "invalid_message"),
    (lambda m: m.update(task_id=5), "invalid_message"),
    (lambda m: m.update(latency_ms=3), "invalid_message"),                    # outcome field at top level
    (lambda m: m["features"].update(latency_ms=3), "invalid_observation"),     # outcome field inside features
    (lambda m: m["features"].update(task_mi="big"), "invalid_observation"),
    (lambda m: m["features"].pop("wan_latency_ms"), "invalid_observation"),
    (lambda m: m.update(available_actions=[]), "invalid_observation"),
    (lambda m: m.update(available_actions=["GPU"]), "invalid_observation"),
    (lambda m: m.update(sim_time_ms=-1), "invalid_message"),
    (lambda m: m.update(protocol_version="0.9"), "protocol_version_mismatch"),
])
def test_observation_rejections(space, mutate, code):
    m = _obs()
    mutate(m)
    with pytest.raises(ProtocolError) as e:
        parse_observation(m, space)
    assert e.value.code == code


def test_version_mismatch_is_fatal(space):
    m = _obs()
    m["protocol_version"] = "9"
    with pytest.raises(ProtocolError) as e:
        parse_observation(m, space)
    assert e.value.fatal


def test_available_actions_accepts_names_and_ids(space):
    assert parse_observation(_obs(available_actions=["Cloud", 0]), space).available == (0, 2)


# ------------------------------------------------------------------ outcome rules
def _out(**kw):
    return json.loads(outcome(**kw))


@pytest.mark.parametrize("mutate", [
    lambda m: m.update(status="weird"), lambda m: m.update(action_executed="GPU"),
    lambda m: m.update(deadline_met="yes"), lambda m: m.pop("latency_ms"),
    lambda m: m.update(latency_ms=-5), lambda m: m.update(latency_ms=True),
    lambda m: m.update(status="failed", deadline_met=True),
    lambda m: m.update(failure_reason="x"),                                    # reason on a completed task
    lambda m: m.update(resource_metrics=[1]), lambda m: m["resource_metrics"].update(bandwidth_bytes=-1),
    lambda m: m["resource_metrics"].update(executing_node_utilization=1.5),
    lambda m: m.update(terminal="no"),
    lambda m: m.update(next_observation={"features": feats()}),                # terminal defaults to true
    lambda m: m.update(unknown=1),
])
def test_outcome_rejections(space, mutate):
    m = _out()
    mutate(m)
    with pytest.raises(ProtocolError) as e:
        parse_outcome(m, space)
    assert e.value.code in ("invalid_outcome", "invalid_message")


def test_failed_outcome_may_omit_latency_and_nulls_are_dropped(space):
    m = _out(status="failed", latency=None, met=False, rm={"bandwidth_bytes": None, "energy_joules": 2})
    o = parse_outcome(m, space)
    assert o.failed and o.latency_ms is None and o.resource_metrics == {"energy_joules": 2.0}


def test_nonterminal_outcome_carries_validated_next_observation(space):
    m = _out(terminal=False, next_observation={"features": feats(task_mi=5000), "available_actions": ["Edge"]})
    o = parse_outcome(m, space)
    assert not o.terminal and o.next_available == (1,) and 0 <= o.next_state_index < 54
    m["next_observation"]["features"]["edge_utilization"] = 3
    with pytest.raises(ProtocolError):
        parse_outcome(m, space)


def test_hello_validation():
    assert parse_hello(json.loads(hello("run_1", "train", 5))).sim_seed == 5
    for bad in ({"run_id": "a b"}, {"run_id": "../x"}, {"phase": "prod"}, {"sim_seed": 1.5}):
        m = json.loads(hello())
        m.update(bad)
        with pytest.raises(ProtocolError):
            parse_hello(m)
