import itertools

import pytest

from helpers import feats
from rl_model.config import ConfigError, FeatureConfig
from rl_model.state import ObservationError, StateSpace


def test_exact_state_count_is_derived_from_config(space):
    assert space.n_states == 3 * 3 * 3 * 2 == 54
    assert space.feature_names == ("task_mi", "wan_latency_ms", "edge_utilization", "deadline_ms")


def test_optional_feature_changes_count(raw_cfg):
    from rl_model.config import Config
    raw_cfg["state"]["features"][-1]["enabled"] = True
    assert StateSpace(Config.from_dict(raw_cfg).features).n_states == 162


@pytest.mark.parametrize("name,value,expected_bin", [
    ("task_mi", 0, 0), ("task_mi", 999.99, 0), ("task_mi", 1000, 1), ("task_mi", 3999.99, 1),
    ("task_mi", 4000, 2), ("task_mi", 1e9, 2),
    ("wan_latency_ms", 19.99, 0), ("wan_latency_ms", 20, 1), ("wan_latency_ms", 79.99, 1),
    ("wan_latency_ms", 80, 2),
    ("edge_utilization", 0.0, 0), ("edge_utilization", 0.3999, 0), ("edge_utilization", 0.4, 1),
    ("edge_utilization", 0.7999, 1), ("edge_utilization", 0.8, 2), ("edge_utilization", 1.0, 2),
    ("deadline_ms", 499.9, 0), ("deadline_ms", 500, 1),
])
def test_threshold_boundaries(space, name, value, expected_bin):
    f = feats()
    f[name] = value
    pos = space.feature_names.index(name)
    assert space.bins(f)[pos] == expected_bin


def test_encode_decode_roundtrip_and_product_order(space):
    radices = [3, 3, 3, 2]
    seen = set()
    for i, b in enumerate(itertools.product(*[range(r) for r in radices])):
        assert space.index_of_bins(b) == i
        assert space.decode(i) == b
        seen.add(i)
    assert len(seen) == 54


def test_describe_uses_labels(space):
    assert space.describe(0) == {"task_mi": "small", "wan_latency_ms": "low",
                                 "edge_utilization": "low", "deadline_ms": "tight"}


@pytest.mark.parametrize("bad", [
    {"edge_utilization": 1.01}, {"edge_utilization": -0.1}, {"task_mi": -1}, {"wan_latency_ms": float("nan")},
    {"deadline_ms": float("inf")}, {"task_mi": "100"}, {"task_mi": True}, {"task_mi": None},
])
def test_invalid_values_rejected(space, bad):
    f = feats()
    f.update(bad)
    with pytest.raises(ObservationError):
        space.encode(f)


def test_missing_and_unknown_features_rejected(space):
    f = feats()
    del f["task_mi"]
    with pytest.raises(ObservationError, match="missing"):
        space.encode(f)
    with pytest.raises(ObservationError, match="unknown"):
        space.encode({**feats(), "latency_ms": 123})          # post-execution value must not leak in


def test_disabled_feature_value_is_ignored(space):
    assert space.encode({**feats(), "device_utilization": 0.5}) == space.encode(feats())


def test_decode_out_of_range(space):
    for bad in (-1, 54, True):
        with pytest.raises(ValueError):
            space.decode(bad)


def test_feature_config_validation():
    with pytest.raises(ConfigError):
        FeatureConfig("x", "u", (5, 5), ("a", "b", "c"))
    with pytest.raises(ConfigError):
        FeatureConfig("x", "u", (5, 10), ("a", "b"))
    with pytest.raises(ConfigError):
        FeatureConfig("x", "u", (0.5,), ("a", "b"), min_value=0, max_value=0.5)


def test_fingerprint_changes_with_thresholds(cfg, raw_cfg):
    from rl_model.config import Config
    raw_cfg["state"]["features"][0]["thresholds"] = [1000, 5000]
    other = StateSpace(Config.from_dict(raw_cfg).features)
    assert other.fingerprint() != StateSpace(cfg.features).fingerprint()
