# Research Specification — IIoT / Smart Manufacturing Draft V1

**Working title:** Risk-Calibrated Adaptive Full and Partial Task Offloading for Industrial IoT in Smart Manufacturing under Workload and Network Shifts  
**Status:** DRAFT FOR TEAM AND SUPERVISOR REVIEW — NOT APPROVED  
**Prepared by:** Mark — Research Lead  
**Base:** Research Specification V2 and the existing repository reference corpus  
**Change boundary:** Additive industrial-domain adaptation. The generic V2 specification, implementation, prior results, and original source documents are preserved unchanged.

> This draft does not authorize a final scope change. The transition to IIoT / Smart Manufacturing remains conditional on the supervisor/teaching-assistant approval stated in the team plan.

## 1. Transition decision

The project will move its application context from generic IoT to a bounded Smart Manufacturing / Industrial IoT (IIoT) setting. It will not become a predictive-maintenance algorithm, a machine-vision classifier, or a production-control project.

The research problem remains adaptive execution placement across Local, Edge, and Cloud. Industrial applications supply the task semantics and workload profiles used to evaluate the existing risk-calibrated feasibility and full/partial offloading path.

The transition is therefore:

- **Change:** application domain, workload semantics, scenario descriptions, and target topology interpretation.
- **Preserve:** the nine-action catalogue, legal-action contract, task lifecycle, risk-calibration mechanism, paired evaluation principles, and iFogSim2 integration wherever their assumptions remain valid.
- **Revalidate:** task-size distributions, data-volume assumptions, deadlines, queue/resource observations, partition and merge costs, topology, and the workload-to-simulator adapter.
- **Do not claim:** that the current synthetic profiles are measured factory workloads, that the current three-device topology is already a deployed smart factory, or that the existing generic-IoT results prove industrial generalization.

## 2. Problem statement

Smart manufacturing systems generate heterogeneous computational tasks from machine-side sensors, production equipment, and inspection stations. Examples include inference over vibration and temperature windows, visual inspection of manufactured products, and aggregation of production-state observations.

The task stream may vary as machine activity changes, inspection volume rises, or communication paths between a production cell, factory-floor edge resources, and a remote cloud experience degradation. A placement choice that is effective under nominal conditions may miss a task deadline after a shift. Full remote execution can increase communication burden; local execution can overload constrained equipment; partial execution can help only when the task is explicitly divisible and the split/merge lifecycle is valid.

This study will evaluate whether a lightweight contextual placement policy, combined with a residual-calibrated completion-time feasibility filter, can make defensible Local / Edge / Cloud full and constrained partial execution decisions for declared industrial task archetypes. It will measure deadline reliability, latency, network traffic, and return-to-baseline behavior under controlled workload and network shifts.

The empirical benchmark will use **synthetic IIoT task inputs plus iFogSim2-produced execution outcomes**. Existing datasets may provide narrowly scoped context or execution-time calibration, but none of the currently audited sources is a complete, measured smart-factory task-offloading trace.

## 3. Industrial application scope

The initial application setting is one smart-manufacturing production cell or small factory domain. Three task archetypes are included.

| Industrial application | Task archetype | Default divisibility | Partial execution condition |
|---|---|---|---|
| Predictive maintenance | Inference over one machine's vibration / temperature window | Indivisible | Only a batch of independent machine windows may be split; do not split a single dependent temporal window by assumption |
| Visual quality inspection | Inspection of one product image | Indivisible | A batch of independent product images may be divided across Local and one remote tier when images are homogeneous under a declared partition model |
| Production monitoring | One machine-state or event inference | Indivisible | Aggregation over independent machine/window shards may be divided when each shard can be processed and merged without cross-shard dependencies |

These are workload archetypes, not claims about the frequency of such tasks in a real factory. Abdo and Mostafa must validate the profile definitions and numerical ranges before they become benchmark inputs.

### 3.1 Divisibility rule

