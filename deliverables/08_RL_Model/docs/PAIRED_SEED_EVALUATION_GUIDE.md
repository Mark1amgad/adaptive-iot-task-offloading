# Running the V2 Paired-Seed Evaluation

## Scope

This guide describes the current runnable pilot and how to aggregate multiple seed-paired runs. It does not claim that the full preregistered policy matrix or A→B→A benchmark is implemented yet.

## 1. Freeze training before test

1. Select training and validation seeds before opening the test set.
2. Train the learner and risk-calibration sidecar using training/validation data only.
3. Freeze both artifacts. Record their hashes and the source commit.
4. Generate one immutable workload file per test seed. Each file must encode the exact task rows, arrival gaps, deadlines, divisibility and profile parameters for that seed.
5. Never regenerate a workload file between policy arms for the same seed.

## 2. Run the five currently supported policy arms per seed

From the repository's Simulation_Source directory:

    $seed = 101
    $workload = (Resolve-Path "..\..\..\workloads\test_seed_$seed.jsonl").Path
    $model = (Resolve-Path "..\..\..\artifacts\frozen_model.json").Path
    $risk = (Resolve-Path "..\..\..\artifacts\frozen_model.json.risk.json").Path
    $out = (Resolve-Path "..\..\..").Path + "\audit_output\test_seed_$seed"

    .\run_v2_policy_comparison.ps1 -WorkloadFile $workload -ModelIn $model -RiskStateIn $risk -OutputRoot $out

Repeat with a different test seed and a different immutable workload file. The runner produces one policy_comparison_summary.json per seed output root.

Current policy arms are Local, Edge, Cloud, Random, and learned evaluation. This is a pilot subset; it does not implement all nine core arms in EXPERIMENT_PROTOCOL_V1.md.

## 3. Aggregate across paired seeds

After at least two seed outputs exist (20 distinct paired seeds are required by the protocol), run:

    $summaryFiles = Get-ChildItem "..\..\..\audit_output\test_seed_*\policy_comparison_summary.json" |
        Sort-Object FullName |
        ForEach-Object { $_.FullName }

    python .\analyze_v2_paired_seed_inference.py @summaryFiles --output "..\..\..\audit_output\paired_seed_inference.json"

The analyzer:
- rejects duplicate workload seeds and mixed workload profiles;
- requires the five current policy arms and finite latency, miss-rate, and bandwidth metrics;
- computes paired seed-level differences (RL evaluation minus each baseline);
- reports paired bootstrap 95% confidence intervals, median/mean differences, standardized paired effect size, and Wilcoxon p-values when SciPy is installed;
- applies Holm correction across the reported baseline/metric comparisons;
- explicitly flags whether the 20-seed protocol minimum has been met.

For latency and bandwidth, negative differences mean the learner used less. For deadline-miss rate, a negative difference means fewer misses. Always interpret effect direction metric by metric.

## 4. What this does not yet solve

- The simulator currently rejects any run with failed tasks as a run-level acceptance failure. Therefore, current pilot summaries cannot yet represent FAILED and UNRESOLVED_AT_HORIZON in the all-generated-task denominator required by the protocol.
- The current runner executes one seed per invocation and only the five policy arms listed above.
- It does not yet execute A→B→A shifts or calculate recovery time / recovery miss burden.
- It does not yet implement the full-only vs partial-enabled and risk-filter ablations.
- The analyzer trusts the per-seed summaries' internal paired-workload checks. Preserve and inspect each raw trace and manifest; the summary file alone is not a complete provenance record.
- Do not claim final statistical evidence until there are at least 20 distinct paired test seeds per principal scenario, all training/test boundaries are audited, and task lifecycle failures are handled without dropping tasks.

## 5. Interpretation rule

A lower mean latency is not sufficient if deadline misses or unresolved tasks rise. Compare on-time ratio and deadline-miss rate first, then latency conditional on completion with coverage reported beside it. The run/seed is the independent unit for inference; tasks within one simulation run are not independent replications.
