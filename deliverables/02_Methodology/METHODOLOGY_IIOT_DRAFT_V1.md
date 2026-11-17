# Methodology — IIoT / Smart Manufacturing Draft V1

**Status:** Draft for team and supervisor review; not yet approved for final experiments.  
**Owner:** Mark — Research Lead  
**Controlling documents:** MARK_RESEARCH_SPECIFICATION_V2.md (generic baseline) and MARK_RESEARCH_SPECIFICATION_IIOT_DRAFT_V1.md (proposed industrial adaptation).  
**Literature boundary:** Use only the already collected and indexed repository references. No new paper search is part of this workstream.

## 1. Study design

The study evaluates adaptive task placement in a small Smart Manufacturing / IIoT environment. Workloads represent three industrial application archetypes: predictive maintenance, visual quality inspection, and production monitoring. The simulator executes each generated task at Local, Edge, or Cloud, using either a full action or a constrained partial action when the workload profile explicitly permits independent parallel execution.

The benchmark is a reproducible **synthetic industrial workload plus simulator-generated outcomes**. It is not a real factory trace. Every profile parameter must be classified as (a) measured from a verified source, (b) derived by an explicit transformation, or (c) a synthetic design assumption.

The experimental factors are separated initially: network-only, workload-only, and Edge-capacity-only. Combined stress is evaluated only after the single-factor pilots pass. A→B→A runs use a fixed deadline policy and replay the A1 task template in A2.

## 2. Industrial task model

Every generated task is created before the policy decision and has a stable task identity across policy arms. The existing task schema remains the contract baseline; industrial metadata is added only after schema review by Abdo and Mark.

Required task fields remain:

- run and task identifier;
- source-device logical identifier;
- task/application profile identifier;
- arrival timestamp;
- required compute demand in MI;
- input and output payload sizes in bytes;
- relative deadline in milliseconds and urgency class;
- divisibility class and partition-model identifier when applicable;
- profile-scoped partition / merge overhead and merge compute demand;
- scenario, regime, and seed provenance.

### 2.1 Initial task archetypes

| Profile family | Representative task | Default class | Permitted batch extension |
|---|---|---|---|
| Predictive maintenance | Feature extraction / anomaly inference on one machine's vibration-temperature window | INDIVISIBLE | Independent windows from separate machines or non-overlapping windows may be batched only if no cross-window dependency is required |
| Visual inspection | Defect classification on one product image | INDIVISIBLE | A homogeneous batch of independent product images can be DATA_PARALLEL_DIVISIBLE |
| Production monitoring | State/event inference for one machine or production event | INDIVISIBLE | Aggregation of independent machine-state windows can be DATA_PARALLEL_DIVISIBLE |

The task class refers to execution semantics, not the urgency label. A task's deadline is assigned before any action. Critical / time-sensitive / delay-tolerant deadline bands may be used only after their numerical ranges are calibrated on development traces and frozen. Do not infer a hard real-time guarantee from a synthetic deadline.

### 2.2 Partial execution eligibility

Partial execution is permitted only for a declared data-parallel batch. The initial supported action set remains the existing nine-action catalogue:

- Local-only;
- full Edge and full Cloud;
- Local+Edge or Local+Cloud at remote shares 25%, 50%, and 75%.

For an eligible homogeneous batch, the remote fraction is the proportion of independent work assigned to the remote branch. The local and remote branches execute concurrently. A two-result barrier waits for both branches. Merge work is created only after both results arrive. A missing branch results in a failed task; the simulator must never report a successful merge from one result.

For heterogeneous image or sensor-record sizes, alpha must not be interpreted as a byte fraction without a profile-specific rule. The profile must define whether the split is by item count, estimated compute, payload, or another validated unit. The estimator and Java executor must use the same rule.

## 3. Dataset and provenance method

The primary workload generator is the existing Abdo package under team-work/Astta-Abdo. It already supports deterministic generation, paired task IDs, scenario manifests, units, divisibility constraints, legal-action checks, and outcome reconciliation. The adaptation is to add industrial application profiles and scenario labels, not to replace the generator or create a second pipeline.

The existing dataset audit supports narrow uses only:

