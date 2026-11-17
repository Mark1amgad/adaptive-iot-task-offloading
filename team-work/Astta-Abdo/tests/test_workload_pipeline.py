from __future__ import annotations

import csv
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import generate_workloads as gen  # noqa: E402
import validate_dataset as val  # noqa: E402


@pytest.fixture
def configs():
    return gen.load_yaml(ROOT / "configs/workload_profiles.yaml"), gen.load_yaml(ROOT / "configs/scenario_profiles.yaml")


@pytest.fixture
def generated(tmp_path, configs):
    workload_cfg, scenario_cfg = configs
    return gen.generate_one("stable_steady", 1300, 80, "stable_steady-seed-01300", workload_cfg, scenario_cfg, tmp_path)


def rows_for(path: Path):
    return val.read_csv(path)


def write_bad(tmp_path: Path, name: str, fields, rows):
    path = tmp_path / name
    gen.write_csv(path, fields, rows)
    return path


def test_deterministic_replay_hashes_and_validator(generated, configs):
    task_path, manifest_path, expected = generated
    workload_cfg, scenario_cfg = configs
    replay_tasks, replay_manifest, actual = gen.generate_one(
        "stable_steady", 1300, 80, "stable_steady-seed-01300", workload_cfg, scenario_cfg,
        task_path.parent / "replay"
    )
    assert actual == expected
    assert task_path.read_bytes() == replay_tasks.read_bytes()
    assert manifest_path.read_bytes() == replay_manifest.read_bytes()
    assert val.validate_replay(task_path, manifest_path,
                               ROOT / "configs/workload_profiles.yaml",
                               ROOT / "configs/scenario_profiles.yaml") == []


def test_all_principal_scenarios_generate_in_registered_development_split(tmp_path, configs):
    workload_cfg, scenario_cfg = configs
    scenario_ids = [k for k, v in scenario_cfg["scenarios"].items()
                    if not k.endswith("_optional") and not v["status"].startswith("BLOCKED")]
    assert len(scenario_ids) == 8
    for scenario_id in scenario_ids:
        task_path, manifest_path, _ = gen.generate_one(
            scenario_id, 1300, 48, f"{scenario_id}-s01300", workload_cfg, scenario_cfg,
            tmp_path / scenario_id, "development"
        )
        _, task_rows = val.read_csv(task_path)
        _, manifest_rows = val.read_csv(manifest_path)
        assert not val.validate_tasks(task_path)
        assert not val.validate_manifest(manifest_path, task_rows)
        assert manifest_rows[0]["dataset_split"] == "development"
        assert manifest_rows[0]["seed"] == "1300"


def test_seed_registry_rejects_cross_split_reuse():
    rows = [
        {"seed": "777", "experiment_family": "dev", "split": "development", "status": "allocated", "source": "test"},
        {"seed": "777", "experiment_family": "heldout", "split": "test", "status": "approved", "source": "test"},
    ]
    assert any("cross-split seed reuse" in error for error in gen.validate_seed_registry_rows(rows))


def test_historical_seed_81_is_not_eligible_for_final_test():
    registry = gen.read_seed_registry()
    row = next(item for item in registry if item["seed"] == "81")
    assert row["split"] == "development"
    assert row["status"] == "retired"
    errors = gen.validate_seed_allocation(81, "test", registry)
    assert errors and any("registered for development" in error for error in errors)


def test_no_final_test_seed_is_approved_yet():
    registry = gen.read_seed_registry()
    assert not any(row["split"] == "test" and row["status"] == "approved" for row in registry)


def test_deadlines_are_positive_predecision_and_profile_urgency_based(generated):
    task_path, manifest_path, _ = generated
    _, rows = val.read_csv(task_path)
    for row in rows:
        assert row["urgency_class"] in {"CRITICAL", "TIME_SENSITIVE", "DELAY_TOLERANT"}
        assert int(row["relative_deadline_ms"]) > 0
        assert int(row["absolute_deadline_ms"]) == int(row["arrival_time_ms"]) + int(row["relative_deadline_ms"])
    assert not any("action" in key or "outcome" in key for key in rows[0])


