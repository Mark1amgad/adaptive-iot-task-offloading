#!/usr/bin/env python3
"""Generate deterministic A -> B -> A workloads with controlled shift factors."""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

SHIFT_MODES = ("combined", "network_only", "workload_only")


def build(
    seed: int,
    tasks_per_phase: int,
    shift_mode: str = "combined",
    fixed_deadline_ms: float | None = None,
) -> list[dict]:
    if shift_mode not in SHIFT_MODES:
        raise ValueError(f"shift_mode must be one of {SHIFT_MODES}")
    if fixed_deadline_ms is not None and fixed_deadline_ms <= 0:
        raise ValueError("fixed_deadline_ms must be positive when supplied")

    rng = random.Random(seed)
    rows: list[dict] = []
    sequence = 0
    template = []
    for _ in range(tasks_per_phase):
        template.append({
            "task_mi": rng.choice([5000, 6000, 7000]),
            "input_bytes": rng.choice([12001, 24000]),
            "output_bytes": rng.choice([512, 1001, 2048]),
            "deadline_ms": 15000.0,
            "arrival_gap_ms": rng.choice([4000.0, 4500.0, 5000.0]),
            "urgency_class": rng.choice(["normal", "high"]),
        })

    if shift_mode == "combined":
        profile = "aba_combined_fixed_deadline_v1" if fixed_deadline_ms else "aba_network_load_v1"
    elif shift_mode == "network_only":
        profile = "aba_network_only_fixed_deadline_v1"
    else:
        profile = "aba_workload_only_fixed_deadline_v1"

    phases = [
        {"regime_id": "A", "regime_index": 0, "wan_latency_ms": 45.0},
        {"regime_id": "B", "regime_index": 1, "wan_latency_ms": 160.0 if shift_mode != "workload_only" else 45.0},
        {"regime_id": "A", "regime_index": 2, "wan_latency_ms": 45.0},
    ]
    for phase in phases:
        for i in range(tasks_per_phase):
            sequence += 1
            base = template[i]
            stress = phase["regime_index"] == 1
            workload_shift = stress and shift_mode in ("combined", "workload_only")
            task_mi = int(round(base["task_mi"] * (1.8 if workload_shift else 1.0)))
            input_bytes = int(round(base["input_bytes"] * (1.5 if workload_shift else 1.0)))
            output_bytes = base["output_bytes"]

            if workload_shift:
                gap = rng.choice([2500.0, 3000.0, 3500.0])
            elif phase["regime_index"] == 2 and i == 0:
                gap = template[1]["arrival_gap_ms"]
            else:
                gap = base["arrival_gap_ms"]

            if fixed_deadline_ms is not None:
                deadline = float(fixed_deadline_ms)
            elif shift_mode == "combined" and stress:
                # Legacy profile retained for exact reproducibility of the original pilot.
                deadline = 20000.0
            else:
                deadline = 15000.0

            rows.append({
                "sequence": sequence,
                "seed": seed,
                "profile": profile,
                "phase_name": ["baseline_A", "stress_B", "return_A"][phase["regime_index"]],
                "regime_id": phase["regime_id"],
                "regime_index": phase["regime_index"],
                "wan_latency_ms": phase["wan_latency_ms"],
                "task_mi": task_mi,
                "input_bytes": input_bytes,
                "output_bytes": output_bytes,
                "output_profile": None if output_bytes == 1001 else f"o{output_bytes}",
                "merge_mi": 1200,
                "merge_output_bytes": 64,
                "deadline_ms": deadline,
                "arrival_gap_ms": 0.0 if sequence == 1 else gap,
                "urgency_class": base["urgency_class"],
                "splittability": "DATA_PARALLEL_DIVISIBLE",
                "partition_model_id": "data-parallel-v1",
            })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--tasks-per-phase", type=int, default=30)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--shift-mode", choices=SHIFT_MODES, default="combined")
    parser.add_argument("--fixed-deadline-ms", type=float, default=None)
    args = parser.parse_args()
    if args.tasks_per_phase < 10 or args.tasks_per_phase > 1000:
        parser.error("--tasks-per-phase must be between 10 and 1000")
    if args.fixed_deadline_ms is not None and args.fixed_deadline_ms <= 0:
        parser.error("--fixed-deadline-ms must be positive")
    rows = build(args.seed, args.tasks_per_phase, args.shift_mode, args.fixed_deadline_ms)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, separators=(",", ":"), sort_keys=True) + "\n")
    print(json.dumps({
        "status": "PASS", "seed": args.seed, "profile": rows[0]["profile"],
        "shift_mode": args.shift_mode, "fixed_deadline_ms": args.fixed_deadline_ms,
        "tasks": len(rows), "phase_boundaries": [1, args.tasks_per_phase + 1, 2 * args.tasks_per_phase + 1],
        "regimes": ["A", "B", "A"], "output": str(args.output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
