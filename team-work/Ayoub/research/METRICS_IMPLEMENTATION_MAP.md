# Metrics Implementation Map

This document maps the requested metrics to mathematical definitions, current simulator fields/events, and implementation gaps. The definitions below are proposed operational definitions for discussion, not final research decisions.

## 1. Metric map

| Metric | Candidate mathematical definition | Current source / support | Gap or required decision |
|---|---|---|---|
| Latency | Mean task latency: \(\bar L = \frac{1}{N_c}\sum_{i \in C} L_i\), where \(C\) is the set of completed tasks | Java records decision time and completion time. Outcome `latency_ms = completion − decision`; Java separately calculates true E2E = completion − sensor generation. Python aggregator averages `latency_ms` over completed tasks | Decide whether reported latency is decision→completion or sensor→completion. E2E is not currently included per task in the Python outcome log |
| Task completion rate | \(CR = N_c/N_g\), completed tasks divided by all generated tasks | Java tracks generated sensor tuples (`origins`), completed tasks, decisions, and pending-at-cutoff. Aggregator computes completed / reported task outcomes | Pending and generated-but-undecided tasks are not normally emitted as task outcomes. Add machine-readable generated-task ledger and explicit cutoff/censoring rule |
| Deadline violation ratio | \(DVR = (N_m + N_f)/N_g\), where \(N_m\) misses deadline and \(N_f\) fails; denominator is all generated tasks | `deadline_met` is computed from sensor generation time and completion time. Python counts failed or `deadline_met=false` among reported outcomes. Java classifies pending tasks as expired or still within deadline at cutoff | Current aggregate excludes pending tasks unless they are reported as failed. Decide treatment of pending tasks whose deadline has not yet elapsed; extend simulation/drain period or report censored separately |
| Energy consumption | Run-level total: \(E_{run}=\sum_{d \in D} E_d\), where \(E_d\) is device energy over the run. Optional per-task energy requires a defined attribution method | `FogDevice` maintains cumulative energy consumption from its power model; devices are created with busy/idle power parameters. Python aggregator can read `energy_joules` if present | Java task outcome currently does not emit `energy_joules`. Per-run energy extraction is feasible; per-task attribution under overlapping tasks is not currently defined |
| Resource utilization | Candidate CPU utilization: \(U_d(t)=MIPS_{used,d}(t)/MIPS_{capacity,d}\); report time-average or task-time sample average | `FogDevice` exposes host utilization helpers. RL manager instead uses `load(d)=min(1, (backlogMI/MIPS)/backlogCapMs)` as a backlog proxy. Outcome field is `executing_node_utilization` | Must choose actual CPU utilization vs backlog proxy and define sampling/aggregation. Current field is a backlog proxy, sampled after removing the completed task from backlog |
| Reliability | Candidate task success ratio: \(R=N_{completed}/N_{attempted}\), or on-time success ratio: \(R_{SLA}=N_{deadline\_met}/N_g\) | Completion status, deadline flag, failures, and pending ledger exist in the Java/Python protocol | No explicit node/link fault injection or retry model was identified. This supports task completion/SLA reliability under simulated load, not fault-tolerance reliability |

## 2. Event and variable map

### Latency

Relevant Java events/variables:

- Sensor emission is recorded by `RLOffloadingManager.recordSensorEmission`.
- Decision time is captured in `tryOffload`.
- Target arrival and execution submission can be captured by lifecycle audit hooks.
- Completion is captured by `onTupleCompleted`.

Current outcome semantics are explicit in the code:
- `latency_ms = CloudSim.clock() - decisionTime`.
- `e2e = CloudSim.clock() - generationTime`.
- `deadline_met` is based on `e2e <= deadlineMs`.

Therefore the current Python `avg_latency_ms` is **not** true sensor-to-completion E2E latency.

### Completion and deadline

The Java manager stores an `Origin` record for generated tuples and a `Pending` record for decided but unfinished tasks. At simulation end, it reports counts for completed, pending, generated-but-undecided, and pending tasks whose deadlines have already passed. These cutoff classifications currently appear in diagnostics, not as complete task rows in the JSONL dataset.

`rl.reportPendingAsFailed` can force pending tasks to be sent to the Python side as failed outcomes, but the source explicitly warns against treating that as the normal lifecycle behavior. This flag should not be used without a declared experimental policy.

### Energy

`FogDevice` extends `PowerDatacenter` and has an `energyConsumption` accumulator updated from elapsed time and the host power model. The random topology builder supplies busy/idle power values. A safe first implementation path, if approved, is to record each device's cumulative energy at the start/end of a run and report total system energy per run. This is a run-level measure, not task-level energy.

### Utilization

`RLOffloadingManager.load(FogDevice)` is calculated from the manager's own backlog map. The map counts MI of RL-routed tasks not yet completed. It is capacity-normalized and clipped using `rl.backlogCapMs`. It does not represent every source of device work in the simulator. The completion outcome's utilization is read after the completed task is removed from this backlog.

## 3. Current reward-related metrics are not the full evaluation metric set

The supplied `edge_cloud_scenario.json` configures reward using:

- `w_latency = 1.0`
- `w_deadline = 2.0`
- `w_cost = 0.5`
- fixed latency reference = 150 ms, clipped at 1
- one required cost term: `bandwidth_bytes`, reference 50,000 bytes
- no energy term in this scenario config
- `epsilon_decay_steps = 8000`

The generic `default.json` has a different placeholder configuration (latency reference 1000 ms and bandwidth + optional energy terms). The curriculum instructions point to `edge_cloud_scenario.json` by default, so the active scenario config matters.

The Python aggregator has an energy column, but that does not mean the current Java run emits energy. Similarly, bandwidth consumption is currently a per-task file-size value for non-Local execution, not a measured sum of all link-hop bytes.

## 4. Recommended minimal implementation sequence (only after approval)

1. Agree whether the primary latency metric is decision-to-completion or sensor-to-completion.
2. Agree on the generated-task denominator and pending/censored task handling.
3. Add machine-readable per-task E2E and cutoff status only if needed by the approved definitions.
4. Add run-level energy totals from device energy counters if energy is an approved objective/metric.
5. Decide whether utilization means host CPU utilization or the existing backlog proxy; label it consistently.
6. Update aggregation and tests to validate denominators, missing fields, and per-run summaries.

No code changes were made.
