import pytest

from rl_model.actions import ACTION_NAMES, Action, action_id, action_name, normalize_mask


def test_mapping_is_explicit_and_stable():
    assert ACTION_NAMES == ("Local", "Edge", "Cloud")
    assert (Action.LOCAL, Action.EDGE, Action.CLOUD) == (0, 1, 2)
    assert [action_id(n) for n in ACTION_NAMES] == [0, 1, 2]
    assert [action_name(i) for i in range(3)] == list(ACTION_NAMES)


@pytest.mark.parametrize("bad", ["local", "GPU", None, 3, -1, True])
def test_invalid_actions(bad):
    with pytest.raises(ValueError):
        action_id(bad) if isinstance(bad, (str, type(None))) else action_name(bad)


def test_mask_normalisation():
    assert normalize_mask(None) == (0, 1, 2)
    assert normalize_mask(["Cloud", "Local"]) == (0, 2)
    assert normalize_mask([2, 1, 1]) == (1, 2)
    with pytest.raises(ValueError):
        normalize_mask([])
