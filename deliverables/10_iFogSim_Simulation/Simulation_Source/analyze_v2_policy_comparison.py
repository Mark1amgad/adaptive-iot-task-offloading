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


def tuple_profile_suffix(output_bytes: int) -> str:
    # 1001 bytes is the simulator's legacy/default edge type and has no suffix.
    return "" if int(output_bytes) == 1001 else f"_O{int(output_bytes)}"


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(p * len(ordered)) - 1)]


def find_recovery_window(
    baseline_miss_rate: float,
    baseline_median_latency_ms: float | None,
    return_tasks: list[dict],
    transition_time_ms: float,
    window_size: int = 10,
    miss_tolerance: float = 0.05,
    latency_tolerance: float = 0.10,
) -> tuple[dict | None, float | None]:
    """Find the first qualifying A2 window; return time from A2 transition to its last completion."""
    if baseline_median_latency_ms is None or len(return_tasks) < window_size:
        return None, None
    for start in range(0, len(return_tasks) - window_size + 1):
        window = return_tasks[start:start + window_size]
        done = [task for task in window if task["latency_ms"] is not None]
        miss_rate = sum(task["outcome"] != "ON_TIME" for task in window) / window_size
        median_latency = statistics.median(task["latency_ms"] for task in done) if done else None
        if (len(done) == window_size
                and miss_rate <= baseline_miss_rate + miss_tolerance
                and median_latency <= baseline_median_latency_ms * (1.0 + latency_tolerance)):
            recovered = {
                "window_start_sequence": window[0]["sequence"],
                "window_end_sequence": window[-1]["sequence"],
                "window_end_completion_time_ms": max(task["terminal_time_ms"] for task in window),
                "window_deadline_miss_rate": miss_rate,
                "window_median_latency_ms": median_latency,
            }
            return recovered, max(0.0, recovered["window_end_completion_time_ms"] - transition_time_ms)
    return None, None


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
    metrics, completed_latency, action_counts, task_observations = {}, {}, {}, {}

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
        observations = {}
        for k, task in expected.items():
            decision, outcome = d_by_seq[k], o_by_seq[k]
            for field in ("task_mi", "input_bytes", "output_bytes", "deadline_ms", "urgency_class", "splittability"):
                if decision.get(field) != task[field]:
                    raise AssertionError(f"{policy}/task{k}: {field} differs from common workload")
            action = decision["action"]
            if "_PARTIAL_" in action and task["splittability"] != "DATA_PARALLEL_DIVISIBLE":
                raise AssertionError(f"{policy}/task{k}: partial action selected for indivisible workload")
            branches = [b for b in trace if b.get("record") == "branch_created" and b.get("task_id") == decision["task_id"]]
            profile_suffix = tuple_profile_suffix(task["output_bytes"])
            for branch in branches:
                expected_base = ("LOCAL_PARTIAL_INPUT" if branch["branch"] == "local" else f"{branch['tier']}_PARTIAL_INPUT") if "_PARTIAL_" in action else "TASK_INPUT"
                if branch.get("tuple_type") != expected_base + profile_suffix:
                    raise AssertionError(f"{policy}/task{k}: AppEdge output-size profile mismatch")
            kind = outcome.get("outcome")
            if kind not in OUTCOMES:
                raise AssertionError(f"{policy}/task{k}: invalid outcome {kind!r}")
            counts[kind] += 1
            all_bandwidth.append(float(outcome.get("bandwidth_bytes", 0.0)))
            latency_value, terminal_time = None, None
            if kind in ("ON_TIME", "LATE"):
                terminal = terminals.get(k)
                if terminal is None or float(outcome["latency_ms"]) != float(terminal["latency_ms"]):
                    raise AssertionError(f"{policy}/task{k}: completed outcome lacks matching terminal latency")
                if terminal["deadline_met"] != (terminal["latency_ms"] <= task["deadline_ms"]):
                    raise AssertionError(f"{policy}/task{k}: deadline flag inconsistent")
                if kind != ("ON_TIME" if terminal["deadline_met"] else "LATE"):
                    raise AssertionError(f"{policy}/task{k}: outcome/deadline classification mismatch")
                latency_value = float(terminal["latency_ms"])
                terminal_time = float(terminal["sim_time_ms"])
                latencies.append(latency_value)
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
                terminal_time = float(failure["sim_time_ms"])
            if "regime_index" in task:
                if decision.get("regime_id") != task["regime_id"] or int(decision.get("regime_index", -1)) != int(task["regime_index"]):
                    raise AssertionError(f"{policy}/task{k}: decision regime differs from workload")
                if float(decision.get("wan_latency_ms", float("nan"))) != float(task["wan_latency_ms"]):
                    raise AssertionError(f"{policy}/task{k}: decision WAN latency differs from workload")
            observations[k] = {
                "sequence": k, "regime_id": task.get("regime_id", "stable"),
                "regime_index": int(task.get("regime_index", 0)),
                "outcome": kind, "latency_ms": latency_value,
                "deadline_ms": float(task["deadline_ms"]),
                "terminal_time_ms": terminal_time,
            }

        actions, modes = {}, {}
        for decision in decisions:
            actions[decision["action"]] = actions.get(decision["action"], 0) + 1
            mode = decision.get("mode", "unknown")
            modes[mode] = modes.get(mode, 0) + 1
        action_counts[policy] = actions
        task_observations[policy] = observations
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
    regime_indices = sorted({int(row.get("regime_index", 0)) for row in workload})
    regime_starts = {}
    for row in workload:
        regime_starts.setdefault(int(row.get("regime_index", 0)), row)
    expected_transitions = [
        (int(index), int(regime_starts[index]["sequence"]), str(regime_starts[index].get("regime_id", "stable")),
         float(regime_starts[index].get("wan_latency_ms", manifest["parameters"]["wan_latency_ms"])))
        for index in regime_indices
    ]
    aba_enabled = len(regime_indices) == 3 and [
        str(regime_starts[i].get("regime_id")) for i in regime_indices
    ] == ["A", "B", "A"]
    regime_analysis = {}
    if aba_enabled:
        for policy in POLICIES:
            trace = rows(args.root / f"policy_{policy}" / "partial_trace.jsonl")
            transitions = [r for r in trace if r.get("record") == "regime_transition"]
            observed = [
                (int(r["regime_index"]), int(r["task_sequence"]), str(r["regime_id"]),
                 float(r["wan_latency_ms"])) for r in transitions
            ]
            if observed != expected_transitions:
                raise AssertionError(f"{policy}: regime transition trace does not match workload schedule")
            obs = task_observations[policy]
            phases = {}
            for index in regime_indices:
                phase = [obs[k] for k in sorted(obs) if obs[k]["regime_index"] == index]
                completed_phase = [x for x in phase if x["latency_ms"] is not None]
                misses = sum(x["outcome"] != "ON_TIME" for x in phase)
                phases[str(index)] = {
                    "regime_id": phase[0]["regime_id"] if phase else None,
                    "tasks": len(phase), "deadline_miss_rate": misses / len(phase) if phase else None,
                    "completion_coverage": len(completed_phase) / len(phase) if phase else None,
                    "median_latency_ms_completed_only": statistics.median(
                        x["latency_ms"] for x in completed_phase
                    ) if completed_phase else None,
                    "p95_latency_ms_completed_only": percentile(
                        [x["latency_ms"] for x in completed_phase], 0.95
                    ) if completed_phase else None,
                }
            baseline = phases["0"]
            baseline_median = baseline["median_latency_ms_completed_only"]
            return_tasks = [obs[k] for k in sorted(obs) if obs[k]["regime_index"] == 2]
            window_size, miss_tolerance, latency_tolerance = 10, 0.05, 0.10
            transition = next(r for r in transitions if int(r["regime_index"]) == 2)
            recovered, recovery_time = find_recovery_window(
                baseline["deadline_miss_rate"], baseline_median, return_tasks,
                float(transition["sim_time_ms"]), window_size, miss_tolerance, latency_tolerance,
            )
            regime_analysis[policy] = {
                "phase_metrics": phases,
                "stress_B_deadline_miss_burden": phases["1"]["deadline_miss_rate"],
                "return_A_recovery": {
                    "recovered": recovered is not None,
                    "recovery_time_ms": recovery_time,
                    "window_size_tasks": window_size,
                    "baseline_miss_rate_tolerance_absolute": miss_tolerance,
                    "baseline_median_latency_tolerance_relative": latency_tolerance,
                    "baseline_reference_phase": "A1",
                    "return_phase": "A2",
                    "first_qualifying_window": recovered,
                    "reason_if_not_recovered": None if recovered else (
                        "baseline phase has no completed-task median" if baseline_median is None
                        else f"no qualifying {window_size}-task window within return phase"
                    ),
                },
            }
    else:
        regime_analysis = {
            "enabled": False,
            "reason": "workload does not contain exactly three ordered regime phases A, B, A",
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
        "regime_shift_analysis": {"enabled": aba_enabled, "policy_results": regime_analysis,
            "definition": "A2 recovery is the first 10-task completed window whose deadline-miss rate is within +5 percentage points of A1 and median completed latency is within +10% of A1; recovery time is measured from A2 transition to that window's last completion."},
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
