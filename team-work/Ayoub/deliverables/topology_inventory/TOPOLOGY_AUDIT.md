# Topology Audit

## Scope

This is a read-only Phase 1 audit of the current experiment-owned topology. No generic iFogSim class, working reference example, RL model, protocol, teammate file, or existing output was modified. The audited integration source is:

`audit_output/integration_prototype/src/org/fog/test/perfeval/RlOffloadingIntegrationExperiment.java`

The external reference is:

`C:\Users\DELL\OneDrive\Desktop\Research\iFogSim\src\org\fog\test\perfeval\DCNSFog.java`

The current topology is the three-device topology used by the accepted Local/Edge/Cloud integration runs, not the larger DCNS surveillance topology.

## Actual Device Inventory

The integration creates exactly three `InstrumentedFogDevice` objects in `run()`:

| Device name | Role | MIPS | RAM | Device uplink BW | Device downlink BW | Level | Busy power | Idle power |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `cloud` | root/cloud executor | 44,800 | 40,000 | 100,000 | 100,000 | 0 | `16 * 103 = 1648` | `16 * 83.25 = 1332` |
| `edge` | intermediate edge/fog executor | 2,800 | 4,000 | 10,000 | 10,000 | 1 | 107.339 | 83.4333 |
| `local` | originating local/IoT executor | 1,000 | 2,000 | 10,000 | 10,000 | 2 | 87.53 | 82.44 |

Source locations:

- Device creation and parameters: `RlOffloadingIntegrationExperiment.java`, lines 100-110.
- Device factory signature and construction: `RlOffloadingIntegrationExperiment.java`, lines 167-180.
- Power values are passed to `FogLinearPowerModel`: line 174.
- Device hierarchy levels: line 180.

### Host and processing properties

Every device is made by the same `createDevice()` factory:

| Property | Actual value | Source / status |
| --- | ---: | --- |
| Processing elements | 1 PE, ID 0 | `createDevice()`, line 170; `new Pe(0, new PeProvisionerOverbooking(mips))` |
| Host RAM | Device-specific RAM above | `RamProvisionerSimple(ram)`, line 171 |
| Host storage | 1,000,000 | `createDevice()`, line 172 |
| Host bandwidth provisioner | 10,000 | `new BwProvisionerOverbooking(10000)`, line 172 |
| VM/cloudlet scheduler | `StreamOperatorScheduler` with the one PE list | line 173 |
| Power model | `FogLinearPowerModel(busyPower, idlePower)` | line 174 |
| Architecture | `x86` | line 176 |
| Operating system | `Linux` | line 176 |
| VMM | `Xen` | line 176 |
| Time zone | 10.0 | line 177 |
| Processing cost | 3.0 | line 177 |
| Memory cost | 0.05 | line 177 |
| Storage cost | 0.001 | line 177 |
| Bandwidth cost | 0.0 | line 177 |
| Storage device list | Empty `LinkedList<Storage>` | line 179 |
| Scheduling interval | 10 | line 178 |
| Device rate per MIPS | 0.0 | line 178, final constructor argument |
| Initial constructor uplink latency | 0.0 | line 178, constructor argument; cloud keeps this value |

The device-level uplink/downlink bandwidth values are passed to `FogDevice`; the host provisioner bandwidth is a separate explicit value of 10,000. These should not be conflated.

The one-PE and scheduler configuration are implemented facts. CPU scheduling, queueing, allocation, and utilization behavior are inherited from iFogSim/CloudSim classes and are not reimplemented by the experiment.

## Parent-Child Links

The source hierarchy is:

```text
cloud (root, parentId = -1)
└── edge (parent = cloud, level 1)
    └── local (parent = edge, level 2)
```

Explicit source locations:

- `cloud.setParentId(-1)`: lines 102-103.
- `edge.setParentId(cloud.getId())`: lines 104-106.
- `edge.setUplinkLatency(45.0)`: line 106 via `WAN_UPLINK_MS`.
- `local.setParentId(edge.getId())`: lines 107-109.
- `local.setUplinkLatency(2.0)`: line 110.

