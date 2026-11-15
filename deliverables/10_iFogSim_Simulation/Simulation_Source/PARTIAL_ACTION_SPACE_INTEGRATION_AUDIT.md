# Partial Action-Space Integration Audit

Date: 2026-11-15  
Branch: `work/multi-task-lifecycle`  
Status: source audit and migration design only; no RL protocol/action/model files changed.

## Executive finding

The multi-task Local+Edge fixture proves that multiple split tasks can independently execute two branches, wait at per-task barriers, and complete real merge Cloudlets. It is **not yet an action the RL agent can select**.

The workload generator already defines a more specific legal action contract than the current RL model. The current implementation and the workload contract must be reconciled before changing the agent.

## 1. Current RL implementation (verified source)

- `actions.py` defines exactly three actions: `Local=0`, `Edge=1`, `Cloud=2`.
- `QLearningAgent` allocates Q and visit tables with `N_ACTIONS=3`; all action selection, random baselines, greedy policy and updates use this dimension.
- `persistence.py` stores the exact action-name list and validates both action-name equality and Q-table shape. A nine-action model cannot load the existing three-action model.
- `protocol.py` validates outcome `action_executed` through the three-name action map. Protocol version is 1.0.
- Observation schema permits only Local/Edge/Cloud names or IDs 0/1/2 in `available_actions`.
- Action schema permits only action IDs 0/1/2 and Local/Edge/Cloud strings.
- `server.py` baseline policy supports local/edge/cloud/random only.
- Frozen-agent fallback order is constrained to a permutation of Local/Edge/Cloud.
- Current state has four enabled features: `task_mi`, `wan_latency_ms`, `edge_utilization`, `deadline_ms`. With 3×3×3×2 bins, the current tabular state space has 54 states.
- The Java full-placement adapter maps one action to one executor module. It cannot interpret an action that requires two execution branches and a merge.

## 2. Existing workload action contract (from team-work/Astta-Abdo)

The workload specification explicitly distinguishes task divisibility:

- `INDIVISIBLE`: Local, Edge full, Cloud full only.
- `DATA_PARALLEL_DIVISIBLE`: Local and one remote tier (Edge **or** Cloud); both remote tiers are never used for one task.

Its candidate actions are:

| Action | Remote compute fraction `alpha` | Local compute fraction | Remote tier |
|---|---:|---:|---|
| `LOCAL` | 0.00 | 1.00 | none |
| `EDGE_PARTIAL_25` | 0.25 | 0.75 | Edge |
| `EDGE_PARTIAL_50` | 0.50 | 0.50 | Edge |
| `EDGE_PARTIAL_75` | 0.75 | 0.25 | Edge |
| `EDGE_FULL` | 1.00 | 0.00 | Edge |
| `CLOUD_PARTIAL_25` | 0.25 | 0.75 | Cloud |
| `CLOUD_PARTIAL_50` | 0.50 | 0.50 | Cloud |
| `CLOUD_PARTIAL_75` | 0.75 | 0.25 | Cloud |
| `CLOUD_FULL` | 1.00 | 0.00 | Cloud |

For partial actions, the spec defines `local_required_mi=(1-alpha)*required_mi` and `remote_required_mi=alpha*required_mi`. The named divisible profiles declare proportional input/output partition models, partition-model IDs, and partition/merge overhead assumptions. Those are synthetic profile-specific assumptions, not universal divisibility rules.

## 3. Mismatch with the current simulator fixture

The current `MultiTaskPartialOffloadingSpike` fixture uses:
- fixed 40% Local / 60% Edge;
- Local+Edge only;
- fixed MI and byte totals;
- a 1,200 MI merge Cloudlet;
- no task-profile input or partition-model ID;
- no partition/merge overhead from the workload record;
- no Local+Cloud partial option;
- no RL action, action mask, or decision/outcome protocol.

Therefore the 40/60 fixture is **mechanism-feasibility evidence only**. It must not be relabelled as `EDGE_PARTIAL_50` or used as an evaluation of the workload spec's 25/50/75 candidate actions.

