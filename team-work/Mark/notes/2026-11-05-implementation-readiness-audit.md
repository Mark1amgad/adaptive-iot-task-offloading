# Implementation Readiness Audit — 2026-11-05

## Scope and safety

This is a read-only audit of the working tree against the latest working specification:
`C:\\Users\\DELL\\OneDrive\\Desktop\\Research\\MARK_RESEARCH_SPECIFICATION_V2.md` (dated 2026-11-04).

No existing project source, configuration, experiment output, Git history, or external simulator file was changed during this audit.

## 1. Git and workspace state

### Main research repository
- Path: `Research/adaptive-iot-task-offloading`
- Branch: `main`, aligned with `origin/main` at commit `39d6cd4`.
- Current working-tree change observed: `M FILE_INDEX.md`.
- Its diff adds links to the canonical research library and supporting audit/methodology material. Preserve it; do not reset or overwrite it.

### External iFogSim repository
- Path: `Research/iFogSim`
- Branch: `main`, aligned with `origin/main` at commit `5f68d39`.
- The working tree is already substantially dirty: many tracked compiled `.class` files are modified/deleted, and multiple experiment, topology, audit, and GUI files are untracked.
- These changes predate this audit as observed. Do not run clean/reset/checkout or compile into its tracked `out/production` directory. Do not assume these files are disposable build artifacts.

## 2. Latest research scope versus repository documentation

The 2026-11-04 working specification defines:
- Risk-calibrated feasibility filtering for full and constrained partial execution.
- Full placement across Local / Edge / Cloud.
- Partial execution only for explicitly divisible tasks, split between Local and exactly one remote tier.
- Per-task deadlines, calibrated prediction residuals, and conservative completion-time estimates.
- Repeated workload/network regime shifts and recovery measurements.
- Paired baselines, ablations, held-out scenarios, and reproducibility controls.

However, repository-level documents such as `README.md`, `docs/research-overview.md`, `docs/state-action-reward.md`, and `docs/experiment-plan.md` still describe the earlier 54-state, three-action tabular Q-learning study. They are not yet aligned with the 2026-11-04 scope.

The Research Gap v29 report is a separate prior-art audit around multi-tenant chance-constrained offloading. It should not be silently treated as the latest project specification; use the 2026-11-04 Mark specification as the current working scope unless the supervisor/team supersedes it.

## 3. Python learner audit

Observed canonical implementation: `deliverables/08_RL_Model/src/rl_model/`.
- The class is named `QLearningAgent` and implements the general tabular Q update.
- `config/default.json` sets `gamma = 0.0` and `decision_model = "contextual_bandit"`; operationally, the configured update is a contextual-bandit update, not sequential multi-step Q-learning.
- The current action set is exactly `Local`, `Edge`, and `Cloud`.
- The default state has 54 states and four enabled features.
- `task_mi` and `deadline_ms` thresholds are explicitly placeholders. Reward cost reference values are also placeholders.
- There are no partial-execution actions, split ratios, legal-action rules for divisible tasks, or residual-calibration layer in this implementation.

## 4. Simulator and integration evidence

Observed accepted experiment source: `deliverables/10_iFogSim_Simulation/Simulation_Source/org/fog/test/perfeval/RlOffloadingIntegrationExperiment.java`.
- The acceptance experiment constructs exactly three simulated devices: one Local, one Edge, and one Cloud.
- It emits exactly one task (`TASK_MI = 2500`) and accepts one Local/Edge/Cloud decision.
- The accepted trace proves a correlated one-task lifecycle and Python update; it is integration evidence, not a comparative performance experiment.
- The retained example chose Local and recorded 3.51 ms latency, 0 counted parent-child transfer bytes, and a 500 ms configured deadline. This single observation cannot establish policy superiority.
- Energy is `null`; the integration status explicitly says per-task energy is not validated.
- `FINAL_STATUS.md` explicitly records multi-task mode as unsupported in the accepted experiment.
- No split/parallel-local-remote/merge execution path is present in the inspected acceptance source.

Topology discrepancy:
- The latest specification mentions a development topology of 4 IoT devices, 2 Edge nodes, and 1 Cloud node.
- The inspected `iFogSim/src/org/fog/test/perfeval/AdaptiveOffloadingFog.java`, `research_topology.json`, and repository acceptance experiment show only one Local, one Edge, and one Cloud device.
- Therefore the 4+2+1 topology is not verified by the inspected implementation. It may exist in another workspace/version, but must be located and audited before it is used as an implementation fact.

## 5. Test execution

Attempted the documented Python test command with the installed default Python 3.14:
`python -B -m pytest -q -p no:cacheprovider`

Result: pytest is not installed in that interpreter (`No module named pytest`). This is an environment blocker, not a failing test result. No dependencies were installed and no environment was modified.

## 6. Blocking gaps before research experiments

