# iFogSim2 tuple event-flow audit

**Scope:** source trace of `C:\Users\DELL\OneDrive\Desktop\Research\iFogSim`. The existing DCNSFog baseline was executed successfully with JDK 25; this document does not claim an RL-integrated run.

## Actual classic iFogSim flow used by DCNSFog

| Stage | Source and method | Event/data path verified in source | Measured / not measured |
|---|---|---|---|
| 1. Application setup | `DCNSFog.main`, `createApplication`, `createFogDevices` | Builds `Application`, `Sensor`, `Actuator`, `FogDevice` topology; calls `Controller.submitApplication`; starts CloudSim | Static topology/application values only; no deadline or RL state |
| 2. Sensor scheduling | `org.fog.entities.Sensor.startEntity` and `processEvent` | Schedules `FogEvents.SENSOR_JOINED`, then `FogEvents.EMIT_TUPLE`; each EMIT calls `transmit` and schedules the next emission from `Distribution` | Simulation clock establishes arrival time; no explicit task record/deadline |
| 3. Tuple creation | `Sensor.transmit` | Finds the application edge whose source matches sensor tuple type; creates `Tuple(appId, FogUtils.generateTupleId(), Tuple.UP, cpuLength, ..., nwLength, outputSize, ...)`; sets tuple type, source/destination module, user, gateway device; calls `updateTimings` | `cloudletId` is from global `FogUtils.TUPLE_ID`; CPU/network lengths are copied from `AppEdge`. `actualTupleId` and emit time exist only when an `AppLoop` contains this source→destination edge. |
| 4. Gateway transmission | `Sensor.transmit` | `send(gatewayDeviceId, sensorLatency, FogEvents.TUPLE_ARRIVAL, tuple)` | Sensor-to-gateway simulated latency is used. No per-tuple byte log is written. |
| 5. Arrival/routing | `FogDevice.processOtherEvent` → `processTupleArrival` | On `TUPLE_ARRIVAL`, sends `TUPLE_ACK`; executes if this device hosts matching destination module/copy, otherwise UP tuples call `sendUp`, DOWN tuples call `sendDown` | Arrival is observable in code. The classic `FogDevice` route is module-host/direction based, not `Tuple.destinationDeviceId` based. |
| 6. Link scheduling | `FogDevice.sendUpFreeLink` / `sendDownFreeLink` | Queues if a link is busy. Transfer delay is `tuple.cloudletFileSize / uplink|downlinkBandwidth` plus configured link latency; sends subsequent `TUPLE_ARRIVAL` | `NetworkUsageMonitor.sendingTuple(latency, cloudletFileSize)` accumulates aggregate latency×size. It does not retain bytes per tuple. |
| 7. Local execution | `FogDevice.executeTuple` | Locates target `AppModule`, calls `TimeKeeper.tupleStartedExecution`, allocates MIPS, then invokes CloudSim cloudlet submission | CPU start is stored keyed by cloudlet id. The running device/module is known at this point. |
| 8. Cloudlet completion | `FogDevice.checkCloudletCompletion` | Polls finished cloudlets; calls `TimeKeeper.tupleEndedExecution`; asks `Application.getResultantTuples`; retains actual tuple id in resultant tuples; self-sends them; sends `CLOUDLET_RETURN` to user/broker | CPU duration is computed but only aggregated by tuple type; the included `FogBroker.processEvent` is empty. |
| 9. Loop completion | `FogDevice.updateTimingsOnReceipt` or `Actuator.processTupleArrival` | If an app loop’s terminal edge is reached, computes `CloudSim.clock - TimeKeeper.emitTimes[actualTupleId]`, updates loop average/count, and removes the emit time | Existing end-to-end loop delay is aggregate only after this point; per-tuple value is not persisted. |
| 10. Controller events | `Controller.processEvent` | Handles APP_SUBMIT, TUPLE_FINISHED, resource management, stop. `FogDevice` sends `TUPLE_FINISHED` only for a cloud tuple with null destination module. `Controller.processTupleFinished` is empty. | No usable classic per-task completion callback is implemented. |
| 11. Stop statistics | `Controller.printTimeDetails`, `printPowerDetails`, `printCostDetails`, `printNetworkUsageDetails` | On STOP_SIMULATION prints loop averages, tuple-type CPU averages, per-device cumulative energy, cloud cost, aggregate network usage | These are run-level/aggregate outputs, not protocol-ready task outcomes. |

## Identifier relationship

- `Tuple.cloudletId`: a global increment from `FogUtils.generateTupleId()`, unique for the JVM run under the inspected implementation.
- `Tuple.actualTupleId`: a TimeKeeper correlation id assigned by `Sensor.updateTimings` only when the first edge belongs to an `AppLoop`; generated result tuples carry it forward in `Application.getResultantTuples`.
- `AppLoop.loopId`: identifies a configured logical chain, not an individual task. `TimeKeeper.loopIdToTupleIds` maps a loop to many actual tuple ids.
- There is no current mapping from either Java identifier to Python `task_id`.

## Important routing distinction

`Tuple.destinationDeviceId` exists and is set by the sensor, but classic `FogDevice.processTupleArrival` does not use it for destination selection. The iFogSim2 `MicroserviceFogDevice` class does use it together with a routing table/service discovery, but DCNSFog and AdaptiveOffloadingFog instantiate classic `FogDevice`. It would be incorrect to assume setting `destinationDeviceId` changes DCNSFog routing.

## Baseline execution observed

Using `C:\Program Files\Eclipse Adoptium\jdk-25.0.3.9-hotspot\bin\java.exe` with existing `out\production\iFogSim` and bundled JARs:

- `org.fog.test.perfeval.AdaptiveOffloadingFog`: exit 0; prints Local/Edge/Cloud topology only.
- `org.fog.test.perfeval.DCNSFog`: exit 0; launches DCNS, reports static module placement and aggregate results.

This verifies the precompiled baseline launch, not task-offloading integration, action control, per-task logging, or Python communication.
