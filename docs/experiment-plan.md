# Experiment Plan

> **Status: PLANNED — pending implementation and validation.**
> This is a design for future experiments. No experiments described here have been
> run, and **no results are reported or claimed** in this document.

---

## 1. Goal

Evaluate whether the **adaptive Q-Learning** offloading policy improves relevant
performance metrics compared with **static placement policies** under controlled,
dynamic conditions.

## 2. Compared policies

| Policy | Description | Type |
| --- | --- | --- |
| **Local-only** | Always execute on the IoT device | Static baseline |
| **Edge-only** | Always execute on the edge/fog node | Static baseline |
| **Cloud-only** | Always execute on the cloud server | Static baseline |
| **Adaptive Q-Learning** | Per-task choice by the learned policy | Adaptive |

All policies must be evaluated under **identical** workload and condition settings
so that comparisons are fair.

## 3. Planned metrics

| Metric | Definition (to finalize) | Notes |
| --- | --- | --- |
| Average end-to-end latency | Mean task completion latency | Primary |
| Deadline violation rate | Fraction of tasks missing their deadline | Primary |
| Task completion / failure rate | Share of tasks completed vs. failed | |
| Energy consumption | Energy used per task / run | **Only if reliably supported** by iFogSim |
| Network usage | Data transferred / network time | |
| Cloud cost | Modeled cost of cloud execution | Model must be documented |
| Resource utilization | Edge/cloud CPU usage | **Only if reliably supported** |

> Metrics that depend on simulator support (energy, utilization) are included only
> if the simulator provides them reliably. Otherwise they are omitted with a note.

## 4. Controlled workloads

- Define task arrival patterns and task mixes explicitly and keep them fixed per
  scenario.
- Define **dynamic condition** profiles (how latency, edge utilization, and load
  change over a run) so all policies face the same conditions.
- Each scenario should be described by a config file in `experiments/configs/` so
  it is reproducible and reviewable.

## 5. Fair comparison requirements

- Same workload, same dynamic-condition trace, same number of tasks per policy.
- Static baselines and the adaptive policy must use the **same** task stream where
  the decision model allows it; if the policy influences future states, the
  comparison protocol must be documented to remain fair.
- The adaptive policy's **training** vs. **evaluation** phases must be separated
  and reported distinctly (e.g., learning curve vs. final-policy performance).
- The evaluation framing must match the chosen decision process (see
  `state-action-reward.md`, Section 1).

## 6. Reproducibility

- **Random seeds:** fix and record seeds for workload generation and for the
  agent's stochastic policy (e.g., ε-greedy). Log the seed with every run.
- **Repeated runs:** run each policy × scenario multiple times (count TBD) and
  report central tendency and spread (e.g., mean ± std), not a single run.
- **Versioning:** record the repository commit, simulator config, and agent config
  used for each result.
- **Environment:** document Java/Python versions and dependencies.

## 7. Experiment workflow (planned)

```
Select scenario config (experiments/configs/)
    ↓
For each policy in {Local, Edge, Cloud, Q-Learning}:
    ↓
    Run simulator with fixed seed & workload
    ↓
    Collect per-task outcomes linked by task_id
    ↓
    Aggregate metrics for the run
    ↓
Repeat across seeds/runs
    ↓
Store raw output in results/raw/
    ↓
Process & compare in results/processed/
```

Driver scripts will live in `experiments/scripts/`; experiment tests in
`experiments/tests/`.

## 8. Reporting (planned)

- Summarize per-metric comparison across the four policies.
- Include variability across repeated runs.
- State limitations (simulation fidelity, metric availability).

## 9. Preconditions before any real claim

1. Custom topology and dynamic task-level offloading are implemented and verified.
2. Q-Learning agent is implemented and its training loop runs reproducibly.
3. Java↔Python integration is verified end-to-end (action actually affects
   execution; outcomes link back to `task_id`).
4. Metrics are confirmed to be reliably measured by the simulator.

> Until the above are true, this plan remains **aspirational**. Do not present
> numbers from it as findings.
