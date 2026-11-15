# Protocol v2 — Partial and Full Execution Acceptance

**Date:** 2026-11-15
**Status:** PASS — all nine v2 action paths and a learned-policy training run executed through live Python and iFogSim.

## Implemented components

- **OffloadingActionV2.java:** stable nine-action catalogue, task feasibility mask, response integrity validation.
- **OffloadingActionV2ExecutionPlan.java:** action-to-branch plan and exact workload conservation.
- **RlOffloadingV2PartialIntegrationExperiment.java:** live Python v2 client, ratio-specific workers, Local+Edge and Local+Cloud branch execution, per-task barriers, merge Cloudlets, measured outcomes, watchdog failure reconciliation, baseline and training modes.
- **run_v2_partial_acceptance.ps1:** compiles the integration, runs every exact action, then runs a live learned-policy training episode.
- **validate_v2_partial_integration.py:** validates traces, task attribution, branch execution, overheads, merge ordering, outcomes, model save, and shutdown reconciliation.
- Python v2 baseline mode supports each exact catalogue action while retaining legacy Local/Edge/Cloud aliases and random baseline.

## Action execution mapping

| Action | Actual execution | Remote compute fraction |
|---|---|---:|
| LOCAL | Local full worker | 0% |
| EDGE_PARTIAL_25 | Local + Edge + merge | 25% |
| EDGE_PARTIAL_50 | Local + Edge + merge | 50% |
| EDGE_PARTIAL_75 | Local + Edge + merge | 75% |
| EDGE_FULL | Edge full worker | 100% |
| CLOUD_PARTIAL_25 | Local + Cloud + merge | 25% |
| CLOUD_PARTIAL_50 | Local + Cloud + merge | 50% |
| CLOUD_PARTIAL_75 | Local + Cloud + merge | 75% |
| CLOUD_FULL | Cloud full worker | 100% |

The percentage suffix is the remote compute fraction. The Local branch receives the complement. The six partial actions create exactly two independent branches per task. Cloud partial branches route over the Local → Edge → Cloud hierarchy and return to the Local merge module.

## Workload conservation and timing

Acceptance workload:
- Task compute: 10,003 MI
- Input data: 12,001 bytes
- Output data: 1,001 bytes
- Merge compute: 1,200 MI
- Merge output: 100 bytes

Integer rounding is performed once for the remote share; the exact remainder is assigned to Local. The validator checks that Local + remote equals the original MI, input bytes, and output bytes for every partial task. The current partition model ID, data-parallel-v1, assumes input and output bytes split in the same proportion as compute MI. That is a workload-profile assumption, not a universal property of divisible tasks; it must be validated against the actual workload before generalizing the model.

The simulator explicitly accounts for:
- Partition overhead: 3.0 simulated ms before branch tuple emission.
- Merge overhead: 2.0 simulated ms after both branch results arrive and before merge tuple emission.

These overhead values are **provisional experiment parameters**, not calibrated measurements. They must be calibrated or swept before performance claims are made.

## Acceptance command

Run from this directory:

**PowerShell:** .\run_v2_partial_acceptance.ps1

The runner compiles only project-owned Java files against the external iFogSim source/jars. It does not modify the external iFogSim checkout. It starts a fresh Java process and live Python v2 server for every exact-action case, the learned-policy training case, and a deliberate branch-failure case.

## Verified result

Latest full run:
**audit_output/v2_partial_acceptance_20261115_163550**

### Exact-action execution coverage

- 9/9 action cases passed.
- 2 overlapping tasks per action; 18 task lifecycles total.
- 6 partial action cases; 12 partial task lifecycles and 12 real merge Cloudlets.
- 3 full-placement action cases; 6 single-branch task lifecycles.
- All branch tuple IDs were unique within each run and attributed to the correct task.
- Every partial merge began only after both branch results arrived and after the configured merge overhead.
- Every task reported the original compound action ID in its outcome.
- All Python sessions acknowledged all outcomes and shut down with zero orphaned tasks.
- Python stderr was empty for all nine action cases.

