# iFogSim Integration Source

This folder contains experiment-owned Java integrations, isolated runners, and trace validators.

## Main integration
- `org/fog/test/perfeval/RlOffloadingIntegrationExperiment.java` — multi-task full-placement integration with the Python RL service.
- `run_acceptance.ps1` — isolated full-placement acceptance runner.
- `validate_integration.py` — full-placement JSONL trace validator.

## Partial-offloading feasibility
- `org/fog/test/perfeval/MultiTaskPartialOffloadingSpike.java` — multi-task Local+Edge split fixture with per-task branch barriers and real CloudSim merge Cloudlets.
- `run_multi_task_partial.ps1` — builds in an isolated output directory, runs primary and repeat simulations, validates both, and compares trace/summary byte-for-byte.
- `validate_multi_task_partial.py` — validates task/branch/merge correlation, conservation, barrier order, and transfer attribution.
- `tests/test_multi_task_partial_validator.py` — negative and positive validator tests using portable CSV fixtures in `tests/fixtures/multi_task_partial_4/`.
- `MULTI_TASK_PARTIAL_ACCEPTANCE.md` — scope, acceptance evidence, metrics, and limitations.

## Scope warning
The Python RL action schema remains Local / Edge / Cloud. The partial fixture is not connected to the learner and uses a fixed 40/60 Local/Edge split. It does not model actual merge-data construction or establish comparative performance.

The external iFogSim source remains a dependency. These experiments do not modify iFogSim core and compile into fresh `audit_output` directories, not the external simulator's tracked `out/production`.