def test_both_divisibility_classes_and_declared_partition_rules(generated):
    task_path, _, _ = generated
    _, rows = val.read_csv(task_path)
    assert {row["splittability"] for row in rows} == {"INDIVISIBLE", "DATA_PARALLEL_DIVISIBLE"}
    for row in rows:
        if row["splittability"] == "DATA_PARALLEL_DIVISIBLE":
            assert row["partition_model_id"]
            assert row["input_partition_model"] == "PROPORTIONAL_TO_COMPUTE_ALPHA"
            assert row["output_partition_model"] == "PROPORTIONAL_TO_COMPUTE_ALPHA"
            assert float(row["partition_overhead_ms"]) >= 0
            assert float(row["merge_overhead_ms"]) >= 0
        else:
            assert all(row[field] == "" for field in (
                "partition_model_id", "partition_overhead_ms", "merge_overhead_ms",
                "input_partition_model", "output_partition_model"))


def test_task_mix_shift_really_contains_heavier_profile_mix(tmp_path, configs):
    wc, sc = configs
    task_path, manifest_path, _ = gen.generate_one(
        "task_size_compute_shift", 1300, 300, "task-size-shift-1300", wc, sc, tmp_path
    )
    _, rows = val.read_csv(task_path)
    _, manifest = val.read_csv(manifest_path)
    profiles = {r["application_profile"] for r in rows}
    assert "VISUAL_INSPECTION_BULK_FRAME_BATCH" in profiles
    assert "PRODUCTION_MONITORING_LARGE_AGGREGATION" in profiles
    assert json.loads(manifest[0]["regime_timeline_json"])[1]["policy_observation"] is False


def test_aba_scenario_manifest_is_a_b_a(tmp_path, configs):
    wc, sc = configs
    _, manifest_path, _ = gen.generate_one(
        "repeated_a_b_a", 1300, 120, "repeated-aba-1300", wc, sc, tmp_path
    )
    _, rows = val.read_csv(manifest_path)
    regimes = json.loads(rows[0]["regime_timeline_json"])
    assert [r["regime_id"] for r in regimes] == ["A", "B", "A"]
    assert all(r["policy_observation"] is False for r in regimes)


def test_duplicate_task_id_fails(tmp_path, generated):
    task_path, _, _ = generated
    fields, rows = rows_for(task_path)
    rows.append(dict(rows[0]))
    bad = write_bad(tmp_path, "duplicate.csv", fields, rows)
    assert any("duplicate task_id" in error for error in val.validate_tasks(bad)[0])


@pytest.mark.parametrize("field,value,fragment", [
    ("urgency_class", "URGENT", "unknown urgency"),
    ("splittability", "SOMETIMES", "unknown splittability"),
    ("relative_deadline_ms", "0", "must be > 0"),
    ("absolute_deadline_ms", "", "missing or non-numeric"),
    ("arrival_time_ms", "-1", "must be >= 0"),
    ("input_size_bytes", "1.5", "integer-valued"),
    ("required_mi", "NaN", "must be finite"),
    ("units_version", "ms-ish", "inconsistent units_version"),
])
def test_bad_task_values_fail(tmp_path, generated, field, value, fragment):
    task_path, _, _ = generated
    fields, rows = rows_for(task_path)
    rows[0][field] = value
    bad = write_bad(tmp_path, f"bad-{field}.csv", fields, rows)
    assert any(fragment in error for error in val.validate_tasks(bad)[0])


def test_absolute_deadline_mismatch_fails(tmp_path, generated):
    task_path, _, _ = generated
    fields, rows = rows_for(task_path)
    rows[0]["absolute_deadline_ms"] = str(int(rows[0]["absolute_deadline_ms"]) + 1)
    bad = write_bad(tmp_path, "bad-deadline.csv", fields, rows)
    assert any("absolute_deadline_ms !=" in error for error in val.validate_tasks(bad)[0])