The unit of work must be explicitly declared.

- A single predictive-maintenance time window is indivisible unless the application semantics demonstrate independently processable sub-windows and a valid merge operation.
- A single product image is indivisible in the initial benchmark. A batch of independent images can be divisible.
- A single production event or state transition is indivisible. A batch of independent machine/window records can be divisible.
- No task may be split across Edge and Cloud simultaneously.
- No partial action may be applied solely because a byte or MI value can be divided numerically.

For the first industrial benchmark, retain the existing remote fractions 0.25, 0.50, and 0.75 only for workload profiles whose partition model justifies proportional work and input/output partitioning. Homogeneous fixed-size image batches or fixed-duration sensor-window shards are safer first cases than arbitrary heterogeneous records. Any profile-specific partition mapping must be documented in its workload configuration and verified against the Java execution trace.

## 4. Execution architecture and topology interpretation

The three tiers receive industrial meanings:

| Existing tier | Smart-manufacturing interpretation | Execution responsibility |
|---|---|---|
| Local | Machine-side controller/gateway or production-cell local compute endpoint | Local inference and processing close to the source |
| Edge | Factory-floor / cell-level industrial edge server | Nearby shared compute for latency-sensitive tasks |
| Cloud | Remote industrial cloud environment | Higher-capacity remote execution and cross-cell / plant-level processing |

These are semantic roles for the experiment. They do not assert that the current iFogSim2 devices emulate certified PLCs, safety controllers, or a real manufacturer's deployment.

### 4.1 Staged topology

**Stage 0 — preserve the verified integration topology.** The checked-in Java topology contains one Local executor, one Edge executor, and one Cloud executor. Recorded capacities are 1,000 / 2,800 / 44,800 MIPS; configured uplink latencies are 2 ms Local-to-Edge and 45 ms Edge-to-Cloud. Raw bandwidth values are present, but the project's topology audit leaves their physical unit unresolved; downlink latency is not explicitly specified. These values are an implementation reference, not validated factory capacities.

**Stage 1 — small Smart Factory topology target.** The existing project target of four IIoT source devices, two Edge nodes, and one Cloud node may be used only after Ayoub confirms that the devices, capacities, parent links, and measurement hooks are actually implemented. Until then, four source IDs are logical workload identities, not proof of four instantiated FogDevices.

If two Edge nodes are introduced while the learned action catalogue still exposes one EDGE tier, node selection must be deterministic and documented (for example, a declared least-queue rule) and the actual Edge node ID must be logged. Do not silently represent EDGE-1 and EDGE-2 as separate learned actions.

**Stage 2 — scale-out.** Increase the number of machines, sources, or Edge resources only after the small topology passes task lifecycle, transfer, queue, partial-branch, and outcome-reconciliation tests.

## 5. Research objectives

- **RO1 — Industrial workload model:** define reproducible predictive-maintenance, visual-inspection, and production-monitoring task profiles with explicit units, deadlines, urgency, divisibility, and provenance.
- **RO2 — Risk-calibrated placement:** evaluate Local, Edge, and Cloud full execution and legal Local-plus-one-remote partial execution using predicted end-to-end completion time and residual-based safety margins.
- **RO3 — Shift response and recovery:** measure transient deadline misses, latency degradation, and recovery after controlled workload, network, or Edge-capacity changes.
- **RO4 — Trade-off analysis:** compare deadline reliability, mean/tail latency, and task-attributed network traffic; include energy only if the simulator's energy model and per-task attribution are independently validated.
- **RO5 — Reproducibility:** use paired task streams and seeds, frozen model artifacts, scenario-family separation, content-addressed manifests, and simulator-produced outcomes.

## 6. Research questions

