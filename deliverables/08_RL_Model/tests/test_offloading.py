import math
import pytest

from rl_model.offloading import (
    ACTION_NAMES, N_OFFLOADING_ACTIONS, CostInputs, OffloadingAction,
    OffloadingModelError, action_spec, estimate_completion_ms, legal_actions,
)


def test_action_catalogue_is_stable_and_complete():
    assert N_OFFLOADING_ACTIONS == 9
    assert ACTION_NAMES == (
        "LOCAL", "EDGE_PARTIAL_25", "EDGE_PARTIAL_50", "EDGE_PARTIAL_75",
        "EDGE_FULL", "CLOUD_PARTIAL_25", "CLOUD_PARTIAL_50",
        "CLOUD_PARTIAL_75", "CLOUD_FULL",
    )
    assert action_spec(OffloadingAction.EDGE_PARTIAL_50).remote_fraction == 0.5
    assert action_spec("CLOUD_PARTIAL_75").local_fraction == 0.25


def test_indivisible_tasks_never_receive_partial_actions():
    assert legal_actions(splittability="INDIVISIBLE", partition_model_id=None) == (0, 4, 8)


def test_divisible_task_gets_only_feasible_tier_actions():
    assert legal_actions(
        splittability="DATA_PARALLEL_DIVISIBLE",
        partition_model_id="frame-batch-v1",
        edge_available=False,
        cloud_available=True,
    ) == (0, 5, 6, 7, 8)


def test_missing_partition_model_disables_partial_actions():
    assert legal_actions(
        splittability="DATA_PARALLEL_DIVISIBLE",
        partition_model_id=None,
    ) == (0, 4, 8)


def test_no_feasible_action_is_rejected():
    with pytest.raises(OffloadingModelError, match="no feasible action"):
        legal_actions(splittability="INDIVISIBLE", partition_model_id=None,
                      local_available=False, edge_available=False, cloud_available=False)


def test_partial_cost_uses_parallel_max_plus_overheads():
    x = CostInputs(
        required_mi=1000, input_bytes=1_000_000, output_bytes=500_000,
        local_mips=1000, remote_mips=2000, uplink_mbps=10, downlink_mbps=20,
        uplink_latency_ms=5, downlink_latency_ms=2,
        partition_overhead_ms=3, merge_overhead_ms=4,
    )
    e = estimate_completion_ms("EDGE_PARTIAL_50", x,
                               splittability="DATA_PARALLEL_DIVISIBLE",
                               partition_model_id="frame-v1")
    assert e.local_branch_ms == pytest.approx(500.0)
    assert e.uplink_ms == pytest.approx(405.0)
    assert e.downlink_ms == pytest.approx(102.0)
    assert e.remote_branch_ms == pytest.approx(757.0)
    assert e.predicted_completion_ms == pytest.approx(764.0)


def test_full_remote_does_not_charge_partition_or_merge():
    x = CostInputs(1000, 1_000_000, 500_000, 1000, 2000, 10, 20,
                   partition_overhead_ms=99, merge_overhead_ms=99)
    e = estimate_completion_ms("EDGE_FULL", x)
    assert e.partition_ms == 0
    assert e.merge_ms == 0
    assert e.local_branch_ms == 0
    assert e.predicted_completion_ms == pytest.approx(e.remote_branch_ms)


@pytest.mark.parametrize("bad", [0, -1, math.inf, math.nan, True])
def test_invalid_resource_inputs_are_rejected(bad):
    x = CostInputs(1000, 100, 100, bad, 1000, 10, 10)
    with pytest.raises(OffloadingModelError):
        estimate_completion_ms("LOCAL", x)


def test_partial_estimation_requires_divisible_semantics():
    x = CostInputs(1000, 100, 100, 1000, 1000, 10, 10)
    with pytest.raises(OffloadingModelError, match="partial action requires"):
        estimate_completion_ms("EDGE_PARTIAL_25", x)


@pytest.mark.parametrize("bad", [1.0, 1.5, True, None, "edge_partial_50"])
def test_action_lookup_rejects_noncanonical_ids_and_names(bad):
    with pytest.raises(OffloadingModelError):
        action_spec(bad)


def test_partial_requires_local_execution_capability():
    assert legal_actions(
        splittability="DATA_PARALLEL_DIVISIBLE",
        partition_model_id="frame-v1",
        local_available=False,
        edge_available=True,
        cloud_available=True,
    ) == (4, 8)


def test_availability_flags_must_be_booleans():
    with pytest.raises(OffloadingModelError, match="edge_available must be a boolean"):
        legal_actions(splittability="INDIVISIBLE", partition_model_id=None,
                      edge_available=1)
