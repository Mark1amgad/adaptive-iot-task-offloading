# Adaptive AI-Based Task Offloading

## Supervisor Deliverable Package

This package presents the current intermediate Java/iFogSim and Python integration prototype for selecting Local, Edge, or Cloud execution for one simulated IoT task. It is a working integration demonstration with preliminary measurements, not a final research system or statistically validated RL evaluation.

## Current Status

Implemented and evidenced:

- Java/iFogSim task creation and measurement adapter.
- Persistent Python JSONL agent integration.
- Real Local, Edge, and Cloud action-dependent execution.
- One-task RL training run with outcome update, model save, and clean shutdown.
- Deterministic Local, Edge, and Cloud baseline runs.
- JSONL validation, timeout/malformed fallback checks, and a deadline-miss check.
- Reproducible isolated PowerShell runner and policy comparison summary.

Measured values from the preserved accepted run:

| Case | Route | Latency | Counted task bytes | Deadline |
| --- | --- | ---: | ---: | --- |
| RL train | Local | 3.51 ms | 0 | Met |
| Local baseline | Local | 3.51 ms | 0 | Met |
| Edge baseline | Edge | 7.302857 ms | 14,000 | Met |
| Cloud baseline | Cloud | 97.685804 ms | 28,000 | Met |

These are single-run integration measurements. They do not prove RL superiority.

## Folder Map

- `01_Project_Overview/` problem, objective, architecture, and implementation status.
- `02_Methodology/` actual lifecycle, parameters, and measurement definitions.
- `03_Source_Code/` copied experiment-owned source and utilities.
- `04_Results/` copied traces, exit codes, comparison, and analysis.
- `05_References/` verified project references and source provenance.
- `06_Reproduction/` Windows reproduction commands and runner.
- `07_Limitations_and_Next_Steps/` unsupported behavior and planned improvements.
- `08_RL_Model/` copied RL implementation, configuration, schemas, tests, and the accepted saved model state.
- `09_Datasets/` original dataset tree, source description, and reproducible statistics.
- `10_iFogSim_Simulation/` experiment source, accepted logs, topology description, and diagram.

## Reproduction

From the repository root:

```powershell
& .\\deliverables\\06_Reproduction\\run_acceptance.ps1
```

The runner uses the external iFogSim directory and local JDK/Python installations documented in `06_Reproduction/`. It builds into a fresh isolated run directory. The focused fallback/deadline command is:

```powershell
& .\\deliverables\\06_Reproduction\\run_acceptance.ps1 -RunErrorTests
```

## Suggested Reading Order

1. `01_Project_Overview/Overview.md`
2. `02_Methodology/Methodology.md`
3. `04_Results/Results_Analysis.md`
4. `03_Source_Code/Source_Code_Notes.md`
5. `06_Reproduction/Reproduction.md`
6. `07_Limitations_and_Next_Steps/Limitations.md`
7. `05_References/References.md`

## Artifact Links

- RL implementation and saved state: [Model_Documentation.md](08_RL_Model/Model_Documentation.md), [src/rl_model](08_RL_Model/src/rl_model/), and [python_model.json](08_RL_Model/Saved_Models/python_model.json).
- Dataset files and statistics: [Dataset_Description.md](09_Datasets/Dataset_Description.md), [Original](09_Datasets/Original/), and [Dataset_Statistics](09_Datasets/Dataset_Statistics/).
- Simulation source and accepted logs: [Simulation_Source](10_iFogSim_Simulation/Simulation_Source/), [Simulation_Logs](10_iFogSim_Simulation/Simulation_Logs/), and [Simulation_Notes.md](10_iFogSim_Simulation/Simulation_Source/Simulation_Notes.md).
- Implemented topology: [Topology_Description.md](10_iFogSim_Simulation/Topology/Topology_Description.md), [topology.svg](10_iFogSim_Simulation/Topology/topology.svg), and [topology.png](10_iFogSim_Simulation/Topology/topology.png).
- Existing results and traces: [04_Results](04_Results/).

## Important Scope Boundary

The experiment is deliberately one-task per run. Native task failure, multi-task operation, per-task energy, and statistically independent policy evaluation remain future work. The original RL model, protocol, teammate files, and external iFogSim source are not included or modified by this package.
