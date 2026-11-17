# Mixed Full/Partial Multi-Task Acceptance Record

Date: 2026-11-15  
Status: simulator acceptance passed; not connected to the RL learner.

## Purpose

Verify that one run-level simulator coordinator can manage both:
- full-placement tasks that execute on exactly one of Local / Edge / Cloud and terminalize directly; and
- partial tasks that execute Local and Edge branches, wait for their own two-result barrier, execute one merge Cloudlet, and terminalize after merge.

This closes the simulator-lifecycle integration gap between the earlier full-placement integration and the separate partial-feasibility fixture. It does not yet connect the partial fixture to the Python RL protocol.

## Deterministic six-task pattern

The fixture generates six overlapping tasks in one CloudSim run:

| Task | Mode | Full action / partial branches | Terminal behavior |
|---|---|---|---|
| 001 | Full | Local | One Local result; direct terminal |
| 002 | Partial | Local + Edge (fixed 40/60) | Two results → task-local barrier → merge Cloudlet → terminal |
| 003 | Full | Edge | One Edge result; direct terminal |
| 004 | Partial | Local + Edge (fixed 40/60) | Two results → task-local barrier → merge Cloudlet → terminal |
| 005 | Full | Cloud | One Cloud result; direct terminal |
| 006 | Partial | Local + Edge (fixed 40/60) | Two results → task-local barrier → merge Cloudlet → terminal |

All six tasks were created at simulation times 5–10 ms, before the first task terminal. Full and partial tasks therefore coexisted in the same simulation run and shared the same completion coordinator.

## Verified invariants

- Exactly six unique task IDs and six terminal events.
- Three full tasks: one each on Local, Edge, and Cloud; each has exactly one registered/executed branch and no merge lifecycle.
- Three partial tasks: each has exactly one Local branch and one Edge branch; both results arrive before one merge barrier.
- Each partial task owns a unique merge tuple and one real CloudSim merge Cloudlet on Local.
- Full tasks terminalize directly; partial tasks terminalize only after their merge result.
- One actualTupleId-to-(TaskRecord, Branch) registry handles all full, partial, and merge tuples.
- All 12 tuple IDs are unique: 3 full + (3 partial × 3 branch/merge tuples).
- No cross-task tuple attribution was detected.
- All six tasks completed under one coordinator; no early termination after a full task or after one partial branch.
- A repeated run produced byte-identical mixed_trace.csv and mixed_summary.csv.

## Observed task-level metrics

| Task | Mode | Route | E2E latency (simulated ms) | Counted transfer bytes | Transfer rows |
|---|---|---|---:|---:|---:|
| 001 | Full | Local | 36.010 | 0 | 0 |
| 002 | Partial | Local + Edge | 98.200 | 7,800 | 2 |
| 003 | Full | Edge | 109.276 | 12,600 | 2 |
| 004 | Partial | Local + Edge | 120.606 | 7,800 | 2 |
| 005 | Full | Cloud | 95.743 | 26,000 | 4 |
| 006 | Partial | Local + Edge | 118.606 | 7,800 | 2 |

These are integration-fixture observations under the current one-Local/one-Edge/one-Cloud topology. They are not calibrated service-time measurements and must not be used to rank the tiers or claim policy superiority.

## Validator and negative tests

The mixed validator checks task-mode-specific lifecycle, expected executor/module for each full route, branch and merge tuple correlation, per-task partition conservation, barrier order, merge contract, unique tuple ownership, and one terminal per task.

The combined standard-library test suite passed 10 tests:
- five partial-fixture validator tests; and
- five mixed full/partial validator tests, including rejection of a wrong full-task terminal tuple, cross-task tuple reuse, premature partial merge barrier, and a merge lifecycle attached to a full task.

Command: python -m unittest discover -s tests -v

## Reproduction

Command: run_mixed_full_partial.ps1 -Tasks 6 -InterArrivalMs 1 -RunRoot audit_output/mixed_full_partial_acceptance_20261115_183000

Retained primary and repeat traces, summaries, and repeatability record:

audit_output/mixed_full_partial_acceptance_20261115_183000/

## Limitations

- The full/partial pattern is deterministic test scheduling, not an RL-selected decision.
- The partial split remains fixed at 40% Local / 60% Edge; it does not match the workload spec's 25/50/75 remote-fraction action candidates.
- No Local+Cloud partial task is included in this fixture.
- Partition/merge data construction, serialization, and semantic reconciliation remain synthetic; the merge Cloudlet receives a synthetic aggregate input.
- The fixture does not yet consume workload-generator task records or their splittability, partition_model_id, partition_overhead_ms, and merge_overhead_ms fields.
- The Python agent remains Local / Edge / Cloud only. No protocol, action schema, Q-table, or model changes were made.
- Failure/cancellation/horizon semantics, per-task energy, target 4 IoT / 2 Edge / 1 Cloud topology, calibrated workloads, and benchmark claims remain unverified.

This acceptance proves shared run-level simulator lifecycle handling for mixed full and Local+Edge partial tasks in the tested fixture only.