- **RQ1 — Deadline feasibility:** Does residual-calibrated feasibility filtering reduce deadline misses for the declared industrial task archetypes relative to the same learner without the filter and to strong non-learning baselines?
- **RQ2 — Full versus partial execution:** Under which industrial task types and operating conditions does constrained partial execution improve or worsen deadline reliability, latency, and network traffic compared with full-only placement?
- **RQ3 — Shift response:** How do policies respond to isolated network, workload, and Edge-capacity shifts, and what deadline-miss burden is incurred before return-to-A recovery?
- **RQ4 — Adaptation value:** Does an explicitly enabled online update / recalibration arm improve recovery relative to a frozen policy, without contaminating held-out evaluation?
- **RQ5 — Application dependence:** Are outcomes materially different across predictive-maintenance, visual-inspection, and production-monitoring tasks after controlling for task size, payload, deadline, divisibility, and network conditions?

## 7. Candidate contribution and research-gap boundary

The existing reference corpus already contains close work on IIoT reliability-aware offloading, Edge-IIoT DQN offloading, reliability-oriented adaptive offloading, forecast-driven contextual offloading, uncertainty-aware feasibility, and hierarchical partial offloading. In particular, the repository index records:

- **CORE-04:** ESFMTO, *A reliable task offloading strategy based on edge server failure model in IIoT*, Ad Hoc Networks (2025), DOI 10.1016/j.adhoc.2025.103887.
- **CONF-03:** *Deep Q-Network based Task Offloading Optimisation for Edge-IIoT System*, ICICIT (2026), DOI 10.1109/ICICIT69063.2026.11634047.
- **CORE-03:** RELTO, reliability-oriented adaptive reward weighting, Ad Hoc Networks (2026), DOI 10.1016/j.adhoc.2025.104065.
- **CORE-01:** forecast-driven adaptive MEC offloading, JNCA (2026), DOI 10.1016/j.jnca.2026.104494.
- **CORE-06:** hierarchical deep reinforcement learning for partial Device-Edge-Cloud offloading, IEEE Transactions on Consumer Electronics (2026), DOI 10.1109/TCE.2025.3611973.
- **CORE-02:** chance-constraint-based dependent task offloading under uncertainty, Applied Soft Computing (2026), DOI 10.1016/j.asoc.2026.115710.

The proposed gap is **not** “RL for IIoT”, “deadline-aware offloading”, “risk-aware learning”, “partial offloading”, or “A→B→A testing” in isolation. Those directions have prior art in the collected corpus.

The candidate contribution is a controlled, reproducible evaluation of **per-action end-to-end completion-time residual calibration across legal full and constrained partial execution options**, applied to declared smart-manufacturing task archetypes and evaluated under separated industrial workload, network, and Edge-capacity shifts. The contribution is an empirical and methodological claim until equation-level comparison against the listed papers is completed from the existing collected materials. No claim of algorithmic novelty is approved by this draft.

## 8. Policy, state, and action contract

### 8.1 Preserve the nine-action catalogue

Retain the implemented V2 actions:

- LOCAL
- EDGE_FULL and EDGE_PARTIAL_25 / 50 / 75
- CLOUD_FULL and CLOUD_PARTIAL_25 / 50 / 75

The suffix is the remote fraction of the task. A partial task runs a Local branch and exactly one remote branch, joins at the existing two-result barrier, and merges only after both branches succeed. Indivisible tasks receive full-only actions. Keep this catalogue unchanged for the first domain adaptation so the industrial workload change can be evaluated without simultaneously changing the action space.

### 8.2 Industrial metadata and learner state

Add application identity and industrial context as **workload / trace metadata first**: application profile, production-cell or machine-source identity, batch unit, and partition-model identifier. Report results by application profile and divisibility class.

Do not immediately add application identity as a new tabular state dimension. The current V2 state already has 13,122 discrete states and nine actions; the sparse table and high fallback rate in the prior pilot make an unmeasured state expansion risky. First test whether the existing observable state — MI, input/output bytes, WAN delay, Local/Edge/Cloud utilization, deadline, and splittability — distinguishes the execution conditions adequately. Add a profile feature only if development evidence demonstrates a material missing context and training coverage is increased accordingly. Do not expose future regime labels or post-decision outcomes to the policy.

