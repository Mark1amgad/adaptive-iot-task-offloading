# Task-Offloading Feature Coverage Matrix

**Scope:** compare the feature requirements documented in the project repository with the actual supplied ECW and SMD files. This is a coverage audit, not a feature-engineering plan or a final experimental schema.

## 1. Classification definitions

| Classification | Meaning in this audit |
|---|---|
| **Directly available** | A value or label is explicitly present in the supplied source files. A raw unnamed numeric channel is direct only as a numeric channel, not as a known physical metric. |
| **Derivable** | Can be calculated from supplied, interpretable values without inventing a new measurement. It may be derivable only for time-series/anomaly analysis, not for task offloading. |
| **Simulated** | Must be created/measured by the future IoT/iFogSim workload and environment after the team agrees on its definition. It is not present in ECW/SMD. |
| **Unavailable** | No value, label, unit, mapping, or reliable evidence is present in the supplied files. It cannot be recovered from the current data alone. |

The parent project describes a candidate four-part RL state (task size, network latency, edge utilization, deadline category), three actions (Local/Edge/Cloud), and possible task outcome metrics. See `../../docs/state-action-reward.md`, `../../docs/system-architecture.md`, `../../docs/integration-contract.md`, and `../../docs/experiment-plan.md`. Those documents also mark units, boundaries, reward weights, and the final state definition as undecided.

## 2. Source-data coverage

| Data item | ECW | SMD | Evidence / interpretation |
|---|---|---|---|
| Numeric multivariate channels | **Directly available** — 16 unnamed channels | **Directly available** — 38 unnamed channels | ECW shape `(1022,720,16)`; SMD matrices have 38 columns per machine. Values observed in both sources are in `[0,1]`. |
| Channel names / semantic descriptions | **Unavailable** | **Unavailable** | Neither supplied file set contains a feature dictionary mapping channels to CPU, RAM, disk, network, or another physical quantity. |
| Physical units and normalization method | **Unavailable** | **Unavailable** | Numeric bounds are visible, but original units and normalization provenance are not documented. |
| Sequence/group structure | **Directly available structurally** — 1,022 groups × 720 positions | **Directly available structurally** — per-machine ordered rows | The domain meaning of ECW axes and the sampling interval of either dataset are not established. |
| Machine/entity identifier | **Unavailable** — no entity field or sidecar | **Directly available** — machine file names identify 28 entities | SMD filenames identify entities; they do not establish that these are IoT/edge/cloud nodes. |
| Timestamp / sample interval | **Unavailable** | **Unavailable** | No timestamp column or cadence metadata is supplied. SMD README describes a five-week collection but no sampling interval. |
| Point-level anomaly flag | **Unavailable** | **Directly available in test only** | SMD `test_label/` contains binary 0/1 labels aligned to every test row. ECW archive has no labels. |
| Anomaly event intervals | **Unavailable** | **Derivable from SMD test labels** | Consecutive positive SMD label points form 327 runs in the supplied files. |
| Anomalous-dimension attribution | **Unavailable** | **Directly available as interpretation annotations** | SMD `interpretation_label/` provides ranges and dimension IDs; exact index and interval conventions need confirmation. |
| Descriptive statistics (mean, percentiles, variance) | **Derivable** | **Derivable** | Computed in the generated report CSVs; statistics are descriptive, not new physical measurements. |
| Normal/anomaly ratio | **Unavailable** | **Derivable from test labels** | ECW has no labels. SMD test anomaly prevalence is 4.1563% overall; no train label directory is supplied. |

## 3. Candidate task state and workload features

| Required / candidate feature | ECW coverage | SMD coverage | Current classification for the IoT research | Evidence and required source |
|---|---|---|---|---|
| `task_id` / stable task identity | Unavailable | Unavailable | **Simulated** | No task records or task IDs exist in either source. Generate a stable ID in the future simulator and preserve it through decision, execution, and outcome logs. |
| Task input size / data size | Unavailable | Unavailable | **Simulated** | No task size field or documented byte/MB quantity. It must be part of an agreed IoT task generator. |
| Task CPU workload / instruction length (e.g., MI) | Unavailable | Unavailable | **Simulated** | No task computational demand is documented. Define in the simulator and use units consistently. |
| Task memory requirement | Unavailable | Unavailable | **Simulated** | No task RAM demand field is present. |
| Task output size | Unavailable | Unavailable | **Simulated** | No task output-byte count. A future application/workload model must define it if relevant. |
| Task arrival timestamp / inter-arrival time | Unavailable | Unavailable | **Simulated** | Row order is not an arrival schedule. Define arrival process and simulation clock in the experiment design. |
| Task arrival rate / burstiness | Unavailable | Unavailable | **Derivable after future task arrivals are simulated** | Can be calculated from generated arrival times; neither supplied dataset contains task arrivals. |
| Task deadline / deadline category | Unavailable | Unavailable | **Simulated** | No task deadlines or Tight/Relaxed labels. The project's deadline mapping is explicitly TBD. |
| Task priority / QoS class | Unavailable | Unavailable | **Simulated** | Not present. Must be defined by the IoT application/workload if used. |
| Task dependency / DAG structure | Unavailable | Unavailable | **Unavailable unless explicitly added to the future workload model** | Neither source contains task dependency graphs. Do not infer dependencies from time-series correlations. |
| Task application / workload type | Unavailable | Unavailable | **Simulated** | No task application type or tuple/task schema. Define only if the study requires workload classes. |

