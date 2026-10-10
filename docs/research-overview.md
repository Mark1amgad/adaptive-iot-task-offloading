# Research Overview

Project: **Adaptive AI-Based Task Offloading in IoT Edge-Cloud Networks Under
Dynamic Conditions**

> This document describes the *intended* research. Items marked **hypothesis**,
> **planned**, or **to be validated** are not established results.

---

## 1. Research Motivation

IoT deployments generate computational tasks that can be executed at multiple
tiers of an edge-cloud hierarchy — the device itself (Local), a nearby edge/fog
node (Edge), or a remote cloud server (Cloud). These tiers differ in latency,
compute capacity, energy profile, network dependence, and cost. Real-world
conditions are **dynamic**: task sizes vary, network latency fluctuates, and edge
nodes experience changing utilization. A single fixed placement rule cannot
adequately track these shifting trade-offs, motivating a **state-aware, adaptive**
decision policy.

## 2. Problem Statement

Under dynamic network and resource conditions, can an adaptive, learning-based
offloading policy select the execution tier (Local / Edge / Cloud) per IoT task in
a way that improves relevant performance metrics relative to static placement
policies?

## 3. Research Questions

- **RQ1 (core):** Can a **state-aware adaptive offloading policy** improve
  relevant performance metrics (e.g., latency, deadline violations) compared with
  **static placement policies** under dynamic conditions?
- **RQ2:** Which observable state features (task size, network latency, edge
  utilization, deadline category, possibly network load) are most useful for the
  placement decision?
- **RQ3:** What is the trade-off between decision quality and the complexity of
  the state representation and learning method?
- **RQ4:** How reproducible and stable are the learned policies across controlled
  workloads and random seeds?

## 4. Objectives

1. Formalize a task-offloading decision model (state, action, reward) for a
   Local/Edge/Cloud hierarchy.
2. Implement an adaptive policy using **Tabular Q-Learning** (Python).
3. Build/extend a **Java/iFogSim** simulation that applies the chosen action and
   measures task outcomes.
4. Define and validate an integration interface between the agent and simulator.
5. Compare the adaptive policy against Local-only, Edge-only, and Cloud-only
   baselines under controlled, dynamic workloads.
6. Report metrics with reproducible methodology (seeds, repeated runs).

## 5. Scope

**In scope:**

- A single logical IoT task stream with Local / Edge / Cloud placement options.
- Tabular Q-Learning over a small, discretized state space.
- Simulation-based evaluation under controlled dynamic conditions.
- Comparison against three static baselines.

**Out of scope (current):**

- Multi-agent coordination or task scheduling across many edge nodes.
- Deep reinforcement learning (the planned method is *tabular*).
- Physical testbeds or real cloud billing integration.
- Modifying the original upstream iFogSim repository.
- Production-grade system hardening.

## 6. Expected Contributions (intended, not yet achieved)

- A documented, reproducible design for adaptive offloading in a small
  edge-cloud simulation.
- An integrated Java↔Python experimental setup for evaluating a learning-based
  placement policy.
- A comparative study of adaptive vs. static placement under dynamic conditions.

> These are **expected/planned** contributions. They become actual contributions
> only after implementation, integration, and validated experiments.

## 7. Assumptions

- Tasks can be characterized by size, an associated deadline, and observable
  network/edge conditions at decision time.
- Placement to Local/Edge/Cloud can be represented and executed within iFogSim.
- Network latency and edge utilization can be measured or modeled by the
  simulator and passed to the agent.
- A discretized (banded) representation of continuous features is acceptable for
  a first tabular approach.
- The decision process framing (one-step contextual vs. sequential MDP) will be
  chosen deliberately and documented (see `state-action-reward.md`).

## 8. Limitations

- **Tabular** Q-Learning restricts the state space; results may not extend to
  high-dimensional or continuous states.
- Simulation results depend on the fidelity of the iFogSim model and the chosen
  dynamic-condition scenarios; they may not transfer to physical deployments.
- Energy, cost, and utilization metrics are included only **if reliably
  supported** by the simulator.
- The **research gap is treated as a hypothesis** to be validated through a
  literature review — novelty is **not** asserted as established fact.
- The integration protocol and reward definition are **provisional** and require
  team agreement and testing.

## 9. Novelty / Research Gap

The intuition is that adaptive, state-aware placement should outperform static
placement under dynamic conditions. Whether this constitutes a *novel* gap in the
literature is **not claimed as fact here**; it is a **hypothesis to be validated
through a systematic literature review** before it is presented as a contribution.