def test_divisible_missing_partition_or_overhead_fails(tmp_path, generated):
    task_path, _, _ = generated
    fields, rows = rows_for(task_path)
    row = next(r for r in rows if r["splittability"] == "DATA_PARALLEL_DIVISIBLE")
    row["partition_model_id"] = ""
    row["merge_overhead_ms"] = "-0.5"
    bad = write_bad(tmp_path, "missing-partition.csv", fields, rows)
    errors = val.validate_tasks(bad)[0]
    assert any("missing partition_model_id" in error for error in errors)
    assert any("merge_overhead_ms must be >= 0" in error for error in errors)


def test_indivisible_partition_fields_must_be_null(tmp_path, generated):
    task_path, _, _ = generated
    fields, rows = rows_for(task_path)
    row = next(r for r in rows if r["splittability"] == "INDIVISIBLE")
    row["partition_model_id"] = "fake-partition"
    bad = write_bad(tmp_path, "bad-indivisible.csv", fields, rows)
    assert any("indivisible task must have null partition_model_id" in error
               for error in val.validate_tasks(bad)[0])


def _decision_row(task, action, alpha, local, tier, local_site, remote_site):
    return {
        "run_id": task["run_id"], "task_id": task["task_id"], "policy_id": "test-policy",
        "decision_time_ms": "0", "requested_action": action, "offload_fraction": str(alpha),
        "local_fraction": str(local), "remote_tier": tier or "",
        "partition_model_id": task["partition_model_id"],
        "selected_local_site_id": local_site or "", "selected_remote_site_id": remote_site or "",
        "feasible_action_set_json": json.dumps([action]), "selected_action_feasible": "true",
        "fallback_used": "false", "fallback_reason": "", "decision_wall_clock_ms": "0.1",
        "model_version": "schema-test-v1",
    }


def test_indivisible_partial_action_is_rejected(tmp_path, generated):
    task_path, _, _ = generated
    _, tasks = rows_for(task_path)
    task = next(r for r in tasks if r["splittability"] == "INDIVISIBLE")
    decision = _decision_row(task, "EDGE_PARTIAL_25", 0.25, 0.75, "EDGE", "local", "edge")
    path = write_bad(tmp_path, "partial-indivisible.csv", list(decision), [decision])
    assert any("indivisible task offered" in e for e in val.validate_decisions(path, tasks))


def test_valid_partial_action_and_invalid_fraction_or_two_remote_tiers(tmp_path, generated):
    task_path, _, _ = generated
    _, tasks = rows_for(task_path)
    task = next(r for r in tasks if r["splittability"] == "DATA_PARALLEL_DIVISIBLE")
    good = _decision_row(task, "EDGE_PARTIAL_25", 0.25, 0.75, "EDGE", "local", "edge-01")
    good_path = write_bad(tmp_path, "good-partial.csv", list(good), [good])
    assert val.validate_decisions(good_path, tasks) == []
    bad = dict(good, offload_fraction="0.3", local_fraction="0.7", remote_tier="EDGE,CLOUD",
               selected_remote_site_id="edge-01,cloud-01")
    bad_path = write_bad(tmp_path, "bad-partial.csv", list(bad), [bad])
    errors = val.validate_decisions(bad_path, tasks)
    assert any("invalid offload fraction" in e or "action name/fraction mismatch" in e for e in errors)
    assert any("exactly one EDGE remote tier" in e for e in errors)


def test_fallback_reason_required(tmp_path, generated):
    task_path, _, _ = generated
    _, tasks = rows_for(task_path)
    task = next(r for r in tasks if r["splittability"] == "INDIVISIBLE")
    row = _decision_row(task, "LOCAL", 0, 1, None, "iot-01", None)
    row["fallback_used"] = "true"
    path = write_bad(tmp_path, "missing-fallback-reason.csv", list(row), [row])
    assert any("requires fallback_reason" in e for e in val.validate_decisions(path, tasks))