### Learned-policy training integration

The same runner also starts Python in train mode and sends 30 divisible tasks through the simulator-selected policy:

- 30/30 decisions and outcomes reconciled.
- 17 partial tasks and 13 full-placement tasks were executed.
- The learner applied 30 measured-outcome updates.
- The model was saved as protocol 2.0 / format 2 with 972 states and nine actions.
- The observed training action distribution was:
  - EDGE_PARTIAL_25: 3
  - EDGE_PARTIAL_75: 4
  - CLOUD_PARTIAL_25: 1
  - CLOUD_PARTIAL_50: 4
  - CLOUD_PARTIAL_75: 5
  - LOCAL: 5
  - EDGE_FULL: 2
  - CLOUD_FULL: 6
- EDGE_PARTIAL_50 was not selected in this 30-task training episode. Its execution path was nevertheless independently covered by the exact-action baseline acceptance above.
- Training session shutdown reported zero orphaned tasks.

This is evidence that the live learner can select and train through both full and partial execution paths. It is not evidence of convergence, generalization, or performance superiority.

### Automated checks

- Java action-plan contract: 56 checks passed across all nine action plans.
- Python suite: 235 passed, one third-party pytest deprecation warning.
- The integration validator checked the exact-action suite and training episode.

## Failure-path acceptance

A fault-injection run dropped the Edge branch of an EDGE_PARTIAL_50 task before tuple arrival. The Local branch returned, but no merge was created. At the 1,000 simulated-ms watchdog horizon:
- the task was marked failed, not completed;
- the failure outcome retained action ID 2 and deadline_met=false;
- Python acknowledged the failed outcome;
- Python shutdown reported zero orphaned tasks and one reported outcome;
- the Java experiment exited non-zero to prevent a false PASS.

Artifact:
**audit_output/v2_partial_acceptance_20261115_163550/failure_drop_edge/partial_trace.jsonl**

## Interpretation and limitations

This is **action-path, training integration, and lifecycle acceptance**, not a performance result:
- The exact-action cases use deterministic Python baselines to guarantee coverage of all nine catalogue entries. They are not learned-policy comparisons.
- The 30-task training episode is a smoke test. It does not demonstrate convergence or generalization.
- The current topology is the existing Local → Edge → Cloud chain, not the proposed target multi-IoT / multi-Edge topology.
- Energy is not currently measured; outcomes report bandwidth and observed execution utilization, with energy omitted.
- Partition/merge overheads are provisional and need sensitivity analysis/calibration.
- The existing fixed 40/60 Local+Edge fixture remains separate from the v2 ratio-selected executor.

No claim that RL outperforms fixed baselines is supported by these acceptance runs.


## Parameterized overhead and deadline sensitivity

The experiment now accepts `--partition-overhead-ms`, `--merge-overhead-ms`, `--deadline-ms`, `--wan-latency-ms`, and `--watchdog-ms`. The PowerShell runner exposes these as `-PartitionOverheadMs`, `-MergeOverheadMs`, `-DeadlineMs`, `-WanLatencyMs`, and `-WatchdogMs`. Values are recorded in the trace `config` record. The watchdog is an execution horizon, separate from the per-task deadline.

A zero/nominal/high overhead sensitivity check passed with partition/merge values of 0/0 ms, 3/2 ms, and 10/10 ms. Each scenario covered all nine exact-action paths (two tasks each), a 30-task live learner integration episode, and the deliberate dropped-branch failure case. See `V2_OVERHEAD_SENSITIVITY.md` for commands, artifacts, and interpretation boundaries.

These are engineering sensitivity runs, not empirical calibration or policy-performance evidence. The fixed-action cases have only two tasks per action; the 30-task episodes remain integration smoke tests.
