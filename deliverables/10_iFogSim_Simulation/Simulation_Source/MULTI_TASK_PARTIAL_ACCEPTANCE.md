# Multi-Task Partial Offloading — Acceptance Record

## Scope

This is a simulator-owned feasibility fixture for multiple concurrent partial tasks. It deliberately does not modify the accepted Local / Edge / Cloud RL action schema. Each synthetic task is split into a Local branch and an Edge branch, and each task owns its own branch registry, two-result barrier, merge tuple, and terminal state.

The merge is a real CloudSim Cloudlet submitted to the Local `merge_worker` module. The branch coordinator is shared, but correlation is by `actualTupleId -> (TaskRecord, Branch)`; no global "current task" is used.

## Implementation

- New experiment source: `org/fog/test/perfeval/MultiTaskPartialOffloadingSpike.java`
- Runner: `run_multi_task_partial.ps1`
- Trace validator: `validate_multi_task_partial.py`
- Validator negative tests: `tests/test_multi_task_partial_validator.py` with portable CSV fixtures under `tests/fixtures/multi_task_partial_4/`
- Retained output roots:
  - `audit_output/multi_task_partial_release_20261115_170000/` — final 4-task run plus exact repeat
  - `audit_output/multi_task_partial_verified_20261115_163000/` — earlier 4-task run plus exact repeat
  - `audit_output/multi_task_partial_8tasks_20261115_164000/` — 8 tasks plus exact repeat
  - `audit_output/partial_single_regression_20261115_165000/` — one-task regression plus exact repeat

## Verified runs

| Run | Tasks | Inter-arrival | Split branches | Merge Cloudlets | Registered tuple IDs | Validation |
|---|---:|---:|---:|---:|---:|---|
| Single-task regression | 1 | 1.0 ms | 2 | 1 | 3 | PASS |
| Multi-task baseline | 4 | 1.0 ms | 8 | 4 | 12 | PASS |
| Higher concurrency | 8 | 0.5 ms | 16 | 8 | 24 | PASS |

All tasks in each run were created before the first task-level terminal event. For every task, exactly one Local branch and one Edge branch were created and executed; both branch results arrived before exactly one merge barrier; exactly one merge tuple was created and executed; and exactly one task completion was recorded.

The validator verifies:
- unique task IDs and unique branch/merge tuple IDs;
- tuple-to-task and tuple-to-branch correlation through execution, transfer, branch result, merge execution, and terminal event;
- Local/Edge MI, input-byte, and output-byte conservation (10,000 MI / 12,000 input bytes / 1,000 output bytes per task);
- branch results cannot precede their execution admission;
- merge barrier cannot precede the later of the two branch results;
- merge Cloudlet contract is 1,200 MI, 1,000 input bytes, and 100 output bytes;
- merge completion cannot precede merge execution admission;
- the fixture's two counted parent-child transfers are correctly attributed to the Edge branch: 7,200 bytes Local→Edge and 600 bytes Edge→Local;
- no unknown or cross-task tuple ID appears in the trace.

## Four-task observed metrics

| Task | Created (ms) | Local result (ms) | Edge result (ms) | Merge result (ms) | E2E latency (ms) | Branch skew (ms) |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 5.0 | 19.010 | 106.219 | 117.229 | 112.229 | 87.209 |
| 2 | 6.0 | 29.010 | 106.279 | 117.229 | 111.229 | 77.269 |
| 3 | 7.0 | 29.010 | 116.219 | 128.489 | 121.489 | 87.209 |
| 4 | 8.0 | 29.010 | 116.279 | 128.489 | 120.489 | 87.269 |

Each task has 7,800 counted link bytes over two parent-child hops in this fixture. These values are simulation-fixture observations, not calibrated benchmark results.

## Eight-task observed metrics

The eight-task run also passed. E2E latencies were 117.840, 117.340, 133.140, 132.640, 132.140, 131.640, 131.140, and 130.640 simulated ms for tasks 1–8 respectively. Each task retained its own 7,800-byte / two-hop transfer attribution and unique Local, Edge, and Merge tuple IDs.

## Determinism

For the 1-, 4-, and 8-task test configurations, the primary and repeat runs passed the validator. For the 4- and 8-task runner executions, both `partial_trace.csv` and `partial_summary.csv` were byte-identical across repeated runs. The one-task regression was also repeated and its output matched.

## Validator negative tests

Standard-library `unittest` suite: **5 tests passed** (using committed, portable CSV fixtures):
1. valid four-task fixture accepted;
2. duplicate branch result rejected;
3. cross-task tuple correlation rejected;
4. merge barrier placed before the second branch result rejected;
5. transfer attributed to an unknown/wrong branch tuple rejected.

Command:

```powershell
python -m unittest discover -s tests -p 'test_multi_task_partial_validator.py' -v
```

## Limits — do not overclaim

- The split is fixed at 40% Local / 60% Edge and assumes MI/input/output can be divided proportionally. This is a controlled simulator fixture, not a general task partitioner.
- The coordinator represents the combined branch output as one 1,000-byte merge input. The actual data copy, serialization, semantic reconciliation, and merge algorithm are not modeled.
- Branch-result endpoint and merge worker are co-located on Local; no additional transfer is counted for handing the aggregate merge input to the merge module.
- Merge result arrival includes CloudSim scheduling and actuator endpoint delay; it is not a pure CPU execution-time measure.
- Local+Cloud partial execution is not implemented.
- The RL agent still selects only full-placement Local / Edge / Cloud actions. It does not choose Partial.
- No energy attribution, task failure/cancellation policy, calibrated workload, paired benchmark campaign, or comparative performance claim is established.
- The tested topology remains one Local, one Edge, and one Cloud device, not the target 4 IoT / 2 Edge / 1 Cloud topology.

This acceptance record proves multi-task lifecycle feasibility for the fixed Local+Edge partial fixture only.