- **ToN-IoT:** IIoT context and possibly host/network context after the actual files and columns are obtained and verified. The project audit says no ToN-IoT data files were downloaded; its described testbed is laboratory-based and is not a production factory.
- **UCI Image Recognition MEC:** a measured image-recognition execution-time reference. It records time and execution time for four compute environments, but does not provide task size, input bytes, compute MI, deadlines, network metrics, or offloading labels. Treat its execution time as a turnaround-time reference, not as a network-only or compute-only component.
- **Google Cluster Data v3:** five schemas were inspected, but task rows were not downloaded or inspected. It cannot currently supply measured industrial task inputs.
- **EUA:** spatial context only, not industrial task workload.
- **CICIoT2023, UNSW-IoTraffic, Bot-IoT, and UNSW-NB15:** security / traffic context only. Network flows and attack labels are not task inputs, CPU demand, deadlines, or offloading outcomes.

Mostafa owns source, license, and suitability verification. Abdo owns the generator and industrial task profiles. Mark reviews that task assumptions are kept separate from measured simulator outcomes.

## 4. Topology and execution tiers

The implementation currently verified in the repository has exactly one Local executor, one Edge executor, and one Cloud executor, with configured capacities 1,000 / 2,800 / 44,800 MIPS. Configured Local-to-Edge and Edge-to-Cloud uplink delays are 2 ms and 45 ms. Raw bandwidth values are present but their physical unit remains unresolved in the topology audit; downlink latency is not explicitly configured there.

For a first industrial pilot, the existing three-tier topology can be **semantically mapped** as:

- Local: machine-side / production-cell gateway compute;
- Edge: factory-floor Edge server;
- Cloud: remote industrial-cloud executor.

This is a testbed interpretation, not a hardware equivalence claim. The target four-source / two-Edge / one-Cloud topology is only a proposal until Ayoub validates and implements device IDs, capacities, links, and queue observations. If two Edge nodes are introduced while the model retains one EDGE action, the Edge-node assignment rule must be deterministic and actual node ID must be logged.

Do not increase to dozens of devices before a small topology demonstrates correct task accounting, branch synchronization, transfer timing, queue snapshots, and policy pairing.

## 5. Policy and decision interface

The first industrial adaptation retains the existing V2 nine-action policy interface and legal-action derivation. This isolates the effect of industrial task semantics from a simultaneous action-space redesign.

The existing nine state features are:

1. task MI;
2. input bytes;
3. output bytes;
4. WAN latency;
5. Local utilization;
6. Edge utilization;
7. Cloud utilization;
8. deadline;
9. splittability.

Application profile, machine/cell identity, product line, and task source should first be stored as trace metadata and used for stratified analysis. Do not add new tabular state dimensions until development experiments show that the current state aliases materially different industrial operating conditions and training coverage is sufficient. The existing 13,122-state table is sparse by construction; uncontrolled feature expansion would make the coverage problem worse.

The agent must be described according to its implementation: a masked tabular/contextual learner. It must not be labelled DQN or deep RL. Any online update variant is a separate experiment arm, not an implicit property of the frozen evaluation.

## 6. Risk-calibrated feasibility method

For each task, derive the legal action mask from task divisibility and tier availability. For each legal action, estimate end-to-end completion time from the pre-decision task and system snapshot. Include queue wait, all required network hops, execution, and partial split/merge work where applicable.

For action a, compute a conservative estimate:

T_safe(a) = T_predicted(a) + q_(1-epsilon,a)

where the residual quantile is estimated using completed training outcomes from the corresponding action or documented fallback group. An action is feasible only when T_safe(a) is no greater than the task's remaining deadline slack.

If no action passes, select the documented least-violation fallback and emit the no-feasible-action reason. Do not drop the task from the denominator. Do not update the Q-table from a forced fallback decision if the current server's rules exclude it.

Industrial adaptation checks:

- partition and merge overheads and merge MI are workload-profile inputs;
- estimator and Java split/merge implementation must agree exactly on partition ratio and data mapping;
- utilization snapshots must be captured before decision and use the same definitions across policy arms;
- queue wait must be measured or marked as an assumption; zero must not be presented as an observed queue;
- bandwidth units and downlink delays must be validated before transfer time is used as evidence;
- training residuals must not include final test tasks;
- frozen model and risk sidecar hashes must be included in every run manifest.

Calibration is an empirical safety margin, not a formal deterministic guarantee. Report calibration group, sample count, margin, predicted completion, observed completion, and residual per task.

## 7. Controlled scenario method

### 7.1 Stable baseline

