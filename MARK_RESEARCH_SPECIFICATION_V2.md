# Research Specification — Version 2.0

**Project:** Risk-Calibrated Adaptive Task Partitioning and Offloading under Repeated Workload and Network Shifts in the IoT–Edge–Cloud Continuum  
**Prepared by:** Research Lead (Mark)  
**Status:** Working specification frozen for immediate implementation; simulator feasibility gates are listed in Section 19  
**Date:** 4 November 2026

> This document freezes the first-scope research problem and the data requirements. It does not claim that the proposed combination is globally novel. Novelty remains a hypothesis that must be defended through a complete comparison with the closest 2025–2026 work.

## 1. Working title

**Risk-Calibrated Adaptive Task Partitioning and Offloading under Repeated Workload and Network Shifts in the IoT–Edge–Cloud Continuum**

## 2. Problem statement

A fixed offloading policy may perform poorly when task arrivals, task characteristics, network conditions, and edge capacity change over time. It may also make poor decisions when it is forced to choose only between fully local execution and fully remote execution, even when a workload is explicitly divisible. A learning-based policy may adapt to observed conditions, but its completion-time estimates can become unreliable after a workload or network shift.

The project will investigate a constrained hybrid decision problem: select Local, Edge, or Cloud execution, and, for explicitly divisible workloads, select whether to execute the task fully at one tier or split it between the IoT device and one remote tier. A residual-calibrated feasibility layer will screen complete and partial execution options against each task’s individual deadline. The policy will then be evaluated under repeated workload and network shifts.

## 3. Research gap and contribution boundary

The project will not claim novelty from any of the following in isolation:

- Selecting Local, Edge, or Cloud using reinforcement learning.
- Adding task deadlines or reporting P95 latency.
- Using a lightweight contextual bandit.
- Evaluating multiple workload or network conditions.
- Treating partial offloading itself as a novel contribution. Partial offloading is established in the literature; the contribution must be in the risk-calibrated decision and evaluation design, not merely adding a split ratio.

These concepts have close prior art. The intended contribution is narrower:

1. A **risk-calibrated feasibility layer for hybrid execution options**. It estimates end-to-end completion time for full and permitted partial execution options, calibrates prediction error from observed outcomes, and excludes options whose conservative completion estimate exceeds the task’s remaining deadline budget.
2. A **recovery-aware adaptation study under repeated, controlled regime shifts**, measuring how the policy and its calibration recover, including transient deadline violations, tail latency, and adaptation overhead.
3. A **controlled full-versus-partial offloading evaluation** that isolates when bounded task partitioning helps or harms deadline reliability and latency, particularly under changing network and edge conditions.
4. A reproducible evaluation that reports results separately for divisible and indivisible workloads.

The literature scan was refreshed through 4 November 2026. Close prior art includes forecast-driven LinUCB offloading (JNCA, 2026), contextual-bandit deadline-feasibility filtering (LITO, 2026), explicit execution-start timing control (arXiv:2608.00892, August 2026), deterministic deadline/priority-aware IoT–Edge–Cloud offloading (arXiv:2610.24617, October 2026), priority-aware DRL offloading (Internet of Things, September 2026), and a newly published healthcare-IoT scheduling study coupling calibration with temporal-shift robustness (Discover Computing, 2 November 2026). These works mean that generic calibration, urgency classes, distribution-shift testing, timing control, and partial offloading are not novelty claims. A 2025 Journal of Network and Computer Applications paper directly studies delay-aware partial task offloading in IoT–fog–cloud networks; a 2024 review also warns that arbitrary task splitting and assuming compute demand scales linearly with input size can be unrealistic. The specific candidate to test is residual-calibrated *end-to-end completion-time feasibility across full and constrained partial execution options*, evaluated jointly with recovery under repeated workload/network shifts. The partial-offloading comparison is a controlled capability of the method, not a standalone novelty claim. This remains provisional until those nearest works are compared in detail.

## 4. Final research objectives

**RO1 — Dynamic system and workload model**  
Model a heterogeneous IoT–Edge–Cloud environment with dynamic task arrivals, variable task sizes and computational demands, per-task deadlines, explicitly divisible and indivisible workload profiles, bounded partition ratios, changing link conditions, and changing edge-resource availability.

**RO2 — Risk-calibrated hybrid placement and partitioning**  
Develop a hybrid placement-and-partitioning policy that evaluates complete execution at Local/Edge/Cloud and constrained partial execution between Local and one remote tier for divisible tasks. Calibrate end-to-end completion-time prediction errors from observed outcomes and reject candidate options whose conservative completion-time estimate exceeds the task's remaining deadline budget.

