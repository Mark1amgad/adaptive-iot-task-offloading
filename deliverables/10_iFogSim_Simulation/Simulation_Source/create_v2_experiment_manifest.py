#!/usr/bin/env python3
"""Create a content-addressed manifest for one paired V2 policy comparison."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--simulation-source", type=Path, required=True)
    parser.add_argument("--rl-root", type=Path, required=True)
    parser.add_argument("--ifogsim-root", type=Path, required=True)
    parser.add_argument("--jdk-home", type=Path, required=True)
    parser.add_argument("--workload", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--risk-state", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--partition-overhead-ms", type=float, required=True)
    parser.add_argument("--merge-overhead-ms", type=float, required=True)
    parser.add_argument("--wan-latency-ms", type=float, required=True)
    parser.add_argument("--watchdog-ms", type=float, required=True)
    args = parser.parse_args()

    root = args.project_root.resolve()
    simulation = args.simulation_source.resolve()
    rl_root = args.rl_root.resolve()
    ifogsim = args.ifogsim_root.resolve()
    workload_path, model_path, risk_path = (
        args.workload.resolve(), args.model.resolve(), args.risk_state.resolve()
    )
    rows = [json.loads(line) for line in workload_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError("workload is empty")
    seeds = {str(row.get("seed")) for row in rows}
    profiles = {str(row.get("profile")) for row in rows}
    if len(seeds) != 1 or len(profiles) != 1:
        raise ValueError("workload rows must share one seed and one profile")

    commit = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    release = (args.jdk_home / "release").read_text(encoding="utf-8")
    java_version = next((line for line in release.splitlines() if line.startswith("JAVA_VERSION=")), None)
    if not java_version:
        raise ValueError("JAVA_VERSION not found in JDK release metadata")

    source_paths = [
        simulation / "org/fog/test/perfeval/OffloadingActionV2.java",
        simulation / "org/fog/test/perfeval/OffloadingActionV2ExecutionPlan.java",
        simulation / "org/fog/test/perfeval/OffloadingActionV2ContractTest.java",
        simulation / "org/fog/test/perfeval/RlOffloadingV2PartialIntegrationExperiment.java",
        simulation / "analyze_v2_policy_comparison.py",
        simulation / "run_v2_policy_comparison.ps1",
        simulation / "generate_v2_aba_workload.py",
        simulation / "create_v2_experiment_manifest.py",
        simulation / "analyze_v2_paired_seed_inference.py",
        simulation / "analyze_v2_aba_regime_inference.py",
        simulation / "test_aba_regime_inference.py",
        simulation / "test_generate_v2_aba_workload.py",
        simulation / "run_v2_aba_paired_seeds.ps1",
        simulation / "PAIRED_SEED_EVALUATION_GUIDE.md",
    ]
    source_paths.extend((rl_root / "src").rglob("*.py"))
    source_paths.extend(
        path for path in (rl_root / "config").rglob("*")
        if path.is_file() and path.suffix.lower() in {".json", ".yaml", ".yml"}
    )
    source_inventory = []
    for path in sorted(set(p.resolve() for p in source_paths)):
        source_inventory.append({
            "path": path.relative_to(root).as_posix(),
            "sha256": sha256(path),
        })

    jar_root = ifogsim / "jars"
    jars = sorted(jar_root.glob("*.jar"))
    if not jars:
        raise ValueError(f"no simulator JAR files found in {jar_root}")
    jar_inventory = [{"name": jar.name, "sha256": sha256(jar)} for jar in jars]

    manifest = {
        "schema_version": "v1",
        "experiment_id": args.output.name,
        "evaluation_split": "test",
        "workload_seed": rows[0]["seed"],
        "workload_profile": rows[0]["profile"],
        "workload_file": workload_path.name,
        "workload_sha256": sha256(workload_path),
        "model_sha256": sha256(model_path),
        "risk_state_sha256": sha256(risk_path),
        "source_git_commit": commit,
        "source_inventory": source_inventory,
        "java_version": java_version,
        "simulator_root": str(ifogsim),
        "simulator_jar_inventory": jar_inventory,
        "parameters": {
            "partition_overhead_ms": args.partition_overhead_ms,
            "merge_overhead_ms": args.merge_overhead_ms,
            "wan_latency_ms": args.wan_latency_ms,
            "watchdog_ms": args.watchdog_ms,
        },
        "policies": ["local", "edge", "cloud", "random", "rl_eval"],
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS", "workload_seed": rows[0]["seed"], "tasks": len(rows),
        "source_files": len(source_inventory), "simulator_jars": len(jar_inventory),
        "manifest_sha256": sha256(args.output), "output": str(args.output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
