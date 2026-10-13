import pytest

from offloading_rl.config import FeatureConfig
from offloading_rl.state import StateSpace

latency = FeatureConfig(
    name="latency", unit="ms", thresholds=(50, 150),
    labels=("Low", "Medium", "High"), min_value=0, max_value=300,
)
space = StateSpace((latency,))


def test_n_states():
    assert space.n_states == 3


def test_bins():
    assert space.to_state_id({"latency": 25}) == 0
    assert space.to_state_id({"latency": 100}) == 1
    assert space.to_state_id({"latency": 200}) == 2


def test_threshold_belongs_to_upper_bin():
    assert space.to_state_id({"latency": 50}) == 1
    assert space.to_state_id({"latency": 150}) == 2


def test_above_max_is_clamped_to_last_bin():
    assert space.to_state_id({"latency": 300}) == 2
    assert space.to_state_id({"latency": 450}) == 2


def test_invalid_values_still_rejected():
    for bad in (-1, float("nan"), float("inf"), True, "10"):
        with pytest.raises(ValueError):
            space.to_state_id({"latency": bad})
    with pytest.raises(ValueError):
        space.to_state_id({"wrong": 10})


def test_multi_feature_encoding_is_unique():
    load = FeatureConfig("load", "%", (30, 70), ("Low", "Mid", "High"), 0, 100)
    two = StateSpace((latency, load))
    assert two.n_states == 9
    ids = {two.to_state_id({"latency": l, "load": c})
           for l in (10, 100, 200) for c in (10, 50, 90)}
    assert ids == set(range(9))
