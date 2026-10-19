# Reproduction

## Prerequisites

Run from the repository root on Windows PowerShell. The existing runner expects:

- JDK 25 at `C:\Program Files\Eclipse Adoptium\jdk-25.0.3.9-hotspot`.
- External iFogSim at `C:\Users\DELL\OneDrive\Desktop\Research\iFogSim`.
- Python executable at `C:\Users\DELL\AppData\Roaming\uv\python\cpython-3.15.0b1-windows-x86_64-none\python.exe`.
- The teammate-owned RL service at `team-work\Ayoub\rl_model\rl_model`.

Override runner parameters if the local paths differ.

## Standard Demonstration

```powershell
& .\deliverables\06_Reproduction\run_acceptance.ps1
```

This compiles the copied experiment source into a fresh isolated output directory, runs one real Python train case and deterministic Local/Edge/Cloud baseline cases, validates the generated JSONL, and writes a policy comparison. It refuses to reuse an existing output directory.

## Focused Error and Deadline Cases

```powershell
& .\deliverables\06_Reproduction\run_acceptance.ps1 -RunErrorTests
```

This also exercises the experiment-owned pre-send timeout and malformed-response fallback boundary and a zero-deadline completed-task case. These fallback tests are not mid-flight Python timeouts: no observation is sent, so no Python decision becomes pending.

## Evidence-Only Validation

The copied utilities can validate or summarize an existing run without running Java:

```powershell
& python .\deliverables\03_Source_Code\validate_integration.py --root .\audit_output\integration_prototype\runs\acceptance_20261013_220748
& python .\deliverables\03_Source_Code\compare_policies.py --root .\audit_output\integration_prototype\runs\acceptance_20261013_220748
```

The deliverables package is not self-contained. It depends on the original repository, external iFogSim tree, JDK, Python environment, and teammate-owned RL service.
