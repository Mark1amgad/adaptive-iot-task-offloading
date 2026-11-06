#!/usr/bin/env python3
"""Generate synthetic IoT task inputs and scenario manifests only.

No policy decisions, execution sites, completion times, latency outcomes, rewards,
energy, or simulator measurements are generated here.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve().parents[1]
GENERATOR_VERSION = "1.1.0"
UNITS_VERSION = "SI-ms-bytes-MI-v1"
TASK_FIELDS = [
    "task_id", "run_id", "seed", "scenario_id", "workload_profile_id",
    "source_device_id", "application_profile", "urgency_class",
    "arrival_time_ms", "input_size_bytes", "output_size_bytes", "required_mi",
    "splittability", "partition_model_id", "partition_overhead_ms", "merge_overhead_ms",
    "input_partition_model", "output_partition_model", "relative_deadline_ms",
    "absolute_deadline_ms", "units_version", "config_hash", "generator_version",
]
MANIFEST_FIELDS = [
    "run_id", "seed", "scenario_id", "scenario_family", "scenario_status",
    "workload_profile_id", "arrival_process_type", "arrival_process_parameters_json",
    "task_count", "generation_window_end_ms", "regime_timeline_json",
    "network_profile_id", "network_profile_json", "edge_capacity_profile_id",
    "edge_capacity_profile_json", "task_mix_profile_id", "task_mix_profile_json",
    "topology_id", "dataset_split", "split_strategy_id", "paired_seed_plan_json",
    "config_hash", "generator_version", "policy_replay_contract",
]
ALLOWED_SPLITS = {"train", "validation", "test"}
URGENCY_LABELS = {"CRITICAL", "TIME_SENSITIVE", "DELAY_TOLERANT"}
SPLIT_LABELS = {"INDIVISIBLE", "DATA_PARALLEL_DIVISIBLE"}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_config_hash(workload_cfg: dict[str, Any], scenario_cfg: dict[str, Any]) -> str:
    material = canonical_json({
        "generator_version": GENERATOR_VERSION,
        "units_version": UNITS_VERSION,
        "workload_profiles": workload_cfg,
        "scenario_profiles": scenario_cfg,
    })
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def derive_seed(seed: int, stream_name: str) -> int:
    """Stable, independent RNG stream seed for each generator sub-process."""
    digest = hashlib.sha256(f"{seed}:{stream_name}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def weighted_choice(rng: random.Random, weights: dict[str, float]) -> str:
    cleaned = {str(k): float(v) for k, v in weights.items()}
    if not cleaned or any(not math.isfinite(v) or v < 0 for v in cleaned.values()):
        raise ValueError("weights must be non-empty, finite and non-negative")
    total = sum(cleaned.values())
    if not math.isclose(total, 1.0, rel_tol=0, abs_tol=1e-9):
        raise ValueError(f"weights must sum to 1.0, got {total}")
    draw = rng.random()
    cumulative = 0.0
    for key, value in cleaned.items():
        cumulative += value
        if draw < cumulative:
            return key
    return next(reversed(cleaned))


def sample_spec(rng: random.Random, spec: dict[str, Any]) -> int:
    distribution = spec.get("distribution")
    if distribution == "choice":
        values = spec.get("values")
        if not isinstance(values, list) or not values:
            raise ValueError("choice distribution requires a non-empty values list")
        value = int(rng.choice(values))
    elif distribution == "uniform_integer":
        low, high = int(spec["min"]), int(spec["max"])
        if low > high:
            raise ValueError("uniform_integer min cannot exceed max")
        value = rng.randint(low, high)
    else:
        raise ValueError(f"unsupported distribution: {distribution!r}")
    return value


def arrival_times(rng: random.Random, count: int, params: dict[str, Any]) -> list[int]:
    """Return sorted integer-millisecond arrivals from Poisson or on/off process."""
    if count < 1:
        raise ValueError("task count must be >= 1")
    kind = params.get("type")
    now_ms = 0.0
    result: list[int] = []
    if kind == "poisson":
        rate = float(params["rate_tasks_per_second"])
        if not math.isfinite(rate) or rate <= 0:
            raise ValueError("Poisson rate must be finite and > 0 tasks/s")
        for _ in range(count):
            now_ms += rng.expovariate(rate / 1000.0)
            result.append(max(0, int(round(now_ms))))
    elif kind == "on_off":
        on_rate = float(params["on_rate_tasks_per_second"])
        off_rate = float(params["off_rate_tasks_per_second"])
        on_duration = float(params["on_duration_ms"])
        off_duration = float(params["off_duration_ms"])
        if any(not math.isfinite(x) or x < 0 for x in (on_rate, off_rate)):
            raise ValueError("on/off arrival rates must be finite and >= 0")
        if on_rate == 0 and off_rate == 0:
            raise ValueError("at least one on/off arrival rate must be > 0")
        if any(not math.isfinite(x) or x <= 0 for x in (on_duration, off_duration)):
            raise ValueError("on/off phase durations must be finite and > 0 ms")
        state = str(params.get("initial_state", "on")).lower()
        if state not in {"on", "off"}:
            raise ValueError("initial_state must be 'on' or 'off'")
        phase_elapsed = 0.0
        while len(result) < count:
            duration = on_duration if state == "on" else off_duration
            rate = on_rate if state == "on" else off_rate
            remaining = duration - phase_elapsed
            wait = math.inf if rate == 0 else rng.expovariate(rate / 1000.0)
            if wait < remaining:
                now_ms += wait
                phase_elapsed += wait
                result.append(max(0, int(round(now_ms))))
            else:
                now_ms += remaining
                state = "off" if state == "on" else "on"
                phase_elapsed = 0.0
    else:
        raise ValueError(f"unsupported arrival process type: {kind!r}")
    return result


def choose_schedule_entry(schedule: list[dict[str, Any]], fraction: float) -> dict[str, Any]:
    for entry in schedule:
        start = float(entry.get("from_fraction", entry.get("start_fraction", 0.0)))
        end = float(entry.get("to_fraction", entry.get("end_fraction", 1.0)))
        if start <= fraction < end:
            return entry
    return schedule[-1]


def resolve_task_mix(profile_id: str, fraction: float,
                     scenario_cfg: dict[str, Any], workload_cfg: dict[str, Any]) -> dict[str, float]:
    definition = scenario_cfg.get("task_mix_profiles", {}).get(profile_id)
    if definition is None:
        definition = workload_cfg.get("mix_profiles", {}).get(profile_id)
    if definition is None:
        raise KeyError(f"missing task_mix_profile {profile_id!r}")
    if "profile_weights" in definition:
        weights = definition["profile_weights"]
    elif "application_profile_weights" in definition:
        weights = definition["application_profile_weights"]
    elif "regimes" in definition:
        entry = choose_schedule_entry(definition["regimes"], fraction)
        weights = entry.get("weights") or entry.get("profile_weights")
    else:
        raise ValueError(f"task mix {profile_id!r} has no profile_weights or regimes")
    if not isinstance(weights, dict):
        raise ValueError(f"task mix {profile_id!r} resolved to a non-object")
    total = sum(float(v) for v in weights.values())
    if not math.isclose(total, 1.0, rel_tol=0, abs_tol=1e-9):
        raise ValueError(f"task mix {profile_id!r} weights must sum to 1.0; got {total}")
    return {str(k): float(v) for k, v in weights.items()}


def scenario_split(scenario: dict[str, Any], seed: int, split_cfg: dict[str, Any]) -> str:
    family = scenario["family"]
    matches = [split for split in ("train", "validation", "test")
               if family in split_cfg[f"{split}_families"]]
    if len(matches) != 1:
        raise ValueError(f"scenario family {family!r} must belong to exactly one split")
    split = matches[0]
    low, high = map(int, split_cfg["seed_bands"][split])
    if not low <= seed <= high:
        raise ValueError(
            f"seed {seed} is outside {split} band [{low}, {high}] for scenario family {family!r}"
        )
    return split


def seeds_for_scenario(scenario: dict[str, Any], split_cfg: dict[str, Any],
                       base_seed: int, seed_count: int) -> list[int]:
    family = scenario["family"]
    matches = [split for split in ("train", "validation", "test")
               if family in split_cfg[f"{split}_families"]]
    if len(matches) != 1:
        raise ValueError(f"scenario family {family!r} must belong to exactly one split")
    split = matches[0]
    low, high = map(int, split_cfg["seed_bands"][split])
    if seed_count == 1:
        seed = base_seed if low <= base_seed <= high else low
        return [seed]
    seeds = list(range(low, min(high, low + seed_count - 1) + 1))
    if len(seeds) != seed_count:
        raise ValueError(f"requested {seed_count} seeds but {split} band has only {len(seeds)} seeds")
    return seeds


def expand_regimes(regimes: list[dict[str, Any]], generation_end_ms: int) -> list[dict[str, Any]]:
    expanded: list[dict[str, Any]] = []
    for item in regimes:
        start_fraction = float(item.get("start_fraction", 0.0))
        end_fraction = float(item.get("end_fraction", 1.0))
        if not (0.0 <= start_fraction < end_fraction <= 1.0):
            raise ValueError(f"invalid regime interval: {item}")
        start_ms = int(round(start_fraction * generation_end_ms))
        end_ms = int(round(end_fraction * generation_end_ms))
        if end_ms < start_ms:
            raise ValueError(f"regime end precedes start: {item}")
        expanded.append({
            "regime_id": item["regime_id"],
            "start_time_ms": start_ms,
            "end_time_ms": end_ms,
            "condition_profile_id": item.get("condition_profile_id"),
            "evaluation_metadata_only": True,
            "policy_observation": False,
        })
    # Regimes are required to be contiguous and cover the full generation window.
    expanded.sort(key=lambda x: x["start_time_ms"])
    if expanded and (expanded[0]["start_time_ms"] != 0 or expanded[-1]["end_time_ms"] != generation_end_ms):
        raise ValueError("regime schedule must cover [0, generation_window_end_ms]")
    for previous, current in zip(expanded, expanded[1:]):
        if previous["end_time_ms"] != current["start_time_ms"]:
            raise ValueError("regime schedule must be contiguous without gaps/overlaps")
    return expanded


def validate_configs(workload_cfg: dict[str, Any], scenario_cfg: dict[str, Any]) -> None:
    if not workload_cfg.get("source_devices"):
        raise ValueError("workload config must define at least one source device")
    for name, profile in workload_cfg["application_profiles"].items():
        if profile.get("splittability") not in SPLIT_LABELS:
            raise ValueError(f"{name}: invalid splittability")
        if profile["splittability"] == "DATA_PARALLEL_DIVISIBLE":
            part = profile.get("partition", {})
            for key in ("partition_model_id", "input_partition_model", "output_partition_model",
                        "partition_overhead_ms", "merge_overhead_ms"):
                if part.get(key) is None:
                    raise ValueError(f"{name}: divisible profile missing partition.{key}")
            if float(part["partition_overhead_ms"]) < 0 or float(part["merge_overhead_ms"]) < 0:
                raise ValueError(f"{name}: overheads must be non-negative")
        urgency_weights = profile.get("urgency_weights", {
            k: v["probability"] for k, v in workload_cfg["urgency_classes"].items()
        })
        if set(urgency_weights) != URGENCY_LABELS:
            raise ValueError(f"{name}: urgency weights must use exactly {sorted(URGENCY_LABELS)}")
        weighted_choice(random.Random(0), urgency_weights)
    for scenario_id, scenario in scenario_cfg["scenarios"].items():
        if scenario.get("status", "").startswith("BLOCKED"):
            continue
        scenario_split(scenario, int(scenario_cfg["split_strategy"]["seed_bands"][
            next(s for s in ("train", "validation", "test") if scenario["family"] in scenario_cfg["split_strategy"][f"{s}_families"])
        ][0]), scenario_cfg["split_strategy"])
        if scenario["arrival_process"].get("type") not in {"poisson", "on_off"}:
            raise ValueError(f"{scenario_id}: unsupported arrival process")
        if scenario["task_mix_profile"] not in scenario_cfg.get("task_mix_profiles", workload_cfg.get("mix_profiles", {})):
            raise ValueError(f"{scenario_id}: unknown task mix profile")
        if scenario["network_profile"] not in scenario_cfg["network_profiles"]:
            raise ValueError(f"{scenario_id}: unknown network profile")
        if scenario["edge_capacity_profile"] not in scenario_cfg["edge_capacity_profiles"]:
            raise ValueError(f"{scenario_id}: unknown edge-capacity profile")
        expand_regimes(scenario["regimes"], 1000)


def generate_one(scenario_id: str, seed: int, count: int, run_id: str,
                 workload_cfg: dict[str, Any], scenario_cfg: dict[str, Any],
                 out_dir: Path) -> tuple[Path, Path, dict[str, str]]:
    if count < 1:
        raise ValueError("task count must be >= 1")
    if scenario_id not in scenario_cfg["scenarios"]:
        raise KeyError(f"unknown scenario_id: {scenario_id}")
    scenario = scenario_cfg["scenarios"][scenario_id]
    if str(scenario.get("status", "")).startswith("BLOCKED"):
        raise ValueError(f"scenario {scenario_id} is blocked: {scenario['status']}")
    if seed < 0:
        raise ValueError("seed must be >= 0")
    split_name = scenario_split(scenario, seed, scenario_cfg["split_strategy"])
    validate_configs(workload_cfg, scenario_cfg)

    arrival_rng = random.Random(derive_seed(seed, "arrivals"))
    task_rng = random.Random(derive_seed(seed, "task_attributes"))
    arrivals = arrival_times(arrival_rng, count, scenario["arrival_process"])
    generation_end_ms = max(1, max(arrivals))
    config_hash = canonical_config_hash(workload_cfg, scenario_cfg)
    task_mix_id = scenario["task_mix_profile"]
    tasks: list[dict[str, Any]] = []

    urgency_default = {k: float(v["probability"]) for k, v in workload_cfg["urgency_classes"].items()}
    for index, arrival_ms in enumerate(arrivals, start=1):
        arrival_fraction = arrival_ms / generation_end_ms
        profile_weights = resolve_task_mix(task_mix_id, arrival_fraction, scenario_cfg, workload_cfg)
        app_name = weighted_choice(task_rng, profile_weights)
        if app_name not in workload_cfg["application_profiles"]:
            raise ValueError(f"task mix references unknown application profile {app_name!r}")
        profile = workload_cfg["application_profiles"][app_name]
        urgency_weights = profile.get("urgency_weights", urgency_default)
        urgency = weighted_choice(task_rng, urgency_weights)
        relative_deadline_ms = sample_spec(task_rng, workload_cfg["urgency_classes"][urgency]["relative_deadline_ms"])
        row: dict[str, Any] = {
            "task_id": f"{scenario_id}-s{seed:04d}-t{index:06d}",
            "run_id": run_id,
            "seed": seed,
            "scenario_id": scenario_id,
            "workload_profile_id": task_mix_id,
            "source_device_id": workload_cfg["source_devices"][(index - 1) % len(workload_cfg["source_devices"])],
            "application_profile": app_name,
            "urgency_class": urgency,
            "arrival_time_ms": arrival_ms,
            "input_size_bytes": sample_spec(task_rng, profile["input_size_bytes"]),
            "output_size_bytes": sample_spec(task_rng, profile["output_size_bytes"]),
            "required_mi": sample_spec(task_rng, profile["required_mi"]),
            "splittability": profile["splittability"],
            "partition_model_id": None,
            "partition_overhead_ms": None,
            "merge_overhead_ms": None,
            "input_partition_model": None,
            "output_partition_model": None,
            "relative_deadline_ms": relative_deadline_ms,
            "absolute_deadline_ms": arrival_ms + relative_deadline_ms,
            "units_version": UNITS_VERSION,
            "config_hash": config_hash,
            "generator_version": GENERATOR_VERSION,
        }
        if profile["splittability"] == "DATA_PARALLEL_DIVISIBLE":
            part = profile["partition"]
            row.update({
                "partition_model_id": part["partition_model_id"],
                "partition_overhead_ms": float(part["partition_overhead_ms"]),
                "merge_overhead_ms": float(part["merge_overhead_ms"]),
                "input_partition_model": part["input_partition_model"],
                "output_partition_model": part["output_partition_model"],
            })
        tasks.append(row)

    network_profile_id = scenario["network_profile"]
    edge_profile_id = scenario["edge_capacity_profile"]
    task_mix_definition = scenario_cfg["task_mix_profiles"].get(task_mix_id)
    if task_mix_definition is None:
        task_mix_definition = workload_cfg["mix_profiles"][task_mix_id]
    manifest = {
        "run_id": run_id,
        "seed": seed,
        "scenario_id": scenario_id,
        "scenario_family": scenario["scenario_family"],
        "scenario_status": scenario["status"],
        "workload_profile_id": task_mix_id,
        "arrival_process_type": scenario["arrival_process"]["type"],
        "arrival_process_parameters_json": canonical_json(scenario["arrival_process"]),
        "task_count": count,
        "generation_window_end_ms": generation_end_ms,
        "regime_timeline_json": canonical_json(expand_regimes(scenario["regimes"], generation_end_ms)),
        "network_profile_id": network_profile_id,
        "network_profile_json": canonical_json(scenario_cfg["network_profiles"][network_profile_id]),
        "edge_capacity_profile_id": edge_profile_id,
        "edge_capacity_profile_json": canonical_json(scenario_cfg["edge_capacity_profiles"][edge_profile_id]),
        "task_mix_profile_id": task_mix_id,
        "task_mix_profile_json": canonical_json(task_mix_definition),
        "topology_id": scenario["topology_id"],
        "dataset_split": split_name,
        "split_strategy_id": scenario_cfg["split_strategy"]["strategy_id"],
        "paired_seed_plan_json": canonical_json(scenario_cfg["split_strategy"]["paired_seed_plan"]),
        "config_hash": config_hash,
        "generator_version": GENERATOR_VERSION,
        "policy_replay_contract": (
            "For each (run_id, scenario_id, seed), pass this exact tasks CSV and the same "
            "exogenous simulator condition trace/config to every policy. Regime labels, "
            "future boundaries and evaluation metadata are not policy observations."
        ),
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{scenario_id}__seed_{seed:04d}"
    tasks_path = out_dir / f"{stem}_tasks.csv"
    manifest_path = out_dir / f"{stem}_scenario_manifest.csv"
    write_csv(tasks_path, TASK_FIELDS, tasks)
    write_csv(manifest_path, MANIFEST_FIELDS, [manifest])
    hashes = {
        "tasks_sha256": sha256_file(tasks_path),
        "manifest_sha256": sha256_file(manifest_path),
    }
    return tasks_path, manifest_path, hashes


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: canonical_json(value) if isinstance(value, (dict, list)) else value
                             for key, value in row.items()})


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be an object: {path}")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", default="all-core", help="Scenario ID or all-core")
    parser.add_argument("--seed", type=int, default=7, help="Base seed for one-run dev generation")
    parser.add_argument("--seed-count", type=int, default=1,
                        help="For all-core, generate N seeds per scenario from that split's seed band")
    parser.add_argument("--task-count", type=int, default=48)
    parser.add_argument("--run-id", default=None, help="Optional run ID prefix")
    parser.add_argument("--output", type=Path, default=HERE / "data" / "dev")
    parser.add_argument("--workload-config", type=Path, default=HERE / "configs" / "workload_profiles.yaml")
    parser.add_argument("--scenario-config", type=Path, default=HERE / "configs" / "scenario_profiles.yaml")
    parser.add_argument("--include-optional", action="store_true")
    parser.add_argument("--hash-report", type=Path, default=None)
    args = parser.parse_args()
    if args.seed < 0 or args.seed_count < 1 or args.task_count < 1:
        parser.error("seed must be >= 0 and seed-count/task-count must be >= 1")

    workload_cfg = load_yaml(args.workload_config)
    scenario_cfg = load_yaml(args.scenario_config)
    validate_configs(workload_cfg, scenario_cfg)
    if args.scenario == "all-core":
        scenario_ids = [
            key for key, scenario in scenario_cfg["scenarios"].items()
            if not scenario.get("status", "").startswith("BLOCKED")
            and (args.include_optional or not key.endswith("_optional"))
        ]
    else:
        scenario_ids = [args.scenario]
    hash_report: dict[str, Any] = {
        "generator_version": GENERATOR_VERSION,
        "config_hash": canonical_config_hash(workload_cfg, scenario_cfg),
        "files": [],
        "scope": "synthetic task inputs and scenario manifests only",
    }
    for scenario_id in scenario_ids:
        scenario = scenario_cfg["scenarios"].get(scenario_id)
        if scenario is None:
            parser.error(f"unknown scenario: {scenario_id}")
        seeds = seeds_for_scenario(scenario, scenario_cfg["split_strategy"], args.seed, args.seed_count)
        for seed in seeds:
            run_id = (f"{args.run_id}-{scenario_id}-s{seed:04d}" if args.run_id
                      else f"{scenario_id}-seed-{seed:04d}")
            task_path, manifest_path, hashes = generate_one(
                scenario_id, seed, args.task_count, run_id, workload_cfg, scenario_cfg, args.output
            )
            item = {"scenario_id": scenario_id, "seed": seed, "run_id": run_id,
                    "tasks_path": str(task_path), "manifest_path": str(manifest_path), **hashes}
            hash_report["files"].append(item)
            print(f"TASKS    {task_path}  sha256={hashes['tasks_sha256']}")
            print(f"MANIFEST {manifest_path}  sha256={hashes['manifest_sha256']}")
    rendered = json.dumps(hash_report, indent=2, sort_keys=True)
    print(rendered)
    if args.hash_report:
        args.hash_report.parent.mkdir(parents=True, exist_ok=True)
        args.hash_report.write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
