# Adaptive AI-Based Task Offloading in IoT Edge-Cloud Networks Under Dynamic Conditions

## Shared Workspace

This repository is the shared workspace for the five-person research team. Start
with [TEAM_GUIDE.md](TEAM_GUIDE.md), [TASK_TRACKER.md](TASK_TRACKER.md), and
[FILE_INDEX.md](FILE_INDEX.md).

- Shared research materials: [shared/](shared/)
- Member workspaces: [team-work/](team-work/)
- Final project package: [deliverables/](deliverables/)
- Experiments and results: [experiments/](experiments/) and [results/](results/)
- Existing implementation artifacts: [deliverables/08_RL_Model/](deliverables/08_RL_Model/)
  and [deliverables/10_iFogSim_Simulation/](deliverables/10_iFogSim_Simulation/)

The repository currently contains both planned project areas and preserved
implementation/audit artifacts. These navigation paths do not replace or move
executable code or historical evidence.

A university research project investigating whether an **adaptive AI-based policy**
can select between **Local**, **Edge**, and **Cloud** execution for IoT tasks under
changing network and resource conditions.

> **Status of this README.** This document describes the *intended* research design
> and the *planned* system. Where a capability has not yet been implemented or
> experimentally validated, it is explicitly marked as **planned** or **pending**.
> No benchmark results, performance improvements, or research findings are claimed
> here. See [Current Implementation Status](#13-current-implementation-status).

---

## 1. Research Motivation

IoT applications increasingly generate tasks that can be executed at different
tiers of an edge-cloud hierarchy:

- **Local** execution on the IoT device itself,
- **Edge** execution on a nearby fog/edge node,
- **Cloud** execution on a remote data-center server.

Each tier offers a different trade-off between latency, resource capacity, energy
use, network dependency, and cost. Under **dynamic conditions** (varying task
sizes, fluctuating network latency, and changing edge resource utilization), a
fixed placement rule can be sub-optimal. A policy that observes the current state
and adapts its placement decision per task is therefore worth studying.

## 2. Problem Statement

Given a stream of IoT tasks arriving under changing network and resource
conditions, can a **state-aware adaptive offloading policy** choose the execution
tier (Local / Edge / Cloud) per task in a way that improves relevant performance
metrics compared with **static placement policies**?

## 3. Research Objectives

1. Define a task-offloading decision model (state, action, reward) for a
   Local/Edge/Cloud hierarchy.
2. Implement a learning-based adaptive policy using **Tabular Q-Learning** (Python).
3. Integrate the policy with a **Java/iFogSim** simulation that actually applies
   the selected placement and measures task outcomes.
4. Compare the adaptive policy against static baselines under controlled, dynamic
   workloads.
5. Report evaluation metrics with reproducible, repeatable experiments.

## 4. Planned System Workflow

The following is the **intended** end-to-end design. It is **not** a claim that the
whole workflow is currently operational.

```text
Task Arrival
    ↓
State Observation
    ↓
Q-Learning Agent
    ↓
Action Selection
    ↓
Java/iFogSim Applies the Action
    ↓
Task Execution
    ↓
Measurement Collection
    ↓
Reward and Evaluation
```

| Stage | Component | Implementation status |
| --- | --- | --- |
| Task Arrival | iFogSim (Java) | Planned / partially in example topology |
| State Observation | iFogSim → integration bridge | Pending verification |
| Q-Learning Agent | Python (`rl-agent/`) | Under development |
| Action Selection | Python (`rl-agent/`) | Under development |
| Apply Action | iFogSim (Java) | Not yet verified as fully implemented |
| Task Execution | iFogSim (Java) | Original example reported to run |
| Measurement Collection | iFogSim (Java) | Pending |
| Reward & Evaluation | Python + `experiments/` | Pending |

## 5. Planned Action Space

The agent selects one of three placement actions per task:

- **Local** — execute on the IoT device.
- **Edge** — execute on the edge/fog node.
- **Cloud** — execute on the remote cloud server.

## 6. Proposed State Features (candidate)

The candidate state is discretized from observable conditions:

1. **Task size** — Low / Medium / High
2. **Network latency** — Low / Medium / High
3. **Edge utilization** — Low / Medium / High
4. **Deadline category** — Tight / Relaxed

Candidate state space: `3 × 3 × 3 × 2 = 54` states.

An optional fifth feature (**network load**, three levels) would expand the space
to `162` states, but it is **not** part of the agreed definition and requires team
agreement before adoption. Full details and caveats are in
[`docs/state-action-reward.md`](docs/state-action-reward.md).

## 7. Planned Q-Learning Approach

- **Algorithm:** Tabular Q-Learning.
- **Learning signal (candidate):**
  `Reward = -(w1 × latency + w2 × deadline_miss + w3 × resource_cost)`
- Exact reward scale, weights, units, and normalization are **to be agreed and
  tested** — they are not finalized in this repository.

> The final algorithm must be specified consistently with the intended decision
> process. A **one-step contextual decision** and a **sequential Markov Decision
> Process** are **not automatically equivalent**; the team must choose and document
> which one applies. This is discussed in `docs/state-action-reward.md`.

## 8. Planned Baseline Comparisons

The final system is **intended** to compare:

- **Local-only** policy (static).
- **Edge-only** policy (static).
- **Cloud-only** policy (static).
- **Adaptive Q-Learning** policy.

These comparisons are **pending implementation and validation**.

## 9. Evaluation Metrics (planned)

- Average end-to-end latency.
- Deadline violation rate.
- Task completion / failure rate.
- Energy consumption (if reliably supported by the simulator).
- Network usage.
- Cloud cost.
- Resource utilization (if reliably supported).

Details, workload control, seeds, and repeated-run methodology are in
[`docs/experiment-plan.md`](docs/experiment-plan.md).

## 10. Repository Structure

```text
adaptive-iot-task-offloading/
├── README.md
├── CONTRIBUTING.md
├── LICENSE_STATUS.md
├── .gitignore
├── .gitattributes
├── docs/                     # Research and design documentation
│   ├── research-overview.md
│   ├── system-architecture.md
│   ├── state-action-reward.md
│   ├── integration-contract.md
│   ├── experiment-plan.md
│   ├── team-responsibilities.md
│   └── decisions/            # Design decision log
├── simulator/                # Java / iFogSim simulation area (Ayoub)
├── rl-agent/                 # Planned Python agent area
├── integration/              # Java <-> Python protocol and examples
│   ├── protocol/             # Draft message schema(s)
│   └── examples/
├── experiments/              # Experiment configs, scripts, tests
├── results/                  # Raw and processed experiment output
└── .github/                  # Issue and PR templates
```

## 11. Team Responsibilities

| Member | Focus |
| --- | --- |
| **Mark** | Research coordination, objective, final analysis, documentation, integration |
| **Omar** | Literature extraction and comparison tables |
| **Mostafa** | Dataset research, source collection, and dataset inventory |
| **Abdo** | Dataset engineering, validation, provenance, and benchmark dataset |
| **Ayoub** | Model development, simulator integration, and experiments |

Shared interface decisions require agreement between the simulator and model owners.
See [`docs/team-responsibilities.md`](docs/team-responsibilities.md).

## 12. Setup Prerequisites

Planned prerequisites (verify versions as the project develops):

- **Java JDK** compatible with the chosen iFogSim version.
- **Maven** (or the build tool required by the iFogSim setup).
- **Python 3.10+** for the Q-Learning agent.
- **Git** with access to this repository.
- iFogSim sources/dependencies (this project does **not** modify the original
  iFogSim repository).

The Python agent environment is described in [`rl-agent/README.md`](rl-agent/README.md).

## 13. Current Implementation Status

Based on inspection of this repository at the time of writing:

| Area | Status | Evidence / note |
| --- | --- | --- |
| Git repository | Initialized locally and cloned from GitHub | Remote `origin` = `Mark1amgad/adaptive-iot-task-offloading`; branch `main`; single `Initial commit` |
| Original iFogSim example | Reported to run successfully by the team | **Not present in this repository**; report is from the team, not verifiable here |
| Custom topology | Preliminary implementation reported | **No code present here**; cannot be confirmed from the repo |
| Dynamic task-level offloading | Not yet verified as fully implemented | No simulator code committed yet |
| Python Q-Learning agent | Under development | `rl-agent/src/` currently empty (placeholder only) |
| Java-Python integration | Pending verification | Only a **draft** schema exists in `integration/protocol/` |
| Baseline comparison | Pending | No experiment scripts or results committed |
| Final experiments | Pending | `results/` contains placeholders only |

> Nothing in this table should be read as a validated research result.

## 14. How to Contribute

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the branch/PR workflow and
[`docs/team-responsibilities.md`](docs/team-responsibilities.md) for ownership.
Use the issue templates under `.github/ISSUE_TEMPLATE/` and the pull request
template for changes.

## 15. Important Limitations

- This repository documents **intent**. Implemented, tested functionality is
  limited; the agent, simulator customization, integration, and experiments are
  **pending**.
- The **integration protocol is a draft**. Field names, units, and discretization
  are provisional until the relevant simulator and model owners agree on them.
- **No novelty claim is asserted as fact.** The stated research gap is a
  **hypothesis** to be validated through a literature review.
- Reward weights, thresholds, and state discretization boundaries are **not
  final**; any example values in the docs are labelled provisional.
- iFogSim's own license and the original upstream project remain the responsibility
  of their authors; see [`LICENSE_STATUS.md`](LICENSE_STATUS.md).
- The original iFogSim repository is **out of scope** and must not be modified by
  this project.
