# iFogSim2 Simulator Readiness Audit

**Reviewed package:** `iFogSim-main-rl-v5-randomtopo.zip`  
**Review scope:** static inspection of the supplied V5 source, Python RL package, configuration, curriculum runner, and project-level RL documentation.  
**Execution status:** this is a code-level audit. A fresh Java simulation, Eclipse build, and full Python test suite were not run as part of this review.

## 1. Executive assessment

The package contains a working-looking integration path for task placement among **Local, Edge, and Cloud**:

- `RandomEdgeCloudOffloadingRL` builds a random Cloud → Edge → IoT topology and a single processing module is mapped to every fog device.
- `RLOffloadingManager` intercepts sensor tuples at their first IoT device, requests an action from the Python process, forwards Edge/Cloud actions, and reports task outcomes.
- `rl_model` implements the Python-side tabular learner, baselines, JSONL logging, model persistence, and metric aggregation.
- `run_topology_curriculum.py` chains training over topology seeds and evaluates the resulting model plus fixed baselines on new topology seeds.

**Readiness conclusion:** suitable as an experimental *infrastructure prototype* and for controlled engineering tests. It is **not yet sufficient to claim that all requested research metrics are implemented and validated**. Main blockers are metric semantics/coverage (especially censored tasks at simulation cutoff), energy attribution, utilization definition, calibration of research parameters, and the absence of the wider methodology/reference files from the supplied ZIP.

## 2. What is implemented

| Area | Verified in supplied source | Readiness |
|---|---|---|
| Local / Edge / Cloud actions | Three action IDs and names in `RLOffloadingManager`; module availability is checked before action selection | Implemented |
| Local execution | Returning `false` from `tryOffload` leaves the tuple on the normal local processing path | Implemented |
| Edge execution | `rlSendUp` sends the tuple to the parent Edge device | Implemented |
| Cloud execution | Tuple first travels upward; `forwardCloudTransit` forwards a Cloud-selected tuple through the intermediate Edge to the top device | Implemented |
| App deployment | `processing` module is mapped to every fog device in `RandomEdgeCloudOffloadingRL` | Implemented |
| Random topology | `RandomTopologyGenerator` generates Cloud, 1–4 Edges, 1–4 IoT devices per Edge, and sensor/task profiles | Implemented |
| Fixed topology | Separate `EdgeCloudOffloadingRL` class remains in the source tree | Present; separate from the random curriculum entry point |
| RL process integration | Java launches `python -m rl_model.server`, exchanges line-delimited JSON through `RLClient` | Implemented |
| Fixed baselines | `local`, `edge`, `cloud` are supported in Python baseline mode | Implemented |
| Training / frozen evaluation | Train/eval modes and persisted model support exist; eval agent is frozen | Implemented |
| Reproducibility controls | Topology, workload/simulation, and agent seeds are represented separately | Implemented, with experiment-design caveats |
| Structured logs | Per-run JSONL, event JSONL, topology registry, and model topology ledger | Implemented |
| Statistical aggregation | `aggregate.py` computes per-run metrics and across-run mean, sample SD, and 95% t-based CI | Implemented as a separate tool; curriculum script does not invoke it |

## 3. Local, Edge, and Cloud execution path

The decision point is a sensor tuple arriving at its first fog/IoT device (`FogDevice.processTupleArrival`). `RLOffloadingManager.tryOffload` checks whether the destination application module is available locally, on the parent Edge, and on the Cloud/top device.

- **Local:** no forwarding is performed; normal iFogSim local tuple processing continues.
- **Edge:** tuple is sent upward to the parent device through `rlSendUp`.
- **Cloud:** tuple is initially sent upward; when it reaches an intermediate fog device, `forwardCloudTransit` detects the Cloud decision and forwards it again. The code comments indicate that the normal link queues are used hop-by-hop.

The current random scenario maps one `processing` module copy to every device. This is what makes all three execution targets available in the standard generated topology. This is placement of the same application module, not a separate application implementation for each tier.

### Baseline behavior

`server.py` supports `local`, `edge`, and `cloud` fixed policies. The action is still subject to the action-availability mask supplied by Java. The curriculum runner evaluates these three policies on the same test topology and workload seed as the trained agent.

## 4. Configurable parameters

### Topology / workload generator

`RandomTopologyGenerator.Config.fromSystemProperties` reads `-Dtopo.*` overrides. Defaults visible in the source include:

- Edge count: 1–4; IoT devices per Edge: 1–4.
- IoT MIPS: 50–250; Edge MIPS: 200–1000; Cloud MIPS: 20,000–50,000.
- IoT→Edge latency: 2–15; Edge→Cloud latency: 5–150 with log-uniform sampling.
- IoT and Edge bandwidth ranges are separately configurable.
- Edge arrival-pressure multiplier: 0.6–2.0.
- IoT and Edge offered-load caps: 2.0× their MIPS by default.
- Sensor inter-arrival profile and workload arrival randomness are generated from the configured seeds.

These are explicitly described by `RL_RANDOM_TOPOLOGY.md` as development ranges, not calibrated research values.

### Runtime / RL parameters

The code and runner expose, among others:

