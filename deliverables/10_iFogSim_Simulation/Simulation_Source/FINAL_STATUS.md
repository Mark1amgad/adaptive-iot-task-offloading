# Integration status

## Verified — 2026-11-15

- The experiment-owned Java integration now supports multiple overlapping full-placement tasks using one run-scoped registry: `tasksById` and `actualTupleId -> TaskRecord`.
- Each task is correlated independently through decision, tuple creation, execution, transfer, terminal result, outcome acknowledgement, and final run shutdown.
- Four-task runs passed in both baseline and training modes. The training run selected Local, Edge, Local, and Cloud within the same simulation, demonstrating multiple destinations in one run.
- All four tasks were registered before the first terminal event. Each task received one outcome acknowledgement; the Python service was saved once after the four outcomes and shut down once with `orphaned_tasks=0`.
- A second fixed-seed four-task training run produced an identical logical summary: actions, executing devices/modules, execution-admission times, latency, counted bytes, transfer counts, and deadline outcomes.
- The final acceptance suite completed ten Java cases with exit code 0: single-task train, Local/Edge/Cloud regressions, four-task baseline overlap, four-task training, fixed-seed repeat, timeout fallback, malformed-response fallback, and zero-deadline.
- The validator checks per-task task/tuple correlation, action-to-executor agreement, expected transfer bytes/counts, unique task IDs and tuple IDs, all outcome acknowledgements, one shutdown after all acknowledgements, zero Python orphans, and repeat-run logical determinism.
- The four-task mixed-action training run measured simulated task latencies of 5.51 ms (Local), 7.302857 ms (Edge), 13.51 ms (Local), and 97.685804 ms (Cloud). Counted link bytes were 0, 14,000, 0, and 28,000 respectively. These are integration-fixture measurements, not calibrated benchmark results.
- The acceptance runner now resolves the actual source, model, and validator locations and compiles to a fresh isolated output directory. It does not write to `iFogSim/out/production`.
- The external iFogSim working tree was already dirty when this work began (488 status entries, including tracked compiled outputs and untracked experiment sources). Its status-entry count remained 488 after the acceptance runs; no reset, clean, checkout, or compilation into that tree was performed.

## Not verified / remaining work

- Partial offloading remains a separate feasibility spike. The Python action schema and learner still expose only Local / Edge / Cloud; the learner does not select a partial action.
- Multi-task partial branch dispatch, branch-result barriers, merge tuple correlation, and mixed full/partial task acceptance remain unimplemented.
- The target 4 IoT / 2 Edge / 1 Cloud topology is not implemented in this integration; the tested topology has one Local, one Edge, and one Cloud device.
- Task failure, cancellation, and unresolved-at-horizon behavior remain undefined and unverified.
- Per-task energy attribution is not implemented; `energy_joules` remains null.
- Calibrated workloads, paired multi-seed benchmark runs, statistical analysis, and claims of policy superiority remain out of scope until the simulation model is calibrated and the benchmark protocol is completed.
- The RL Python unit-test suite was not rerun in this session because the selected Python interpreter does not have `pytest` installed. The Java/Python integration acceptance suite and JSONL validator did run successfully.

No claim above treats configured task size, topology, deadline, or workload parameters as calibrated real-world values.
