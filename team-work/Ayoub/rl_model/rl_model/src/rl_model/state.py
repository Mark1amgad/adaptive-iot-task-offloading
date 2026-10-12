"""State discretisation, observation validation and encoding.

Only features available *before* the offloading decision may be part of the state.
Bin rule for thresholds t0<t1<...: bin = number of thresholds <= value, i.e.
[min,t0)->0, [t0,t1)->1, ..., [t_last,max]->len(thresholds).
"""
from __future__ import annotations

import math
from bisect import bisect_right
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from .config import FeatureConfig, fingerprint


class ObservationError(ValueError):
    """The observation is malformed or out of the declared range."""


class StateSpace:
    def __init__(self, features: Sequence[FeatureConfig]):
        self.all_features = tuple(features)
        self.features = tuple(f for f in features if f.enabled)
        if not self.features:
            raise ValueError("no enabled features")
        names = [f.name for f in self.all_features]
        if len(set(names)) != len(names):
            raise ValueError("duplicate feature names")
        self._radix = tuple(len(f.thresholds) + 1 for f in self.features)
        n = 1
        for r in self._radix:
            n *= r
        self.n_states = n

    # ---- validation -----------------------------------------------------
    @property
    def feature_names(self) -> Tuple[str, ...]:
        return tuple(f.name for f in self.features)

    def validate(self, values: Mapping[str, Any]) -> Dict[str, float]:
        if not isinstance(values, Mapping):
            raise ObservationError("features must be an object")
        disabled = {f.name for f in self.all_features if not f.enabled}
        unknown = set(values) - set(self.feature_names) - disabled
        if unknown:
            raise ObservationError(f"unknown feature(s): {sorted(unknown)} "
                                   f"(post-execution values must never be sent in an observation)")
        out: Dict[str, float] = {}
        for f in self.features:
            if f.name not in values:
                raise ObservationError(f"missing feature: {f.name}")
            v = values[f.name]
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                raise ObservationError(f"{f.name} must be a number, got {type(v).__name__}")
            if not math.isfinite(v):
                raise ObservationError(f"{f.name} must be finite")
            if v < f.min_value or (f.max_value is not None and v > f.max_value):
                rng = f"[{f.min_value}, {f.max_value if f.max_value is not None else 'inf'}]"
                raise ObservationError(f"{f.name}={v} outside valid range {rng} ({f.unit})")
            out[f.name] = float(v)
        return out

    # ---- encoding -------------------------------------------------------
    def bins(self, values: Mapping[str, Any]) -> Tuple[int, ...]:
        v = self.validate(values)
        return tuple(bisect_right(f.thresholds, v[f.name]) for f in self.features)

    def index_of_bins(self, bins: Sequence[int]) -> int:
        if len(bins) != len(self._radix):
            raise ValueError("wrong number of bins")
        idx = 0
        for b, r in zip(bins, self._radix):
            if not 0 <= b < r:
                raise ValueError(f"bin {b} out of range 0..{r - 1}")
            idx = idx * r + b
        return idx

    def encode(self, values: Mapping[str, Any]) -> int:
        return self.index_of_bins(self.bins(values))

    def decode(self, index: int) -> Tuple[int, ...]:
        if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < self.n_states:
            raise ValueError(f"state index {index!r} out of range 0..{self.n_states - 1}")
        out: List[int] = []
        for r in reversed(self._radix):
            index, b = divmod(index, r)
            out.append(b)
        return tuple(reversed(out))

    def describe(self, index: int) -> Dict[str, str]:
        return {f.name: f.labels[b] for f, b in zip(self.features, self.decode(index))}

    # ---- spec / compatibility ------------------------------------------
    def spec(self) -> Dict[str, Any]:
        return {"features": [f.spec() for f in self.features], "state_count": self.n_states}

    def fingerprint(self) -> str:
        return fingerprint(self.spec())

    def placeholder_features(self) -> List[str]:
        return [f.name for f in self.features if f.status == "placeholder"]
