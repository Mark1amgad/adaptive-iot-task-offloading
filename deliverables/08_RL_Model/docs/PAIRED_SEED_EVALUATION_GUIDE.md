# Running the V2 Paired-Seed Evaluation

## Scope

This guide describes the current runnable pilot and how to aggregate multiple seed-paired runs. It does not claim that the full preregistered policy matrix or A→B→A benchmark is implemented yet.

## 1. Freeze training before test

1. Select training and validation seeds before opening the test set.
2. Train the learner and risk-calibration sidecar using training/validation data only.
3. Freeze both artifacts. The runner records SHA-256 hashes for the model, risk sidecar, workload, source commit, Java runtime, iFogSim JAR inventory, and simulator parameters.
4. Generate one immutable workload file per test seed. Each file must encode the exact task rows, arrival gaps, deadlines, divisibility, seed, and profile parameters for that seed.
5. Never regenerate a workload file between policy arms for the same seed. The runner hashes the exact file bytes, not its parsed JSON content.

## 2. Run the five currently supported policy arms per seed

From the repository's Simulation_Source directory:

    $seed = 101
    $workload = (Resolve-Path "..\..\..\workloads\test_seed_$seed.jsonl").Path
    $model = (Resolve-Path "..\..\..\artifacts\frozen_model.json").Path
    $risk = (Resolve-Path "..\..\..\artifacts\frozen_model.json.risk.json").Path
    $out = (Resolve-Path "..\..\..").Path + "\audit_output\test_seed_$seed"

    .\run_v2_policy_comparison.ps1 -WorkloadFile $workload -ModelIn $model -RiskStateIn $risk -OutputRoot $out

Repeat with a different test seed and a different immutable workload file. The runner explicitly enables `--evaluation-mode` for every policy arm and produces one `policy_comparison_summary.json` per seed output root. In this mode, task-level failures and watchdog-censored tasks are reconciled and retained in the all-generated-task denominator; protocol errors, missing acknowledgements, and orphaned tasks still fail the run.

Current policy arms are Local, Edge, Cloud, Random, and learned evaluation. This is a pilot subset; it does not implement all nine core arms in EXPERIMENT_PROTOCOL_V1.md.

## 3. Provenance and integrity checks

The runner creates `experiment_manifest.json` at the output root and copies the byte-identical manifest into every policy directory. The manifest records:
- exact workload SHA-256, seed, profile, and test split;
- frozen model and risk-calibration sidecar SHA-256;
- source Git commit and Java runtime;
- SHA-256 inventory of the iFogSim JAR files;
- simulator parameters and the exact five policy arms.

The policy analyzer refuses to summarize a run if the workload hash differs, a policy manifest is missing/modified, a run's simulator parameters differ, or workload seed/profile do not match the manifest. Each per-seed summary includes a manifest hash and a provenance fingerprint.

Across seeds, the paired inference analyzer requires the same provenance fingerprint. Thus all seeds in one inferential batch must use the same source commit, model, risk state, Java/iFogSim binaries, and simulator parameters. Only the workload seed/content should vary. The inference analyzer also rejects summaries not explicitly marked as test split.

## 4. Aggregate across paired seeds

After at least two seed outputs exist (20 distinct paired seeds are required by the protocol), run:

    $summaryFiles = Get-ChildItem "..\..\..\audit_output\test_seed_*\policy_comparison_summary.json" |
        Sort-Object FullName |
        ForEach-Object { $_.FullName }

    python .\analyze_v2_paired_seed_inference.py @summaryFiles --output "..\..\..\audit_output\paired_seed_inference.json"

The analyzer:
- rejects duplicate workload seeds and mixed workload profiles;
- requires the five current policy arms and finite deadline-miss/bandwidth metrics; conditional latency inference is included only when every seed/policy has at least one completion;
- computes paired seed-level differences (RL evaluation minus each baseline);
- reports paired bootstrap 95% confidence intervals, median/mean differences, standardized paired effect size, and Wilcoxon p-values when SciPy is installed;
- applies Holm correction across the reported baseline/metric comparisons;
- explicitly flags whether the 20-seed protocol minimum has been met.

For latency and bandwidth, negative differences mean the learner used less. For deadline-miss rate, a negative difference means fewer misses. Always interpret effect direction metric by metric. If any policy has zero completed tasks in any seed, latency inference is withheld for the entire paired batch rather than silently conditioning on a selected subset of seeds; deadline-miss and bandwidth inference remain available.

## 5. A→B→A regime-shift pilot

Generate a deterministic 30-task-per-phase A→B→A workload (90 tasks total):

    python .\\generate_v2_aba_workload.py --seed 101 --tasks-per-phase 30 --output "..\\..\\..\\workloads\\test_aba_seed_101.jsonl"

Then run the ordinary five-arm comparison runner with this workload, a frozen model, and its matching risk sidecar. The runner and simulator now:
- replay the same A task template in phases A1 and A2;
- increase task MI/input volume and arrival pressure in B while WAN latency changes from 45 ms to 160 ms;
- restore the A task template and WAN latency at A2;
- record each phase transition and per-task regime/WAN identity.

The policy analyzer adds phase-specific deadline-miss rate, completion coverage, and completed-task latency. It reports A2 recovery as the first sliding 10-task window with all tasks completed, deadline-miss rate within 5 percentage points of A1, and median latency within 10% of A1. Recovery time runs from the A2 transition to the last completion in that qualifying window. A missing qualifying window is reported as not recovered within the observed A2 horizon.

This is a joint workload/network stress pilot, not a network-only causal experiment. Run separate factor-isolation scenarios before attributing any observed effect to WAN latency alone. One seed validates execution only; the paired-seed protocol still requires at least 20 test seeds per principal scenario.

## 6. What this does not yet solve

- The current runner executes one seed per invocation and only the five policy arms listed above.
- It does not yet execute A→B→A shifts or calculate recovery time / recovery miss burden.
- It does not yet implement the full-only vs partial-enabled and risk-filter ablations.
- The analyzer validates each run against its manifest, but preserve and inspect raw traces and manifests; a summary alone is not a complete provenance record.
- Do not claim final statistical evidence until there are at least 20 distinct paired test seeds per principal scenario and all training/test boundaries are audited.

## 7. Interpretation rule

A lower mean latency is not sufficient if deadline misses or unresolved tasks rise. Compare on-time ratio and deadline-miss rate first, then latency conditional on completion with coverage reported beside it. The run/seed is the independent unit for inference; tasks within one simulation run are not independent replications.
