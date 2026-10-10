# System Architecture

This document describes the **intended** architecture of the adaptive task-offloading
system. Each component is labelled with an implementation status so that planned
design is clearly separated from working functionality.

Status legend: **Planned** (not started) · **Under development** · **Pending
verification** (reported but not confirmed in this repo) · **Implemented** (working,
tested in this repo).

> As of repository inspection, **no component is confirmed "Implemented" in this
> repository.** The Java simulation and the original iFogSim example are reported by
> the team but are not present/verifiable here.

---

## High-level view

```
+----------------+     state (JSON)      +---------------------+
|  Java / iFogSim | -------------------> |  Python Q-Learning   |
|  (simulator)    |                       |  Agent (rl-agent)    |
|                 | <------------------- |                      |
+----------------+   action (JSON)        +---------------------+
       |                                          |
       | applies action, runs task,               | selects Local/Edge/Cloud
       v measures outcome                          v
+----------------+                        +---------------------+
| Task Execution |                        | Reward + Evaluation |
| + Measurement  |                        | (experiments/)      |
+----------------+                        +---------------------+
```

---

## 1. IoT Task Generation — *Planned / partially in example topology*

- Tasks are generated inside iFogSim as the workload source.
- Each task carries attributes used later for state and reward: size, deadline,
  and (at decision time) observed network latency and edge utilization.
- **To decide:** arrival pattern, task mix, and how "dynamic conditions" are
  introduced over the run.

## 2. State Measurement — *Pending verification*

- At task arrival, the simulator captures the current observable state.
- Candidate features: task size, network latency, edge utilization, deadline
  category (see `state-action-reward.md`).
- **Open:** where continuous values are discretized (Java side vs. Python side),
  and the units of each measurement.

## 3. Python Agent — *Under development*

- Hosted in `rl-agent/`. Owns the Q-Learning table, policy (e.g., ε-greedy), and
  learning update logic.
- Receives a state, returns a chosen action.
- **Status:** no production code committed yet; `rl-agent/src/` is a placeholder.

## 4. Action Selection — *Under development*

- The agent selects one of **Local / Edge / Cloud** for the given state.
- Exploration vs. exploitation strategy is planned but not finalized.

## 5. Java ↔ Python Simulator Integration — *Pending verification*

- A bridge passes the state to Python and the action back to Java.
- The interface is defined as a **draft** in `integration/protocol/` and
  `docs/integration-contract.md`.
- **No integration method is final** until Ayoub and Ibrahim agree on the protocol.

## 6. Task Execution — *Pending verification (original example reported to run)*

- Java/iFogSim **must actually apply** the selected action by routing the task to
  the chosen tier and executing it there.
- The action must have a real effect on execution, not merely be recorded.

## 7. Outcome Collection — *Planned*

- The simulator measures the outcome of each executed task (latency, deadline
  miss, resource usage, etc.).
- **Requirement:** every outcome must be linked back to the originating `task_id`
  so it can be paired with the state and action used for that decision.

## 8. Reward Calculation — *Planned*

- Candidate reward: `-(w1 × latency + w2 × deadline_miss + w3 × resource_cost)`.
- Weights, units, scale, and normalization are **not final**.
- **To decide:** whether reward is computed in Java, Python, or the experiment
  layer, and how it is attributed to the (state, action) transition.

## 9. Experiment Evaluation — *Planned*

- `experiments/` will drive comparisons among Local-only, Edge-only, Cloud-only,
  and Adaptive Q-Learning policies.
- `results/` will hold raw and processed outputs.
- Methodology (seeds, repeats, controlled workloads) is in `experiment-plan.md`.

---

## Data & control responsibilities

| Concern | Owner | Notes |
| --- | --- | --- |
| Generating tasks & measuring state | Ayoub (Java) | Must expose consistent units |
| Discretization boundaries | Ayoub + Ibrahim (agreement) | Single source of truth required |
| Choosing actions | Ibrahim (Python) | Policy + learning update |
| Applying action to execution | Ayoub (Java) | Action must change real routing |
| Verifying execution destination | Ayoub (Java) | Java confirms where the task ran |
| Linking outcome to task | Ayoub (Java) | Preserve `task_id` traceability |
| Reward & evaluation | Team (to be agreed) | Location of computation undecided |

## Cross-cutting requirements

- **Traceability:** every decision (state → action → outcome → reward) must be
  joinable by `task_id`.
- **Honesty of status:** components above are design intent. Nothing here should be
  reported as validated until code exists and tests/experiments pass.
- **Consistency of the decision model:** the architecture must match whichever
  decision framing is chosen (one-step contextual vs. sequential MDP) — see
  `state-action-reward.md`.
