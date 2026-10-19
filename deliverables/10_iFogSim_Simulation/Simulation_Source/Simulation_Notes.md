# Simulation Artifacts

## Exact Experiment Source

The accepted run was produced by the copied experiment-owned source:

`org/fog/test/perfeval/RlOffloadingIntegrationExperiment.java`

It is compiled against the external iFogSim source tree at `C:\Users\DELL\OneDrive\Desktop\Research\iFogSim`, using that tree's `src` and `jars` directories. The experiment source is not the generic upstream `FogDevice` implementation and the external tree was not copied or modified here.

## Accepted Logs

`Simulation_Logs/` contains the accepted Java trace, Python run/event JSONL logs, and recorded exit codes from the RL training case. The full Local/Edge/Cloud evidence is already organized under `deliverables/04_Results/`.

## Reproduction

From repository root, the copied runner is:

```powershell
& .\deliverables\06_Reproduction\run_acceptance.ps1
```

It requires the external iFogSim directory, JDK 25, Python, and the teammate-owned RL service documented in `deliverables/06_Reproduction/Reproduction.md`. This package does not claim to be self-contained.