# iFogSim Integration Source

This folder contains the experiment-owned Java integration, isolated acceptance runner, and JSONL validator.

- `org/fog/test/perfeval/RlOffloadingIntegrationExperiment.java` — Java integration experiment with run-scoped multi-task lifecycle management.
- `run_acceptance.ps1` — isolated compiler and acceptance runner.
- `validate_integration.py` — validates single-task regressions, multi-task overlap, mixed-tier routing, outcome/shutdown ordering, fixed-seed repeatability, fallback, and deadline behavior.
- `ONE_TASK_ACCEPTANCE_TEST.md` — single-task regression contract.
- `MULTI_TASK_ACCEPTANCE_TEST.md` — current multi-task scope, acceptance matrix, and retained evidence.
- `FINAL_STATUS.md` — verified results and remaining limitations.
- `MEASUREMENT_CONTRACT_V1.md` — measurement definitions.

The implementation supports multiple overlapping **full-placement** tasks with Local / Edge / Cloud actions. It does not yet implement learner-selected partial offloading or multi-task merge barriers.

The original iFogSim source remains an external dependency. The experiment does not modify upstream iFogSim core source and compiles into a fresh isolated output directory, not the external simulator's tracked output folder.
