#!/usr/bin/env python3
"""Generate a deterministic A -> B -> A workload with explicit per-task WAN regimes."""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


def build(seed: int, tasks_per_phase: int) -> list[dict]:
    rng = random.Random(seed)
    rows: list[dict] = []
    sequence = 0
    # The same A template is replayed in phases 0 and 2. Only the seed-specific
    # within-phase ordering is shared; the return phase is not a newly sampled A.
    template = []
    for i in range(tasks_per_phase):
        template.append({
            "task_mi": rng.choice([5000, 6000, 7000]),
            "input_bytes": rng.choice([12001, 24000]),
            "output_bytes": rng.choice([512, 1001, 2048]),
            "deadline_ms": 4500.0,
            "arrival_gap_ms": rng.choice([1200.0, 1400.0, 1600.0]),
            "urgency_class": rng.choice(["normal", "high"]),
        })

    phases = [
        {"regime_id": "A", "regime_index": 0, "wan_latency_ms": 45.0, "scale": 1.0},
        {"regime_id": "B", "regime_index": 1, "wan_latency_ms": 220.0, "scale": 2.4},
        {"regime_id": "A", "regime_index": 2, "wan_latency_ms": 45.0, "scale": 1.0},
    ]
    for phase in phases:
        for i in range(tasks_per_phase):
            sequence += 1
            base = template[i]
            stress = phase["regime_index"] == 1
            task_mi = int(round(base["task_mi"] * phase["scale"]))
            input_bytes = int(round(base["input_bytes"] * (2.0 if stress else 1.0)))
            output_bytes = base["output_bytes"]
            gap = rng.choice([450.0, 550.0, 650.0]) if stress else base["arrival_gap_ms"]
            rows.append({
                "sequence": sequence,
                "seed": seed,
                "profile": "aba_network_load_v1",
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
                "deadline_ms": 4500.0 if not stress else 7000.0,
                "arrival_gap_ms": 0.0 if sequence == 1 else gap,
                "urgency_class": base["urgency_class"],
                "splittability": "DATA_PARALLEL_DIVISIBLE",
                "partition_model_id": "data-parallel-v1",
            })
    # Keep the first arrival gap at zero; later phase boundaries are genuine
    # workload shifts, not artificial pauses.
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--tasks-per-phase", type=int, default=30)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.tasks_per_phase < 10 or args.tasks_per_phase > 1000:
        parser.error("--tasks-per-phase must be between 10 and 1000")
    rows = build(args.seed, args.tasks_per_phase)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, separators=(",", ":"), sort_keys=True) + "\\n")
    print(json.dumps({
        "status": "PASS", "seed": args.seed, "profile": "aba_network_load_v1",
        "tasks": len(rows), "phase_boundaries": [1, args.tasks_per_phase + 1, 2 * args.tasks_per_phase + 1],
        "regimes": ["A", "B", "A"], "output": str(args.output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