1. Reconcile the current specification with the older repository documentation and task tracker.
2. Locate and verify the claimed 4-IoT/2-Edge/1-Cloud topology, or explicitly revise the implementation topology baseline.
3. Prove that the simulator can represent a divisible task as two concurrent branches (Local + one remote tier), including partition, synchronization, and merge overheads.
4. Extend the simulator from the accepted one-task lifecycle to multiple concurrent task records with unique IDs and exactly one reconciled terminal status per task.
5. Validate the full completion-time decomposition (queue + transfer + execution + partition/merge) against event traces without double counting.
6. Audit the exact learner behavior, then implement the residual-calibrated feasibility layer and option-specific fallback hierarchy.
7. Calibrate thresholds/reward parameters using training/validation data only; keep held-out test scenarios untouched.
8. Re-run Python tests in a known project environment, then run simulator acceptance tests before any comparative experiment.

## 7. Recommended execution order

**Gate A — Specification and topology:** preserve this audit; confirm the current specification is the agreed working scope; identify the authoritative simulator workspace and topology.

**Gate B — Simulator feasibility spike:** implement a tiny isolated divisible-task proof of concept in a new experiment-owned source/output location. Demonstrate two branches, merge, task correlation, and truthful timing. Do not modify upstream iFogSim core files or compile into tracked output directories.

**Gate C — Multi-task lifecycle:** add a task registry and event logging that can handle overlapping decisions/outcomes without cross-task attribution or duplicate shutdown.

**Gate D — Learner and calibration:** integrate legal full/partial actions, per-option predicted completion time, residual windows, conservative feasibility masks, and explicit no-feasible-option logging.

**Gate E — Experiments:** only after Gates A–D pass, freeze paired workload/seed manifests, baselines, ablations, and held-out regime-shift tests.

## Audit conclusion

The existing work provides a useful Python learner and a one-task Java/Python/iFogSim integration proof. It does **not** yet implement the current research scope. The highest-risk dependency is not the bandit algorithm: it is whether the simulator can faithfully model and measure concurrent partial execution and task-level outcomes. Resolve that feasibility question before expanding the learner or claiming results.

## 8. Additional source-level feasibility findings

A focused read of the external iFogSim source confirms:
- `FogDevice.processTupleArrival` routes a tuple to an application module when the destination module is hosted on that device; otherwise it forwards the tuple up/down the hierarchy.
- `FogDevice.executeTuple`, `sendUpFreeLink`, and `sendDownFreeLink` are protected methods. The existing experiment-owned `InstrumentedFogDevice` subclass already overrides these hooks for execution and per-hop transfer observation.
- `Application.getResultantTuples` can create resultant tuples from an input tuple according to configured application edges/selectivity, and carries `actualTupleId` forward.
- These are useful extension points, but they do **not** provide a generic task-partition/parallel-branch/merge primitive. A correct partial-offloading implementation still needs an experiment-owned task/branch registry, unique branch correlation, a two-branch completion barrier, explicit split/merge overhead events, and exactly one task-level terminal outcome.
- Do not infer that one original tuple can simply be sent to two executors and counted as a valid partial task. The computational work and input/output data must be partitioned consistently, and each branch's execution must represent its assigned fraction.

This changes the feasibility assessment from “unknown whether instrumentation hooks exist” to “instrumentation hooks exist; task-level split/merge semantics remain unimplemented and must be proven in an isolated spike.”

## 9. Partial-offloading feasibility spike — 2026-11-05

Created an isolated experiment package:
`deliverables/10_iFogSim_Simulation/partial_offloading_spike/`

Files:
- `src/org/fog/test/perfeval/PartialOffloadingFeasibilitySpike.java`
- `run.ps1` — compiles to the spike's own `build/classes` and runs into a new timestamped results directory.
- `README.md` — scope, reproducibility, measurements, and modeling limitations.
- `results/run_001/` — retained failed setup attempt; do not use as evidence.
- `results/run_002/` and `results/run_20261105_211023/` — successful deterministic runs.

### Successful execution

The source compiled against the external iFogSim source/JARs with JDK 25. The reproducibility runner then compiled and executed the spike successfully (exit code 0). Both successful runs produced the same trace and summary values.

Configuration:
- One task, 10,000 MI, 12,000 input bytes, 1,000 output bytes.
- Local branch: 40% = 4,000 MI, 4,800 input bytes, 400 output bytes.
- Edge branch: 60% = 6,000 MI, 7,200 input bytes, 600 output bytes.
- Local MIPS: 1,000; Edge MIPS: 2,800.
- Local↔Edge configured link latency: 45 ms.
- Fixed coordinator merge delay: 2.0 ms.

Observed in both successful traces:
- Both branches were created at simulation time 5.0 ms with distinct propagated `actualTupleId` values.
- Local branch execution started at 5.0 ms; its result arrived at 10.01 ms.
- Edge branch input transfer was 7,200 bytes; Edge execution started at 50.72 ms.
- Edge result transfer was 600 bytes; its result arrived at 98.932857 ms.
- The merge barrier began only after both branch results arrived.
- One task-level completion was recorded at 100.932857 ms.
- End-to-end latency from task creation: 95.932857 ms.
- Branch-result skew: 88.922857 ms.
- Counted parent-child transfer bytes: 7,800 across exactly two hops.
- MI, input bytes, and output bytes passed conservation assertions; each branch had one execution and one result; merge delay matched its configured value.

