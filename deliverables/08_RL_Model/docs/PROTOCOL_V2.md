# Protocol v2.0 — Nine-Action Feasibility-Masked Offloading

## Compatibility boundary

Protocol v1.0 and its three-action model remain unchanged. The v2 implementation is isolated in:
- `src/rl_model/protocol_v2.py`
- `src/rl_model/agent_v2.py`
- `src/rl_model/persistence_v2.py`
- `src/rl_model/config_v2.py`
- `src/rl_model/server_v2.py`

Run v2 from `deliverables/08_RL_Model`:

```powershell
python -m rl_model.server_v2 --mode train --config config/v2.json --model-out artifacts/model_v2.json
python -m rl_model.server_v2 --mode eval --config config/v2.json --model-in artifacts/model_v2.json
```

A v1 message is rejected by v2. A v1 saved model is rejected by the v2 model loader. There is no padding, truncation, or action-index remapping.

## Observation: Java → Python

Every observation includes:
- protocol version `2.0`
- unique `task_id`
- exactly the configured pre-decision numeric features
- `available_actions`
- `task_constraints`

The task constraints must include:
- `splittability`: `INDIVISIBLE` or `DATA_PARALLEL_DIVISIBLE`
- `local_available`, `edge_available`, `cloud_available`: booleans

For a divisible task, the message must also include:
- non-empty `partition_model_id`
- `partition_overhead_ms`
- `merge_overhead_ms`

Python independently derives the expected legal action IDs from the constraints and rejects an observation if Java's advertised mask differs. Partial actions require a divisible task, a partition model, and Local availability. This prevents a malformed or stale mask from reaching the learner.

The numeric `features.splittability` is 0 for indivisible and 1 for divisible; it must agree with the categorical task constraint.

## Action: Python → Java

The action response contains both a stable ID and explicit execution semantics:
- `action_id` and `action`
- `remote_tier` (`EDGE`, `CLOUD`, or null)
- `remote_fraction`
- `local_fraction`
- model version, decision mode, and epsilon

Java must validate all fields and execute the compound action from these values. It must not infer a partial action from a single worker module or silently replace the selected action.

## Outcome: Java → Python

The outcome reports the actual action executed, task status, measured latency, deadline result, and resource metrics. Python rejects an outcome if its executed action was not in that task's feasible mask. Training updates the Q-value for the action actually executed, not merely the action requested.

The v2 server currently uses the same measured-outcome reward function as v1. It is a contextual-bandit update (one-step reward; no bootstrapping). Partial branch failure must be represented as a failed task outcome; Java must not report a merged success if either required branch failed.

## State design

The proposed v2 config contains seven features:
1. task MI
2. WAN latency
3. Local utilization
4. Edge utilization
5. Cloud utilization
6. deadline
7. splittability (binary)

With the current provisional bins this produces 972 states and 8,748 Q values. The new Local/Cloud utilization and splittability thresholds are placeholders, not calibrated simulator facts.

Partition and merge overheads are carried as task constraints and execution metadata, not currently discretized into the Q state. This avoids increasing the state space to 8,748 states before we have enough training samples. It also means the learner cannot distinguish two tasks with identical current state features but different partition/merge overheads. This is a known modeling limitation; if overhead heterogeneity proves decision-relevant, test one combined overhead feature in a controlled ablation after calibration.

## Baseline behavior

- `local`: LOCAL
- `edge`: EDGE_FULL
- `cloud`: CLOUD_FULL
- `random`: uniform random over the feasible mask

A fixed baseline errors if its action is infeasible; it does not silently switch to another placement. This is intentional for fair baseline accounting.

## Current scope and blockers

The Python v2 engine and protocol are implemented and tested in isolation. The iFogSim Java adapter is not yet migrated to protocol v2 and does not yet produce these observations or execute all nine actions. Until that adapter and end-to-end acceptance tests exist, v2 is not an integrated simulator result and must not be used for performance claims.
