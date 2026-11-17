# Experimental Protocol V1 — Preregistered Evaluation Plan

**Applies to:** Research Specification V2 / branch `mark/risk-calibration-v1`  
**Status:** Protocol draft for implementation freeze; parameter values marked TBD must be selected on training/validation data before held-out testing.  
**Purpose:** Convert the research questions into an executable, auditable comparison. This document is not evidence that the benchmark has been run.

## 1. Claims this protocol can and cannot test

The primary claim under test is whether a residual-calibrated feasibility layer improves deadline reliability for a contextual placement policy under changing conditions, without unacceptable latency or decision overhead.

The partial-offloading claim is conditional: for explicitly divisible profiles, compare partial-enabled and full-only policies on identical tasks. Partial offloading is an established capability, not a novelty claim by itself.

No claim of universal superiority is permitted. Report trade-offs and scenario-specific effects. Integration acceptance, unit tests, and smoke runs are not benchmark results.

## 2. Experimental factors and policy arms

### Core policy arms

| ID | Policy | Legal actions | Risk layer | Online learner |
|---|---|---|---|---|
| P0 | Local-only | LOCAL | No | No |
| P1 | Edge-only | EDGE_FULL | No | No |
| P2 | Cloud-only | CLOUD_FULL | No | No |
| P3 | Deterministic full-only heuristic | LOCAL, EDGE_FULL, CLOUD_FULL | No | No |
| P4 | Deterministic partial-enabled heuristic | All legal V2 actions | No | No |
| P5 | Contextual learner, full-only | LOCAL, EDGE_FULL, CLOUD_FULL | No | Yes |
| P6 | Contextual learner, partial-enabled | All legal V2 actions | No | Yes |
| P7 | Risk-calibrated contextual learner, full-only | LOCAL, EDGE_FULL, CLOUD_FULL | Yes | Yes |
| P8 | Risk-calibrated contextual learner, partial-enabled | All legal V2 actions | Yes | Yes |

The heuristic must be specified before test: among legal actions, choose the minimum predicted end-to-end completion time; ties use a deterministic fixed order. It must use the same predictor inputs as the learner. Do not quietly give the proposed method a stronger predictor.

P5 vs P7 isolates the risk layer for indivisible/full-only decisions. P6 vs P8 isolates it with partial actions. P5 vs P6 and P7 vs P8 isolate the partial-action capability. P3/P4 show whether learning adds value beyond a transparent heuristic.

### Risk-calibration ablations

Run these on the same policy and workload traces:
- R0: no feasibility filter.
- R1: fixed residual safety margin estimated on validation data.
- R2: rolling empirical residual quantile.
- R3: rolling residual quantile with predeclared shift-aware refresh rule, only if the trigger is implemented and logged.

Do not compare a rolling/shift-aware calibrator to a fixed margin using different training data or different task streams.

## 3. Scenario matrix

Use one-factor-at-a-time scenarios before combined stress. Every scenario manifest must include a unique ID, workload profile, network profile, resource profile, queue discipline, task horizon, warm-up/cool-down policy, and shift timestamps.

| Scenario family | A regime | B regime | Sequence / purpose |
|---|---|---|---|
| S0 Stable | Nominal | — | A throughout; baseline |
| S1 Arrival shift | Nominal arrivals | Burst or higher arrival rate | A→B; workload intensity response |
| S2 Task-mix shift | Nominal task mix | Larger/heavier task mix | A→B; workload composition response |
| S3 Network shift | Nominal bandwidth/propagation | Degraded bandwidth OR increased delay | A→B; isolate network factors |
| S4 Edge-capacity shift | Nominal edge capacity | Reduced capacity/background load | A→B; isolate edge congestion |
| S5 Repeated workload shift | Workload A | Workload B | A→B→A; recovery and hysteresis |
| S6 Repeated network shift | Network A | Network B | A→B→A; recovery and hysteresis |
| S7 Combined stress | Nominal | Selected workload + network degradation | A→B→A; secondary stress test |
| S8 Held-out generalization | Training/validation profiles excluded | Unseen profile | Frozen-policy evaluation; adaptation reported separately |

