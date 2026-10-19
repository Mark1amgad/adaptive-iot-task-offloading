# First integration implementation blocker

## Why no Java adapter or experiment source was added

The implemented Python protocol v1.0 requires every `outcome` to contain a boolean `deadline_met`. For a completed task, it also needs a real latency and (under the current reward configuration) required `resource_metrics.bandwidth_bytes`.

The inspected classic iFogSim flow used by DCNS/Adaptive has no deadline field or deadline-enforcement rule in `Sensor`, `Tuple`, `AppEdge`, `FogDevice`, or `Controller`. The source audit also established that current network reporting is aggregate `latency × tuple-size`, not a per-task byte counter. The request explicitly prohibits inventing deadline outcomes or synthetic values presented as simulator measurements.

Therefore adding a Java client now would require either:

1. sending an ungrounded `deadline_met` value, or
2. silently changing/replacing the implemented Python protocol or reward behavior.

Both would violate the stated safety requirements. No external iFogSim source, Python agent source, protocol, or RL setting was modified.

## Exact approval needed

Approve and document, for the first one-task *integration-only* experiment:

1. A task deadline definition: source, unit (ms), start time (sensor emission or another event), endpoint, and rule `deadline_met = end_to_end_latency <= deadline_ms`.
2. Which task transfers count toward `bandwidth_bytes`, with an instrumentation rule that sums actual `Tuple.cloudletFileSize` / output sizes for each counted simulated link.
3. The task model mapping of the configured iFogSim cloudlet length to `task_mi`, and the meaning of `wan_latency_ms` as a topology-configured path quantity.
4. The Java response timeout and fallback action. The fallback path must remain outside Python learning when no valid action was received.

After approval, the smallest safe change set remains the dedicated experiment/adapters described in `../ONE_TASK_INTEGRATION_DESIGN.md`: a new experiment class beside `AdaptiveOffloadingFog`, a task-emitter/JSONL adapter, and a narrow completion/measurement observer. No generic `FogDevice`, Controller, DCNSFog, or RL model change is currently justified.

## Files created in this prototype directory

- `BUILD_PREFLIGHT.md`
- `INTEGRATION_BLOCKER.md`
- `classes_preflight/` (isolated compilation output)

There is no one-task trace or Python protocol log because no scientifically valid outcome message can yet be formed.
