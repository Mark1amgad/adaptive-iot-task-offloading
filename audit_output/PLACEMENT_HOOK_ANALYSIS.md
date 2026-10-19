# Placement-hook analysis for adaptive task offloading

## Existing behavior

`ModulePlacementMapping.mapModules` and `ModulePlacementEdgewards.mapModules` create module instances on devices before simulation execution. `Controller.processAppSubmit` then sends `LAUNCH_MODULE` events. Later, classic `FogDevice.processTupleArrival` executes a tuple only at a device that hosts its destination module; otherwise it forwards by UP/DOWN direction. This is application-module placement, not an action for each arriving computational task.

| Design | Existing classes affected | Per-task decisions? | Uses simulator behavior? | Risks / outcome quality |
|---|---|---|---|---|
| A. Pre-simulation module/device placement | Experiment entry point, `ModuleMapping`, `ModulePlacementMapping` or `ModulePlacementEdgewards`, Controller submission | No: one mapping is fixed before tasks emit | Yes, normal module launch/routing/execution | Valid static baseline only; cannot answer adaptive per-task offloading question or attribute different actions to tasks |
| B. Runtime per-tuple routing in classic model | `Sensor.transmit`/a subclass, `FogDevice.processTupleArrival` or a targeted adapter, application graph/modules | Potentially, but only after defining routing semantics | Potentially, but classic FogDevice ignores `destinationDeviceId`; must avoid bypassing queues/execution | Altering generic FogDevice is invasive; merely changing a label does not route to target. A module must be available at the selected tier and routing must remain real. |
| C. Explicit per-task offloading abstraction in a dedicated experiment | New/extended `AdaptiveOffloadingFog` experiment, custom task-emitter/adapter, app graph/tier-specific modules, targeted completion instrumentation | Yes | Yes, if the selected tier maps to deployed modules and the tuple still follows FogDevice/CloudSim events | More initial design work, but gives explicit Local/Edge/Cloud semantics, action traceability, actual execution destination, and an honest per-task outcome |

## Recommendation

Use **C**, scoped narrowly: create a dedicated one-task experiment based on the existing `AdaptiveOffloadingFog` topology, rather than modifying upstream generic classes first. Model one offloadable computation as tier-specific target modules deployed on the Local, Edge, and Cloud devices through the existing module-placement mechanism. A pre-decision adapter chooses the target-module name based on the Python action; the selected tuple then travels through normal `FogDevice` link queues and cloudlet execution. The design must preserve one parent task correlation id through any result tuple.

This is scientifically more defensible than A because the policy can choose different tiers per task, and safer than directly altering generic `FogDevice` routing because the classic code does not honor `destinationDeviceId`. It does not claim that a module placement itself is an offloading action; the experiment must explicitly record the selected tier, target module, and actual executing device.

## Safe extension points to inspect/extend later

1. `AdaptiveOffloadingFog.main` / new dedicated experiment class: define topology, application, and run lifecycle without modifying upstream base classes.
2. A purpose-built sensor/task emitter derived from the behavior in `Sensor.transmit`: construct the task, create the Python observation before first `TUPLE_ARRIVAL`, select the tier-specific destination module, and retain a task record.
3. `Application.getResultantTuples`: inspect whether the task correlation id is copied along all chosen result paths.
4. A dedicated completion observer placed at the terminal application/actuator event, or narrowly instrumented completion path in the experiment—not `Controller.processTupleFinished`, which is empty in this classic flow.
5. `FogDevice.checkCloudletCompletion` only if a narrow, reviewed per-tuple completion hook is unavoidable. It is a generic upstream engine class and therefore higher risk.

## Why not direct `destinationDeviceId`

It is a field on `Tuple`, but classic `FogDevice` bases its behavior on hosted `destModuleName` and UP/DOWN direction. The microservice branch (`MicroserviceFogDevice`) does route using `destinationDeviceId`, but that is a different device model than the one instantiated by DCNS/Adaptive. Moving to that branch would be a larger architecture change and needs a separate compatibility audit.

## Minimum Java files likely to change for the recommended design

- `src/org/fog/test/perfeval/AdaptiveOffloadingFog.java` or a new dedicated experiment class beside it.
- One new task-emitter/adapter class in the experiment package.
- Potentially one small explicit task-record/completion-observer class.
- The Python launcher/JSONL adapter class.

Do not modify `ModulePlacementMapping`, `ModulePlacementEdgewards`, `Controller`, or generic `FogDevice` for the first implementation unless the dedicated experiment proves an unavoidable, reviewed hook is missing.