**RO3 — Recovery-aware adaptation**  
Investigate and improve the policy's response to workload and network distribution shifts, including repeated A→B→A regime changes. Measure recovery time, transient deadline violations, tail latency, and adaptation overhead.

**RO4 — Multi-objective performance evaluation**  
Evaluate deadline reliability and end-to-end latency as primary outcomes, and resource balance and energy consumption as secondary outcomes where the simulator supports valid measurement. Quantify trade-offs instead of assuming one policy dominates every objective.

**RO5 — Reproducible and generalizable evaluation**  
Compare the proposed policy with fixed, heuristic, and learning baselines using paired workloads/seeds, disjoint train/validation/test scenarios, and held-out workload/network conditions. Include a held-out topology test if the simulator supports it reliably.

## 5. Research questions

- **RQ1 — Deadline feasibility:** Does residual-calibrated feasibility filtering across full and partial execution options reduce per-task deadline violations compared with the same adaptive policy without calibration and with strong non-learning baselines?
- **RQ2 — Full-versus-partial trade-off:** For divisible tasks, when does partial execution improve or worsen deadline reliability and mean/P95/P99 end-to-end latency compared with full-only placement, and how does the selected split ratio and remote tier affect the outcome? Also quantify throughput and resource balance; energy is included only if validated.
- **RQ3 — Adaptation and recovery:** After workload or network conditions change, how quickly does the policy regain its stable-regime performance, and how many deadline violations or how much tail-latency degradation occur during recovery?
- **RQ4 — Generalization:** How does the frozen policy perform on held-out workload profiles, network conditions, and, if feasible, a different topology/capacity configuration?
- **RQ5 — Decision cost:** What decision-time, action-selection, and model/update overhead does the lightweight learner incur as the legal action set expands from full-only to full-plus-partial execution options?

## 6. Scope decisions for Milestone 1

### Included

- Three execution tiers: **Local, Edge, Cloud**.
- Full-task placement at Local, Edge, or Cloud, plus constrained partial offloading for tasks explicitly marked divisible. A partial task is split between the IoT device and exactly one remote tier (Edge or Cloud).
- Mixed-urgency workload classes: **Critical, Time-Sensitive, Delay-Tolerant**.
- A distinct relative and absolute deadline for every task, generated before any policy decision.
- Risk-calibrated feasibility screening based on predicted completion time and observed prediction errors.
- Online adaptation under controlled and repeated workload/network shifts.
- Multi-objective measurement: deadline reliability, end-to-end latency, resource balance, and energy only after energy-model validation.

### Explicitly excluded from Milestone 1

- An explicit **Defer / Wait / Execute Later** action. Tasks are dispatched for a decision at arrival; queue waiting that naturally occurs inside the simulator is still included in end-to-end latency.
- Arbitrary task decomposition, dependency-aware DAG/workflow scheduling, splitting one task across multiple remote sites, and multi-agent coordination. Partial offloading is limited to independent divisible workloads split between Local and one remote tier.
- A claim that execution-start timing control is novel.
- Federated learning, meta-RL, forecasting modules, or a newly invented deep-RL architecture unless later evidence requires one.
- Using anonymous ECW/SMD numeric channels as CPU, memory, network, or failure measurements without authoritative mapping.

**Reason for excluding explicit deferral:** execution-start timing control is already addressed by recent work, and adding a wait action would materially expand queueing, deadline-slack, and action-space implementation. It is not required to test the selected contributions in this milestone.

## 7. System model

The target environment contains:

- **IoT devices:** task sources and local execution resources.
- **Edge tier:** one or more edge servers with separately configured compute capacity and network paths.
- **Cloud tier:** a remote execution resource with its own capacity and network delay.
- **Network:** links with configurable bandwidth and propagation/communication delay. Jitter or loss is included only if the simulator model and logging support it correctly.

The current project notes describe a development topology with 4 IoT devices, 2 Edge nodes, and 1 Cloud node. Treat this as the initial implementation topology, not as a final generality claim. If the two Edge nodes are not independently exposed to the policy, retain the three high-level actions and log the actual selected Edge node ID. Do not silently imply that Edge-1 and Edge-2 are separate learned actions unless the code exposes them as such.

## 8. Task and urgency model

