# Research Brief — Version 2.0

**Working title:** Risk-Calibrated Adaptive Task Partitioning and Offloading under Repeated Workload and Network Shifts in the IoT–Edge–Cloud Continuum  
**Date:** 4 November 2026

## 1. Problem

Static offloading decisions can become unreliable when task arrivals, workload composition, network conditions, or edge capacity change. Binary full-task placement can also be suboptimal for genuinely divisible workloads. The proposed system therefore evaluates full execution at Local, Edge, and Cloud, as well as constrained partial execution between the IoT device and one remote tier for divisible tasks. A residual-calibrated feasibility layer screens candidate execution options against each task's individual deadline, while an online policy adapts to repeated operating-regime changes.

## 2. Research objectives

**RO1 — Dynamic system and workload model:** Model IoT, Edge, and Cloud resources, dynamic task arrivals, individual deadlines, variable network conditions, and both divisible and indivisible workload profiles.

**RO2 — Risk-calibrated hybrid placement and partitioning:** Estimate end-to-end completion time for legal full and partial execution options, calibrate prediction errors from observed outcomes, and filter options whose conservative completion estimate exceeds the task's remaining deadline budget.

**RO3 — Recovery-aware adaptation:** Evaluate policy and calibration recovery after workload/network changes, including repeated A→B→A transitions.

**RO4 — Multi-objective evaluation:** Prioritize deadline reliability and end-to-end latency; report resource balance and validated energy as secondary measures.

**RO5 — Reproducible and generalizable evaluation:** Compare baselines and ablations using identical task streams, paired seeds, held-out workload profiles, and controlled regime shifts.

## 3. Research questions

- **RQ1:** Does residual-calibrated feasibility filtering reduce deadline misses across full and partial execution options?
- **RQ2:** For divisible tasks, when does partial execution improve or worsen deadline reliability and tail latency versus full-only placement, and how do remote tier and split ratio affect the result?
- **RQ3:** How quickly does the adaptive policy recover after workload/network shifts, and what deadline/latency cost occurs during recovery?
- **RQ4:** Does the frozen policy generalize to held-out workload and network profiles?
- **RQ5:** What decision and update overhead is introduced by the expanded action set and calibration layer?

## 4. System and task model

Three execution tiers: Local (IoT device), Edge, and Cloud. Tasks receive an urgency class (`CRITICAL`, `TIME_SENSITIVE`, `DELAY_TOLERANT`) and an independent task-specific deadline before any policy acts.

Two task types:

- `INDIVISIBLE`: only `LOCAL`, `EDGE_FULL`, and `CLOUD_FULL` are legal.
- `DATA_PARALLEL_DIVISIBLE`: full actions plus partial actions where one fraction executes locally and the remainder executes at exactly one remote tier.

Initial discrete remote fractions: 0.25, 0.50, and 0.75. A partial task is never split across Edge and Cloud simultaneously. Arbitrary DAG decomposition and multi-remote splitting are out of scope. The data-partition rule must be explicit per synthetic workload profile; proportional work/data splitting is not assumed for all IoT tasks.

For a divisible task with total work `W` and remote fraction `alpha`:

`W_local = (1 - alpha) * W`  
`W_remote = alpha * W`

The completion time must account for both branches, transfer, queueing, partition, synchronization, and merge costs. A task is complete only after all required branches and the merge are complete.

## 5. Candidate method

The current online contextual-bandit-style learner remains the lightweight proposed policy, subject to a source-code audit of its exact update rule. Current project notes describe `gamma = 0`; this must not be presented as sequential DQN or conventional multi-step Q-learning. The legal-action mask disables partial actions for indivisible tasks.

For each legal execution option `a`:

`T_safe(i,a) = T_hat(i,a) + q_(1-epsilon,a)`

An option is feasible only when `T_safe(i,a) <= remaining_deadline_slack_i`. The residual quantile is estimated from prior completed tasks only. Use a predefined fallback hierarchy when a specific option has too few residual observations, and log the fallback level.

## 6. Experimental design

**Scenarios:** stable baseline; bursty arrivals; reduced bandwidth; increased WAN delay; Edge-capacity degradation; task-mix shift; repeated A→B→A shifts; combined stress only after single-factor experiments.

**Baselines:** Local-only, Edge-only, Cloud-only, full-only heuristic, partial-enabled heuristic, current learner without calibration, proposed learner with calibration; DQN only if a fair identical-action comparison is feasible.

**Ablations:** full-only vs partial-enabled; no feasibility filter; fixed vs rolling residual margin; frozen vs shift-aware recalibration; no adaptation vs online adaptation.

**Primary metrics:** on-time completion ratio, deadline miss rate, mean/median/P95/P99 end-to-end latency, recovery time, cumulative deadline misses during recovery.

**Secondary metrics:** throughput, CPU utilization, queue/backlog, load balance, decision time, model/update overhead. Energy is reported only after validating the simulator's energy model and units.

**Statistical protocol:** at least 20 paired seeds per principal scenario; target 30 where runtime permits. Use identical tasks, deadlines, topology, queue discipline, and exogenous traces across policy comparisons. Separate divisible and indivisible results.

## 7. Required implementation outputs

1. Versioned task/workload generator with divisible/indivisible task types and partition parameters.
2. iFogSim2 integration that actually executes and records local/remote branches, transfer, queue, split/merge, and final completion events.
3. Legal-action masking and full/partial action encoding in the learner.
4. Per-option completion-time prediction and residual calibration logs.
5. Full-only and partial-enabled baselines and paired ablation runs.
6. Reproducible per-task logs, scenario manifests, configuration hashes, and result tables.

## 8. Readiness and evidence boundary

The research specification, task schema, team responsibilities, and experiment plan are now documented in V2. Partial offloading is included as a constrained execution capability, not claimed as a novel idea by itself. Before any partial-offloading performance result is reported, the simulator must demonstrate correct two-branch execution and end-to-end join/merge timing. Smoke-test results must be labelled as implementation validation; statistically supported performance conclusions require the paired benchmark protocol above.
