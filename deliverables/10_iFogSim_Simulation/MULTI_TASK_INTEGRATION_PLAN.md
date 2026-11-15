# Multi-Task Lifecycle Integration Plan

**Status:** phase 1 (multi-task full placement) implemented and simulator-validated on 2026-11-15; partial-action integration and several invariant fault-injection cases remain pending
**Base revision:** `fe91665` on `main`  
**Working branch:** `work/multi-task-lifecycle`  
**Scope:** extend the accepted one-task Java/iFogSim2 + Python integration to multiple overlapping tasks without cross-task attribution, duplicate terminal outcomes, or premature shutdown.

## 1. Why this is the next gate

Before this gate, the accepted integration prototype owned one mutable task record and shut down the Python service after its first task reached the terminal endpoint. The partial-offloading spike separately demonstrates two correlated branches plus a real merge Cloudlet, but it remains a one-task feasibility fixture. Phase 1 now addresses the full-placement lifecycle; multi-task partial merging remains open.

Neither prototype can be made multi-task-safe by adding a task count. The required change is to make task identity and lifecycle explicit at every event boundary.

This work must remain experiment-owned. Do not modify upstream iFogSim/CloudSim core files, and do not compile into the external simulator's tracked output directory.

## 2. Design invariants

The implementation is not accepted unless all of these hold:

1. Every generated task has one unique, immutable `task_id` within a run.
2. Every execution tuple/branch has one unique simulator correlation ID (`actualTupleId`) mapped to exactly one task and one branch record.
3. A merge tuple has its own simulator correlation ID, but its registry mapping points back to the original task.
4. Every transfer, execution, branch result, merge event, and terminal event resolves through the tuple-to-branch index. No event is attributed using a global "current task".
5. A task may become terminal exactly once. A second terminal event is a validation failure, not silently ignored.
6. A partial task may enter merge only after every required branch has one valid result.
7. A full-execution task has one execution branch and no merge stage.
8. The Python process remains alive until every task with an accepted decision has a reconciled outcome, then receives exactly one shutdown request.
9. The simulation must not terminate after the first completed task. It may terminate only when the configured task set is terminal, or when a separately specified simulation horizon is reached and unresolved tasks are explicitly accounted for.
10. Task failures and horizon-unresolved tasks must not be fabricated. Only emit these states when the simulator/experiment has a defined, testable event semantics for them.

## 3. Registry model

Use one run-scoped registry, owned by the experiment, with indexes:

- `tasksById: Map<String, TaskRecord>`
- `branchesByTupleId: Map<Integer, BranchRef>`
- `mergeTupleIdsByTask: Map<String, Integer>` (or derive this from each task record)
- A run-level expected-task count and terminal-task count.

### TaskRecord

One record per original workload task:

- Identity/input: `taskId`, arrival time, original workload fields, deadline, divisibility/profile metadata.
- Decision: requested action, action ID, policy/model version, decision source, whether Python accepted the decision.
- Lifecycle: state, created/dispatched/terminal timestamps, terminal status, terminal-event count.
- Measurements: per-task transfer bytes/count, execution records, end-to-end latency, deadline result.
- Branches: a map keyed by stable branch key (e.g. `LOCAL`, `EDGE`, `CLOUD`, or `MERGE`) to `BranchRecord`.

Do not store a single mutable `executingDevice` on the task as the sole execution record: a partial task has multiple executions. Keep execution data per branch and derive task-level summaries only after the lifecycle is reconciled.

### BranchRecord

One record per simulator execution tuple:

- `taskId`, `branchKey`, branch kind (`EXECUTION` or `MERGE`), `actualTupleId`.
- Destination module/site and assigned MI/input/output work.
- Execution admission/start evidence and result-arrival timestamp.
- Branch transfer bytes/count, execution node/module, and terminal branch state.

The tuple index maps `actualTupleId -> (taskId, branchKey)`. Register the mapping before sending the tuple into iFogSim. Reject duplicate tuple IDs.

### Lifecycle states

Recommended task states:

`CREATED -> DECIDED -> DISPATCHED -> EXECUTING -> [WAITING_FOR_BRANCHES -> MERGING] -> COMPLETED`

For full placement, the path is:

`CREATED -> DECIDED -> DISPATCHED -> EXECUTING -> COMPLETED`

A terminal state is immutable. Failure and unresolved-at-horizon states remain reserved until their event semantics and Python outcome protocol are explicitly validated.

Branch states should be separate from task states: `REGISTERED`, `EXECUTION_OBSERVED`, `RESULT_RECEIVED`. A partial task enters `MERGING` only when all expected execution branches are `RESULT_RECEIVED`.

## 4. Event handling and correlation

### Task arrival and decision

