# Experiment Runner Audit — 2026-11-17

## Scope

Historical audit of the V2 policy comparison runner and analyzer on branch `mark/risk-calibration-v1`. The limitations below describe the state at the time of this audit; subsequent commits address the task-outcome denominator and failure reconciliation items.

## Verified artifacts

- Runner: `deliverables/10_iFogSim_Simulation/Simulation_Source/run_v2_policy_comparison.ps1`
- Analyzer: `deliverables/10_iFogSim_Simulation/Simulation_Source/analyze_v2_policy_comparison.py`
- Experiment: `org/fog/test/perfeval/RlOffloadingV2PartialIntegrationExperiment.java`
- Protocol: `deliverables/08_RL_Model/docs/EXPERIMENT_PROTOCOL_V1.md`

## Correction committed

The runner previously passed `--risk-filter` and `--risk-state-in` to every fixed baseline (Local, Edge, Cloud, Random) as well as the learned evaluation arm. That confounds a fixed-action baseline with the proposed risk-calibration mechanism and can make a baseline fail if the risk filter rejects its forced action.

The runner now:
- passes only shared workload/simulator parameters to fixed baselines;
- passes `--risk-filter` and the calibration sidecar only to the learned evaluation arm.

This is a fairness correction, not a benchmark result.

## Important limitations still present

1. **Single seed only.** The runner launches one run per policy on one workload file. Its task-level pairing is useful for a pilot, but it is not the preregistered paired-seed evaluation (minimum 20 seeds).
2. **Policy coverage is incomplete.** It currently runs Local, Edge, Cloud, Random, and learned evaluation. It does not implement the full preregistered matrix: deterministic deadline-aware heuristic, partial-enabled heuristic, learner full-only/partial-enabled ablation, and risk/no-risk ablations.
3. **Random is not the deterministic heuristic.** It is a useful sanity baseline but cannot substitute for the specified minimum heuristic baseline.
4. **Task outcome handling (subsequently addressed).** At audit time, the analyzer could not represent FAILED or UNRESOLVED_AT_HORIZON in the all-generated-task denominator. Later commits added explicit evaluation mode, unified `task_outcome` records, outcome reconciliation, and coverage-aware metrics. See `PAIRED_SEED_EVALUATION_GUIDE.md` for the current behavior.
5. **No paired-seed inference.** The analyzer reports per-task differences for one seed. Tasks within a run are not independent experimental replicates. It does not compute paired-seed confidence intervals, paired tests, effect sizes, or multiple-comparison correction.
6. **No regime-shift recovery metrics.** It does not yet calculate recovery time, recovery miss burden, or A→B→A hysteresis.
7. **No held-out split enforcement.** The runner accepts one workload file; the analyzer does not verify a frozen train/validation/test manifest or test-seed disjointness.
8. **Partial/full stratification is incomplete.** It counts actions but does not provide the full preregistered stratification by task divisibility, split ratio, and remote tier.
9. **No proof of energy validity.** The runner's current output is not an energy benchmark.

## Interpretation

The runner should be treated as a **single-seed paired integration/pilot comparison**, not as the final experimental framework and not as evidence of statistical superiority. The analyzer's explicit single-seed interpretation is correct and should be retained.

The next safe implementation sequence is:
1. Extend the analyzer's task reconciliation to preserve ON_TIME, LATE, FAILED, and UNRESOLVED_AT_HORIZON without dropping generated tasks.
2. Add manifest-based seed pairing and verify identical task/config hashes across policies.
3. Add paired-seed inference with run/seed as the independent pairing unit.
4. Add A→B→A windowed recovery and cumulative miss burden.
5. Expand policy arms and ablations only after the workload and simulator interfaces expose those modes truthfully.

## Commit

Runner fairness correction: `73ba92fed8c8d8bd8a9979467e701f774d28239b`.
