# iFogSim project discovery report

## Scope and safety

Read-only search target: `C:\Users\DELL\OneDrive\Desktop\Research`. No files were changed, moved, compiled, committed, or reverted. Existing changes in the main research repository were not touched. The external iFogSim worktree also already contains many modified compiled files under `out/`; this audit did not alter them.

## Located candidates

Only one plausible iFogSim project directory was found in the requested workspace:

| Candidate | Evidence | Recommendation |
|---|---|---|
| `C:\Users\DELL\OneDrive\Desktop\Research\iFogSim` | iFogSim2 README, Eclipse metadata, `src`, bundled JARs, compiled output, `DCNSFog.java`, and `AdaptiveOffloadingFog.java` | **Use this copy** for the first integration test after resolving its Java-version/build mismatch. |

The other directories at that workspace level are `adaptive-iot-task-offloading` and `rl_model`; neither is an iFogSim Java project.

## Exact requested files

- DCNS example: `C:\Users\DELL\OneDrive\Desktop\Research\iFogSim\src\org\fog\test\perfeval\DCNSFog.java`
- Adaptive experiment: `C:\Users\DELL\OneDrive\Desktop\Research\iFogSim\src\org\fog\test\perfeval\AdaptiveOffloadingFog.java`
- Project metadata: `C:\Users\DELL\OneDrive\Desktop\Research\iFogSim\.project`
- Eclipse build classpath: `C:\Users\DELL\OneDrive\Desktop\Research\iFogSim\.classpath`
- Project README: `C:\Users\DELL\OneDrive\Desktop\Research\iFogSim\README.md`
- Java source root: `C:\Users\DELL\OneDrive\Desktop\Research\iFogSim\src`
- Existing compiled-output root: `C:\Users\DELL\OneDrive\Desktop\Research\iFogSim\out\production\iFogSim`
- Bundled dependency root: `C:\Users\DELL\OneDrive\Desktop\Research\iFogSim\jars`

## Project provenance and configuration

This is an Eclipse Java project, not a Maven or Gradle project: there is no `pom.xml`, `build.gradle`, or wrapper. Its README identifies it as **iFogSim2**, and Git reports upstream `origin` as `https://github.com/Cloudslab/iFogSim.git`, current checked-out commit `5f68d3947e450d8d2b4af42670be819206be68c9` (2025-10-03). Therefore it is an upstream iFogSim2 clone/copy with local state, not a separate build-managed experiment project.

`AdaptiveOffloadingFog.java` is untracked in that Git worktree, so it is a local experiment added to the upstream-style source tree. Its source creates `local-device`, `edge-device`, and `cloud`, establishes parent links, and prints the topology. It does **not** create an `Application`, `Sensor`, `Controller`, module mapping, start `CloudSim`, or execute tasks. It is an appropriate topology starting point, but not an executable offloading experiment yet.

The Eclipse classpath declares source `src`, output `out/production/iFogSim`, default Eclipse JRE container, and these local libraries:

- `commons-io-2.17.0.jar`, `commons-lang3-3.17.0.jar`, `commons-net-3.11.1.jar`
- `easymock-5.3.0.jar`, `geoip2-4.2.0.jar`, `guava-18.0.jar`
- `json-simple-1.1.1.jar`, `junit-jupiter-engine-5.11.3.jar`, `opencsv-5.9.jar`, `uncommons-maths-1.2.3.jar`
- `jars\commons-math3-3.5\commons-math3-3.5.jar`

No project file declares a source/target Java release. The installed runtime/compiler is Temurin OpenJDK 8 (`1.8.0_504`). The pre-existing compiled classes are class-file version **69.0** (Java 25), proven by both launch failures; Java 8 supports only version 52.0. A Java 25 runtime is required to launch the current `out/production/iFogSim` artifacts. Whether this source tree can instead be cleanly rebuilt for Java 8 cannot be claimed without a separate build that must be coordinated because it would overwrite build output.

## Launch check

The README documents Eclipse/IntelliJ launch after adding the local JARs. To perform a read-only equivalent check, the existing compiled output and exactly those JARs were placed on the Java classpath and these entry points were invoked:

```text
org.fog.test.perfeval.AdaptiveOffloadingFog  -> exit 1
org.fog.test.perfeval.DCNSFog                -> exit 1
```

Both fail before user code runs with `UnsupportedClassVersionError`: class file version 69.0 was compiled by a newer Java release than the installed Java 8 runtime. This establishes that the existing launch method is **not runnable in the current Java environment**. It does not demonstrate a source defect or a simulator failure.

## Inspected simulator responsibilities

