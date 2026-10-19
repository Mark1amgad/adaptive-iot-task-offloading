# One-task acceptance test — Java / Python / iFogSim

## Purpose

This is a deterministic integration acceptance test for one real iFogSim task. It establishes traceability and message correctness; it is not a latency, energy, or RL-performance experiment. No pass condition depends on a preferred action.

## Preconditions

- Compile the dedicated experiment into an isolated output directory with the inspected iFogSim classpath; do not overwrite simulator output.
- Start one persistent implemented Python `rl_model` JSONL server in `dev` phase, retaining stdout protocol lines and stderr separately.
- Use a unique `run_id`, fixed simulation seed, one task, one selected terminal endpoint, and three statically deployed tier-specific target modules (one Local, one Edge, one Cloud).
- Configure and trace an edge-to-cloud uplink latency, a single-PE task MI, a relative deadline, and the explicit counted-link policy from Measurement Contract V1.
- Install the task registry, transfer observer, execution observer, endpoint observer, and Java-side JSONL trace before task emission.

## Lifecycle and pass/fail criteria

| Step | Required evidence | Pass | Fail |
|---|---|---|---|
| 1. Handshake | `hello` and `hello_ack` trace | Ack has protocol 1.0, advertised Local/Edge/Cloud actions, and supports the sent feature names. | Timeout, fatal/error response, wrong version, or unsupported capability. |
| 2. Create / observe | Immutable task record and observation JSONL | One nonempty `task_id`; finite `task_mi`, `wan_latency_ms`, `edge_utilization`, `deadline_ms`; all values have sources recorded before routing. | Missing/nonfinite field, duplicate id, no source, or observation validation error. |
| 3. Action correlation | Python action response and task record | `type=action`; action id/name form a valid matching pair; returned task id exactly equals the observation id; action is available. | Timeout, malformed/error reply, invalid action pair, or id mismatch. |
| 4. Apply destination | Placement/action trace | The requested action maps to exactly one tier-specific deployed module, and routing begins with the selected target. | Mapping absent/ambiguous, module unavailable, or generic `destinationDeviceId` assumed to route the classic path. |
| 5. Capture execution | Execution observer trace | Exactly one executing device/module is recorded for the task and maps to Local/Edge/Cloud. | No execution event, more than one unmodelled executor, or no tier mapping. |
| 6. Completion callback | Endpoint arrival trace | Result with the correlated task id arrives at the explicitly selected endpoint; terminal time is >= creation time. | Simulation ends without endpoint arrival, uncorrelated result, or negative latency. |
| 7. Per-task bandwidth | Per-hop transfer rows | Every included actual up/down traversal has one bytes row, rows join to the task, and `bandwidth_bytes` is their exact sum. | Aggregate `NetworkUsageMonitor` used, missing correlation, duplicate hop accounting, or an unexplained transfer. |
| 8. Construct outcome | Outcome JSONL and task record | `action_executed` derives from actual executor; completed latency uses endpoint minus creation; deadline uses configured relative deadline; resource metrics meet protocol constraints. `energy_joules`/utilization may be null only as allowed by protocol. | Requested action copied as executed action, fabricated metric, invalid status/deadline combination, or field validation error. |
| 9. Outcome acknowledgement | `outcome_ack` | Ack task id equals the single task id and is retained with update/model metadata. | Error, timeout, id mismatch, or no acknowledgement. |
| 10. Shutdown | `shutdown_ack`, process status, trace locations | Graceful shutdown, zero `orphaned_tasks`, normal subprocess exit, and durable Java/Python traces. | Orphaned pending task, forced shutdown without recorded reason, or missing trace. |

## Timeout branch acceptance

The 1000 ms response timeout is a proposed configuration, not verified timing evidence. If the test deliberately exercises this branch, it passes only as a **fallback-path test** when the trace proves: no valid action was accepted; `decision_source` is `fallback_timeout` or `fallback_error`; Edge availability was checked; actual executor is recorded; and no outcome was sent to Python for that task. It must not be counted as the normal agent-decision end-to-end acceptance test.

## Required retained artifacts

One auditable run directory must contain the launch command/classpath and hashes, configuration/seed, Java JSONL send/receive transcript, Python stdout/stderr and service event log, task registry record, per-hop byte rows, execution/endpoint rows, outcome acknowledgement, shutdown acknowledgement, and exit statuses. Numeric values in these artifacts are the only values that may later be reported as measured results.