The implementation must be named accurately as a masked tabular / contextual learner as established by its update rule. Do not call it DQN or deep RL.

## 9. Risk-calibrated feasibility

Preserve the existing V2 mechanism:

1. Build a pre-decision context for each legal action using tier capacity, utilization, queue-wait estimate, transfer path, task demand, and remaining deadline.
2. Predict end-to-end duration for full or partial execution.
3. Add a one-sided residual margin calculated from prior completed training outcomes, using the existing exact-action → action-family → pooled fallback.
4. Remove actions whose conservative predicted completion exceeds remaining deadline slack.
5. If no action passes, record the forced fallback and reason; retain the task in the all-generated-task outcome denominator.
6. Update the learner and residual calibrator only in the declared training or explicitly registered online-adaptation arm.

Industrial adaptation requirements:

- The task's partition and merge parameters must come from its declared industrial profile; the same values and compute/data partition rule must be used by the estimator and Java simulator.
- Queue wait must be a measured or clearly labelled pre-decision estimate. A zero queue value must not be described as measured queueing.
- Link delay and bandwidth must use verified simulator units and directions. Do not infer physical units from raw topology numbers.
- The calibration sidecar must be frozen for the primary held-out comparison. If online recalibration is tested, it must be a separate, pre-registered arm with logged update times, counts, residuals, and model versions.
- Calibration is empirical, not a deterministic deadline guarantee.

## 10. Scenario design

Use one-factor-at-a-time experiments before combined stress. Every scenario has an immutable manifest and paired policy inputs.

| Scenario | A → B change | Held constant | Purpose |
|---|---|---|---|
| Stable factory baseline | No regime shift | Nominal task, network, and capacity profile | Establish nominal behavior |
| Network-only A→B→A | Change one declared network factor at a time (WAN delay **or** bandwidth) | Task MI, input/output profile, task mix, arrival pattern, per-profile deadline, Edge capacity | Isolate network sensitivity |
| Workload-only A→B→A | Change one declared workload factor at a time (compute demand, payload profile, arrival rate, or task mix) | Network and Edge capacity; per-profile deadlines | Isolate workload sensitivity |
| Edge-capacity-only A→B→A | Reduce or increase Edge service capacity / background load | Task stream, network, deadlines | Isolate compute-resource sensitivity |
| Combined industrial stress | Combine selected workload and network factors | Preserve declared deadline policy | Assess interaction after single-factor effects are understood |

For each A→B→A run, A2 must replay A1's task template and relevant exogenous profile. Deadlines must not be relaxed in B in the primary controlled experiments. If application-specific deadlines differ, the deadline mapping is frozen before evaluation and remains unchanged across phases for the same application profile. Do not attribute a phase difference to workload or network if the deadline definition changes at the same time.

The older generic A→B→A 20-seed result used a B deadline of 20 s versus 15 s in A1/A2. Keep it as historical generic evidence; do not treat it as the fixed-deadline industrial benchmark.

## 11. Metrics and analysis

Primary outcomes:

- Deadline miss rate = late + failed + unresolved-at-horizon tasks divided by all generated tasks.
- Completion coverage, on-time count, late count, failed count, unresolved count.
- End-to-end latency among completed tasks, with mean, median, P95, and P99; always report completion coverage beside conditional latency.
- Recovery time under a pre-registered operational definition.
- Cumulative deadline-miss burden during B and from the A2 transition until recovery.

Secondary outcomes:

- Task-attributed transmitted bytes, with explicit uplink/downlink counting semantics.
- Throughput and backlog / queue behavior.
- Decision latency and model / calibration update overhead.
- Per-application, per-divisibility, per-remote-tier, and per-split-ratio results.
- Energy only after validating the power model and per-task accounting.

