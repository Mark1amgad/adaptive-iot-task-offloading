#!/usr/bin/env python3
"""Verify immutable Generator V1.2 inputs before handing them to V2.

This script does NOT map to unconfirmed V2 JSONL destination keys and does not
run the simulator. It verifies source CSV/manifest consistency, source IDs,
target-only mapping, and computes byte-level SHA-256 hashes.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, os, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "dev"
SCENARIOS = (
    "stable_steady", "bursty_on_off", "reduced_bandwidth",
    "increased_wan_delay", "reduced_edge_capacity",
    "task_size_compute_shift", "repeated_a_b_a", "repeated_aba_task_mix",
)
REQUIRED = {
    "task_id", "run_id", "seed", "scenario_id", "source_device_id",
    "urgency_class", "arrival_time_ms", "input_size_bytes", "output_size_bytes",
    "required_mi", "splittability", "partition_model_id",
    "partition_overhead_ms", "merge_overhead_ms", "input_partition_model",
    "output_partition_model", "relative_deadline_ms", "absolute_deadline_ms",
    "units_version", "config_hash", "generator_version",
}
EXPECTED_SOURCES = {f"iot-{i:03d}" for i in range(1, 101)}
TARGET_MAPPING = {
    f"edge-{edge:03d}": [f"iot-{i:03d}" for i in range((edge-1)*5+1, edge*5+1)]
    for edge in range(1, 21)
}

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def read_one_manifest(path: Path) -> dict:
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 1:
        raise ValueError(f"{path}: expected exactly one manifest row, got {len(rows)}")
    return rows[0]

def verify(scenario: str, data_dir: Path = DATA) -> dict:
    task_path = data_dir / f"{scenario}__seed_1300_tasks.csv"
    manifest_path = data_dir / f"{scenario}__seed_1300_scenario_manifest.csv"
    for path in (task_path, manifest_path):
        if not path.is_file():
            raise FileNotFoundError(path)
    manifest = read_one_manifest(manifest_path)
    with task_path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        fields = set(reader.fieldnames or [])
        missing = sorted(REQUIRED - fields)
        if missing:
            raise ValueError(f"{scenario}: missing required task columns: {missing}")
        tasks = list(reader)
    errors = []
    if manifest.get("scenario_id") != scenario:
        errors.append("manifest scenario_id mismatch")
    if int(manifest.get("seed", -1)) != 1300:
        errors.append("manifest seed is not registered Development seed 1300")
    if int(manifest.get("task_count", -1)) != len(tasks):
        errors.append(f"manifest task_count={manifest.get('task_count')} but CSV rows={len(tasks)}")
    if manifest.get("actual_topology_id", "") not in ("", "null"):
        errors.append("actual_topology_id must remain null pending Ayoub")
    if manifest.get("actual_topology_status") != "NOT_VERIFIED_PENDING_AYOUB_CONFIRMATION":
        errors.append("actual topology status was changed")
    if manifest.get("target_topology_id") != "v2_target_100iot_20edge_1cloud":
        errors.append("target topology ID mismatch")
    if manifest.get("config_hash") != (tasks[0].get("config_hash") if tasks else None):
        errors.append("manifest/task config_hash mismatch")
    if any(row.get("seed") != "1300" for row in tasks):
        errors.append("task seed mismatch")
    if any(row.get("scenario_id") != scenario for row in tasks):
        errors.append("task scenario_id mismatch")
    if any(row.get("run_id") != manifest.get("run_id") for row in tasks):
        errors.append("task run_id mismatch")
    ids = [row.get("task_id") for row in tasks]
    if len(ids) != len(set(ids)):
        errors.append("duplicate task_id")
    for row in tasks:
        if not row.get("source_device_id") or row["source_device_id"] not in EXPECTED_SOURCES:
            errors.append(f"missing/unknown source_device_id for task {row.get('task_id')}")
        try:
            arrival = int(row["arrival_time_ms"])
            relative = int(row["relative_deadline_ms"])
            absolute = int(row["absolute_deadline_ms"])
            if absolute != arrival + relative:
                errors.append(f"deadline identity mismatch for {row['task_id']}")
        except (KeyError, ValueError, TypeError):
            errors.append(f"invalid timestamp/deadline type for {row.get('task_id')}")
        split = row.get("splittability")
        partition_values = [row.get(k, "") for k in (
            "partition_model_id", "partition_overhead_ms", "merge_overhead_ms",
            "input_partition_model", "output_partition_model")]
        if split == "INDIVISIBLE" and any(partition_values):
            errors.append(f"indivisible task has partition fields: {row.get('task_id')}")
        elif split == "DATA_PARALLEL_DIVISIBLE" and not all(partition_values):
            errors.append(f"divisible task missing partition fields: {row.get('task_id')}")
        elif split not in ("INDIVISIBLE", "DATA_PARALLEL_DIVISIBLE"):
            errors.append(f"invalid splittability: {row.get('task_id')}")
    try:
        declared_mapping = json.loads(manifest["target_device_mapping_json"])
        if declared_mapping != TARGET_MAPPING:
            errors.append("manifest target mapping differs from the 5-sources-per-edge contract")
    except Exception as exc:
        errors.append(f"cannot parse target_device_mapping_json: {exc}")
    try:
        counts = json.loads(manifest["target_topology_tier_counts_json"])
        if counts != {"IOT": 100, "EDGE": 20, "CLOUD": 1}:
            errors.append("target tier counts mismatch")
    except Exception as exc:
        errors.append(f"cannot parse target_topology_tier_counts_json: {exc}")
    if errors:
        raise ValueError(f"{scenario}: " + "; ".join(errors))
    return {
        "scenario_id": scenario, "seed": 1300, "task_count": len(tasks),
        "run_id": manifest["run_id"], "config_hash": manifest["config_hash"],
        "target_topology_id": manifest["target_topology_id"],
        "actual_topology_id": None,
        "actual_topology_status": manifest["actual_topology_status"],
        "task_csv": f"data/dev/{task_path.name}",
        "task_csv_sha256": sha256(task_path),
        "manifest_csv": f"data/dev/{manifest_path.name}",
        "manifest_csv_sha256": sha256(manifest_path),
        "status": "SOURCE_INPUTS_VALIDATED_ONLY_NOT_SIMULATOR_VALIDATED",
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "v2_integration" / "reproducibility_report.json")
    parser.add_argument("--data-dir", type=Path, default=DATA)
    args = parser.parse_args()
    try:
        scenarios = [verify(name, args.data_dir.resolve()) for name in SCENARIOS]
        report = {
            "package": "Generator V1.2 to V2 workload integration",
            "generator_version": "1.2.0",
            "seed": 1300,
            "seed_scope": "Development/CI only; existing Seed Registry governs allocations",
            "expected_scenario_count": 8,
            "expected_task_count_per_scenario": 48,
            "actual_total_task_count": sum(x["task_count"] for x in scenarios),
            "scenarios": scenarios,
            "source_config_hashes": {
                "workload_profiles_yaml_sha256": sha256(ROOT / "configs" / "workload_profiles.yaml"),
                "scenario_profiles_yaml_sha256": sha256(ROOT / "configs" / "scenario_profiles.yaml"),
            },
            "verifier_sha256": sha256(Path(__file__)),
            "simulator_validation": "PENDING_AYOUB_V2_ADAPTER_EXECUTION",
            "note": "No simulator output, runtime source mapping, or performance result is created by this verifier.",
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temp_name = None
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=args.output.parent, prefix=args.output.name + ".", suffix=".tmp", delete=False) as stream:
                temp_name = stream.name
                json.dump(report, stream, indent=2, allow_nan=False)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_name, args.output)
            temp_name = None
        finally:
            if temp_name and os.path.exists(temp_name):
                os.unlink(temp_name)
        print(json.dumps({"status": "PASS_SOURCE_INPUTS_ONLY", "scenarios": 8,
                          "tasks": report["actual_total_task_count"],
                          "report": str(args.output)}, indent=2))
        return 0
    except Exception as exc:
        print(f"VALIDATION_ERROR: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
