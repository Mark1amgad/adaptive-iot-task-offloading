# Experiment Scripts

> **Planned — empty placeholder.** No scripts exist yet.

This directory will hold the driver scripts that:

1. Load a scenario config from `../configs/`.
2. Run each policy (Local-only, Edge-only, Cloud-only, Adaptive Q-Learning) against
   the simulator with a fixed seed and workload.
3. Collect per-task outcomes (linked by `task_id`).
4. Aggregate metrics for each run.
5. Write raw output to `../../results/raw/`.

## Requirements before scripts are meaningful

- A verified simulator↔agent integration (see `docs/integration-contract.md`).
- An implemented, testable agent (`rl-agent/`).
- Agreed config format and metric definitions.

Language/tooling for these scripts is **not yet decided** (likely Python, calling or
coordinating with the Java simulator). Record the choice in `docs/decisions/` when
made. Do not add scripts that imply the pipeline works until it has actually been
verified.