## 4. Required action/protocol migration

If the nine-action contract is approved, implement it as one versioned change across Python, schemas, Java, and model persistence. Do not extend only `actions.py`.

1. **Action IDs/names:** define the exact nine stable actions and IDs in one canonical mapping. Update Q-table dimensions, action masks, random baseline, greedy selection, fallback order, policy-table export, and tests.
2. **Protocol:** move to protocol 2.0 (or another explicitly versioned compatible contract). Update observation/action/outcome schemas and Java validation together. Action response must return the exact action name and ID.
3. **Legality:** derive the observation mask from task `splittability`, declared `partition_model_id`, and currently feasible Local/remote tiers. An indivisible task must never receive a partial candidate.
4. **Observation features:** current state does not expose Local or Cloud utilization, splittability, or partition/merge overhead. Before training a contextual bandit over nine actions, specify which of these are state features and calibrate their thresholds. The mask alone prevents illegal choices but does not give the Q-table context about the task's split semantics.
5. **Execution adapter:** decode partial action into remote tier and `alpha`; create Local and one remote branch; apply the task's declared input/output partition models; apply partition overhead; correlate each branch by actual tuple ID; wait for both results; apply merge overhead and run one merge Cloudlet; produce one task-level outcome.
6. **Outcome semantics:** `action_executed` must remain the selected compound action (e.g. `EDGE_PARTIAL_50`), not be inferred from one branch's module. Per-task metrics must aggregate both branches, network transfers, partition/merge costs, and the final joined latency.
7. **Failure semantics:** specify what happens if either branch fails, misses the horizon, or cannot be dispatched. No merge or success outcome may be fabricated.
8. **Persistence:** old three-action models must be rejected as incompatible. Retrain a fresh nine-action model under the new state/action fingerprints; do not silently pad or remap old Q columns.

## 5. State-space warning

The current 54-state table is based on four features and is already using placeholder thresholds for some features. Adding Local/Cloud utilization, splittability, and partition/merge overhead can multiply the state count. The exact feature set and bins must be justified and kept small enough for the available training episodes. More actions and more state bins do not automatically produce a better policy; with sparse visits, they can make the Q-table less learnable.

A reasonable first candidate for discussion is to add:
- Local utilization;
- Cloud utilization;
- a binary splittability indicator;
- partition overhead;
- merge overhead;

while retaining current task MI, WAN latency, Edge utilization, and deadline. This would create a much larger tabular state space, so thresholds should not be chosen until simulator measurements and workload distributions are available. It is a candidate, not an approved configuration.

## 6. Integration sequence

1. Keep current three-action full-placement integration and its accepted evidence unchanged.
2. Keep the multi-task Local+Edge 40/60 fixture as a separate mechanics test.
3. Complete a mixed full/partial simulator run using task-profile-driven legal modes, but do not connect the learner yet.
4. Approve the nine-action contract, action IDs, state features, and fallback order.
5. Implement protocol/model versioning and Python unit tests; verify old model rejection and fresh model save/load.
6. Extend the Java adapter to Local/Edge/Cloud full and Local+Edge/Local+Cloud partial routes, including 25/50/75 ratios and per-task merge lifecycle.
7. Run legality tests for indivisible/divisible tasks, repeated deterministic traces, mixed full/partial tasks, and failure cases.
8. Only then run training and paired evaluation using identical workload seeds for all policies.

## 7. Explicit blockers

- The workload profile config is marked `PROPOSED_UNTIL_MARK_APPROVAL`; its action ratios, task mixes, and overhead values must not be treated as approved benchmark settings.
- The target 4 IoT / 2 Edge / 1 Cloud topology is still not implemented or verified in the current simulator.
- Bandwidth physical units remain unresolved.
- Local/Cloud utilization observation hooks and calibrated thresholds remain unresolved.
- Merge data construction/serialization and branch failure semantics remain unmodeled.

No source changes to the Python RL action space or protocol were made during this audit.
