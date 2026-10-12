"""Aggregate per-run logs (written by the server from REAL simulator outcomes) into a comparison.

Per run (one simulator seed, one policy):
  completion_rate            = completed / all tasks
  avg_latency_ms             = mean latency over COMPLETED tasks (failed tasks have no valid latency)
  deadline_violation_rate    = (deadline missed OR failed) / all tasks
  avg_bandwidth_bytes        = mean resource_metrics.bandwidth_bytes per task (tasks reporting it)
  avg_node_utilization       = mean resource_metrics.executing_node_utilization (tasks reporting it)
  avg_energy_joules          = mean resource_metrics.energy_joules (tasks reporting it)
Across runs (seeds) of the same policy: mean, sample std (ddof=1), 95% CI (Student t).
Train/test separation is enforced: only phase='test' runs are compared, the Q-learning test runs
must be frozen (updates_enabled=false) and test seeds must not overlap train seeds.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

T95 = [12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228, 2.201, 2.179, 2.160,
       2.145, 2.131, 2.120, 2.110, 2.101, 2.093, 2.086, 2.080, 2.074, 2.069, 2.064, 2.060, 2.056,
       2.052, 2.048, 2.045, 2.042]
METRICS = ["completion_rate", "avg_latency_ms", "deadline_violation_rate", "avg_bandwidth_bytes",
           "avg_node_utilization", "avg_energy_joules", "avg_reward"]


class AggregationError(ValueError):
    pass


def read_run(path: str | Path) -> Dict[str, Any]:
    start, tasks, end = None, [], None
    with open(path, "r", encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                raise AggregationError(f"{path}:{n}: invalid JSON ({e})") from e
            kind = rec.get("record")
            if kind == "run_start":
                if start is not None:
                    raise AggregationError(f"{path}: more than one run_start")
                start = rec
            elif kind == "task":
                tasks.append(rec)
            elif kind == "run_end":
                end = rec
    if start is None:
        raise AggregationError(f"{path}: no run_start record")
    return {"path": str(path), "start": start, "tasks": tasks, "end": end}


def _mean(xs: List[float]) -> Optional[float]:
    return sum(xs) / len(xs) if xs else None


def run_metrics(run: Dict[str, Any]) -> Dict[str, Optional[float]]:
    tasks = run["tasks"]
    if not tasks:
        raise AggregationError(f"{run['path']}: run has no task records")
    n = len(tasks)
    completed = [t for t in tasks if t["outcome"]["status"] == "completed"]
    missed = sum(1 for t in tasks
                 if t["outcome"]["status"] == "failed" or not t["outcome"]["deadline_met"])

    def metric(key: str) -> Optional[float]:
        return _mean([t["outcome"]["resource_metrics"][key] for t in tasks
                      if t["outcome"]["resource_metrics"].get(key) is not None])

    return {
        "n_tasks": n,
        "completion_rate": len(completed) / n,
        "avg_latency_ms": _mean([t["outcome"]["latency_ms"] for t in completed]),
        "deadline_violation_rate": missed / n,
        "avg_bandwidth_bytes": metric("bandwidth_bytes"),
        "avg_node_utilization": metric("executing_node_utilization"),
        "avg_energy_joules": metric("energy_joules"),
        "avg_reward": _mean([t["reward"]["reward"] for t in tasks]),
    }


def summarize(values: List[Optional[float]]) -> Dict[str, Any]:
    v = [x for x in values if x is not None]
    if not v:
        return {"n": 0, "mean": None, "std": None, "ci95": None}
    mean = sum(v) / len(v)
    if len(v) < 2:
        return {"n": len(v), "mean": mean, "std": None, "ci95": None}
    sd = statistics.stdev(v)
    t = T95[len(v) - 2] if len(v) - 1 <= len(T95) else 1.96
    return {"n": len(v), "mean": mean, "std": sd, "ci95": t * sd / math.sqrt(len(v))}


def check_separation(runs: List[Dict[str, Any]], extra_train_seeds: Iterable[int] = ()) -> List[str]:
    """Return a list of violations (empty = OK)."""
    problems: List[str] = []
    train_seeds = set(extra_train_seeds)
    for r in runs:
        s = r["start"]
        if s["phase"] == "train" and s.get("sim_seed") is not None:
            train_seeds.add(s["sim_seed"])
    for r in runs:
        s = r["start"]
        if s["phase"] != "test":
            continue
        if s["policy"] == "qlearning" and s.get("updates_enabled"):
            problems.append(f"{r['path']}: Q-learning test run had updates enabled (not frozen)")
        if s.get("sim_seed") is None:
            problems.append(f"{r['path']}: test run has no sim_seed")
        elif s["sim_seed"] in train_seeds:
            problems.append(f"{r['path']}: test sim_seed {s['sim_seed']} also used for training")
    return problems


def aggregate(paths: List[str | Path], extra_train_seeds: Iterable[int] = (),
              include_non_test: bool = False) -> Dict[str, Any]:
    runs = [read_run(p) for p in paths]
    problems = check_separation(runs, extra_train_seeds)
    if problems:
        raise AggregationError("train/test separation violated:\n  " + "\n  ".join(problems))
    sel = [r for r in runs if include_non_test or r["start"]["phase"] == "test"]
    if not sel:
        raise AggregationError("no phase='test' runs found; nothing to compare")
    by_policy: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in sel:
        by_policy[r["start"]["policy"]].append(r)
    seeds = {p: sorted(r["start"].get("sim_seed") for r in rs) for p, rs in by_policy.items()}
    warnings = []
    if len({tuple(v) for v in seeds.values()}) > 1:
        warnings.append(f"policies were not evaluated on identical sim seeds: {seeds}")
    for p, s in seeds.items():
        if len(s) != len(set(s)):
            raise AggregationError(f"policy {p}: duplicate sim_seed among runs {s}")
    out: Dict[str, Any] = {"policies": {}, "warnings": warnings, "source_files": [r["path"] for r in sel]}
    for p, rs in sorted(by_policy.items()):
        per_run = [run_metrics(r) for r in rs]
        out["policies"][p] = {
            "n_runs": len(rs), "sim_seeds": seeds[p],
            "total_tasks": sum(m["n_tasks"] for m in per_run),
            "metrics": {k: summarize([m[k] for m in per_run]) for k in METRICS},
        }
    return out


def to_markdown(res: Dict[str, Any]) -> str:
    def cell(s: Dict[str, Any], fmt: str) -> str:
        if s["mean"] is None:
            return "n/a"
        txt = format(s["mean"], fmt)
        return txt + (f" ± {format(s['ci95'], fmt)}" if s["ci95"] is not None else "")
    cols = [("Avg latency (ms)", "avg_latency_ms", ".2f"), ("Deadline viol. rate", "deadline_violation_rate", ".4f"),
            ("Completion rate", "completion_rate", ".4f"), ("Avg node util.", "avg_node_utilization", ".3f"),
            ("Avg bandwidth (B/task)", "avg_bandwidth_bytes", ".0f"),
            ("Avg energy (J)", "avg_energy_joules", ".3f"), ("Avg reward", "avg_reward", ".4f")]
    lines = ["# Evaluation (computed from run logs; mean ± 95% CI across seeds)", "",
             "| Policy | runs | tasks | " + " | ".join(c[0] for c in cols) + " |",
             "|---|---|---|" + "---|" * len(cols)]
    for p, d in res["policies"].items():
        lines.append(f"| {p} | {d['n_runs']} | {d['total_tasks']} | "
                     + " | ".join(cell(d["metrics"][k], f) for _, k, f in cols) + " |")
    for w in res["warnings"]:
        lines += ["", f"**Warning:** {w}"]
    lines += ["", "Source files:"] + [f"- {f}" for f in res["source_files"]]
    lines += ["", "_Avg reward depends on the reward weights/normalisation in the config; compare policies "
              "on the physical metrics first._"]
    return "\n".join(lines) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_logs", nargs="+", help="logs/run_<run_id>.jsonl files (train runs may be included "
                                                 "only to check seed separation)")
    ap.add_argument("--train-seeds", type=int, nargs="*", default=[])
    ap.add_argument("--out-dir", default="artifacts")
    a = ap.parse_args(argv)
    try:
        res = aggregate(a.run_logs, a.train_seeds)
    except (AggregationError, OSError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "evaluation.json").write_text(json.dumps(res, indent=2))
    (out / "evaluation.md").write_text(to_markdown(res))
    print(to_markdown(res))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
