# Experiments

> **Status: planned — pending implementation and validation.**
> This area will drive the comparison of Local-only, Edge-only, Cloud-only, and
> Adaptive Q-Learning policies. No experiments have been run and **no results are
> claimed here.**

Full methodology is in [`../docs/experiment-plan.md`](../docs/experiment-plan.md).

## Layout

- `configs/` — scenario/workload configuration files (see `configs/README.md`).
- `scripts/` — driver scripts that run policies against the simulator
  (see `scripts/README.md`).
- `tests/` — experiment-harness tests (currently a placeholder).

## Principles (summary)

- **Fair comparison:** identical workload and dynamic-condition trace for every
  policy.
- **Reproducibility:** fixed, logged random seeds; recorded config and commit.
- **Repeated runs:** multiple seeds/runs per policy; report mean and spread.
- **Metric honesty:** include energy/utilization only if the simulator measures
  them reliably.

Results are written to `../results/raw/` and processed into `../results/processed/`.
