# State, Action, and Reward Design

This document specifies the **candidate** (not final) reinforcement-learning
formulation. All thresholds, weights, and discretization boundaries below are
**provisional** and require team agreement and testing. Nothing here is validated.

---

## 1. Decision-process framing (important preliminary)

The final algorithm must be specified **consistently** with the intended decision
process. Two framings are *not* automatically equivalent:

- **One-step contextual decision (contextual bandit):** each task is an
  independent decision; the chosen action produces an immediate reward, and there
  is **no meaningful next-state transition** caused by the decision itself.
- **Sequential Markov Decision Process (MDP):** actions influence future states,
  so a sequence of decisions is optimized over time (credit assignment across
  steps matters).

**Why it matters:** Tabular Q-Learning is a sequential-MDP algorithm (it uses a
next-state term in the Bellman update). If the real problem is effectively a
one-step contextual decision, applying full MDP Q-Learning requires an explicit,
justified definition of "next state" and episode/step structure; otherwise the
learning update may not match the actual decision process.

> **Team decision required:** choose one framing and define states, transitions,
> episodes, and rewards to be consistent with it. Until then, the design below is
> a candidate. Record the decision in `docs/decisions/`.

---

## 2. Candidate State Design

Discretized features:

| # | Feature | Levels (candidate) |
| --- | --- | --- |
| 1 | Task size | Low / Medium / High |
| 2 | Network latency | Low / Medium / High |
| 3 | Edge utilization | Low / Medium / High |
| 4 | Deadline category | Tight / Relaxed |

**Candidate state space:** `3 × 3 × 3 × 2 = 54` states.

### Optional fifth feature: network load

Network load **may** be included as an independent three-level feature
(Low / Medium / High). If added, the state space becomes:

`3 × 3 × 3 × 3 × 2 = 162` states.

> Network load is **not** part of the agreed state definition. It must **not** be
> added to the final state without **team agreement** (Ayoub + Ibrahim), because it
> triples the table size and changes data-collection needs on the Java side.

### Provisional discretization boundaries (for discussion ONLY)

These are **example cut points to seed discussion**, not final values. Actual
boundaries must be derived from the simulator's real value ranges and units.

```
task_size (MB):        Low < X ≤ ...   (boundaries TBD)
network_latency (ms):  Low / Medium / High  (boundaries TBD)
edge_utilization (%):  Low / Medium / High  (boundaries TBD)
deadline_category:     Tight / Relaxed      (rule TBD)
```

- **Do not** treat the "Low/Medium/High" labels as having fixed numeric ranges yet.
- The **units** of each raw measurement (MB, ms, %, …) must be documented and
  agreed before discretization is implemented.

---

## 3. Action Space

The action space is fixed and small:

| Action | Meaning |
| --- | --- |
| **Local** | Execute the task on the IoT device |
| **Edge**  | Execute the task on the edge/fog node |
| **Cloud** | Execute the task on the remote cloud server |

The selected action **must** affect actual task execution in the simulator (see
`integration-contract.md`).

---

## 4. Candidate Reward Structure

Candidate form:

```
Reward = -(w1 × latency + w2 × deadline_miss + w3 × resource_cost)
```

- **Negative** because lower latency, fewer deadline misses, and lower resource
  cost are better.
- `w1, w2, w3` are **weights** whose values are **not decided**.
- `deadline_miss` may be binary or graded — **not yet specified**.
- `resource_cost` may combine energy/cost/utilization terms — **not yet specified**.

### What is NOT yet decided (explicitly)

- The exact **scale** of the reward.
- The **weights** `w1, w2, w3`.
- The **units** of each term and whether they are **normalized**.
- Whether reward is computed per-step, per-task, or aggregated.

> **Do not invent final thresholds, reward weights, or units.** Example values may
> appear in discussions only and must be labelled provisional. Any numeric example
> used for illustration here is provisional and non-binding.

### Provisional numeric illustration (NOT a recommendation)

For discussion of the *shape* of the formula only — for example, one might initially
consider equal weights such as `w1 = w2 = w3 = 1` and normalize each term to
`[0, 1]`. This is **purely illustrative**; the team must choose and test the real
values. These numbers are **provisional** and should not be copied into code as if
final.

---

## 5. Open items requiring team agreement

1. Choose the decision-process framing (contextual bandit vs. sequential MDP).
2. Fix the state feature list (including whether network load is in or out).
3. Agree on units and discretization boundaries for each continuous feature.
4. Agree on the reward terms, their units, normalization, and weights.
5. Decide where discretization and reward computation happen (Java vs. Python).

Record each resolved item as a short decision note in `docs/decisions/`.