## 4. Environment state and network/resource features

| Required / candidate feature | ECW coverage | SMD coverage | Current classification for the IoT research | Evidence and required source |
|---|---|---|---|---|
| IoT-device CPU utilization | Unavailable semantically | Unavailable semantically | **Simulated** | Raw channels cannot be called CPU utilization without a codebook. Measure/model the IoT device in the simulator. |
| Edge CPU utilization | Unavailable semantically | Unavailable semantically | **Simulated** | No node-tier identity or CPU mapping. Obtain from the edge host/VM state in the simulator. |
| Cloud CPU utilization | Unavailable semantically | Unavailable semantically | **Simulated** | SMD machine identity is not equivalent to a cloud-tier identity. Model/measure the cloud tier explicitly. |
| RAM/memory utilization by tier | Unavailable semantically | Unavailable semantically | **Simulated** | No documented memory channel or node tier. Requires simulator resource accounting if supported. |
| CPU capacity / cores / frequency | Unavailable | Unavailable | **Simulated** | No host specification, core count, MIPS, or frequency. Define local/edge/cloud capacities in topology configuration. |
| Edge queue length / waiting tasks | Unavailable | Unavailable | **Simulated** | No queue or pending-task counts. Requires a simulator event/queue observation. |
| Network latency / RTT | Unavailable semantically | Unavailable semantically | **Simulated** | No named delay metric, units, endpoints, or timestamps. Model link latency or expose a verified simulator measurement. |
| Bandwidth / link capacity | Unavailable | Unavailable | **Simulated** | No link bandwidth or throughput field. Define per-link capacities in the simulator. |
| Network load / congestion | Unavailable semantically | Unavailable semantically | **Simulated** | Anonymous channels do not establish link load. Add background traffic or a validated network model if required. |
| Packet loss / jitter | Unavailable | Unavailable | **Simulated** | No packet-level network observations. Requires an explicit network model/trace. |
| Local / edge / cloud topology and distance | Unavailable | Unavailable | **Simulated** | No device graph, parent/child relation, link path, geographic distance, or tier labels in ECW/SMD. |
| Dynamic abnormal-condition indicator | Unavailable | **Directly available for SMD test points** | **Directly available from SMD test labels; not an offloading metric** | SMD label 1 marks a benchmark anomaly. It cannot be reinterpreted as CPU overload, deadline miss, or network outage without additional evidence. |

## 5. Task outcomes, objective metrics, and reward inputs

| Outcome / metric | ECW coverage | SMD coverage | Current classification for the IoT research | Evidence and required source |
|---|---|---|---|---|
| Per-task execution/completion time | Unavailable | Unavailable | **Simulated** | No task boundaries or task-level start/finish events. Capture task-level times in iFogSim. |
| End-to-end latency | Unavailable | Unavailable | **Simulated** | Time-series rows are not task response times. Requires task ID and end-to-end measurement points. |
| Task completion success/failure | Unavailable | Unavailable | **Simulated** | SMD anomaly labels are not task failures. The simulator must report completion outcome. |
| Deadline miss flag / violation | Unavailable | Unavailable | **Derivable after simulation** | Requires an agreed deadline plus measured task completion time. Neither exists in the supplied data. |
| Resource utilization outcome | Unavailable semantically | Unavailable semantically | **Simulated** | Requires documented per-host utilization from iFogSim or an explicitly justified resource model. |
| Energy consumption / battery use | Unavailable | Unavailable | **Simulated, conditional on a validated power model** | No power/energy/battery fields. Include only after simulator support and per-task attribution are verified. |
| Cloud execution cost | Unavailable | Unavailable | **Simulated, conditional on an agreed pricing model** | No prices or billing records. Requires explicit cost assumptions and units. |
| Network bytes / traffic cost | Unavailable | Unavailable | **Simulated** | No task-associated input/output bytes or link traffic. |
| Actual execution destination (Local/Edge/Cloud) | Unavailable | Unavailable | **Simulated / logged by future integration** | Neither dataset has placement-action labels. Java must log both requested action and actual execution location. |
| Reward value | Unavailable | Unavailable | **Derivable after task outcomes and reward definition exist** | Project reward weights, normalization, units, and per-step/per-task attribution are not finalized in `docs/state-action-reward.md`. |
| State → action → outcome linkage | Unavailable | Unavailable | **Unavailable until a simulator/agent trace contract exists** | No cross-record task key. Future implementation must join observations, decisions, executions, and reward by `task_id`. |

## 6. Coverage conclusion

1. The only task-offloading-relevant direct data currently present is indirect multivariate telemetry (anonymous channels) and SMD test anomaly labels. Neither dataset has direct task-level features.
2. SMD's anomaly labels can supply abnormal-condition context for experiments, but they are not deadline, resource, network, or task outcome labels.
3. The project's core task state — task size, network latency, edge utilization, and deadline category — is not directly available in either supplied dataset.
4. Most actual offloading inputs and all per-task outcomes must be created/measured by the future simulator. Any use of ECW/SMD channels requires authoritative semantic mapping first.
5. Do not add `network_load` to the state by assumption: the parent state design explicitly lists it as optional and not agreed.

The matrix is a coverage decision aid. It does not finalize feature engineering, task schema, source mapping, discretization thresholds, reward weights, or experimental protocol.