The independent statistical unit is a workload seed / paired simulation run, not an individual task. Use at least 20 paired seeds per principal scenario and prefer 30 when runtime permits. Report paired differences, 95% paired-seed bootstrap intervals, effect sizes, paired non-parametric tests where appropriate, and Holm correction across the predeclared family of comparisons.

## 12. Data provenance and dataset use

The primary benchmark is a transparent synthetic industrial task stream plus simulator-produced execution records. It must not be called a measured smart-factory trace.

| Existing source | Permitted role in this transition | Prohibited interpretation |
|---|---|---|
| ToN-IoT | IIoT / Edge-Fog-Cloud context; possible host/network context only after actual files and fields are obtained and verified | Not a task-offloading benchmark; current project audit says no data files were downloaded; laboratory testbed is not proof of production-factory operation |
| UCI Image Recognition MEC | Narrow execution-time reference / calibration context for image-recognition workloads | Not factory inspection data; turnaround time is not a separate network or compute component; no payload size, MI, deadline, or offloading labels |
| Google Cluster Data v3 | Potential cloud workload/context reference only if actual rows are acquired and inspected | Downloaded schemas are not a measured task stream; Borg scheduling events are not IoT task offloading |
| EUA | Optional spatial-context material only | Not a manufacturing workload or offloading dataset |
| CICIoT2023, UNSW-IoTraffic, Bot-IoT, UNSW-NB15 | Network-security context only after data access and field audit | Traffic flows are not compute tasks, execution demand, deadlines, or offloading decisions |

Dataset sourcing and license confirmation remain Mostafa's responsibility. A proposed industrial workload profile must be labelled synthetic unless its source data and transformation are documented at field level.

## 13. Data split and test integrity

The currently proposed seed plan in the workload package is not sufficient to declare the existing runs a clean final IIoT test:

- The development pilot used seed 101.
- The previous generic paired batch used seeds 102–121.
- The proposed test band is 81–120, so 121 is outside it and the pilot seed lies within the nominal test band.
- The old batch used the legacy combined profile without a fixed deadline.

Therefore, do not reuse the old 20-seed batch as the final industrial test or claim it satisfies a final held-out industrial split. Mark and Abdo must audit all seed manifests and training provenance, then reserve a new untouched seed band for the IIoT test. Train, validation, and test must be separated by both scenario family and seed, not random task rows. The frozen model and risk sidecar used for final evaluation must have training provenance inside the approved training allocation.

## 14. Explicit exclusions

- Safety-critical closed-loop machine actuation or certified industrial control.
- Real PLC firmware, machinery certification, production deployment, or physical-factory validation.
- Arbitrary DAG decomposition, cross-machine dependencies, or splitting one task across multiple remote tiers.
- Treating attack labels as task failures or network outages without an explicit mapping and validation.
- Introducing new learners, DQN, forecasting, or a larger action space merely to make the project sound more complex.
- New literature-search work during this transition; the existing reference corpus is the evidence base for this draft.
- Energy claims without validated simulator evidence.

## 15. Approval and freeze gates

1. Supervisor / teaching-assistant confirms the IIoT / Smart Manufacturing domain and application scope.
2. Mark freezes the research questions, candidate contribution wording, task semantics, and evaluation boundaries.
3. Mostafa supplies the dataset suitability / source / license mapping and flags unsupported industrial claims.
4. Abdo updates industrial task profiles, schemas, and manifests without inventing measured values.
5. Ayoub confirms the simulator topology, device mapping, capacities, units, queue hooks, and partial-execution event semantics.
6. Mark and Ayoub accept a small end-to-end industrial pilot before any 20–30 seed batch.
7. Final test seeds and the model / calibration artifacts are frozen before inferential runs.

Numerical industrial deadlines, workload distributions, Edge capacities, bandwidth units, and partition/merge overheads remain **unapproved** until these gates produce evidence.