def test_context_future_outcome_regime_and_scenario_leakage_fails(tmp_path, generated):
    task_path, _, _ = generated
    _, tasks = rows_for(task_path)
    fields = ["run_id", "task_id", "candidate_action", "actual_completion_time_ms", "regime_label"]
    row = {"run_id": tasks[0]["run_id"], "task_id": tasks[0]["task_id"],
           "candidate_action": "LOCAL", "actual_completion_time_ms": "10", "regime_label": "B"}
    path = write_bad(tmp_path, "leaky-context.csv", fields, [row])
    errors = val.validate_contexts(path, tasks)
    assert any("leakage" in e for e in errors)


def test_nested_context_leakage_fails(tmp_path, generated):
    task_path, _, _ = generated
    _, tasks = rows_for(task_path)
    fields = ["run_id", "task_id", "extra_json"]
    row = {"run_id": tasks[0]["run_id"], "task_id": tasks[0]["task_id"],
           "extra_json": json.dumps({"model": {"future_regime_id": "B"}})}
    path = write_bad(tmp_path, "nested-leaky-context.csv", fields, [row])
    assert any("leakage" in e for e in val.validate_contexts(path, tasks))


def test_identical_paired_policy_inputs_pass(tmp_path, generated):
    task_path, _, _ = generated
    twin = tmp_path / "paired-identical.csv"
    shutil.copy(task_path, twin)
    assert val.validate_paired_inputs([task_path, twin]) == []


def test_paired_policy_input_mismatch_fails(tmp_path, generated):
    task_path, _, _ = generated
    duplicate = tmp_path / "paired-different.csv"
    shutil.copy(task_path, duplicate)
    fields, rows = rows_for(duplicate)
    rows[0]["input_size_bytes"] = str(int(rows[0]["input_size_bytes"]) + 1)
    gen.write_csv(duplicate, fields, rows)
    assert val.validate_paired_inputs([task_path, duplicate])


def test_manifest_cannot_mark_regime_as_policy_observation(tmp_path, generated):
    _, manifest_path, _ = generated
    _, rows = rows_for(manifest_path)
    fields, _ = rows_for(manifest_path)
    timeline = json.loads(rows[0]["regime_timeline_json"])
    timeline[0]["policy_observation"] = True
    rows[0]["regime_timeline_json"] = json.dumps(timeline)
    bad = write_bad(tmp_path, "leaky-manifest.csv", fields, rows)
    assert any("evaluation-only" in e for e in val.validate_manifest(bad, rows_for_generated(generated)))


def rows_for_generated(generated):
    return rows_for(generated[0])[1]