The primary shift tests are S5 and S6. S7 is secondary because combined changes make causal attribution harder. Do not expose future regime labels or shift timestamps to the policy.

## 4. Pairing, seeds, and data splits

- Minimum 20 paired seeds per principal scenario; target 30 if simulator runtime permits.
- For each seed, generate one immutable task stream and exogenous network/resource trace. Replay the exact same stream/trace for every policy arm.
- Separate random streams for task generation, network perturbation, and policy exploration. Record each seed independently.
- Keep task IDs stable across policies and runs. A task's deadline, divisibility flag, profile, and workload parameters must not depend on the selected action.
- Split by seed and scenario family, not by randomly sampling task rows from a run:
  - Training: learner fitting and initial predictor fitting.
  - Validation: reward/threshold/window/epsilon/fallback selection and recovery tolerance selection.
  - Test: held out until every parameter and comparison is frozen.
- Do not use test outcomes to tune calibration, action heuristics, reward weights, deadline ranges, or recovery thresholds.
- Save code revision, simulator revision, dependency versions, config hash, scenario manifest, and raw logs for every run.

## 5. Task-level lifecycle and denominator

Every generated task must be accounted for exactly once at the end of the run. Preserve both the decision reason and final outcome.

Required final outcomes:
- `ON_TIME`
- `LATE`
- `FAILED`
- `UNRESOLVED_AT_HORIZON`

Also preserve `NO_FEASIBLE_SITE_AT_ARRIVAL` as a decision-time reason/flag. It is not a terminal outcome if the fallback task later completes or fails.

Primary denominator is **all generated tasks**, not only completed tasks:
- on-time = ON_TIME / generated
- miss = (LATE + FAILED + UNRESOLVED_AT_HORIZON) / generated
- no-feasible-at-arrival rate = tasks flagged NO_FEASIBLE_SITE_AT_ARRIVAL / generated

Report counts alongside percentages. Never discard unfinished tasks or convert them into successes. A task completed after its absolute deadline is LATE even if the simulator reports successful execution.

## 6. Metric definitions

Let N be generated tasks; arrival_i, completion_i, and deadline_i are simulator timestamps in one canonical time unit.

### Primary outcomes
1. **On-time completion ratio:** count(completion_i exists AND completion_i <= deadline_i) / N.
2. **Deadline miss rate:** count(LATE, FAILED, UNRESOLVED_AT_HORIZON) / N.
3. **End-to-end latency:** completion_i - arrival_i. Report mean, median, P95, P99 among completed tasks, and separately report completion coverage. Do not present completed-only latency without its coverage denominator.
4. **Recovery time:** after a shift, first evaluation window at which the rolling on-time ratio returns within the preregistered tolerance of the post-shift stable target for K consecutive windows. Define window length W, tolerance delta, and K using validation data and freeze them before test.
5. **Recovery miss burden:** number of deadline misses from shift time through the recovery point; also report misses per generated task during this interval.
6. **Decision overhead:** wall-clock policy decision latency (median/P95/P99), calibration update time, and model memory/size. Measure separately from simulated task latency.

### Secondary outcomes
- Throughput: completed tasks per simulated second.
- Resource balance: per-node utilization distribution and queue/backlog over time; clearly distinguish reserved capacity from active task utilization.
- Network bytes: measured transferred bytes, with parent-child and WAN bytes separated if available.
- Energy: report only after validating the simulator power model, units, idle-vs-dynamic accounting, and network transmission accounting. Otherwise mark unavailable; do not infer it from CPU utilization.

### Stratification
Always report divisible and indivisible tasks separately. For divisible tasks, stratify by selected remote fraction (25/50/75/full) and remote tier (Edge/Cloud). Also report the fraction of generated tasks for which partial actions were legal and the fraction actually assigned a partial action.

## 7. Risk calibration protocol

For each task-option pair, log:
- predicted end-to-end completion time at decision time;
- selected calibration group and sample count;
- residual quantile/margin used;
- safe completion estimate and remaining deadline slack;
- feasible mask and fallback reason;
- actual end-to-end completion time and signed residual after outcome.

Residual is actual minus predicted; negative residuals are valid. Calibration must use only outcomes observed before the current decision.