1. The workload emitter receives a pre-generated task row and creates a `TaskRecord`.
2. The task is registered before any decision or tuple emission.
3. Build the observation using only fields available at decision time.
4. Send one observation to the persistent Python adapter, including the stable `task_id`.
5. Validate the response type, task ID, action ID, and legal-action set.
6. Record the decision and dispatch the selected full or partial action.

The Java simulation event loop is single-threaded, but the Python adapter is a synchronous subprocess protocol. Keep request/response serialization explicit; do not assume responses can be matched by arrival order if the protocol is later made asynchronous.

### Dispatch

- For the first multi-task milestone, keep the existing Python action set (Local/Edge/Cloud) and implement multiple concurrent full-placement tasks end-to-end.
- Partial branch dispatch remains a separately tested simulator fixture until the Python action schema, action IDs, legal-action mask, and learner are explicitly extended to partial actions. Do not pretend the current Python agent can select partial actions.
- Once the policy/action contract is extended, a partial action must validate that the task profile is divisible; register all required execution branches and tuple mappings before sending any branch; then dispatch the branches.
- A partial task is limited to Local plus exactly one remote tier. Do not add multi-remote splitting in this milestone.
- Use a task-specific split rule supplied by the workload profile. Do not assume MI and bytes can always be divided by the same ratio.

### Execution and transfers

Instrumented FogDevice hooks must resolve the tuple ID through `branchesByTupleId`. Unknown/unregistered tuple IDs should be handled explicitly: ignore known non-task/control tuples with a documented allowlist, but fail validation for an unknown tuple that purports to belong to a workload task.

All transfer counters are branch-scoped first, then aggregated to the task. This prevents bytes from one task being charged to another while tasks overlap.

### Branch results and merge barrier

On a branch result:

1. Resolve its tuple ID to the owning task and branch.
2. Verify expected endpoint/type and that execution was observed.
3. Reject duplicate branch results.
4. Mark that branch result received.
5. If any required execution branch is still pending, do nothing further.
6. If all required branches are complete, atomically transition that task to `MERGING`, create/register exactly one merge tuple, and submit it to the merge module.

The merge tuple receives a fresh `actualTupleId`; its mapping points to the original task with branch key `MERGE`. The final endpoint resolves that merge tuple back to the original task before terminal completion.

For full placement, the execution result endpoint can terminalize the task directly; it must not accidentally enter the partial merge path.

## 5. Python process and shutdown lifecycle

- Start one Python service per simulation run, not one per task.
- Send one observation per task and one outcome per accepted decision, each correlated by `task_id`.
- Do not send a second observation while a prior request is awaiting a response unless the Python protocol explicitly supports concurrent pending observations.
- On task completion, send its outcome and validate the matching acknowledgement. Do not save/shutdown after the first task.
- After the expected task set is terminal and all accepted decisions have acknowledged outcomes, send one shutdown request.
- Validate `orphaned_tasks == 0` and process exit status.
- If the Python server only supports one pending task, first implement a sequential request/outcome handshake while keeping multiple simulator tasks in flight. A later task may wait for its decision turn; this is acceptable for a first correct multi-task milestone, provided decision waiting is included consistently in the declared timing model. Do not silently assume the current server supports multiple outstanding decisions.

Protocol audit result: `deliverables/08_RL_Model/src/rl_model/server.py` stores pending decisions in a dictionary keyed by task ID, rejects duplicate IDs, and accepts outcomes by matching task ID. The protocol documentation explicitly says several tasks may be pending concurrently. The Java adapter can remain synchronous request/response per message; it does not need concurrent I/O threads to support multiple in-flight simulator tasks. Preserve this existing protocol rather than introducing an unnecessary protocol redesign.

## 6. Termination rule

Replace the one-task assumption behind terminal-triggered `CloudSim.abruptallyTerminate()` with a run coordinator:

- `expectedTaskCount` is known from the generated workload.
- Increment terminal count only after a successful, unique terminal transition and (for accepted agent decisions) a matching outcome acknowledgement.
- When `terminalTaskCount == expectedTaskCount`, assert all registry invariants, send one Python shutdown, validate its acknowledgement, then terminate the simulation.
- Do not call abrupt termination from a branch result or the first task terminal event.
- Define a maximum simulation horizon separately. If the horizon is reached with pending tasks, record them as unresolved only if the experiment has a valid horizon event and the outcome protocol supports this status. Otherwise fail the acceptance run and report the pending task IDs.

## 7. Required trace fields

Every task-related JSONL event should carry:

- `run_id`, `task_id`, `event`, `sim_time_ms`
- `actual_tuple_id` and `branch_key` where the event refers to a tuple/branch
- `action_id` / action where applicable
- node/module and direction for execution/transfer events
- raw bytes and per-task cumulative bytes where applicable

Required event families:

- `task_created`, `decision`, `branch_created`, `execution`, `transfer`
- `branch_result`, `merge_created`, `merge_execution`, `terminal`
- `outcome_ack`, `shutdown_ack`, `process_exit`

