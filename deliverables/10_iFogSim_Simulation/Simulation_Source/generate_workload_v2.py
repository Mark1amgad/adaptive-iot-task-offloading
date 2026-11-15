#!/usr/bin/env python3
"""Generate deterministic, replayable iFogSim v2 workload traces (JSONL)."""
from __future__ import annotations
import argparse
import json
import random
from pathlib import Path

OUTPUT_CLASSES = (512, 2048, 8192)
URGENCY = {
    "critical": (90.0, 180.0),
    "high": (180.0, 400.0),
    "normal": (400.0, 1000.0),
}

def generate(seed: int, tasks: int, profile: str) -> list[dict]:
    if tasks < 1 or tasks > 10000:
        raise ValueError("tasks must be in 1..10000")
    if profile not in {"mixed", "divisible", "indivisible"}:
        raise ValueError("profile must be mixed, divisible, or indivisible")
    rng = random.Random(seed)
    rows = []
    for sequence in range(1, tasks + 1):
        if profile == "divisible":
            divisible = True
        elif profile == "indivisible":
            divisible = False
        else:
            divisible = rng.random() < 0.70
        urgency = rng.choices(("critical", "high", "normal"), weights=(0.20, 0.35, 0.45), k=1)[0]
        lo, hi = URGENCY[urgency]
        output_bytes = rng.choice(OUTPUT_CLASSES)
        task_mi = rng.randint(1000, 30000)
        rows.append({
            "sequence": sequence,
            "task_mi": task_mi,
            "input_bytes": rng.randint(1024, 262144),
            "output_bytes": output_bytes,
            "merge_mi": max(50, round(task_mi * rng.uniform(0.04, 0.12))) if divisible else 0,
            "merge_output_bytes": 64,
            "deadline_ms": round(rng.uniform(lo, hi), 3),
            "urgency_class": urgency,
            "splittability": "DATA_PARALLEL_DIVISIBLE" if divisible else "INDIVISIBLE",
            "partition_model_id": "data-parallel-v1" if divisible else None,
            "arrival_gap_ms": 0.0 if sequence == 1 else round(rng.uniform(1.0, 20.0), 3),
            "output_profile": f"o{output_bytes}",
            "seed": seed,
            "profile": profile,
        })
    return rows

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--tasks", type=int, default=100)
    parser.add_argument("--profile", choices=("mixed", "divisible", "indivisible"), default="mixed")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = generate(args.seed, args.tasks, args.profile)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"status": "PASS", "seed": args.seed, "profile": args.profile,
                      "tasks": len(rows), "output": str(args.output)}, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
