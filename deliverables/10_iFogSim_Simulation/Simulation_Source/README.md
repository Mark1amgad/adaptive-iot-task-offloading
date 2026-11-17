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
- `PARTIAL_ACTION_SPACE_INTEGRATION_AUDIT.md` — current RL/workload action-contract mismatch and versioned migration requirements.

## Mixed full/partial simulator fixture
- `org/fog/test/perfeval/MixedMultiTaskOffloadingSpike.java` — six-task run with full Local/Edge/Cloud tasks and partial Local+Edge tasks under one coordinator.
- `run_mixed_full_partial.ps1` — isolated build, primary/repeat simulations, validation, and byte-identity comparison.
- `validate_mixed_full_partial.py` — validates mode-specific lifecycle and tuple ownership.
- `tests/test_mixed_full_partial_validator.py` — five positive/negative mixed-lifecycle validator tests using portable CSV fixtures.
- `MIXED_FULL_PARTIAL_ACCEPTANCE.md` — acceptance evidence and limitations.

## Scope warning
The Python RL action schema remains Local / Edge / Cloud. The partial fixture is not connected to the learner and uses a fixed 40/60 Local/Edge split. It does not model actual merge-data construction or establish comparative performance.

The external iFogSim source remains a dependency. These experiments do not modify iFogSim core and compile into fresh `audit_output` directories, not the external simulator's tracked `out/production`.


## V2 risk-calibrated feasibility filter

The V2 partial-integration runner now accepts --risk-filter; this adds a pre-decision completion-time context to observations and records per-action estimates, residual margin, calibration source/sample count, feasible mask, and fallback state in the decision trace. Training persists the residual state beside python_model.json as python_model.json.risk.json. For frozen evaluation, pass --risk-state-in and use the same sidecar for every compared policy. run_v2_policy_comparison.ps1 requires and shares that sidecar across the paired Local/Edge/Cloud/Random/RL runs.

run_v2_workload_smoke.ps1 and the learned-policy phase of run_v2_partial_acceptance.ps1 exercise the filter during training. Exact-action executor acceptance remains unfiltered, so it continues to test the nine concrete paths independently of risk-policy choices.

The current risk context uses explicit but provisional Local/Edge/Cloud MIPS and link profiles, zero queue-wait estimates, directional link profiles taken from FogDevice uplink/downlink capacities, and configured partition/merge overhead. iFogSim's CloudSim clock is in seconds; the runner now converts all protocol/trace timestamps to milliseconds and converts workload/event delays from milliseconds to seconds. It includes merge MI because partial execution creates a real Local merge Cloudlet. These inputs require calibration against the actual topology/traces. The residual quantile is empirical, not a deterministic deadline guarantee; uncalibrated decisions and forced fallbacks must be separately reported. See ../../08_RL_Model/docs/RISK_CALIBRATION_V1.md.
