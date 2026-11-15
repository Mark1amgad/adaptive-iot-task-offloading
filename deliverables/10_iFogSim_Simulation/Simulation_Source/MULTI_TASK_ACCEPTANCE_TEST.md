# Multi-task acceptance test — Java / Python / iFogSim

## Purpose and scope

This acceptance suite verifies the first multi-task integration milestone: several full-placement tasks may remain in flight in one iFogSim run while one persistent Python RL service retains and reconciles each task by `task_id`.

Supported policy actions remain **Local / Edge / Cloud**. Partial offloading and merge barriers are not part of this milestone. The suite is an integration/lifecycle test, not a performance benchmark or evidence of policy superiority.

## Implementation invariants

- One immutable `TaskRecord` per generated task, indexed by `task_id`.
- One unique `actualTupleId -> TaskRecord` mapping per execution tuple.
- Transfer and execution observations resolve the owning task from the tuple ID; no global current-task field is used.
- Duplicate task IDs, tuple IDs, execution admissions, and terminal events fail explicitly.
- Each accepted decision receives one matching outcome acknowledgement.
- Training mode saves once, after all task outcomes have been acknowledged.
- Python receives exactly one shutdown request after the configured task set is reconciled.
- The run passes only when all configured tasks are terminal, all expected outcomes are acknowledged, Python reports `orphaned_tasks=0`, and the process exits with code 0.

## Acceptance suite

`run_acceptance.ps1` builds into a fresh directory under `audit_output`; it does not compile into `iFogSim/out/production`.

| Case | Mode | Tasks | Purpose |
|---|---|---:|---|
| `one_task_train_pass` | train | 1 | Single-task learning regression |
| `regression_local` | baseline Local | 1 | Local route regression |
| `regression_edge` | baseline Edge | 1 | Edge route regression |
| `regression_cloud` | baseline Cloud | 1 | Cloud route regression |
| `multi_task_overlap` | baseline Edge | 4 | Four overlapping tasks, per-task tuple/transfer accounting |
| `multi_task_train` | train | 4 | Multiple pending decisions and outcomes in one training process |
| `multi_task_train_repeat` | train | 4 | Fixed-seed logical-summary repeatability |
| `fallback_timeout` | baseline + injected timeout | 1 | Adapter-boundary fallback regression |
| `fallback_malformed` | baseline + injected malformed reply | 1 | Adapter-boundary fallback regression |
| `deadline_miss` | baseline Local, deadline 0 | 1 | Truthful deadline-miss regression |

## Observed mixed-action multi-task run

In the retained four-task training run, the agent selected different destinations within the same simulation:

| Task | Action | Actual executor | Latency (simulated ms) | Counted transfer bytes | Transfer rows |
|---|---|---|---:|---:|---:|
| 1 | Local | local | 5.51 | 0 | 0 |
| 2 | Edge | edge | 7.302857 | 14,000 | 2 |
| 3 | Local | local | 13.51 | 0 | 0 |
| 4 | Cloud | cloud | 97.685804 | 28,000 | 4 |

All four tasks were created at simulation times 5, 6, 7, and 8 ms before the first terminal event. Their results were reconciled independently. The Python service received four outcomes, acknowledged all four, saved the training model once, then shut down with zero orphaned tasks.

The fixed-seed repeat produced an identical logical summary for each task: selected action, executor/module, execution-admission time, latency, counted bytes, transfer count, and deadline result.

These values are retained integration evidence only. They are not calibrated benchmark results and must not be used to claim that one policy or tier is superior.

## Retained run

Final full-suite output:

`audit_output/multi_task_final_acceptance_20261115_151500/`

The `exit_codes.json` file records exit code 0 for all ten Java cases. The JSONL traces, Python service logs, model artifact, and validator output are retained beside it.

## Explicitly not verified

- Learner-selected partial actions, multiple branches per task, merge barriers, and multi-task partial merge correlation.
- Failure events, cancellation, or unresolved-at-horizon semantics.
- The target 4 IoT / 2 Edge / 1 Cloud topology; this integration still instantiates one Local, one Edge, and one Cloud device.
- Per-task energy attribution; `energy_joules` remains null.
- Calibrated workload distributions, paired multi-seed benchmarks, statistical comparisons, or policy superiority.

The current pass establishes multi-task full-placement lifecycle correctness for the tested topology and cases only.
