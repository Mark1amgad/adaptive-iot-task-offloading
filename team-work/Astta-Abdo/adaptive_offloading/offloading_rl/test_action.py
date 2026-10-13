import pytest

from offloading_rl.action import (
    ACTION_ID, ACTION_NAMES, N_ACTIONS, action_id, allowed_actions,
)


def test_action_constants():
    assert ACTION_NAMES == ("Local", "Edge", "Cloud")
    assert ACTION_ID == {"local": 0, "edge": 1, "cloud": 2}
    assert N_ACTIONS == 3


def test_action_id_is_case_insensitive():
    assert action_id("Local") == 0
    assert action_id("edge") == 1
    assert action_id("CLOUD") == 2


@pytest.mark.parametrize("bad", ["fog", "", 1, None])
def test_action_id_rejects_bad_values(bad):
    with pytest.raises(ValueError):
        action_id(bad)


def test_allowed_actions():
    assert allowed_actions() == (0, 1, 2)
    assert allowed_actions([True, False, True]) == (0, 2)


@pytest.mark.parametrize(
    "bad", [[True, True], [1, 0, 1], [False, False, False]]
)
def test_allowed_actions_rejects_bad_masks(bad):
    with pytest.raises(ValueError):
        allowed_actions(bad)
