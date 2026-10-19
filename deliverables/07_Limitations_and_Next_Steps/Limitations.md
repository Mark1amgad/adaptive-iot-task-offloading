# Limitations and Next Steps

## Current Limitations

- **Single task:** the Java registry and terminal lifecycle support one task per run. Multi-task operation is deferred because task records, transfer hooks, outcome coordination, and final Python shutdown would need a task map and coordinated completion.
- **Task failure:** native failure was not verified in the exercised iFogSim path. The current experiment has a successful result endpoint and does not invent a failure event or false measurements.
- **Energy:** `energy_joules` is `null`; cumulative device energy is not attributed defensibly to one task.
- **Fallback scope:** timeout and malformed-response cases inject before observation transmission. They demonstrate deterministic fallback and cleanup, not a true mid-flight response timeout after Python has accepted a pending task.
- **Evaluation scope:** results are one-task, single-run integration measurements. They do not prove RL superiority, generalization, or statistically significant performance differences.
- **State/model scope:** the Python service reports a 54-state contextual-bandit-like configuration; broader state thresholds, training/evaluation separation, and research methodology remain future work.
- **External dependency:** the deliverables require the original repository, external iFogSim source, JDK, Python environment, and teammate-owned RL service.

## Safe Next Steps

1. Design a multi-task registry with one immutable record per task ID, per-task transfer attribution, one outcome per accepted decision, and shutdown only after all tasks are terminal.
2. Define a simulator-supported failure mechanism before adding failure outcomes; validate mandatory protocol fields and measurements for failed tasks.
3. Separate training from frozen evaluation and run repeated seeds under identical workloads.
4. Decide and validate state discretization, reward semantics, and dynamic-condition scenarios with the team.
5. Add an approved per-task energy attribution method or continue reporting energy as unavailable.
6. Verify complete bibliographic metadata and upstream licenses before public distribution.