Generate the declared industrial application mix under nominal factory conditions. Fix the task mix, deadline mapping, source mapping, topology, and all network/capacity parameters. Replay the same workload to every policy.

### 7.2 Network-only A→B→A

Change one network variable per experiment: WAN delay or bandwidth, not both in the same network-only pilot. Keep task MI, payload sizes, application mix, arrival pattern, per-profile deadline mapping, and Edge capacity unchanged. A2 restores the A1 network condition and replays the A1 task template.

### 7.3 Workload-only A→B→A

Change one workload factor per experiment, such as compute demand, input payload, arrival rate, or application mix. Keep network links and Edge capacity fixed. Keep the per-profile deadline mapping fixed across phases. A2 replays A1's task template. If multiple workload factors are changed together, label the test as a workload-combination experiment rather than a single-factor experiment.

### 7.4 Edge-capacity-only A→B→A

Change Edge service capacity or a declared background-load factor while task stream, network, and deadline mapping remain fixed. The actual capacity and utilization changes must be visible in the simulator trace.

### 7.5 Combined stress

Only after the isolated pilots pass, combine selected workload and network shifts. Interpret combined stress as an interaction experiment, not as evidence about one factor.

## 8. Recovery definition and analysis

The A2 reference is A1 performance for the same policy and same seed. The existing pilot operational rule uses a sliding ten-task window, with completion coverage and deadline-miss tolerance relative to A1 and a median-latency tolerance. Retain this as the starting operational definition, but perform sensitivity analysis on window length and thresholds using development / validation data before freezing the rule for IIoT test runs.

Report:

- A1, B, and A2 miss rates;
- completion coverage and outcome counts in each phase;
- conditional latency distribution;
- cumulative misses during B;
- cumulative misses between the A2 transition and recovery;
- recovery rate and recovery-time distribution;
- seeds with no observed recovery as censored / not observed, not as zero time.

For online adaptation, distinguish the time of the shift from the time of detection and the time when the learner / calibrator state is updated. A frozen model returning to its earlier behavior is not evidence of online learning.

## 9. Baselines and ablations

Keep Local-only, Edge-only, Cloud-only, and Random as reference arms, but Random is not an adequate strong heuristic baseline.

Before final claims, add or plan paired arms for:

- deterministic deadline-aware heuristic over full actions;
- deterministic heuristic over the same legal full / partial action set;
- learner without risk filter;
- learner with risk filter;
- full-only learner versus partial-enabled learner;
- fixed safety margin versus rolling residual calibration;
- frozen calibration versus explicitly enabled online recalibration;
- frozen learner versus explicitly enabled online learner update.

The first industrial pilot may use a reduced subset for pipeline validation. Do not present the reduced pilot as a complete ablation study.

## 10. Outcome metrics

Primary metrics:

- all-generated-task deadline miss rate, counting late, failed, and unresolved-at-horizon outcomes;
- completion coverage and on-time ratio;
- end-to-end latency mean, median, P95, and P99 among completed tasks, always paired with coverage;
- A→B→A recovery time and miss burden.

Secondary metrics:

- task-attributed transmitted bytes with explicit hop/direction semantics;
- throughput, queue / backlog, and per-tier utilization;
- inference time and learner / calibrator update overhead;
- action mix and the proportion of tasks eligible for partial execution;
- results stratified by application archetype, divisibility, remote tier, and split ratio.

Energy is excluded from primary claims until a validated power model and defensible per-task attribution are available.

## 11. Pairing, seeds, and reproducibility

The workload seed / paired simulation run is the independent unit. Every policy must receive the same immutable task file and exogenous network / capacity schedule for a seed. Use at least twenty paired seeds per principal scenario; thirty is preferred where runtime permits.

The existing seed plan and old A→B→A outputs require reconciliation before final test allocation: the pilot uses 101, the prior generic batch uses 102–121, and 121 lies outside the currently proposed 81–120 test band. The pilot seed is also inside that nominal band. Reserve a new untouched IIoT test allocation after auditing all manifests and training artifacts. Do not reuse development / pilot seeds as final held-out evidence.

For each seed, preserve workload hash, scenario configuration, model and risk-sidecar hashes, source commit and source inventory, Java / iFogSim version, JAR inventory, topology parameters, policy names, and output summaries. Raw traces must be archived so that task outcomes and calibration records can be independently reconciled.

Use paired bootstrap confidence intervals, paired tests where appropriate, effect sizes, and Holm correction across a predeclared comparison family. Never treat the 90 tasks in a single run as 90 independent seeds.

