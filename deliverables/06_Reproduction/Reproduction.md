# Reproduction

## Requirements

The retained runners are Windows PowerShell scripts and use:

- JDK 25 (the original workstation used Eclipse Adoptium JDK 25.0.3).
- External iFogSim source at sibling folder `Research/iFogSim`.
- Python compatible with the model package under [`08_RL_Model/`](../08_RL_Model/).
- The model package and dependencies preserved in this repository.

Paths can be overridden in the runner when the local installation differs.

## Run the one-task integration acceptance suite

From the repository root:

```powershell
& .\deliverables\10_iFogSim_Simulation\Simulation_Source\run_acceptance.ps1
```

The runner compiles the experiment-owned Java source into an isolated output directory, runs the retained train/baseline cases, and validates the resulting JSONL traces.

To include the response-boundary fallback and deadline cases:

```powershell
& .\deliverables\10_iFogSim_Simulation\Simulation_Source\run_acceptance.ps1 -RunErrorTests
```

The timeout/malformed fallback tests inject errors before an observation is sent. They do not demonstrate a true mid-flight timeout after Python has accepted a pending task.

## Validate or summarize the retained evidence without rerunning Java

```powershell
python .\deliverables\10_iFogSim_Simulation\Simulation_Source\validate_integration.py --root .\audit_output\integration_prototype\runs\acceptance_20261013_220748
python .\deliverables\04_Results\compare_policies.py --root .\audit_output\integration_prototype\runs\acceptance_20261013_220748
```

The retained results are one-task integration measurements, not a multi-task benchmark or evidence of adaptive-policy superiority. The package depends on the external iFogSim tree and a local JDK/Python environment; it is not fully self-contained.
