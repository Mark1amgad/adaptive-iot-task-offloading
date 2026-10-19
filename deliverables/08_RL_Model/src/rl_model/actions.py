"""Explicit action mapping and action-mask helpers."""
from __future__ import annotations

from enum import IntEnum
from typing import Iterable, Optional, Tuple


class Action(IntEnum):
    LOCAL = 0
    EDGE = 1
    CLOUD = 2


ACTION_NAMES: Tuple[str, ...] = ("Local", "Edge", "Cloud")
N_ACTIONS = len(ACTION_NAMES)
_NAME_TO_ID = {n: i for i, n in enumerate(ACTION_NAMES)}


def action_name(action_id: int) -> str:
    if not isinstance(action_id, int) or isinstance(action_id, bool) or not 0 <= action_id < N_ACTIONS:
        raise ValueError(f"invalid action id: {action_id!r}")
    return ACTION_NAMES[action_id]


def action_id(name: str) -> int:
    try:
        return _NAME_TO_ID[name]
    except (KeyError, TypeError):
        raise ValueError(f"invalid action name: {name!r}; expected one of {ACTION_NAMES}") from None


def normalize_mask(available: Optional[Iterable]) -> Tuple[int, ...]:
    """Return a sorted tuple of allowed action ids. ``None`` means all actions.

    Accepts action names or ids. An empty mask is an error (the agent could not act).
    """
    if available is None:
        return tuple(range(N_ACTIONS))
    ids = set()
    for a in available:
        if isinstance(a, str):
            ids.add(action_id(a))
        else:
            action_name(a)  # validates range/type
            ids.add(int(a))
    if not ids:
        raise ValueError("action mask is empty: at least one action must be available")
    return tuple(sorted(ids))
