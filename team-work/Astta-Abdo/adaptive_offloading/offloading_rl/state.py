
from __future__ import annotations

import math
from typing import Mapping, Sequence

from .config import FeatureConfig


class StateSpace:
    def __init__(self, features: Sequence[FeatureConfig]) -> None:
        active = tuple(
            feature for feature in features
            if feature.enabled
        )

        if not active:
            raise ValueError(
                "At least one enabled feature is required"
            )

        names = tuple(feature.name for feature in active)

        if len(set(names)) != len(names):
            raise ValueError("Feature names must be unique")

        self.features = active

        self.radices = tuple(
            len(feature.labels)
            for feature in active
        )

        self.n_states = math.prod(self.radices)

    def discretize(
        self,
        raw_state: Mapping[str, float],
    ) -> tuple[int, ...]:

        expected = {
            feature.name for feature in self.features
        }
        provided = set(raw_state)

        if expected != provided:
            raise ValueError(
                f"State features mismatch. "
                f"Expected: {expected}, got: {provided}"
            )

        bins = []

        for feature in self.features:
            value = raw_state[feature.name]

            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                raise ValueError(
                    f"{feature.name} must be a finite number"
                )

            if value < feature.min_value:
                raise ValueError(
                    f"{feature.name} is below min_value"
                )

            # Values above max_value (e.g. latency spikes under
            # congestion) are clamped into the last bin instead of
            # crashing the simulation.
            if (
                feature.max_value is not None
                and value > feature.max_value
            ):
                value = feature.max_value

            bin_index = sum(
                value >= threshold
                for threshold in feature.thresholds
            )

            bins.append(bin_index)

        return tuple(bins)

    def encode(
        self,
        bins: Sequence[int],
    ) -> int:
        if len(bins) != len(self.radices):
            raise ValueError(
                "Number of bins does not match number of features"
            )

        state_id = 0

        for bin_index, radix in zip(bins, self.radices):
            if (
                isinstance(bin_index, bool)
                or not isinstance(bin_index, int)
                or not 0 <= bin_index < radix
            ):
                raise ValueError(
                    f"Invalid bin index: {bin_index}"
                )

            state_id = state_id * radix + bin_index

        return state_id

    def to_state_id(
        self,
        raw_state: Mapping[str, float],
    ) -> int:
        bins = self.discretize(raw_state)
        return self.encode(bins)