- `sim.time`, `rl.enabled`, `rl.mode`, `rl.phase`, `rl.runId`.
- `topology.seed`, `workload.seed`, `rl.simSeed`, `rl.agentSeed`.
- `rl.home`, `rl.config`, `rl.python`, `rl.modelIn`, `rl.modelOut`.
- `topology.trainSeeds`, `topology.logDir`, `topology.allowOverlap`.
- `rl.deadlineMs` or `rl.deadlineBaseMs` + `rl.deadlinePerMi`.
- `rl.backlogCapMs`, `rl.reportPendingAsFailed`.
- Audit switches such as `rl.auditRouting`, `rl.auditLatency`, `rl.auditLifecycle`, and `rl.auditE2E`.

The curriculum runner also accepts `--classes`, `--train-seeds`, `--test-seeds`, `--sim-time`, `--agent-seed`, workload seed bases, `--baselines`, `--jobs`, `--home`, `--config`, `--out`, `--java`, `--python`, `--gui`, repeatable `--vm`, and `--dry-run`.

## 5. Current outputs and metrics

### Per-task JSONL outcome

On completion, Java reports:

- `status = completed`
- `latency_ms` = decision time → completion time
- `deadline_met` = true end-to-end deadline result, measured from sensor generation
- `resource_metrics.bandwidth_bytes`
- `resource_metrics.executing_node_utilization`

The Python server computes and logs the reward breakdown from these values.

### Java summary / diagnostic output

The manager also tracks decisions, completions, pending-at-cutoff tasks, fallbacks, action counts, decision-to-completion latency, true E2E latency, and deadline misses. Optional audit switches produce per-task lifecycle/routing/latency diagnostics.

### Python aggregation

`rl_model/src/rl_model/aggregate.py` can report:

- Completion rate
- Average latency
- Deadline violation rate
- Average bandwidth
- Average executing-node utilization
- Average energy **if an `energy_joules` field is present**
- Average reward

It aggregates run-level values across seeds and reports mean, sample standard deviation, and 95% confidence interval.

**Important distinction:** the curriculum script currently writes a smaller `summary.csv` containing topology seed, policy, task count, mean reward, mean latency, deadline-miss percentage, and agent action mix. It does not call the richer `aggregate.py` workflow.

## 6. Technical limitations and required decisions

1. **Cutoff/censoring:** by default, tasks still pending when the simulation stops are classified in Java diagnostics but are not emitted as completed/failed task outcomes. The aggregator's completion and deadline rates therefore use reported outcomes, not necessarily every generated task. `rl.reportPendingAsFailed` exists, but the code comments explicitly warn that this is not recommended for the lifecycle test. A research-grade denominator needs a consistent generated-task ledger and a declared censoring policy.
2. **Latency definition:** `latency_ms` in the task outcome is decision→completion. The true E2E value is sensor-generation→completion and is used for deadline checking and Java summary totals, but it is not currently included as a per-task resource/outcome field for Python aggregation. Decide which latency is the primary reported metric; if E2E is primary, expose it per task.
3. **Energy:** `FogDevice` maintains cumulative energy consumption using its power model, and the topology builder supplies busy/idle power parameters. However, the current per-task outcome does not send `energy_joules`. Per-task energy attribution is not implemented in the RL outcome path. Per-run/device energy may be feasible by reading device energy totals at run boundaries; attribution to individual concurrent tasks needs a separate design.
4. **Utilization semantics:** the RL manager's `load()` is a custom backlog proxy: outstanding RL-routed MI divided by device MIPS and `rl.backlogCapMs`, clipped to 1. It is not the same as actual host CPU utilization. `executing_node_utilization` is sampled after the completed task is removed from that backlog. The source also exposes `rlCpuUtilization()` but comments note iFogSim's host utilization can be coarse (0/1). The study must choose and name the intended measure.
5. **Baseline comparison scope:** fixed Local/Edge/Cloud baselines are present. A “static offloading” strategy with a nontrivial rule (e.g., threshold-based) is not implemented as a distinct baseline; its rule must be specified before adding it.
6. **Adaptive strategy:** current `eval` is the learned tabular policy. The supervisor's instruction says the final adaptive strategy/design remains pending approval; this audit does not recommend changing or finalizing it.
7. **Calibration:** `edge_cloud_scenario.json` says its thresholds and ranges are development values, not calibrated. Its reward uses latency reference 150 ms, clip 1, deadline weight 2, bandwidth-only cost reference 50,000 bytes, and epsilon decay 8,000. These settings should not be treated as approved research parameters.
8. **Legacy audit scope:** `rl_model/docs/AUDIT.md` primarily audits the earlier toy prototype and design note. It is useful background, but it is not a complete audit of the current iFogSim Java integration.
9. **Missing project context:** this ZIP does not contain `FILE_INDEX.md`, `research/references/REFERENCES_INDEX.md`, or `deliverables/02_Methodology/`. Those materials must be supplied before cross-checking the audit against the approved research method and reference set.

## 7. Minimal changes to consider (not implemented)

Do not modify the simulator until the research team decides the metric definitions and protocol. Likely minimal candidates are:

- Add per-task `e2e_latency_ms` to outcomes if E2E latency is required in the main results.
- Add a generated-task / cutoff ledger to machine-readable logs, and define pending-task treatment.
- Add per-run energy totals from device energy counters; only add per-task energy if a defensible attribution method is selected.
- Label the backlog metric explicitly as backlog-based estimated utilization, or add a separately sampled host utilization metric.
- Make the curriculum output use the shared aggregator or provide an equivalent run-level summary with uncertainty intervals.

No code was changed in this audit.