The controller then performs the link registration. In external iFogSim `src/org/fog/placement/Controller.java`, `connectWithLatencies()` obtains each child’s `getUplinkLatency()`, puts it into the parent’s `childToLatencyMap`, and appends the child ID to the parent’s children list. In `FogDevice.sendDownFreeLink()`, the downlink delay is read from that child-latency map. Therefore the configured parent-child values apply to both directions in the current simulator link implementation:

| Link | Directional topology | Device bandwidth setting | Configured latency used by Controller/FogDevice | Status |
| --- | --- | ---: | ---: | --- |
| Edge-cloud | `edge -> cloud` uplink; `cloud -> edge` downlink | Edge up/down 10,000; cloud up/down 100,000 | 45 ms from edge uplink latency | Explicit and verified |
| Local-edge | `local -> edge` uplink; `edge -> local` downlink | Local up/down 10,000; edge up/down 10,000 | 2 ms from local uplink latency | Explicit and verified |

The integration source does not separately set a downlink latency. The downlink uses the controller-populated child map, which is derived from the child uplink latency. It is therefore not an independent downlink parameter.

The cloud root has no parent link. Its constructor receives uplink latency 0.0, but no cloud uplink is traversed in the accepted topology.

## Application Targets and Routing

The experiment defines three application modules and maps one module to each device:

- `local_executor` -> device name `local`.
- `edge_executor` -> device name `edge`.
- `cloud_executor` -> device name `cloud`.

Source locations: `createApplication()` lines 155-165 and `ModuleMapping` lines 121-123.

The Python action is converted to the module name by `moduleFor()` at lines 211-217. The emitted tuple sets its destination module name and is sent to the local device at lines 200-207. Normal iFogSim module placement and tuple routing then move the tuple through the parent hierarchy. The experiment records actual execution in `InstrumentedFogDevice.executeTuple()` and actual transfer bytes in `sendUpFreeLink()` / `sendDownFreeLink()` at lines 229-239.

The mapping is therefore:

```text
Python action Local -> local_executor -> local device
Python action Edge  -> edge_executor  -> edge device
Python action Cloud -> cloud_executor -> cloud device
```

The Python service is not a FogDevice, cloud node, network node, or simulated executor. It is a Java-launched control-plane subprocess that exchanges JSONL messages with the experiment.

## Sensor and Actuator APIs

The current integration does not instantiate a `Sensor`. `TaskEmitter` is an experiment-owned `SimEntity` that creates a tuple directly at simulation time 5.0; see lines 185-207. Therefore sensor transmission distribution, sensor gateway latency, and sensor output size are not part of this current topology.

The experiment does instantiate one `ResultEndpoint`, a subclass of `Actuator`, with gateway device `local` and actuator latency 1.0; see lines 115-118 and the `ResultEndpoint` constructor around lines 253-263. The endpoint receives the result tuple and records terminal arrival before delegating to normal actuator handling.

For API comparison, the DCNS reference uses `Sensor` and `Actuator` objects with explicit 1.0 ms sensor/actuator latency and camera gateway IDs at `DCNSFog.java`, lines 141-150. Those values belong to the DCNS topology, not the current integration topology.

## Tuple and Link Payloads

The emitted task tuple is constructed at `RlOffloadingIntegrationExperiment.java`, lines 200-202:

- Task length: 2,500 MI.
- Processing elements: 1.
- Input file size: 12,000 bytes.
- Output size: 2,000 bytes.
- Direction: `Tuple.UP`.

The experiment counts `tuple.getCloudletFileSize()` once at each instrumented parent-child transfer. Accepted traces show the resulting counted totals: Local 0 bytes, Edge 14,000 bytes, Cloud 28,000 bytes.

## Implemented, Inherited, and Unknown Values

