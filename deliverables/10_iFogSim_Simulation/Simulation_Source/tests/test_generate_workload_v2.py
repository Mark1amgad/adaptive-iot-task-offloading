import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "generate_workload_v2.py"
SPEC = importlib.util.spec_from_file_location("workload_v2", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

def test_seed_replays_identical_workload():
    assert MODULE.generate(1234, 50, "mixed") == MODULE.generate(1234, 50, "mixed")

def test_different_seed_changes_workload():
    assert MODULE.generate(1234, 20, "mixed") != MODULE.generate(1235, 20, "mixed")

def test_mixed_profile_contains_both_task_classes_and_all_output_sizes():
    rows = MODULE.generate(42, 500, "mixed")
    assert {row["splittability"] for row in rows} == {"DATA_PARALLEL_DIVISIBLE", "INDIVISIBLE"}
    assert {row["output_bytes"] for row in rows} == set(MODULE.OUTPUT_CLASSES)
    assert {row["urgency_class"] for row in rows} == set(MODULE.URGENCY)

def test_workload_fields_and_constraints_are_consistent():
    rows = MODULE.generate(9, 100, "mixed")
    for i, row in enumerate(rows, 1):
        assert row["sequence"] == i
        assert 1000 <= row["task_mi"] <= 30000
        assert 1024 <= row["input_bytes"] <= 262144
        assert row["output_bytes"] in MODULE.OUTPUT_CLASSES
        assert row["deadline_ms"] > 0
        assert row["arrival_gap_ms"] == 0 if i == 1 else row["arrival_gap_ms"] > 0
        if row["splittability"] == "INDIVISIBLE":
            assert row["partition_model_id"] is None and row["merge_mi"] == 0
        else:
            assert row["partition_model_id"] == "data-parallel-v1" and row["merge_mi"] > 0

def test_profile_modes_force_expected_splittability():
    assert all(x["splittability"] == "DATA_PARALLEL_DIVISIBLE" for x in MODULE.generate(1, 10, "divisible"))
    assert all(x["splittability"] == "INDIVISIBLE" for x in MODULE.generate(1, 10, "indivisible"))

def test_invalid_profile_and_task_count_rejected():
    import pytest
    with pytest.raises(ValueError): MODULE.generate(1, 0, "mixed")
    with pytest.raises(ValueError): MODULE.generate(1, 2, "unknown")