Every task has an application/workload profile and an urgency class. These are separate concepts.

**Urgency classes:**

- `CRITICAL`: tight task-specific deadline.
- `TIME_SENSITIVE`: intermediate task-specific deadline.
- `DELAY_TOLERANT`: wider task-specific deadline.

The workload generator must distinguish divisible data-parallel profiles from indivisible profiles. Only the former may use partial execution. For the first benchmark, the remotely offloaded share is selected from a small fixed set of ratios `{0.25, 0.50, 0.75}`; `0.0` denotes Local-only and `1.0` denotes full execution at the selected remote tier. The share is the fraction of total divisible computation and its associated input/output data assigned to the remote branch. This proportional mapping is a declared synthetic workload assumption, not a universal property of IoT applications. Each divisible profile must include explicit partition and merge overhead parameters.

The exact deadline ranges must be calibrated against the verified simulator topology and workload profiles. They must be stored in a versioned configuration file and frozen before final test runs. They must not be selected based on the action chosen by a policy or on test-set results.

For task i:

- `arrival_time_i`: simulator arrival time.
- `relative_deadline_i`: the task's deadline budget, determined at generation time.
- `absolute_deadline_i = arrival_time_i + relative_deadline_i`.
- `completion_time_i`: actual end-to-end completion timestamp if completed.
- `slack_i(t) = absolute_deadline_i - current_time`.

All policies must receive the same task stream, class, and deadline. The urgency class must not be used to fabricate different task outcomes. Any queue discipline (e.g., FCFS or EDF) must be identical across policies and documented; do not change queue discipline at the same time as the placement policy in the primary comparison.

## 9. Candidate state, action, and policy interface

### Candidate state/context

At decision time, provide only information available to the policy at that time:

**Task context**
- Input size (bytes).
- Required computation (MI or a clearly documented cycle unit; choose one canonical unit in the simulator adapter).
- Optional output size and memory requirement if modeled.
- `splittability` (`INDIVISIBLE` or `DATA_PARALLEL_DIVISIBLE`).
- For divisible tasks: `partition_model_id`, configured split/merge overheads, and the documented input/output partition rule.
- Urgency class.
- Remaining deadline/slack.

**System/network context**
- Local, Edge, and Cloud CPU utilization or available capacity, with exact definitions and units.
- Queue length and/or estimated queue wait for each candidate site.
- Link bandwidth and propagation/communication delay to each candidate site.
- Resource availability/load at the candidate site.
- Current workload/regime indicators only if they are observable and available online.

**Risk context**
- Predicted end-to-end completion time for each legal execution option (including each allowed split ratio).
- Current calibrated residual allowance/upper-bound margin for the corresponding option or documented fallback group.
- Feasibility flag for each legal option.

Do not include future test labels, future regime identifiers, actual completion times, or any post-decision information in the state.

### Action space

For every task, legal actions are determined by its workload profile:

- Indivisible task: `LOCAL`, `EDGE_FULL`, `CLOUD_FULL`.
- Divisible task: `LOCAL`, `EDGE_FULL`, `CLOUD_FULL`, `EDGE_PARTIAL_25`, `EDGE_PARTIAL_50`, `EDGE_PARTIAL_75`, `CLOUD_PARTIAL_25`, `CLOUD_PARTIAL_50`, `CLOUD_PARTIAL_75`.

The suffix denotes the fraction of total task work assigned to the remote tier. For a partial action, the remaining fraction executes locally. Do not split a task across Edge and Cloud simultaneously. Record action type, remote fraction, local fraction, remote tier, actual selected Edge node ID, and partition/merge overhead. If the policy cannot select individual Edge nodes, record the deterministic Edge-node selection rule.

There is no explicit defer action in this milestone.

### Learning-policy choice and naming accuracy

The proposed lightweight learner for this implementation is the existing online contextual-bandit-style policy, subject to a code audit of its exact update rule. Current project validation notes describe `gamma = 0`; this is not sequential DQN or conventional multi-step Q-learning. Name the method accurately in code, plots, and the paper. The legal action mask must prevent partial actions for indivisible tasks.

Use DQN only as an additional learning baseline if a fair implementation is feasible with the same observable state, legal action mask, task stream, and evaluation budget. Do not delay the core implementation for DQN, and do not describe the contextual bandit as deep RL.

## 10. Risk-calibrated feasibility layer

For each task i and legal execution option a, estimate the total task completion time. For a full action, include the applicable queue, input transfer, execution, and result-transfer components. For a partial action with remote fraction α, predict both branches:

