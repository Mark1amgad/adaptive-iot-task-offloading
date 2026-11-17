# Risk Calibration V1 — Acceptance Report

**Date:** 2026-11-17  
**Branch:** `mark/risk-calibration-v1`  
**Scope:** Python risk calibration, V2 protocol, Java/iFogSim partial-execution integration.

## Results

### Python

- Main suite: **247 passed**, 1 test deselected, 1 third-party deprecation warning.
- The deselected subprocess smoke test was run separately: **1 passed**.
- Combined coverage: **248/248 tests passed**.
- Risk-focused and V2-server subset: **29 passed**.

The signed-residual persistence regression is covered: residuals may be negative when execution is faster than predicted, and persisted calibration state now reloads those values correctly.

### Java and iFogSim

- Java action-contract checks: **80 passed** across the 9 action execution plans.
- All **9 V2 actions** completed in the iFogSim acceptance run (2 tasks per action; 18 baseline tasks).
- Partial actions exercised real local/remote branches and merge execution.
- Risk-filtered training completed **30 tasks**: **16 partial** and **14 full** placements.
- The training run saved the model and residual-calibration sidecar.
- The injected dropped-branch case failed closed as intended and left **0 orphaned tasks**.
- The acceptance validator returned **PASS**.

The training acceptance workload uses a 15,000 ms inter-arrival interval and 20,000 ms deadline so the run contains feasible decisions as well as realistic resource contention. This is an integration workload, not a benchmark workload.

## Important implementation semantics

- A risk-forced fallback intentionally suppresses the learner update; it must still update residual calibration when a valid measured outcome and prediction are available.
- The acceptance validator now checks learner updates and residual-calibration updates separately instead of treating every non-update as a failure.
- Fog-device utilization is computed from active Cloudlets and their currently allocated MIPS. The legacy `lastUtilization` value represents VM-reserved/allocated MIPS and can report full utilization while no task Cloudlet is running; using it directly made the feasibility filter incorrectly treat Local and Edge as saturated.

## Interpretation and limitations

These results establish software and simulator integration acceptance only. They do **not** establish that the proposed policy outperforms Local, Edge, Cloud, or other baselines. No research-performance claim should be made from this smoke/acceptance run.

The isolated subprocess smoke test passed, but was run separately because running it in the same full-suite invocation stalled in this Windows environment. All 248 tests passed across the two completed invocations.

The comparative experiment matrix, repeated A→B→A shift evaluation, statistical analysis, and validated energy measurements remain separate research tasks.