Do not overload the one-task trace schema by adding ambiguous global counters. Keep raw branch-level records so per-task measurements can be reconstructed.

## 8. Acceptance test matrix

The first implementation should pass these deterministic cases before workload-scale experiments:

| Case | Input | Required assertions |
|---|---|---|
| A | 1 full Local task | One decision, one branch, one terminal, one outcome ack |
| B | 2 full tasks with overlapping execution | Two independent records; no cross-attribution; two outcomes |
| C | 2 partial tasks with interleaved branch results | Each merge waits for its own branches; no cross-task merge |
| D | 1 full + 1 partial task | Full task terminalizes directly; partial task merges once |
| E | 3 tasks with different selected destinations | Per-task transfer/execution accounting matches tuple ownership |
| F | Duplicate branch result injected | Run fails with duplicate-result invariant; no second merge |
| G | Duplicate terminal event injected | Run fails with duplicate-terminal invariant; no duplicate outcome |
| H | Unknown task/tuple correlation | Run fails with explicit correlation error |
| I | All tasks complete in different orders | Python shutdown occurs once, after all outcomes are acknowledged |
| J | One task remains pending at horizon | No false success; pending task IDs are reported and status is handled under the declared horizon contract |

For every accepted run, assert:

- `generated_tasks == registered_tasks == terminal_tasks` (except a deliberately horizon-censored test, where pending tasks are explicitly reported).
- Every task ID is unique.
- Every execution tuple ID maps to exactly one branch.
- Every branch has at most one execution admission and one result.
- Every partial-fixture task has exactly the configured number of branch results before merge.
- Every task has exactly one terminal event.
- Every accepted decision has exactly one matching outcome acknowledgement.
- No orphaned Python tasks remain at shutdown.
- Repeated deterministic runs produce identical logical event summaries and stable task-level metrics.

## 9. Implementation sequence

1. **Done:** audited the Python server; pending decisions are keyed by task ID and outcomes are matched by task ID.
2. **Done for the experiment path:** added a run-scoped Java task registry. A separate pure-Java unit-test suite for the registry is not yet present.
3. **Done for full placement:** tuple correlation and per-task transfer/execution accounting are keyed by actual tuple ID. Partial branch references are still pending.
4. **Done:** four overlapping tasks were tested, including a training run that selected Local, Edge, Local, and Cloud in one simulation.
5. **Pending:** partial dispatch, branch barrier, and per-task merge correlation; learner-selected partial actions require a versioned action contract.
6. **Done:** one run-level completion coordinator saves once (training mode), sends one shutdown, and terminates only after all task outcomes are acknowledged.
7. **Done for current scope:** acceptance runner and validator cover one-task regressions, multi-task overlap, mixed-tier decisions, fixed-seed repeatability, fallback, and deadline behavior. Duplicate branch/terminal and unknown-correlation fault injection remain pending.
8. **Pending:** connect calibrated generated workloads and proceed to benchmark calibration.

Keep the one-task acceptance suite as regression coverage throughout. Preserve existing evidence and write each new run into a fresh output directory.

## 10. Explicit non-goals for this gate

- No claim of policy superiority or statistical performance.
- No energy optimization or per-task energy attribution until the power model is validated.
- No native failure model unless a simulator-supported failure event is implemented and verified.
- No arbitrary DAG/workflow splitting or multiple remote branches.
- No topology expansion to 4 IoT / 2 Edge / 1 Cloud until the actual device inventory and site-selection mechanism are implemented and audited.
- No calibration-layer or reward redesign in this gate; multi-task lifecycle correctness comes first.

## 11. Current blockers and handoff requirements

The MARK desktop was reconnected and the implementation was performed on branch `work/multi-task-lifecycle`.

Verified on 2026-11-15:

- Java compiled successfully with JDK 25 into a fresh `audit_output` run directory.
- The full acceptance runner passed ten Java cases with exit code 0: four single-task route/train cases, four-task baseline overlap, four-task training, a fixed-seed training repeat, timeout fallback, malformed-response fallback, and deadline miss.
- The mixed-action four-task training run chose Local, Edge, Local, and Cloud. All four tasks were registered before the first terminal event; all four outcomes were acknowledged; training was saved once; shutdown was acknowledged once with zero orphans.
- The fixed-seed repeat produced the same logical task summary.
- The external iFogSim working tree had 488 status entries before and after this work. It was not reset, cleaned, checked out, or compiled into.

Remaining gates:

- Extend the same lifecycle model to partial tasks, branch result barriers, merge tuple correlation, and mixed full/partial runs.
- Add fault-injection acceptance cases for duplicate terminal/result events and unknown task/tuple correlations.
- Implement and audit the target 4 IoT / 2 Edge / 1 Cloud topology.
- Calibrate workload assumptions before benchmark-scale experiments.

This is evidence for multi-task **full-placement** support only; it is not evidence that multi-task partial offloading or benchmark claims are complete.