## 12. Validity limits and freeze conditions

The industrial workload parameter ranges, deadline distributions, and partition costs are not yet calibrated. The ToN-IoT data files were not downloaded in the existing audit; UCI MEC is an image-recognition execution-time dataset, not an industrial inspection trace. The current simulator topology is one Local / one Edge / one Cloud, not the proposed four-source / two-Edge / one-Cloud target.

Accordingly, do not launch the final industrial seed batch until:

1. the IIoT scope is approved;
2. Mostafa supplies dataset-source and license decisions;
3. Abdo supplies the industrial profiles and validates generator / schema compatibility;
4. Ayoub verifies the topology, bandwidth units, downlink delay, queue/utilization measurement, and partial execution hooks;
5. Mark freezes the final RQs, policy arms, deadlines, calibration settings, and seed split;
6. the small pilot passes per-task input/output reconciliation and repeated deterministic replay.

## 13. Related-work boundary

Use `research/references/REFERENCES_INDEX.md` for the formal Core / Supporting / Conference classification and use the distinct Research Gap v29 workbook as a targeted 21-record, non-systematic method-overlap matrix. Do not merge the classifications. Mandatory close comparisons include E2DA (deadline-aware contextual neural bandit), LITO (continuum contextual-bandit feedback plus explicit feasibility filter/fallback), O2C/CCMAB (chance-constrained deadline reliability), H-DQAC (hybrid DQL/Actor-Critic and iFogSim2), hierarchical DDQN/PPO partial offloading, ESFMTO (IIoT failure-aware offloading), forecast-driven LinUCB, RELTO, and IEEE TMC paper 7 (MECTOS-MU/DGOLB).

IEEE TMC paper 7 jointly optimizes task offloading and resource allocation in a multi-device / multi-MEC-server model under device-energy, wireless-channel, MEC-server-load, task-size/task-count uncertainty and per-task maximum latency. Its TOPRFM stage ranks tasks using the number of feasible allocation modes; TODC allocates tasks; DGOLB adds static game coordination and MEC-server load balancing/migration. It therefore precludes a generic novelty claim for uncertainty-aware feasibility, deadline-constrained offloading, resource allocation, or load balancing. Its task modes are local, MEC, cooperative-device execution, and task drop; the inspected manuscript does not describe our Local-plus-one-remote split/merge action catalogue or an explicit A1→B→A2 recovery protocol.

The candidate study must be framed as a controlled empirical evaluation: quantify the incremental effect of per-action end-to-end completion-time residual calibration beyond an analytical feasibility screen and the same frozen contextual policy, with legal full/constrained partial execution on declared industrial task profiles and isolated workload/network/capacity shifts. This requires matched learner ablations, training-only calibration, paired exogenous traces, false-safe/fallback reporting, and fresh held-out seeds. The current five-arm runner does not isolate the risk filter because only the learner arm receives it. Until the equation-level comparison against LITO/E2DA/O2C and the supervisor's scope/contribution decision are complete, the result remains an empirical research question rather than a proven algorithmic novelty claim.

The official IEEE bibliographic record for TMC paper 7 is in `REFERENCES_INDEX.md`. The technical audit currently uses accessible accepted-author-version text from a third-party repost because an official local copy is still pending. Do not cite the repost or claim it is the final IEEE version; obtain the authorized manuscript before submission.


## 14. Research-positioning and TMC-7 integration note

The controlling evidence for the revised research question is `docs/RESEARCH_POSITIONING_AND_TMC7_AUDIT_V1.md`. Use it together with the References Index and the Research Gap v29 workbook. The minimum direct ablation needed to support a residual-calibration-specific conclusion is:
1. identical frozen contextual learner, no feasibility filter;
2. the same learner with analytical completion-time feasibility and zero residual margin;
3. the same learner with the frozen residual-calibrated margin.

All three receive identical per-seed industrial workload and exogenous traces. If training provenance differs between arms, report the design as a test-time intervention rather than a fully matched end-to-end method comparison. The baseline runner currently does not implement these three arms; this is an engineering task, not an existing completed experiment.

A1→B→A2 recovery with frozen V2 evaluation measures whether performance returns when exogenous conditions return to A. It does not establish online learning, model adaptation, or recalibration. Any online-update experiment must be pre-registered as a separate arm, with exact update events and model/calibrator versions logged.
