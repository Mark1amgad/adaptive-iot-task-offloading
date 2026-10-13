from __future__ import annotations

from typing import Iterable

ACTION_NAMES = ("Local", "Edge", "Cloud")
ACTION_ID = {name.lower(): idx for idx, name in enumerate(ACTION_NAMES)}
N_ACTIONS = len(ACTION_NAMES)


def action_id(name: str) -> int:
    """Return the action index for a name (case-insensitive)."""
    if not isinstance(name, str):
        raise ValueError("Action name must be a string")
    key = name.strip().lower()
    if key not in ACTION_ID:
        raise ValueError(f"Unknown action: {name!r}")
    return ACTION_ID[key]


def allowed_actions(
    availability: Iterable[bool] | None = None,
) -> tuple[int, ...]:
    """Return the indices of the actions that can be chosen.

    availability: one bool per action, e.g. (True, False, True) means
    Edge is unavailable. None means every action is allowed.
    """
    if availability is None:
        return tuple(range(N_ACTIONS))

    mask = tuple(availability)

    if len(mask) != N_ACTIONS:
        raise ValueError(f"Mask length must equal N_ACTIONS ({N_ACTIONS})")

    if any(not isinstance(flag, bool) for flag in mask):
        raise ValueError("Mask values must be True or False")

    allowed = tuple(i for i, flag in enumerate(mask) if flag)

    if not allowed:
        raise ValueError("At least one action must be available")

    return allowed