def test_outcome_reconciliation_works_and_orphan_missing_duplicate_fail(tmp_path, generated):
    task_path, _, _ = generated
    _, tasks = rows_for(task_path)
    fields = [
        "run_id", "task_id", "policy_id", "arrival_time_ms", "observed_until_ms",
        "action_type", "offload_fraction", "local_fraction", "remote_tier", "full_execution_site_id", "local_execution_site_id", "remote_execution_site_id",
        "full_execution_start_ms", "full_execution_end_ms", "local_branch_start_ms", "local_branch_end_ms",
        "remote_input_transfer_start_ms", "remote_input_transfer_end_ms", "remote_branch_start_ms",
        "remote_branch_end_ms", "partition_start_ms", "partition_end_ms", "merge_start_ms",
        "merge_end_ms", "result_transfer_start_ms", "result_transfer_end_ms", "completion_time_ms",
        "end_to_end_latency_ms", "deadline_met", "final_status", "unresolved_at_horizon", "failure_or_unresolved_reason",
    ]
    outcomes = []
    for task in tasks:
        arrival = int(task["arrival_time_ms"])
        completion = arrival + min(10, int(task["relative_deadline_ms"]) - 1)
        outcomes.append({
            "run_id": task["run_id"], "task_id": task["task_id"], "policy_id": "local-baseline",
            "arrival_time_ms": str(arrival), "observed_until_ms": "",
            "action_type": "LOCAL", "offload_fraction": "0", "local_fraction": "1", "remote_tier": "",
            "full_execution_site_id": task["source_device_id"], "local_execution_site_id": "", "remote_execution_site_id": "",
            "full_execution_start_ms": str(arrival), "full_execution_end_ms": str(completion),
            "local_branch_start_ms": "", "local_branch_end_ms": "", "remote_input_transfer_start_ms": "",
            "remote_input_transfer_end_ms": "", "remote_branch_start_ms": "", "remote_branch_end_ms": "",
            "partition_start_ms": "", "partition_end_ms": "", "merge_start_ms": "", "merge_end_ms": "",
            "result_transfer_start_ms": "", "result_transfer_end_ms": "", "completion_time_ms": str(completion),
            "end_to_end_latency_ms": str(completion-arrival), "deadline_met": "true", "final_status": "ON_TIME",
            "unresolved_at_horizon": "false", "failure_or_unresolved_reason": "",
        })
    good = write_bad(tmp_path, "outcomes-valid.csv", fields, outcomes)
    errors, summary = val.validate_outcomes(good, tasks)
    assert not errors, errors
    assert summary["policy_reconciliation"]["local-baseline"]["reconciles"] is True
    assert summary["policy_reconciliation"]["local-baseline"]["reconciled_total"] == len(tasks)
    bad_rows = list(outcomes)
    bad_rows.pop()
    bad_rows.append(dict(outcomes[0], task_id="orphan"))
    bad_rows.append(dict(outcomes[0]))
    bad = write_bad(tmp_path, "outcomes-invalid.csv", fields, bad_rows)
    errors, _ = val.validate_outcomes(bad, tasks)
    assert any("orphan simulator outcome" in e for e in errors)
    assert any("duplicate/contradictory" in e for e in errors)
    assert any("silently missing" in e for e in errors)


def test_partial_outcome_requires_both_branch_traceability(tmp_path, generated):
    task_path, _, _ = generated
    _, tasks = rows_for(task_path)
    task = next(r for r in tasks if r["splittability"] == "DATA_PARALLEL_DIVISIBLE")
    fields = [
        "run_id", "task_id", "policy_id", "arrival_time_ms", "observed_until_ms",
        "action_type", "offload_fraction", "local_fraction", "remote_tier",
        "full_execution_site_id", "local_execution_site_id", "remote_execution_site_id", "full_execution_start_ms",
        "full_execution_end_ms", "local_branch_start_ms", "local_branch_end_ms", "remote_input_transfer_start_ms",
        "remote_input_transfer_end_ms", "remote_branch_start_ms", "remote_branch_end_ms", "partition_start_ms",
        "partition_end_ms", "merge_start_ms", "merge_end_ms", "result_transfer_start_ms", "result_transfer_end_ms",
        "completion_time_ms", "end_to_end_latency_ms", "deadline_met", "final_status", "unresolved_at_horizon",
        "failure_or_unresolved_reason",
    ]
    row = {field: "" for field in fields}
    arrival = int(task["arrival_time_ms"])
    row.update({
        "run_id": task["run_id"], "task_id": task["task_id"], "policy_id": "partial-policy",
        "arrival_time_ms": str(arrival), "observed_until_ms": "",
        "action_type": "EDGE_PARTIAL_25", "offload_fraction": "0.25", "local_fraction": "0.75",
        "remote_tier": "EDGE", "local_execution_site_id": task["source_device_id"],
        "remote_execution_site_id": "edge-01", "partition_start_ms": str(arrival),
        "partition_end_ms": str(arrival+1), "local_branch_start_ms": str(arrival+1),
        "local_branch_end_ms": str(arrival+6), "remote_input_transfer_start_ms": str(arrival+1),
        "remote_input_transfer_end_ms": str(arrival+2), "remote_branch_start_ms": str(arrival+2),
        "remote_branch_end_ms": str(arrival+4), "merge_start_ms": str(arrival+6),
        "merge_end_ms": str(arrival+7), "result_transfer_start_ms": str(arrival+4),
        "result_transfer_end_ms": str(arrival+5), "completion_time_ms": str(arrival+7),
        "end_to_end_latency_ms": "7", "deadline_met": "true", "final_status": "ON_TIME",
        "unresolved_at_horizon": "false",
    })
    good = write_bad(tmp_path, "partial-outcome.csv", fields, [row])
    assert val.validate_outcomes(good, [task])[0] == []
    row["remote_branch_end_ms"] = ""
    bad = write_bad(tmp_path, "partial-outcome-missing-event.csv", fields, [row])
    assert any("missing branch/partition/merge/transfer event remote_branch_end_ms" in e
               for e in val.validate_outcomes(bad, [task])[0])


