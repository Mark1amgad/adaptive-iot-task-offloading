# 2. State, reward and decision model

All values below live in `config/default.json`; the code reads them, nothing is hard-coded.

## 2.1 State (exactly **54** states with the default config)

State count = ∏ (number of bins per enabled feature) = 3 × 3 × 3 × 2 = **54** — computed by `StateSpace.n_states`, asserted in tests, and printed in `hello_ack`. It happens to equal the earlier number, but it is derived, and changes automatically (e.g. enabling `device_utilization` → 162).

Bin rule: with thresholds t0 < t1 < …, `bin = #thresholds ≤ value`, i.e. `[min,t0)→0, [t0,t1)→1, …, [t_last,max]→last`. Index = mixed-radix over features in config order (same order as `itertools.product`).

| Feature | Unit | Thresholds → bins | Source (to confirm with Java dev) | Measured when | Threshold status |
|---|---|---|---|---|---|
| `task_mi` | MI (million instructions) | 1000, 4000 → small / medium / large | task's computational length | at task creation, before the decision | **placeholder** — calibrate from workload (e.g. terciles of the real distribution) |
| `wan_latency_ms` | ms | 20, 80 → low / medium / high | latency of the path to the Cloud (configured or recently measured) | latest value known at decision time | from design note (80 ms belongs to *high*) |
| `edge_utilization` | fraction 0..1 | 0.4, 0.8 → low / medium / high | utilisation of the edge node that would run the task | sampled at decision time, before placement | from design note |
| `deadline_ms` | ms, relative to creation | 500 → tight / relaxed | per-task deadline from the workload | at task creation | **placeholder** |
| `device_utilization` (**disabled**) | fraction 0..1 | 0.5, 0.85 | originating IoT device CPU | decision time | placeholder; enable if Local execution cost depends on device load |

Why these four: task size and deadline determine feasibility; WAN latency penalises Cloud; edge utilisation penalises Edge. Local's behaviour depends on the device, which is why `device_utilization` is offered but off by default (state-space growth vs. information; team decision). "Network load" from the design note is not included: it is not separately defined and WAN latency is the network signal assumed available; revisit if Java can supply link load.

Leakage rule: an observation may contain **only** these features. Unknown keys (e.g. `latency_ms`, `deadline_met`) make the observation invalid. Outcomes use a different message type.

## 2.2 Reward

```
reward = −( w_latency · L  +  w_deadline · M  +  w_cost · C )          ≤ 0
```
* **L** (normalised latency) = `min(latency_ms / ref, latency_clip)`; `ref = latency_ref_ms` (mode `fixed`) or the task's `deadline_ms` (mode `deadline`). Defaults: ref 1000 ms (**placeholder**), clip 1.
* **M** = 1 if `deadline_met` is false or the task failed, else 0. `deadline_met` is Java's flag; a warning is logged if it contradicts `latency_ms` vs `deadline_ms`.
* **C** (explicit resource cost) = Σ wₖ·min(metricₖ/refₖ, 1) / Σ wₖ over the configured `cost_terms` (metrics from `outcome.resource_metrics`): default `bandwidth_bytes` (ref 1e6, required) and `energy_joules` (ref 10, optional); both refs are **placeholders**. A missing optional metric contributes 0; a missing required metric on a completed task rejects the outcome (nothing is learned).
* Weights default 1 / 2 / 0.5 (carried over from the prototype).
* **Failures**: `L = latency_clip`, `M = 1`, plus optional `failure_penalty` (default 0); C uses whatever metrics were reported (missing → 0).
* Bounds: `min_reward = −(w_latency·clip + w_deadline + w_cost + failure_penalty)`; property-tested.
* Computed only from the outcome message (and the stored deadline for `deadline` mode). Never from the observation alone.

## 2.3 Decision model: contextual bandit by default (not an MDP)

*Assumption, unverified against iFogSim.* Each offloading decision is made when a task arrives; the next observation is the *next, different task* arriving at an exogenous time, and several tasks are typically in flight when decisions overlap, so the outcome of action *a* for task *t* often arrives after later decisions were made. The action affects the next state only weakly (via edge queueing), with no well-defined `s'` timing. Forcing `s'` = "next arrival" would make the bootstrapped target ill-defined. Therefore the default is `decision_model = "contextual_bandit"`: γ must be 0 (config validation enforces it), every transition is terminal, and the update is `Q(s,a) += α(r − Q(s,a))`.

The agent fully supports the general rule: set `decision_model = "sequential"`, `gamma > 0`, and have Java send `terminal=false` with a `next_observation` whenever it can define a proper next decision point (e.g. one task in flight at a time, or a defined per-task episode). Whether the simulation supports that is a **Java-developer decision** (see JAVA_QUESTIONNAIRE Q9).

## 2.4 Agent behaviour summary
* Training: ε-greedy (ε linear 0.3 → 0.02 over 16000 *training decisions*, persisted so resumed runs continue the schedule), ties among best actions broken randomly with the seeded RNG; exploration uniform over *allowed* actions.
* Evaluation: frozen, ε = 0, no updates (`FrozenAgentError`), deterministic. Only actions with ≥ 1 real update are candidates; an unvisited state uses `fallback_order` (default Edge, Cloud, Local) and is reported as `mode="fallback"` so it is visible in logs. *Assumption* — change the order in config.
* Action mask: `available_actions` in the observation (e.g. Edge down); masked actions are never chosen or used in the `max` of a bootstrapped target.