`T_local(i,a) = local_queue_wait + (1-α) * required_MI / effective_local_MIPS`

`T_remote(i,a) = input_transfer(α) + remote_queue_wait + α * required_MI / effective_remote_MIPS + result_transfer(α)`

`T_hat(i,a) = partition_overhead + max(T_local(i,a), T_remote(i,a)) + merge_overhead`

The split model assumes independent divisible work and proportionally partitionable input/output data for the relevant synthetic workload profile. Validate these assumptions and every timing component against simulator events. Do not apply this formula to indivisible tasks.

Avoid double-counting queue or network components. Validate each component against simulator event logs.

After completed tasks, calculate the option-specific prediction residual:

`e(i,a) = actual_end_to_end_completion_time(i,a) - predicted_end_to_end_completion_time(i,a)`.

For the first implementation, maintain bounded rolling residual windows keyed by execution-option family and split ratio where sample counts permit. Use a predeclared fallback hierarchy (exact option → destination/mode family → pooled conservative margin) when an option has insufficient history. Log the calibration group and sample count used. Derive a conservative residual quantile `q_(1-epsilon,a)` from prior completed tasks only. Do not split calibration further by load/workload bucket until each bucket has enough observations; sparse buckets must fall back to a documented broader option-family estimate. Compare a fixed margin, a rolling window, and (only if it can be implemented cleanly) a change-triggered refresh as ablations.

`T_safe(i,a) = T_hat(i,a) + q_(1-epsilon,a)`

`A_i = { a in LegalActions(i) : T_safe(i,a) <= slack_i }`

The learner selects among the feasible full/partial execution options in `A_i`. If `A_i` is empty, apply a documented fallback (lowest estimated violation risk / earliest conservative completion) and log `NO_FEASIBLE_SITE_AT_ARRIVAL`. Do not remove such tasks from the denominator or report them as ordinary successful decisions.

This is empirical risk calibration, not a formal deterministic guarantee. Calibration parameters, window length, minimum sample count, and epsilon must be chosen using training/validation data, then frozen before held-out testing. The shift-adaptation mechanism may update from online observations according to a pre-registered rule; all updates must be logged.

## 11. Multi-objective objective and metrics

### Primary outcomes

1. **On-time completion ratio / deadline reliability**: number of generated tasks completed by their own deadline divided by all generated tasks.
2. **Deadline miss rate**: late + failed + unresolved-at-cutoff tasks divided by all generated tasks; report the components separately.
3. **End-to-end latency**: `completion_time - arrival_time`; report mean, median, P95, and P99. Also report how unfinished tasks are treated.
4. **Recovery performance** after a regime shift: recovery time and cumulative deadline misses during the recovery window.

### Required stratified reporting

Report all principal metrics separately for `INDIVISIBLE` and `DATA_PARALLEL_DIVISIBLE` tasks. For divisible tasks, also report performance by selected remote fraction (0.25, 0.50, 0.75, and full remote) and by remote tier (Edge/Cloud). Report the fraction of tasks for which partial execution was legal and selected.

### Secondary outcomes

- Throughput and completed-task ratio.
- Per-node CPU utilization, queue/backlog, and load distribution.
- Network bytes/transmitted data if the simulator captures it reliably.
- Decision inference time (wall-clock), model size, and update overhead.
- Energy per task / per completed task only after validating the simulator's power model, units, and computation/transmission accounting. Otherwise report energy as unavailable or preliminary, not as a primary finding.

### Reward policy

The reward must reflect the declared objectives and must be documented separately from the dataset schema. Do not let Abdo invent reward values or weights. Use deadline feasibility as a constraint/strong penalty and optimize latency plus validated secondary costs. Normalize terms using training/validation statistics only. Pre-register weights or a constrained/lexicographic rule before final test. Keep raw metric columns in the dataset so that results can be re-aggregated without retraining.

## 12. Experimental scenarios

Create a controlled set of operating regimes:

1. **Stable baseline:** steady arrivals and nominal link/resource conditions.
2. **Bursty arrivals:** burst/on-off arrival process or a step increase in arrival rate.
3. **Network degradation:** reduce bandwidth and/or increase WAN delay; isolate each factor initially.
4. **Edge-capacity degradation:** reduce one Edge node's capacity or increase its background load.
5. **Task-mix shift:** change the distribution of task sizes and compute demands.
6. **Repeated regime shift:** A→B→A and, where feasible, A→B→C→A transitions.
7. **Combined stress:** combine selected workload and network changes only after single-factor effects are understood.
8. **Unseen topology/capacity test:** optional held-out topology or capacity profile, with a frozen policy first and adaptation evaluated separately.