def test_unresolved_outcome_requires_horizon_and_reason(tmp_path, generated):
    task_path, _, _ = generated
    _, tasks = rows_for(task_path)
    task = tasks[0]
    fields = [
        "run_id", "task_id", "policy_id", "arrival_time_ms", "observed_until_ms", "action_type",
        "offload_fraction", "local_fraction", "remote_tier", "full_execution_site_id",
        "local_execution_site_id", "remote_execution_site_id", "full_execution_start_ms",
        "full_execution_end_ms", "local_branch_start_ms", "local_branch_end_ms",
        "remote_input_transfer_start_ms", "remote_input_transfer_end_ms", "remote_branch_start_ms",
        "remote_branch_end_ms", "partition_start_ms", "partition_end_ms", "merge_start_ms",
        "merge_end_ms", "result_transfer_start_ms", "result_transfer_end_ms", "completion_time_ms",
        "end_to_end_latency_ms", "deadline_met", "final_status", "unresolved_at_horizon",
        "failure_or_unresolved_reason",
    ]
    arrival = int(task["arrival_time_ms"])
    row = {field: "" for field in fields}
    row.update({
        "run_id": task["run_id"], "task_id": task["task_id"], "policy_id": "local-baseline",
        "arrival_time_ms": str(arrival), "observed_until_ms": str(arrival+100), "action_type": "LOCAL",
        "offload_fraction": "0", "local_fraction": "1", "full_execution_site_id": task["source_device_id"],
        "final_status": "UNRESOLVED_AT_HORIZON", "deadline_met": "", "unresolved_at_horizon": "true",
        "failure_or_unresolved_reason": "run horizon reached",
    })
    path = write_bad(tmp_path, "unresolved-valid.csv", fields, [row])
    errors = val.validate_outcomes(path, [task])[0]
    assert not errors, errors
    row["observed_until_ms"] = ""
    bad = write_bad(tmp_path, "unresolved-no-horizon.csv", fields, [row])
    assert any("requires observed_until_ms" in error for error in val.validate_outcomes(bad, [task])[0])


