# Protocol v2 — Partial Execution Plan

**Date:** 2026-11-15  
**Status:** IMPLEMENTED AND ACCEPTED — see `V2_PARTIAL_EXECUTION_ACCEPTANCE.md`.

## Action mapping

| Action | Execution | Merge |
|---|---|---|
| LOCAL | Full Local | No |
| EDGE_FULL | Full Edge | No |
| CLOUD_FULL | Full Cloud | No |
| EDGE_PARTIAL_25 / 50 / 75 | Local + Edge | Yes |
| CLOUD_PARTIAL_25 / 50 / 75 | Local + Cloud | Yes |

The suffix is the remote compute fraction. The Local fraction is its complement.

## Execution-plan contract

`OffloadingActionV2ExecutionPlan` creates branch plans with action-specific module names, branch identities, tier labels, MI, input bytes, output bytes, and merge requirements. The remote share is rounded once; Local receives the exact remainder so task-level workload is conserved.

## Simulator execution

`RlOffloadingV2PartialIntegrationExperiment.java` now:
1. Obtains each action through the live Python protocol-v2 service.
2. Validates protocol version, task correlation, action ID/name, tier, fractions, and feasibility mask.
3. Applies the configured partition delay before emitting partial branches.
4. Executes the Local branch with exactly one remote tier (Edge or Cloud).
5. Correlates results by unique tuple IDs and task ID.
6. Opens a per-task barrier only after both branch results arrive.
7. Applies merge overhead and executes a real merge Cloudlet on Local.
8. Sends one terminal outcome with the original compound action ID.
9. Uses a watchdog to report incomplete tasks as failed, never as successful.

Ratio-specific workers are registered for all 25/50/75 Local, Edge, and Cloud shares. Full-placement workers remain distinct.

## Verified acceptance

The runner executes all nine actions in separate JVM/Python sessions, with two overlapping tasks per action:
- 9/9 action cases passed.
- 18 task lifecycles reconciled.
- 12 partial tasks and 12 merge Cloudlets completed.
- Exact MI/input/output conservation passed.
- Every merge began after both branch results and after the configured merge delay.
- All outcomes were acknowledged; zero orphaned tasks.
- A separate 30-task learned-policy run executed 17 partial and 13 full tasks, applied 30 measured-outcome updates, saved the v2 model, and shut down with zero orphaned tasks.
- Python suite: 235 passed.
- Java action-plan contract: 56 checks passed.

A deliberate dropped-Edge-branch test verified fail-closed behavior: no merge or success outcome was fabricated; Python acknowledged a failed outcome, shut down with zero orphaned tasks, and Java returned a non-zero acceptance exit.

## Important research boundary

The 3 ms partition and 2 ms merge overheads are provisional experiment parameters, not calibrated facts. Exact-action baselines provide deterministic action coverage but do not prove learned-policy convergence or RL superiority. The current topology remains Local → Edge → Cloud. Energy is not measured. This milestone establishes the execution path, not the performance result.

See `V2_PARTIAL_EXECUTION_ACCEPTANCE.md` for commands, trace evidence, and limitations.
