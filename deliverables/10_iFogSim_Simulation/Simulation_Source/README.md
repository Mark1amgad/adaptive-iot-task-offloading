# One-Task iFogSim Integration Source

This folder contains the experiment-owned Java integration source, runner, and validation utility.

- `org/fog/test/perfeval/RlOffloadingIntegrationExperiment.java` — Java integration experiment.
- `run_acceptance.ps1` — isolated build and acceptance runner.
- `validate_integration.py` — checks task correlation, routing, transfer accounting, outcomes, fallback, deadline, and cleanup.
- `FINAL_STATUS.md` — what the retained acceptance evidence verifies and what remains unverified.
- `MEASUREMENT_CONTRACT_V1.md` and `ONE_TASK_ACCEPTANCE_TEST.md` — measurement and acceptance definitions.

The implementation is a one-task integration prototype. The retained traces are not a multi-task benchmark and do not establish policy superiority. The original iFogSim source remains an external dependency and is not modified by this package.
