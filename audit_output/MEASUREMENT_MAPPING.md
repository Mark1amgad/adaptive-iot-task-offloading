# iFogSim measurement and identifier mapping

| Needed item | Source evidence | Classification | Honest first-test use / limitation |
|---|---|---|---|
| Java tuple/cloudlet id | `Sensor.transmit` → `FogUtils.generateTupleId`; `Tuple.getCloudletId` | Directly available | Unique counter within one JVM simulation; use it in a composed protocol task id with run id. |
| Logical loop correlation id | `Sensor.updateTimings` → `TimeKeeper.getUniqueId`, `Tuple.actualTupleId` | Directly available conditionally | Exists only when a configured AppLoop has the sensor→destination edge; propagated by `Application.getResultantTuples`. |
| Task creation simulation time | `TimeKeeper.emitTimes[actualTupleId] = CloudSim.clock()` | Directly available conditionally | Available only for timed app loops; it is removed at loop completion. Copy it into task trace before removal for auditability. |
| CPU work demand | `AppEdge.tupleCpuLength` copied into Tuple cloudlet length | Directly available | This is the simulator work specification; map to `task_mi` only after confirming iFogSim/CloudSim unit semantics. |
| Input network size | `AppEdge.tupleNwLength` copied to Tuple cloudlet file size | Directly available | A task byte input field exists; record it without interpreting it as total network use. |
| CPU start | `FogDevice.executeTuple` → `TimeKeeper.tupleStartedExecution` | Directly available internally | Stored by cloudlet id but not exported in current output. Read/copy in a task observer. |
| CPU finish / CPU duration | `FogDevice.checkCloudletCompletion` → `TimeKeeper.tupleEndedExecution` | Small instrumentation | Current method calculates duration then updates only per-tuple-type average. Retain `(cloudletId,start,end,duration,executingDevice)` in a task record. |
| Actual execution device | `FogDevice.processTupleArrival` / `checkCloudletCompletion` has `getName`/device id and module | Small instrumentation | Record at execution/completion; it is not emitted as a per-task log now. |
| End-to-end latency | `FogDevice.updateTimingsOnReceipt` and `Actuator.processTupleArrival` compute `CloudSim.clock - emitTime` | Small instrumentation | Existing code updates an aggregate then removes emit time. Record the value and endpoint for each terminal task before removal. |
| Link transmission delay | `FogDevice.sendUpFreeLink` / `sendDownFreeLink` | Directly computable from existing per-event values | Delay formula is modeled from file size/bandwidth + configured latency; record per hop only if instrumentation is added. |
| Bandwidth bytes per task | Tuple input/output size fields | Small instrumentation | Sum actual tuple sizes for each traversed link/task. `NetworkUsageMonitor` is only aggregate latency×size, not bytes/task. Must define which links count. |
| Device energy | `FogDevice.getEnergyConsumption`, updated in `updateAllocatedMips` | Directly available aggregate | Cumulative per device only. |
| Energy per task | No attribution map | New modeling assumption | Snapshot deltas are ambiguous with concurrent work; per-task allocation policy must be approved before reporting energy. |
| Edge CPU utilization at decision | `FogDevice.updateAllocatedMips` calculates `lastUtilization = min(1, totalAllocatedMips/totalMips)`; PE provisioner exposes utilization | Small instrumentation / definition required | A current utilization exists internally but is not a public protocol metric. Decide whether to use last utilization or a fresh allocation snapshot and document timing. |
| Cloud/WAN latency | Topology `setUplinkLatency` plus transfer delay in `sendUpFreeLink` | Directly available topology parameter | This is configured simulated latency, not an RTT measurement. Define path/endpoints before sending `wan_latency_ms`. |
| Deadline / deadline_met | No deadline field/use in inspected DCNS `Sensor`, `Tuple`, `AppEdge`, `FogDevice`, or classic Controller | New modeling assumption | Other CloudSim network classes mention deadlines but DCNS/classic iFogSim flow does not enforce one. Add an explicit per-task deadline and compare a defined terminal time. |
| Failure status/reason | No per-task failure model in inspected classic flow | New modeling assumption | First test may truthfully report completed only if it completes; do not synthesize failures. |

## Identifier policy for the first test

Use an adapter-owned `task_id = <run_id>:tuple:<cloudletId>` and log the associated `actualTupleId` when one exists. Do not use `AppLoop.loopId` as a task id: it identifies a loop shared by many tasks. Ensure every resulting tuple or terminal observer can be joined to the originating record through `actualTupleId` and/or explicit adapter correlation.
