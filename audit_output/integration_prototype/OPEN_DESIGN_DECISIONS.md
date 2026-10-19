# Open design decisions for the first integration

## Verified simulator facts versus proposed defaults

| Topic | Verified fact from inspected source | Proposed V1 default | Approval / decision still needed |
|---|---|---|---|
| Deadline | Classic Sensor, Tuple, AppEdge, FogDevice, and Controller do not enforce or store a per-task deadline. Terminal loop timing events exist. | Relative deadline from creation to result arrival; completed task meets `latency <= deadline`; failed task is false. | Select actual deadline(s), endpoint, and failure model. |
| Bandwidth | Up/down transfer methods use `cloudletFileSize`; `NetworkUsageMonitor` stores only global `latency * size`. Resultant tuples retain `actualTupleId`. | Count actual bytes once per included transfer, both request uplinks and result downlinks; exclude module deployment/unrelated traffic. | Confirm whether sensor-to-gateway is included and whether any application fan-out is permitted in the first task. |
| Task work | `Cloudlet` documents `cloudletLength` in MI; `getCloudletTotalLength` accounts for PEs. | One PE; send initial tuple `getCloudletLength()` as `task_mi`. | Approve multi-PE interpretation before extending beyond one task. |
| WAN latency | `FogDevice.uplinkLatency` is a configured one-way parent-link delay added on `sendUpFreeLink`; DCNS labels its proxy-cloud value 100 ms. Adaptive topology leaves the value at constructor default 0. | Read edge/proxy `getUplinkLatency()` as configured `wan_latency_ms`. | Choose a topology value and whether WAN means edge→cloud only, or a broader path. Do not call it a measured RTT. |
| Utilization | FogDevice computes a capped internal last utilization while allocating MIPS; no public per-task utilization metric is emitted. | Sample the edge/executor allocation state immediately before observation/at admission. | Approve exact accessor and sample definition; do not silently replace it with a different statistic. |
| Energy | Per-device cumulative energy is available; per-task attribution is not. | Permit protocol `energy_joules:null` unless an approved isolated-run delta rule is installed. | Approve whether a delta is scientifically acceptable and how concurrency is excluded. |
| Routing | Classic FogDevice routes based on module placement and tuple destination module; the initial tuple's `destinationDeviceId` is not the classic routing control. | Three tier-specific target modules, one deployed per tier, selected by adapter mapping. | Confirm task semantics/module names and whether Local must be the originating FogDevice. |
| Timeout/fallback | No Java client or timeout policy exists. Python service supports a persistent ordered JSONL session. | 1000 ms wall-clock response timeout; Edge fallback if available; no Python outcome without a valid agent action. | Validate subprocess behavior on the target interpreter/machine and approve timeout/fallback. |
| Learning mode | Default model behavior is contextual-bandit-like (`gamma=0`) and existing Python validation/learning remains unchanged. | Use `dev` phase and `terminal:true` for a single task. | Approve whether the test should update the model; no algorithm/configuration change is proposed. |

## Scientific and implementation guardrails

1. A configured latency, static task size, or chosen deadline is an input—not an observed performance result.
2. Do not report aggregate loop latency, aggregate network usage, or cumulative device energy as per-task measurements.
3. A fallback route must remain distinguishable from an agent action in every trace and must not train the server where no valid pending action exists.
4. A completion-only first task does not validate failure semantics. Failure injection/modeling requires a separate approved design.
5. The first task should use a single, non-fan-out result path, one PE, and an otherwise idle topology so identifiers, energy scope, and byte sums are auditable.

## Smallest safe implementation path

The contract **can be implemented without changing generic `FogDevice` behavior**. Create a new, dedicated experiment package/class alongside the unmodified examples, with:

1. a Java JSONL subprocess adapter and immutable task registry;
2. one controlled task emitter and three statically placed tier modules;
3. narrow experiment-only `FogDevice`/endpoint subclasses or observers that call existing behavior while recording execution, up/down link bytes, and terminal arrival; and
4. a JSONL/audit trace writer.

Do not alter `FogDevice` routing, `NetworkUsageMonitor`, `TimeKeeper`, the Python protocol, or RL configuration. This path uses normal `processTupleArrival`, `sendUpFreeLink`/`sendDownFreeLink`, `executeTuple`, and completion events, while recording the missing per-task facts externally.

