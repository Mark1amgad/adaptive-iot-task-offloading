# Topology Presentation Validation Report

## Build and Run Evidence

Source:

`C:\Users\DELL\OneDrive\Desktop\Research\iFogSim\src\org\fog\test\perfeval\TopologyPresentation.java`

Isolated class output:

`audit_output/topology-work/presentation-classes/`

Captured console output:

`audit_output/topology-work/presentation-run/console_output.txt`

Observed build exit code: `0`.

Observed demonstration run exit code: `0`.

The GUI-enabled source also compiled successfully with the existing iFogSim GUI classes (`org.fog.gui.core.Bridge`, `Graph`, and `GraphView`) using the same isolated classpath. GUI build exit code: `0`.

The run initializes and stops CloudSim after constructing and reporting the topology. It does not start the RL Python service and is not a rerun of the accepted integration experiment.

## Runtime Validation

The presentation output was compared with:

`audit_output/topology-work/runtime/TOPOLOGY_INVENTORY.json`

| Property | Presentation output | Runtime inventory | Result |
| --- | --- | --- | --- |
| Device count | cloud, edge, local | 3 devices | PASS |
| Runtime IDs | cloud 2, edge 3, local 4 | cloud 2, edge 3, local 4 | PASS |
| Parent hierarchy | cloud root, edge -> cloud, local -> edge | same | PASS |
| Cloud resources | 44,800 MIPS; 40,000 RAM; 1 PE; 100,000/100,000 BW | same | PASS |
| Edge resources | 2,800 MIPS; 4,000 RAM; 1 PE; 10,000/10,000 BW | same | PASS |
| Local resources | 1,000 MIPS; 2,000 RAM; 1 PE; 10,000/10,000 BW | same | PASS |
| Host bandwidth | 10,000 for all devices | 10,000 for all devices | PASS |
| Effective links | edge-cloud 45 ms; local-edge 2 ms | same Controller-registered values | PASS |
| Power values | cloud 1648/1332; edge 107.339/83.4333; local 87.53/82.44 | same | PASS |
| Scheduler | `StreamOperatorScheduler` | same | PASS |
| Modules | matching `<tier>_executor` placement | same | PASS |

Runtime host storage is printed as `990000` for all three devices. The audited factory constructor passes `1000000`; this inherited runtime discrepancy is explicitly reported and is not treated as a corrected or fabricated value.

## Scope and Limitations

- This is a standalone topology explanation program, not the RL integration experiment.
- It does not start Python or change the JSONL protocol.
- It does not run tasks or produce latency/bandwidth research measurements.
- It uses no external dependencies beyond the existing iFogSim/JDK classpath.
- It uses the existing iFogSim GUI classes rather than adding external dependencies. The GUI-compatible JSON is generated from runtime devices and Controller-populated link maps, then loaded by `Bridge.jsonToGraph(...)` into `GraphView`.
- The presentation GUI is explanatory only; it does not execute an RL task or claim to be the accepted integration run.
