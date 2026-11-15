# Protocol v2.0 — Full-Placement iFogSim Acceptance

**Date:** 2026-11-15

**Status:** PASS — full-placement vertical slice only

## What was integrated

The new `RlOffloadingV2IntegrationExperiment.java` starts `rl_model.server_v2`, performs a protocol-v2 handshake, sends pre-decision observations, validates Python's compound action response in Java, routes each indivisible task to the selected full-placement module, and reports the measured task outcome back to Python.

The experiment intentionally declares every generated task `INDIVISIBLE`. Therefore its exact feasible mask is:
- `LOCAL` (ID 0)
- `EDGE_FULL` (ID 4)
- `CLOUD_FULL` (ID 8)

The nine-action catalogue is advertised at handshake, but the three partial actions per tier are correctly masked for these indivisible tasks.

## Acceptance command

From `deliverables/10_iFogSim_Simulation/Simulation_Source`:

```powershell
.\run_v2_full_acceptance.ps1
```

The runner compiles the new experiment against the external iFogSim source/jars and executes:
1. 4-task overlapping RL training run
2. 2-task Local fixed baseline
3. 2-task Edge fixed baseline
4. 2-task Cloud fixed baseline

It validates decision/execution correlation, terminal/outcome counts, protocol version, zero orphaned tasks, baseline routing, and the saved model dimensions.

## Verified result

Run output:
`audit_output/v2_full_acceptance_20261115_163210`

| Case | Tasks | Verified routing |
|---|---:|---|
| RL training | 4 | 2 LOCAL, 2 EDGE_FULL |
| Local baseline | 2 | 2 LOCAL |
| Edge baseline | 2 | 2 EDGE_FULL |
| Cloud baseline | 2 | 2 CLOUD_FULL |
| **Total** | **10** | **All task lifecycles reconciled** |

The training model was saved as protocol 2.0 / format 2 with 972 states, nine action columns, and four measured-outcome updates. Python stderr was empty. Every run reported zero orphaned tasks. The expanded Java action-plan contract passed 56 checks.

## Important limitations

This is an integration and lifecycle acceptance test, not a performance benchmark:
- All tasks are indivisible; no partial action was executed in this experiment.
- The training run contains only four tasks and does not demonstrate policy convergence or generalization.
- The current simulator topology is the existing Local → Edge → Cloud chain, not proof of the proposed 4-IoT / 2-Edge / 1-Cloud target topology.
- No claims about RL outperforming fixed baselines are supported by these smoke runs.

## Subsequent milestone (completed)

The partial-action executor has since been implemented and accepted. See `V2_PARTIAL_EXECUTION_ACCEPTANCE.md` for the nine-action run, branch/merge lifecycle checks, overhead modeling, failure-path test, and current limitations.

This document remains the historical full-placement-only acceptance record. Its indivisible-task experiment still does not execute partial actions. The fixed 40/60 Local+Edge feasibility fixture remains separate from the v2 ratio-selected executor.