Fallback hierarchy:
1. exact action and split ratio;
2. destination/mode family;
3. pooled conservative margin.

Minimum sample count per group, rolling window length, target tail probability epsilon, and quantile convention must be selected on validation data. Record every fallback to a broader group.

For a finite empirical residual sample of size n, document the quantile index convention explicitly. A conservative order-statistic convention is rank = min(n, ceil((n+1)(1-epsilon))); report the realized rank and sample count. If n is too small to support the requested tail level, use the predeclared broader group rather than pretending the tail estimate is reliable.

A rolling residual quantile is **not** a formal deadline guarantee. Distribution shifts can invalidate exchangeability; report empirical exceedance/coverage by regime and calibration group. Do not describe the filter as deterministic or guaranteed.

## 8. Partial-execution validity gates

Before a workload profile is admitted to the partial-offloading benchmark:
- its divisibility contract must explain why work and associated data can be partitioned;
- local and remote branches must represent the assigned computation fractions;
- partition/synchronization/merge costs must be represented in the simulator;
- branch outputs must be correlated to one parent task and joined exactly once;
- task-level completion must occur only after the merge result is produced;
- MI/work, input bytes, and output bytes must satisfy profile-specific conservation assertions;
- full-only and partial-enabled runs must use identical parent tasks and exogenous traces.

If any gate fails, exclude that profile from measured partial-offloading claims and document the limitation. A synthetic proportional split is valid only for the synthetic profile that explicitly defines it.

## 9. Statistical analysis

For every primary policy comparison:
- compute per-seed paired differences on the same task stream/trace;
- report mean paired difference, median paired difference, 95% paired bootstrap confidence interval, and a standardized effect size where appropriate;
- use a paired non-parametric test (e.g. Wilcoxon signed-rank) when assumptions for a paired parametric test are not defensible;
- correct for multiple primary comparisons (Holm procedure is a reasonable default);
- report both statistical uncertainty and practical effect size.

Do not treat individual tasks from the same simulation seed as independent experimental replicates. The seed/run is the pairing unit; task-level bootstrap may be a supplementary within-run uncertainty analysis, not a replacement for paired-seed inference.

For latency, account for censored/unresolved tasks explicitly. Completed-only latency is a conditional distribution and can look artificially good when a policy leaves difficult tasks unfinished; always pair it with completion coverage and deadline miss rate.

## 10. Required run artifacts

Each run directory must contain:
- `manifest.json`: scenario, seed streams, task generator version, simulator/code revision, configuration hash, policy ID, and split (train/validation/test).
- `tasks.csv`: one row per generated parent task, stable task ID, task class, divisibility, deadline, decision reason, selected action, and final outcome.
- `events.csv`: timestamped branch, queue, transfer, execution, merge, failure, and completion events with parent/branch IDs.
- `predictions.csv`: option-level predictions, calibration group, residual margin, safe estimate, slack, and feasibility mask.
- `summary.json`: aggregate counts and metrics, plus schema/version identifiers.
- `checksums.txt`: hashes for immutable manifests and raw logs.

## 11. Benchmark release gate

A run is eligible for the final benchmark only if:
1. task lifecycle reconciliation has zero missing/duplicate terminal outcomes;
2. timing units and end-to-end decomposition pass manual/automated checks;
3. legal action masking is correct for divisible and indivisible tasks;
4. partial-execution gates pass for every included divisible profile;
5. calibration has no look-ahead leakage;
6. paired run manifests match except for the policy-specific fields;
7. held-out test parameters were frozen before test execution;
8. raw logs and environment/code metadata are retained.

## 12. Current unresolved implementation inputs

The following are deliberately not invented here and must be confirmed from the integrated workload/simulator:
- final task-profile and deadline distributions;
- arrival process parameters and scenario magnitudes;
- canonical MI/MIPS/time units and exact queue/transfer timing semantics;
- whether the simulator supports a valid Local+Cloud partial path as well as Local+Edge;
- whether active Edge node selection is policy-controlled or deterministic;
- calibration window length, minimum sample count, epsilon, and refresh trigger;
- recovery window W, tolerance delta, and consecutive-window count K;
- energy model validity.

These values are configuration decisions, not opportunities to tune against test outcomes.