### What this establishes — and what it does not

**Established:** this iFogSim2 setup can execute two separately correlated branches on Local and Edge, route both results to a shared endpoint, enforce a two-result barrier, and produce one terminal task result. The experiment-owned source and build output are isolated from the external simulator core/output.

**Not established:** this does not yet model a real merge CPU workload. The 2 ms merge is a fixed scheduled delay. The 40/60 proportional MI/byte split is only a deterministic fixture and is not a valid divisibility rule for arbitrary tasks. No performance superiority, general partial-offloading policy, multi-task concurrency, or RL support is demonstrated.

### Debugging note

The first run exposed a hard-coded broker user id and the classic Controller's expectation of a device named `cloud`. Both were corrected in the experiment source; the failed run was retained. No upstream iFogSim source files were edited.

### Next gate

Replace the fixed merge delay with an actual merge execution path (including merge data, CPU admission/completion, and task-level accounting), then test split-ratio validity and a Local+Cloud variant. Do not integrate the RL policy or run comparative claims until these are verified.

Reproducibility check:
- The checked-in runner `partial_offloading_spike/run.ps1` completed successfully with exit code 0 and created `results/run_20261105_211023/`.
- `summary.txt` contents in `run_002` and `run_20261105_211023` compare byte-for-byte equal.
- Both `spike_trace.csv` files have the same SHA-256: `9D357664D66E88B3E584B45F5C5215C0335738222DDACA3D3B3001D12A199727`.
- The spike's `build/classes` output is ignored by the repository's existing `**/build/` rule.
- Final status check found no modifications to the external iFogSim `FogDevice.java` or `Application.java`; the external repository remains pre-dirty and must not be cleaned. The main research repository's pre-existing `FILE_INDEX.md` modification remains untouched.

## 10. Real merge-Cloudlet extension — 2026-11-05

The first feasibility spike used a fixed coordinator delay after the two branch results arrived. That was replaced with a real iFogSim/CloudSim execution stage:

- Added a `merge_worker` AppModule hosted on Local.
- Split branch results now terminate at a dedicated `branch_result_endpoint`.
- The coordinator waits for both branch results, then creates one correlated `MERGE_INPUT` tuple (1,200 MI, 1,000 input bytes, 100 output bytes).
- The merge tuple is submitted to the Local FogDevice through the normal `TUPLE_ARRIVAL` path and admitted to the Local `merge_worker` Cloudlet scheduler.
- The merge module emits `MERGED_RESULT` to a separate `final_result_endpoint`.
- The final endpoint must return a tuple correlated to the merge tuple before the task registry records its single terminal completion.
- The coordinator now ignores normal `TUPLE_ACK` events instead of treating them as fatal.

### Current verified runs

- `results/run_20261105_211737/`
- `results/run_20261105_211838/`

Both were generated by the PowerShell reproduction runner; both exited 0 and their `summary.txt` contents and `spike_trace.csv` SHA-256 hashes are identical.

Current measured event values:
- Task creation: 5.000 ms.
- Local branch result: 10.010 ms.
- Edge branch result: 98.932857 ms.
- Merge barrier satisfied: 98.932857 ms.
- Merge Cloudlet admitted to `merge_worker`: 98.932857 ms.
- Final merged result arrived: 101.142857 ms.
- End-to-end task latency: 96.142857 ms.
- Merge module admission-to-endpoint interval: 2.210 ms, including the configured 1 ms actuator endpoint latency; this is not a pure CPU time.
- Split conservation: 10,000 MI; 12,000 input bytes; 1,000 output bytes.
- Counted parent-child transfer: 7,800 bytes across two hops.

The successful run now demonstrates actual Cloudlet submission and a final result produced by the merge module. It still does not model the actual data-copy/serialization algorithm that combines the branch outputs: the coordinator represents the combined 1,000-byte output as a synthetic merge-input tuple, injected locally because the endpoint and merge module are co-located. No extra network transfer is claimed for that local handoff.

### Failed intermediate run retained

`results/run_20261105_211659/` is retained as a failed intermediate attempt. It exposed the need to ignore `TUPLE_ACK` in the coordinator. The subsequent `run_20261105_211737/` and `run_20261105_211838/` runs passed.

### Updated conclusion

The isolated feasibility spike now proves a two-branch Local+Edge task can pass through a real merge Cloudlet and one final task-level result in this iFogSim2 setup. The next research risk is no longer whether a merge Cloudlet can be executed; it is whether the task's computational/data partition and merge semantics are valid for the target workload family. Establish those workload contracts before adding more placement actions, RL integration, or comparative claims.
