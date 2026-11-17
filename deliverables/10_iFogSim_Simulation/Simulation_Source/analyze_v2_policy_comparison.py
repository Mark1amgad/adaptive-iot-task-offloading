#!/usr/bin/env python3
"""Validate paired policy runs while retaining every generated task in outcome metrics."""
from __future__ import annotations
import argparse
import json
import hashlib
import math
import statistics
from pathlib import Path

POLICIES = ("local", "edge", "cloud", "random", "rl_eval")
OUTCOMES = ("ON_TIME", "LATE", "FAILED", "UNRESOLVED_AT_HORIZON")


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def one(data: list[dict], kind: str) -> dict:
    found = [r for r in data if r.get("record") == kind]
    if len(found) != 1:
        raise AssertionError(f"expected one {kind}, got {len(found)}")
    return found[0]


def seq(task_id: str) -> int:
    return int(task_id.rsplit(":", 1)[1])


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(p * len(ordered)) - 1)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--workload", type=Path, required=True)
    ap.add_argument("--manifest", type=Path)
    args = ap.parse_args()
    manifest_path = args.manifest or (args.root / "experiment_manifest.json")
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    if manifest.get("schema_version") != "v1" or manifest.get("evaluation_split") != "test":
        raise AssertionError("manifest must declare schema_version=v1 and evaluation_split=test")
    actual_workload_sha = hashlib.sha256(args.workload.read_bytes()).hexdigest()
    if actual_workload_sha != manifest.get("workload_sha256"):
        raise AssertionError("workload SHA-256 does not match frozen experiment manifest")
    if Path(manifest.get("workload_file", "")).name != args.workload.name:
        raise AssertionError("workload filename does not match experiment manifest")
    if manifest.get("policies") != list(POLICIES):
        raise AssertionError("manifest policy arms differ from analyzer policy contract")
    workload = [json.loads(x) for x in args.workload.read_text(encoding="utf-8").splitlines() if x.strip()]
    expected = {r["sequence"]: r for r in workload}
    if not expected or len(expected) != len(workload):
        raise AssertionError("workload must contain unique, non-empty task sequences")
    n = len(expected)
    seeds = {str(row.get("seed")) for row in workload}
    profiles = {str(row.get("profile")) for row in workload}
    if seeds != {str(manifest.get("workload_seed"))} or profiles != {str(manifest.get("workload_profile"))}:
        raise AssertionError("workload row seed/profile do not match experiment manifest")
    metrics, completed_latency, action_counts = {}, {}, {}

    for policy in POLICIES:
        run_dir = args.root / f"policy_{policy}"
        run_manifest = run_dir / "experiment_manifest.json"
        if not run_manifest.is_file() or hashlib.sha256(run_manifest.read_bytes()).hexdigest() != manifest_sha256:
            raise AssertionError(f"{policy}: missing or modified per-policy experiment manifest")
        trace = rows(run_dir / "partial_trace.jsonl")
        cfg = one(trace, "config")
        if cfg.get("task_count") != n or Path(cfg.get("workload_file", "")).name != args.workload.name:
            raise AssertionError(f"{policy}: workload identity/config mismatch")
        for field, expected_value in (
            ("partition_overhead_ms", manifest["parameters"]["partition_overhead_ms"]),
            ("merge_overhead_ms", manifest["parameters"]["merge_overhead_ms"]),
            ("wan_latency_ms", manifest["parameters"]["wan_latency_ms"]),
            ("watchdog_ms", manifest["parameters"]["watchdog_ms"]),
        ):
            if float(cfg.get(field, float("nan"))) != float(expected_value):
                raise AssertionError(f"{policy}: {field} differs from frozen manifest")
        decisions = [r for r in trace if r.get("record") == "decision"]
        outcomes = [r for r in trace if r.get("record") == "task_outcome"]
        acks = [r for r in trace if r.get("record") == "outcome_ack"]
        if len(decisions) != n or len(outcomes) != n or len(acks) != n:
            raise AssertionError(f"{policy}: every generated task needs one decision, outcome, and ack")
        d_by_seq = {seq(r["task_id"]): r for r in decisions}
        o_by_seq = {seq(r["task_id"]): r for r in outcomes}
        if len(d_by_seq) != n or len(o_by_seq) != n or set(d_by_seq) != set(expected) or set(o_by_seq) != set(expected):
            raise AssertionError(f"{policy}: duplicate or missing task sequence")
        if len({r["task_id"] for r in acks}) != n or {r["task_id"] for r in acks} != {r["task_id"] for r in decisions}:
            raise AssertionError(f"{policy}: outcome acknowledgements do not reconcile exactly")

        terminals = {seq(r["task_id"]): r for r in trace if r.get("record") == "task_terminal"}
        failures = {seq(r["task_id"]): r for r in trace if r.get("record") == "task_failed"}
        if set(terminals) & set(failures) or set(terminals) | set(failures) != set(expected):
            raise AssertionError(f"{policy}: completed/failed trace records do not partition all tasks")

        counts = {name: 0 for name in OUTCOMES}
        all_bandwidth, latencies = [], []
        for k, task in expected.items():
            decision, outcome = d_by_seq[k], o_by_seq[k]
            for field in ("task_mi", "input_bytes", "output_bytes", "deadline_ms", "urgency_class", "splittability"):
                if decision.get(field) != task[field]:
                    raise AssertionError(f"{policy}/task{k}: {field} differs from common workload")
            action = decision["action"]
            if "_PARTIAL_" in action and task["splittability"] != "DATA_PARALLEL_DIVISIBLE":
                raise AssertionError(f"{policy}/task{k}: partial action selected for indivisible workload")
            branches = [b for b in trace if b.get("record") == "branch_created" and b.get("task_id") == decision["task_id"]]
            profile_suffix = f"_O{task['output_bytes']}"
            for branch in branches:
                expected_base = ("LOCAL_PARTIAL_INPUT" if branch["branch"] == "local" else f"{branch['tier']}_PARTIAL_INPUT") if "_PARTIAL_" in action else "TASK_INPUT"
                if branch.get("tuple_type") != expected_base + profile_suffix:
                    raise AssertionError(f"{policy}/task{k}: AppEdge output-size profile mismatch")
            kind = outcome.get("outcome")
            if kind not in OUTCOMES:
                raise AssertionError(f"{policy}/task{k}: invalid outcome {kind!r}")
            counts[kind] += 1
            all_bandwidth.append(float(outcome.get("bandwidth_bytes", 0.0)))
            if kind in ("ON_TIME", "LATE"):
                terminal = terminals.get(k)
                if terminal is None or float(outcome["latency_ms"]) != float(terminal["latency_ms"]):
                    raise AssertionError(f"{policy}/task{k}: completed outcome lacks matching terminal latency")
                if terminal["deadline_met"] != (terminal["latency_ms"] <= task["deadline_ms"]):
                    raise AssertionError(f"{policy}/task{k}: deadline flag inconsistent")
                if kind != ("ON_TIME" if terminal["deadline_met"] else "LATE"):
                    raise AssertionError(f"{policy}/task{k}: outcome/deadline classification mismatch")
                latencies.append(float(terminal["latency_ms"]))
            else:
                failure = failures.get(k)
                if failure is None:
                    raise AssertionError(f"{policy}/task{k}: non-completed outcome lacks task_failed record")
                expected_failure_class = (
                    "UNRESOLVED_AT_HORIZON"
                    if str(failure.get("reason", "")).startswith("execution_horizon_exceeded")
                    else "FAILED"
                )
                if kind != expected_failure_class:
                    raise AssertionError(
                        f"{policy}/task{k}: outcome {kind} conflicts with failure reason "
                        f"(expected {expected_failure_class})"
                    )

        actions, modes = {}, {}
        for decision in decisions:
            actions[decision["action"]] = actions.get(decision["action"], 0) + 1
            mode = decision.get("mode", "unknown")
            modes[mode] = modes.get(mode, 0) + 1
        action_counts[policy] = actions
        completed_latency[policy] = {k: float(terminals[k]["latency_ms"]) for k in terminals}
        completed = counts["ON_TIME"] + counts["LATE"]
        misses = n - counts["ON_TIME"]
        metrics[policy] = {
            "generated_tasks": n, "on_time_tasks": counts["ON_TIME"], "late_tasks": counts["LATE"],
            "failed_tasks": counts["FAILED"], "unresolved_at_horizon": counts["UNRESOLVED_AT_HORIZON"],
            "deadline_misses": misses, "deadline_miss_rate": misses / n,
            "completion_coverage": completed / n,
            "mean_latency_ms": statistics.mean(latencies) if latencies else None,
            "mean_latency_ms_completed_only": statistics.mean(latencies) if latencies else None,
            "median_latency_ms_completed_only": statistics.median(latencies) if latencies else None,
            "p95_latency_ms_completed_only": percentile(latencies, 0.95) if latencies else None,
            "mean_bandwidth_bytes": statistics.mean(all_bandwidth),
            "mean_bandwidth_bytes_all_tasks": statistics.mean(all_bandwidth),
            "action_counts": actions, "decision_modes": modes,
            "latency_condition": "completed tasks only; interpret together with completion_coverage and deadline_miss_rate",
        }
        shutdown = one(trace, "shutdown_ack")
        if shutdown.get("orphaned_tasks") != 0 or shutdown.get("tasks_reported") != n:
            raise AssertionError(f"{policy}: Python shutdown reconciliation failed")
        stderr = args.root / f"policy_{policy}" / "python_stderr.log"
        if stderr.exists() and stderr.read_text(encoding="utf-8").strip():
            raise AssertionError(f"{policy}: Python stderr not empty")

    paired = {}
    for baseline in ("local", "edge", "cloud", "random"):
        common = sorted(set(completed_latency["rl_eval"]) & set(completed_latency[baseline]))
        diffs = [completed_latency["rl_eval"][k] - completed_latency[baseline][k] for k in common]
        paired[f"rl_minus_{baseline}_latency_ms_completed_pairs"] = {
            "paired_completed_tasks": len(common),
            "mean_difference": statistics.mean(diffs) if diffs else None,
            "rl_faster_tasks": sum(x < 0 for x in diffs),
            "baseline_faster_tasks": sum(x > 0 for x in diffs),
            "ties": sum(x == 0 for x in diffs),
            "warning": "conditional paired latency; differing completion sets are not treated as equal coverage",
        }
    provenance = {
        "source_git_commit": manifest["source_git_commit"],
        "source_inventory": manifest["source_inventory"],
        "model_sha256": manifest["model_sha256"],
        "risk_state_sha256": manifest["risk_state_sha256"],
        "java_version": manifest["java_version"],
        "simulator_jar_inventory": manifest["simulator_jar_inventory"],
        "parameters": manifest["parameters"],
        "policies": manifest["policies"],
        "evaluation_split": manifest["evaluation_split"],
    }
    provenance_canonical = json.dumps(provenance, sort_keys=True, separators=(",", ":"))
    provenance_fingerprint = hashlib.sha256(provenance_canonical.encode("utf-8")).hexdigest()
    report = {
        "status": "PASS", "workload_seed": workload[0]["seed"],
        "workload_profile": workload[0]["profile"], "tasks": n,
        "comparison_design": "paired task stream and exogenous inputs; all generated tasks retained in outcome denominator",
        "manifest_sha256": manifest_sha256,
        "provenance": provenance,
        "provenance_fingerprint": provenance_fingerprint,
        "source_git_commit": manifest["source_git_commit"],
        "evaluation_split": manifest["evaluation_split"],
        "policy_metrics": metrics, "paired_rl_differences": paired,
        "interpretation": "Descriptive single-seed evaluation only; not evidence of statistical significance, convergence, or generalization.",
    }
    out = args.root / "policy_comparison_summary.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2), flush=True)
        raise