### Implemented explicitly by the experiment

- Three devices and their names.
- Parent IDs and levels.
- Device MIPS, RAM, device link bandwidth, power values, host storage, PE count, scheduler, host provisioner bandwidth, characteristics, scheduling interval, rate, and constructor latency.
- Module placement for Local, Edge, and Cloud.
- Edge-cloud and local-edge uplink latency values.
- Direct task emitter, result endpoint, task payload sizes, and task execution/transfer instrumentation.

### Inherited from iFogSim/CloudSim

- Entity IDs generated by `FogUtils.generateEntityId()`.
- Parent child-list and child-latency-map registration performed by `Controller.connectWithLatencies()`.
- Tuple queueing, link busy state, network scheduling, CPU allocation, VM/module lifecycle, and CloudSim event scheduling.
- Downlink latency lookup from the parent’s child-latency map.
- Actual module execution mechanics and power/utilization update behavior.

### Currently unknown or not independently exposed by this experiment

- Independent downlink latency values; none are configured separately.
- A physical or graphical topology editor. Search of the available iFogSim source did not identify a drag-and-drop topology editor or a verified GUI topology builder. The project uses Java source configuration.
- Runtime inventory export from the current experiment; it records task traces but does not emit a full device/link inventory record.
- Dynamic latency variation during one run; the current parent-link latency values are static.
- A sensor-to-gateway link measurement; no Sensor is used by this integration.
- Per-task energy attribution; the existing integration intentionally reports energy as unavailable/null.

## DCNS Reference Comparison

`DCNSFog.java` is a different working reference. With `numOfAreas=1` and `numOfCamerasPerArea=4`, it constructs one cloud, one proxy, one router, and four camera FogDevices: seven FogDevices total, plus four sensors and four actuators. It uses cloud/proxy/router/camera capacities and links documented in its `createFogDevices()`, `addArea()`, and `addCamera()` methods. Its cloud-proxy latency is 100 ms, router-proxy latency is 2 ms, camera-router latency is 2 ms, and sensor/actuator gateway latencies are 1 ms. It is useful as an API/topology reference, but it is not the topology used by the accepted RL integration run.

## Visualization and Runtime Inspection

A topology diagram can be generated from the inspected Java configuration because the device and link declarations are explicit. A source-driven inventory exporter could also be added as a future experiment-owned utility by iterating the `devices` list, reading device names/IDs/parents/bandwidths/latencies, and reading each parent’s child-latency map after `Controller` construction. That would be preferable to manually typing values.

No evidence was found that iFogSim provides a graphical drag-and-drop topology editor. The current project uses Java code and placement classes (`ModuleMapping`, `ModulePlacementMapping`, and `Controller`) to define the topology.

## Recommended Defensible Research Topology

Do not change the current experiment in this audit. For the next topology revision, retain the same semantic three-tier path but make the following experiment-owned changes deliberately and document them:

1. Keep separate Local, Edge, and Cloud FogDevices with one executor module per tier, preserving actual action-dependent routing.
2. Add an explicit topology inventory record at setup time containing device ID/name, parent ID, level, MIPS, RAM, PE count, host storage, host bandwidth, device up/down bandwidth, scheduler, and power-model parameters.
3. Add explicit, independent link configuration for every direction only if the simulator API supports it; otherwise state clearly that downlink latency derives from child uplink latency.
4. Define a controlled latency profile for repeated scenarios by changing experiment-owned link parameters between runs, not by modifying generic `FogDevice` behavior.
5. Define an edge-utilization workload profile and record the exact sampling point before each decision.
6. Keep Python outside the simulated topology and label it as the decision service/control plane.
7. Preserve the existing parent-child transfer hooks and task correlation before extending to more devices or tasks.
8. Validate each topology revision with deterministic Local/Edge/Cloud routing and an independent runtime inventory trace.

These are recommendations for a future topology revision, not claims about the current accepted run.
