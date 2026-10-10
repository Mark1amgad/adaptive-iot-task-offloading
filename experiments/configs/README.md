# Experiment Configurations

> **Planned — empty placeholder.** No config files exist yet.

This directory will hold one configuration file per experimental **scenario**, so
that workloads and dynamic-condition profiles are explicit, reviewable, and
reproducible.

## What a config should capture (candidate fields)

- Scenario name and purpose.
- Workload: task arrival pattern, task count, task-size / deadline distributions.
- Dynamic-condition profile: how network latency, edge utilization (and optionally
  network load) vary over the run.
- Policies to evaluate: `local_only`, `edge_only`, `cloud_only`, `q_learning`.
- Random seeds and number of repeated runs.
- Metric selection (only those the simulator reliably supports).
- Agent hyperparameters (learning rate, discount, exploration schedule) — values
  to be decided and documented, not hard-coded blindly.

> Format (JSON / YAML / TOML) is **not yet chosen**. Pick one and document it here
> before adding files. The exact units and discretization boundaries must match the
> integration contract and `docs/state-action-reward.md`.

Config files should be added only once the simulator and agent can consume them.
