# Topology Inventory Validation Report

## Scope

Phase 2 adds an experiment-owned runtime inventory exporter and renderer under `audit_output/topology-work/`. The existing integration experiment, generic iFogSim classes, RL model, JSONL protocol, teammate files, and previous run directories were not modified or overwritten.

## Build

Exporter source:

`audit_output/topology-work/src/org/fog/test/perfeval/TopologyInventoryExporter.java`

The exporter was compiled with JDK 25 into:

`audit_output/topology-work/classes/`

The compile used the external iFogSim source root and bundled jars:

```powershell
$jdk = 'C:\Program Files\Eclipse Adoptium\jdk-25.0.3.9-hotspot\bin\javac.exe'
$jarRoot = 'C:\Users\DELL\OneDrive\Desktop\Research\iFogSim\jars'
$sourceRoot = 'C:\Users\DELL\OneDrive\Desktop\Research\iFogSim\src'
& $jdk -encoding UTF-8 -cp "$jarRoot\*;$jarRoot\commons-math3-3.5\commons-math3-3.5.jar" `
  -sourcepath "$sourceRoot;audit_output\topology-work\src" `
  -d audit_output\topology-work\classes `
  audit_output\topology-work\src\org\fog\test\perfeval\TopologyInventoryExporter.java
```

Observed compile result: exit code 0, with only the existing deprecation/unchecked notes.

## Runtime Export

The exporter was run against the same three-device baseline declarations as the accepted integration topology and exited 0:

```powershell
& 'C:\Program Files\Eclipse Adoptium\jdk-25.0.3.9-hotspot\bin\java.exe' `
  -cp "audit_output\topology-work\classes;C:\Users\DELL\OneDrive\Desktop\Research\iFogSim\jars\*;C:\Users\DELL\OneDrive\Desktop\Research\iFogSim\jars\commons-math3-3.5\commons-math3-3.5.jar" `
  org.fog.test.perfeval.TopologyInventoryExporter `
  (Resolve-Path audit_output\topology-work\runtime).Path
```

Observed exporter exit code: `0`.

Runtime inventory facts:

- 3 devices: cloud ID 2, edge ID 3, local ID 4.
- Parent hierarchy: local ID 4 -> edge ID 3 -> cloud ID 2.
- 2 controller-registered links.
- Edge-to-cloud effective latency: 45.0 ms.
- Local-to-edge effective latency: 2.0 ms.
- Each device: 1 PE, scheduler `org.fog.scheduler.StreamOperatorScheduler`.
- Modules: cloud_executor, edge_executor, local_executor on their matching devices.
- Python is recorded as an external control-plane description, not a FogDevice.

## Runtime Versus Source Validation

The exported runtime inventory was checked against the source audit and baseline Java declarations:

| Property | Source declaration | Runtime export | Assessment |
| --- | --- | --- | --- |
| Device count/names | cloud, edge, local | 3 matching names | PASS |
| Parent IDs | -1, cloud ID, edge ID | cloud -1; edge parent 2; local parent 3 | PASS |
| Levels | 0, 1, 2 | 0, 1, 2 | PASS |
| MIPS | 44,800 / 2,800 / 1,000 | 44,800 / 2,800 / 1,000 | PASS |
| RAM | 40,000 / 4,000 / 2,000 | matching | PASS |
| PEs | one per factory call | one per runtime host | PASS |
| Device link bandwidth | cloud 100,000; edge/local 10,000 | matching | PASS |
| Link latency | edge 45 ms; local 2 ms | controller map 45/2 ms | PASS |
| Host bandwidth provisioner | 10,000 | 10,000 | PASS |
| Host storage | factory argument 1,000,000 | runtime `Host.getStorage()` 990,000 | REPORTING DISCREPANCY |
| Scheduler/module placement | StreamOperatorScheduler and one module per tier | matching runtime class/module fields | PASS |

The host storage discrepancy is preserved rather than hidden. The factory passes `1,000,000` to the `PowerHost` constructor, while the runtime getter reports `990,000` after the inherited simulator initialization. The inventory reports the runtime-observed value and the audit/source report retains the configured constructor value. This is a simulator-runtime detail requiring follow-up before using storage as a research measurement.

Busy/idle power values are exported from the `FogLinearPowerModel` runtime object using protected getter reflection: cloud 1648/1332, edge 107.339/83.4333, local 87.53/82.44. Architecture, OS, VMM, scheduler, bandwidths, levels, IDs, and links are read from runtime objects. Parent/module roles are joined from the exporter’s baseline declarations.

## Diagram Validation

`render_topology.ps1` reads `TOPOLOGY_INVENTORY.json` and generates:

- `topology.svg`
- `topology.png`

The diagram contains the three runtime device names/IDs, MIPS, RAM, PEs, device/host bandwidth, module placement, parent-child links, effective latencies, hierarchy direction, task paths, legend, and an external Python control-plane component. It does not add physical devices or imply Python is simulated.

## Regression Scope

Existing Local, Edge, and Cloud regression scenarios were not rerun. The request explicitly prohibited rerunning completed simulator experiments. No existing output was overwritten. The exporter uses the same baseline device declarations and only creates a fresh inventory process under `topology-work/runtime`; it does not alter the integration experiment behavior.

Existing accepted routing evidence remains in:

`audit_output/integration_prototype/runs/acceptance_20261013_220748/`

## Limitations

- The exporter’s baseline declarations intentionally mirror the current experiment; it is not yet a refactored shared topology factory.
- The exporter is intentionally isolated and duplicates the current three-device constructor values to create a fresh inspection run; it does not import or modify the existing integration class. The emitted device/link properties are then read from the runtime objects and Controller-populated link maps.
- Parent/module roles are experiment metadata because the generic runtime object does not intrinsically know research roles.
- Power model parameters are obtained through narrow reflection because iFogSim exposes those getters as protected.
- Host storage must be resolved before using it as a scientific variable because configured and runtime-observed values differ.
- The topology remains static; this phase does not implement variable latency, utilization changes, multi-task execution, or new devices.