def test_partial_outcome_event_order_is_enforced(tmp_path, generated):
    task_path, _, _ = generated
    _, tasks = rows_for(task_path)
    task = next(r for r in tasks if r["splittability"] == "DATA_PARALLEL_DIVISIBLE")
    fields = [
        "run_id", "task_id", "policy_id", "arrival_time_ms", "observed_until_ms", "action_type",
        "offload_fraction", "local_fraction", "remote_tier", "full_execution_site_id",
        "local_execution_site_id", "remote_execution_site_id", "full_execution_start_ms",
        "full_execution_end_ms", "local_branch_start_ms", "local_branch_end_ms",
        "remote_input_transfer_start_ms", "remote_input_transfer_end_ms", "remote_branch_start_ms",
        "remote_branch_end_ms", "partition_start_ms", "partition_end_ms", "merge_start_ms",
        "merge_end_ms", "result_transfer_start_ms", "result_transfer_end_ms", "completion_time_ms",
        "end_to_end_latency_ms", "deadline_met", "final_status", "unresolved_at_horizon",
        "failure_or_unresolved_reason",
    ]
    arrival = int(task["arrival_time_ms"])
    row = {field: "" for field in fields}
    row.update({
        "run_id": task["run_id"], "task_id": task["task_id"], "policy_id": "partial-policy",
        "arrival_time_ms": str(arrival), "action_type": "EDGE_PARTIAL_25", "offload_fraction": "0.25",
        "local_fraction": "0.75", "remote_tier": "EDGE", "local_execution_site_id": task["source_device_id"],
        "remote_execution_site_id": "edge-01", "partition_start_ms": str(arrival),
        "partition_end_ms": str(arrival+1), "local_branch_start_ms": str(arrival+1),
        "local_branch_end_ms": str(arrival+6), "remote_input_transfer_start_ms": str(arrival+1),
        "remote_input_transfer_end_ms": str(arrival+2), "remote_branch_start_ms": str(arrival+2),
        "remote_branch_end_ms": str(arrival+4), "merge_start_ms": str(arrival+6),
        "merge_end_ms": str(arrival+7), "result_transfer_start_ms": str(arrival+4),
        "result_transfer_end_ms": str(arrival+5), "completion_time_ms": str(arrival+7),
        "end_to_end_latency_ms": "7", "deadline_met": "true", "final_status": "ON_TIME",
        "unresolved_at_horizon": "false",
    })
    row["merge_start_ms"] = str(arrival+3)  # before the Local branch ends at arrival+6
    path = write_bad(tmp_path, "partial-bad-event-order.csv", fields, [row])
    errors = val.validate_outcomes(path, [task])[0]
    assert any("merge starts before Local branch and remote result transfer complete" in error for error in errors)


def test_optional_blocked_scenario_cannot_generate(tmp_path, configs):
    wc, sc = configs
    with pytest.raises(ValueError, match="blocked"):
        gen.generate_one("unseen_topology_optional", 1300, 10, "blocked", wc, sc, tmp_path)


def test_schema_required_fields_match_generated_and_header_only_csvs():
    mappings = {
        "tasks": ROOT / "data/dev/stable_steady__seed_1300_tasks.csv",
        "scenario_manifest": ROOT / "data/dev/stable_steady__seed_1300_scenario_manifest.csv",
        "decision_contexts": ROOT / "data/dev/schemas_only/decision_contexts.csv",
        "decisions": ROOT / "data/dev/schemas_only/decisions.csv",
        "task_outcomes": ROOT / "data/dev/schemas_only/task_outcomes.csv",
        "calibration_log": ROOT / "data/dev/schemas_only/calibration_log.csv",
    }
    for table, path in mappings.items():
        schema = json.loads((ROOT / "schemas" / f"{table}.schema.json").read_text(encoding="utf-8"))
        header, _ = val.read_csv(path)
        assert set(schema["required"]) <= set(header), table
        assert set(header) <= set(schema["properties"]), table


def test_json_schemas_are_valid_json_and_present():
    assert val.validate_schemas(ROOT / "schemas") == []


def test_generator_cli_all_core_is_reproducible(tmp_path):
    import subprocess
    args = [sys.executable, str(ROOT / "scripts/generate_workloads.py"), "--scenario", "all-core",
            "--task-count", "12", "--seed", "1300", "--dataset-split", "development", "--output", str(tmp_path)]
    first = subprocess.run(args, capture_output=True, text=True, check=True)
    hashes_first = sorted(line.split("sha256=")[-1] for line in first.stdout.splitlines() if "sha256=" in line)
    second = subprocess.run(args, capture_output=True, text=True, check=True)
    hashes_second = sorted(line.split("sha256=")[-1] for line in second.stdout.splitlines() if "sha256=" in line)
    assert hashes_first == hashes_second
    assert len(hashes_first) == 16  # eight core scenarios x tasks + manifests