| Concern | Inspected class/file | Verified behavior | Integration implication |
|---|---|---|---|
| Task generation | `src\org\fog\entities\Sensor.java` | `startEntity` schedules `EMIT_TUPLE`; `processEvent` calls `transmit`; `transmit` builds a `Tuple` from application-edge CPU/network lengths, assigns ids/timing, and sends it to gateway device | Candidate pre-decision hook; must inspect/apply a design before synchronously blocking it for Python |
| DCNS workload/topology | `...\DCNSFog.java` | Creates sensor/camera topology and periodic camera sensor; constructs application edges/loops | Existing runnable-style example, but its placement is module-level and static |
| Adaptive topology | `...\AdaptiveOffloadingFog.java` | Creates only three `FogDevice`s and parent links | Local experiment baseline; has no task/workload/routing test yet |
| Application/module placement | `...\DCNSFog.java` plus `src\org\fog\placement\ModuleMapping.java`, `ModulePlacementMapping.java`, `ModulePlacementEdgewards.java` | DCNS builds `ModuleMapping`, then calls `Controller.submitApplication` with `ModulePlacementMapping` or `ModulePlacementEdgewards` | These are the verified placement mechanisms currently exercised by DCNS; no per-task RL adapter is present |
| Tuple routing and execution | `src\org\fog\entities\FogDevice.java` | `processTupleArrival` executes locally when target module is hosted; otherwise routes UP/DOWN. `sendUpFreeLink` uses tuple file size/uplink bandwidth + uplink latency; `sendDownFreeLink` uses file size/downlink bandwidth + child latency | A Local/Edge/Cloud choice must map to actual module/tuple routing semantics, not just a device label |
| Simulation completion | `src\org\fog\placement\Controller.java` | handles `FogEvents.TUPLE_FINISHED`, stop event, and printing. In this copy `processTupleFinished` is empty | Not a per-task feedback callback; a first integration trace needs an explicit listener/hook |
| End-to-end loop delay | `FogDevice.updateTimingsOnReceipt`, `org\fog\utils\TimeKeeper.java` | uses `CloudSim.clock()` and sensor `emitTimes` to update loop-average delay | Existing aggregate loop timing; exact desired per-task endpoint requires design/inspection |
| CPU timing | `TimeKeeper.tupleStartedExecution` / `tupleEndedExecution` | records per-tuple CPU start and aggregates by tuple type | Existing CPU-time source; must retain per-task value if needed by protocol |
| Energy | `FogDevice.getEnergyConsumption`; `Controller.printPowerDetails` | Controller prints per-device aggregate energy at simulation stop | Aggregate per-device measure exists; no verified per-task energy attribution |
| Network usage | `NetworkUsageMonitor.java`; `FogDevice.sendUpFreeLink` / `sendDownFreeLink` | accumulates latency × tuple network size and Controller prints an aggregate normalized value | Existing aggregate network metric; not yet a direct per-task `bandwidth_bytes` value |
| Stable identifiers | `Tuple` creation in `Sensor`, `TimeKeeper` ids | a tuple has Cloudlet/actual tuple ids; protocol `task_id` mapping is not implemented | Java adapter must define and persist one mapping before Python exchange |

## Placement and outcome conclusion

The actual current task-placement decision in DCNS happens at application submission, through `ModulePlacementMapping`/`ModulePlacementEdgewards`; it is not a dynamic Local/Edge/Cloud decision per emitted tuple. `AdaptiveOffloadingFog` contains no placement decision. Therefore no existing class can honestly be called the RL placement adapter. The likely extension points are now identifiable, but the exact modification must wait for inspection of the next files below and an agreed definition of whether a decision controls module placement, tuple destination/routing, or a distinct per-task abstraction.

## Java files to inspect next

1. `C:\Users\DELL\OneDrive\Desktop\Research\iFogSim\src\org\fog\placement\ModulePlacementMapping.java`
2. `C:\Users\DELL\OneDrive\Desktop\Research\iFogSim\src\org\fog\placement\ModulePlacementEdgewards.java`
3. `C:\Users\DELL\OneDrive\Desktop\Research\iFogSim\src\org\fog\placement\Controller.java`
4. `C:\Users\DELL\OneDrive\Desktop\Research\iFogSim\src\org\fog\entities\FogDevice.java`
5. `C:\Users\DELL\OneDrive\Desktop\Research\iFogSim\src\org\fog\entities\Sensor.java`
6. `C:\Users\DELL\OneDrive\Desktop\Research\iFogSim\src\org\fog\application\Application.java`
7. `C:\Users\DELL\OneDrive\Desktop\Research\iFogSim\src\org\fog\entities\Tuple.java`
8. `C:\Users\DELL\OneDrive\Desktop\Research\iFogSim\src\org\fog\utils\TimeKeeper.java`
9. `C:\Users\DELL\OneDrive\Desktop\Research\iFogSim\src\org\fog\utils\NetworkUsageMonitor.java`

For a first real integration, inspect these before changing any code. The project above is the recommended and only located simulator copy; first resolve the JDK 25 compiled-output mismatch or agree on a clean rebuild strategy in a separate working copy.
