"""Print the experiment plan (exact server commands + hello fields) with enforced seed separation."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional


def build_plan(train_seeds: List[int], test_seeds: List[int], config: str = "config/default.json") -> List[dict]:
    if set(train_seeds) & set(test_seeds):
        raise ValueError(f"train and test seeds overlap: {sorted(set(train_seeds) & set(test_seeds))}")
    if len(set(train_seeds)) != len(train_seeds) or len(set(test_seeds)) != len(test_seeds):
        raise ValueError("duplicate seeds")
    plan = []
    prev = None
    for i, s in enumerate(train_seeds):
        model_out = f"artifacts/train_seed{s}.json"
        cmd = f"python -m rl_model.server --config {config} --mode train --model-out {model_out}"
        if prev:
            cmd += f" --model-in {prev}"
        plan.append({"run_id": f"train-q-seed{s}", "phase": "train", "sim_seed": s, "cmd": cmd})
        prev = model_out
    final = prev or "artifacts/model_latest.json"
    for s in test_seeds:
        for pol in ("local", "edge", "cloud"):
            plan.append({"run_id": f"test-{pol}-seed{s}", "phase": "test", "sim_seed": s,
                         "cmd": f"python -m rl_model.server --config {config} --mode baseline --policy {pol}"})
        plan.append({"run_id": f"test-q-seed{s}", "phase": "test", "sim_seed": s,
                     "cmd": f"python -m rl_model.server --config {config} --mode eval --model-in {final}"})
    return plan


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--train-seeds", type=int, nargs="+", required=True)
    ap.add_argument("--test-seeds", type=int, nargs="+", required=True)
    ap.add_argument("--config", default="config/default.json")
    a = ap.parse_args(argv)
    try:
        plan = build_plan(a.train_seeds, a.test_seeds, a.config)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    for r in plan:
        print(f"# run_id={r['run_id']} phase={r['phase']} sim_seed={r['sim_seed']}  (send these in the hello message)")
        print(r["cmd"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