@pytest.mark.parametrize("scenario_id", ["repeated_a_b_a", "repeated_aba_task_mix"])
def test_aba_a1_a2_are_exact_task_and_exogenous_replays(tmp_path, configs, scenario_id):
    wc, sc = configs
    task_path, manifest_path, _ = gen.generate_one(
        scenario_id, 1300, 120, f"{scenario_id}-exact-aba", wc, sc, tmp_path
    )
    _, tasks = val.read_csv(task_path)
    _, manifests = val.read_csv(manifest_path)
    regimes = json.loads(manifests[0]["regime_timeline_json"])
    assert [item["regime_id"] for item in regimes] == ["A", "B", "A"]
    assert val.validate_aba_exact_replay(tasks, regimes) == []
    phase_rows = [[row for row in tasks if int(item["start_time_ms"]) <= int(row["arrival_time_ms"]) < int(item["end_time_ms"])] for item in regimes]
    a1, b, a2 = phase_rows
    assert len(a1) == len(b) == len(a2) == 40
    for left, right in zip(a1, a2):
        for field in ("source_device_id", "application_profile", "urgency_class", "input_size_bytes",
                      "output_size_bytes", "required_mi", "splittability", "partition_model_id",
                      "partition_overhead_ms", "merge_overhead_ms", "input_partition_model",
                      "output_partition_model", "relative_deadline_ms"):
            assert left[field] == right[field]
        assert int(left["arrival_time_ms"]) - int(regimes[0]["start_time_ms"]) == (
            int(right["arrival_time_ms"]) - int(regimes[2]["start_time_ms"])
        )
    assert regimes[0]["condition_profile_id"] == regimes[2]["condition_profile_id"]
    assert [(r["application_profile"], r["required_mi"]) for r in a1] != [
        (r["application_profile"], r["required_mi"]) for r in b
    ]
    if scenario_id == "repeated_aba_task_mix":
        b_profiles = {row["application_profile"] for row in b}
        assert "VISUAL_INSPECTION_BULK_FRAME_BATCH" in b_profiles
        assert "PRODUCTION_MONITORING_LARGE_AGGREGATION" in b_profiles


def test_aba_validator_detects_changed_a2_task_template(tmp_path, configs):
    wc, sc = configs
    tasks_path, manifest_path, _ = gen.generate_one(
        "repeated_a_b_a", 1300, 120, "aba-negative-replay", wc, sc, tmp_path
    )
    _, tasks = val.read_csv(tasks_path)
    _, manifests = val.read_csv(manifest_path)
    regimes = json.loads(manifests[0]["regime_timeline_json"])
    a2_start = int(regimes[2]["start_time_ms"])
    next(row for row in tasks if int(row["arrival_time_ms"]) >= a2_start)["input_size_bytes"] = "999999"
    assert any("A1/A2 task templates" in err for err in val.validate_aba_exact_replay(tasks, regimes))


def test_industrial_archetypes_cover_indivisible_and_divisible_forms(configs):
    profiles = configs[0]["application_profiles"]
    expected = {
        "PREDICTIVE_MAINTENANCE_INFERENCE": "INDIVISIBLE",
        "VISUAL_INSPECTION_SINGLE_IMAGE_INFERENCE": "INDIVISIBLE",
        "VISUAL_INSPECTION_FRAME_BATCH": "DATA_PARALLEL_DIVISIBLE",
        "PRODUCTION_MONITORING_SINGLE_EVENT": "INDIVISIBLE",
        "PRODUCTION_MONITORING_AGGREGATION": "DATA_PARALLEL_DIVISIBLE",
        "VISUAL_INSPECTION_BULK_FRAME_BATCH": "DATA_PARALLEL_DIVISIBLE",
        "PRODUCTION_MONITORING_LARGE_AGGREGATION": "DATA_PARALLEL_DIVISIBLE",
    }
    for name, kind in expected.items():
        assert profiles[name]["splittability"] == kind