Use one-factor-at-a-time shifts before combined stress to preserve causal interpretability. Predefine shift timestamps and scenario identifiers in the manifest; do not expose future shift labels to the policy.

## 13. Baselines and ablations

Minimum baseline set:

- Local-only.
- Edge-only full execution (with explicit Edge selection rule).
- Cloud-only full execution.
- Full-only deterministic heuristic over `{LOCAL, EDGE_FULL, CLOUD_FULL}`.
- Partial-enabled deterministic heuristic over the same legal full/partial action set as the learner.
- Existing contextual learner without the risk-calibration layer, tested in both full-only and partial-enabled action modes.
- Proposed contextual learner with risk calibration and shift-aware recalibration, with full-only and partial-enabled variants.
- DQN reference only if it can use the same state, legal action mask, action encoding, tasks, and evaluation budget fairly.

Minimum ablations:

- Full-only versus partial-enabled action set (primary partial-offloading ablation).
- No feasibility filter.
- Fixed safety margin versus rolling calibrated residual margin.
- Calibration frozen versus shift-aware/rolling recalibration.
- No adaptive update versus adaptive update after a detected/observed shift.
- Report all partial-offloading effects separately for divisible tasks; do not mix them with indivisible-task results.

All policies must run against identical tasks, seeds, topology, and exogenous network/workload traces (paired comparisons).

## 14. Dataset generation and integrity requirements

The benchmark is a **transparent synthetic task workload plus simulator-produced execution logs**. It must never be described as a real measured IoT offloading trace.

- Generate task arrivals, task properties, urgency classes, and deadlines before any policy acts.
- Keep task IDs stable across policies and runs.
- Keep task-generation random streams separate from policy randomness where possible.
- Use identical generated task streams and exogenous conditions for paired policy runs.
- Split training, validation, and test by seeds and scenario families, not random rows from the same run.
- Do not tune thresholds, reward weights, calibration, or class deadline ranges on final test results.
- Preserve source provenance for any optional ECW/SMD-derived scenario context.
- Keep generated workload fields, observed simulator fields, policy decisions, and measured outcomes in separate logical tables.
- Every generated task must end in exactly one reconciled status: `ON_TIME`, `LATE`, `FAILED`, `UNRESOLVED_AT_HORIZON`, or `NO_FEASIBLE_SITE_AT_ARRIVAL` (the last may later end in another final outcome; retain both decision reason and final status if so).
- Never silently drop pending, failed, rejected, or late tasks.

## 15. Use of ECW and SMD

- Neither supplied source is a direct task-offloading dataset. Both lack task IDs, task sizes/compute demand, individual deadlines, placement actions, and per-task completion outcomes.
- Do not concatenate or row-wise merge ECW and SMD.
- SMD may be considered only as a separately identified abnormal-condition/anomaly context source; its anomaly label is not a task failure, deadline miss, network outage, or proven resource-exhaustion cause.
- ECW may be used only after the original provenance, channel dictionary, axis meanings, units, and time basis are verified. An anonymous normalized channel must not be assigned a physical meaning by guesswork.
- The primary task records and execution outcomes are generated/measured by the workload generator and simulator. Keep any ECW/SMD influence traceable and separate.

## 16. Statistical and reproducibility protocol

- Use at least 20 paired seeds for each principal scenario; target 30 if runtime permits.
- Report mean and standard deviation, median and tail percentiles, 95% confidence intervals, paired differences, and effect sizes.
- Use paired bootstrap or a paired non-parametric test such as Wilcoxon where appropriate; account for multiple comparisons.
- Save raw per-task logs, scenario configuration, generator version, simulator version/commit, code revision, seed, and dependency versions.
- Report in-distribution and held-out-shift results separately.
- Define recovery before running tests: first time after the shift at which a pre-registered rolling metric (primary: on-time completion ratio; secondary: P95 latency) returns within a pre-registered tolerance of the post-shift stable target for a specified consecutive window. Also report cumulative deadline misses from the shift until recovery. The tolerance/window must be selected on validation data and frozen before test.

## 17. Current literature checks to retain in the formal matrix

The following recent work must be included in the final novelty comparison; these references are not all equivalent in venue or evidence level:

- Li et al., *Forecast-driven task offloading for reliable and adaptive mobile edge computing*, Journal of Network and Computer Applications, 2026, DOI `10.1016/j.jnca.2026.104494` (forecasting + LinUCB/contextual offloading).
- *LITO: Lemur-Inspired Task Offloading for Edge–Fog–Cloud Continuum Systems*, Sensors, 2026 (contextual-bandit feedback and deadline/capacity feasibility mechanisms).
- Aghababaiyan et al., *Execution Timing Control for Deterministic Task Offloading in the IoT-Edge-Cloud Continuum*, arXiv:2608.00892, 1 August 2026 (preprint; joint placement and start timing).
- Aghababaiyan et al., *Task Offloading and Resource Allocation for Deterministic Service Provisioning in the IoT-Edge-Cloud Continuum*, arXiv:2610.24617, 17 October 2026 (preprint; deadline/priority-aware deterministic service provisioning).
- *Task-driven priority-aware computation offloading with distributed CPU resource allocation in edge-cloud IoT networks*, Internet of Things, 39 (September 2026), article 102068, DOI `10.1016/j.iot.2026.102068`.
- Kalmani et al., *Reliable healthcare IoT scheduling using calibration and uncertainty aware learning*, Discover Computing, published 2 November 2026, DOI `10.1007/s10791-026-10786-7` (adjacent healthcare communication scheduling; calibration under temporal distribution shift).
- *Delay-aware partial task offloading using multicriteria decision model in IoT–fog–cloud networks*, Journal of Network and Computer Applications, Volume 242, October 2025, article 104278, DOI `10.1016/j.jnca.2025.104278` (directly relevant partial-offloading prior art).
- *A comprehensive review on internet of things task offloading in multi-access edge computing*, Heliyon, 2024, DOI `10.1016/j.heliyon.2024.e29916` (review discussing practical constraints and limitations of partial task splitting).

The 2025 JNCA article directly addresses delay-aware partial task offloading in IoT–fog–cloud networks (DOI `10.1016/j.jnca.2025.104278`). The 2024 Heliyon review (DOI `10.1016/j.heliyon.2024.e29916`) cautions that arbitrary task splitting can be unrealistic when task types and computational demand are not proportional to input size. These works mean partial offloading must be treated as established prior art and modelled with explicit divisibility assumptions. The healthcare-IoT paper is adjacent rather than an identical task-placement problem, but it weakens any broad claim that calibration plus temporal-shift robustness is itself new. The manuscript must distinguish our task-specific, per-candidate-site completion-time calibration and deadline-feasibility use from generic probability calibration or communication-priority scheduling.

## 18. Partial-offloading modelling constraints

1. Partial offloading is permitted only for synthetic task profiles marked `DATA_PARALLEL_DIVISIBLE`; indivisible tasks retain full-only actions.
2. A partial action divides work between Local and exactly one remote tier (Edge or Cloud). Simultaneous Local+Edge+Cloud splitting is out of scope.
3. The initial discrete remote fractions are 0.25, 0.50, and 0.75. Continuous ratio optimization is out of scope for the first implementation.
4. The fraction applies to computational work and associated data only for profiles whose partition model explicitly supports proportional division. If input/output data cannot be partitioned proportionally, define a profile-specific mapping rather than assuming linearity.
5. Include partition, synchronization, and merge costs in end-to-end completion time. If the simulator cannot represent these costs and the two execution branches faithfully, do not report partial-offloading performance as measured; report the limitation and keep it as an unvalidated extension.
6. Keep full-only and partial-enabled policy comparisons paired on identical task streams, seeds, topology, and exogenous traces.

## 19. Decisions that remain technical validation items (not open research-scope questions)

1. Confirm the actual iFogSim2 topology and whether Edge nodes are separately selectable.
2. Confirm whether custom task partitioning, parallel local/remote execution, synchronization, and merge events can be implemented cleanly in the current iFogSim2 model; do not assume a built-in generic partial-offloading switch exists.
3. Confirm exact units and correctness of local/remote queue, transfer, execution, split/merge, and end-to-end completion-time event hooks.
4. Validate the energy model before energy becomes a primary optimized objective.
5. Confirm whether per-task state snapshots can be logged consistently at decision time.
6. Confirm the existing learner's exact algorithm/update rule from source code before naming it in the paper.

These are implementation checks. They do not authorize expanding the scope to arbitrary DAG partitioning, multi-remote splitting, or explicit deferral.
