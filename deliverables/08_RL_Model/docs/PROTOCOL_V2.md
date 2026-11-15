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

The v2 config contains nine state features:
1. task MI
2. input payload bytes
3. output payload bytes
4. WAN latency
5. Local utilization
6. Edge utilization
7. Cloud utilization
8. deadline
9. splittability (binary)

With the current provisional bins, the nine features produce 13,122 states and 118,098 Q values across nine actions. Payload-size bins are initial workload-profile boundaries, not calibrated simulator facts. The Local/Cloud utilization and splittability thresholds remain provisional.

Partition and merge overheads are carried as task constraints and execution metadata, not currently discretized into the Q state. The learner therefore cannot distinguish two otherwise identical observations with different partition/merge overheads. This remains a known modeling limitation; test overhead-aware state features in a controlled ablation after calibration. Input and output payload sizes are state features. Deadline thresholds at 180 and 400 ms align with the current generator's critical/high/normal deadline ranges, so urgency is represented through deadline bins rather than a separate urgency feature; recalibrate this mapping for real workload distributions.

## Baseline behavior

- `local`: LOCAL
- `edge`: EDGE_FULL
- `cloud`: CLOUD_FULL
- `random`: uniform random over the feasible mask
- `local`, `edge_partial_25`, `edge_partial_50`, `edge_partial_75`, `edge_full`, `cloud_partial_25`, `cloud_partial_50`, `cloud_partial_75`, `cloud_full`: exact-action baselines for deterministic coverage of each catalogue entry

A fixed baseline errors if its action is infeasible; it does not silently switch to another placement. Exact-action baselines are used for executor acceptance, not as learned-policy performance comparisons.

## iFogSim integration status (2026-11-15)

Two separate end-to-end vertical slices now exist:

1. **Full-placement training acceptance:** an indivisible-task experiment uses the exact mask `[LOCAL, EDGE_FULL, CLOUD_FULL]`, validates the Python response, routes to the corresponding worker, and returns measured outcomes. See [V2_FULL_PLACEMENT_ACCEPTANCE.md](../../10_iFogSim_Simulation/Simulation_Source/V2_FULL_PLACEMENT_ACCEPTANCE.md).
2. **All-nine-action execution acceptance:** a divisible-task experiment runs all nine exact-action baselines through the live Python v2 server and iFogSim. It executes Local+Edge and Local+Cloud branches at 25/50/75, per-task barriers, merge Cloudlets, partition/merge delays, task outcomes, and watchdog-based failed-outcome reconciliation. The 18-task exact-action suite passed, followed by a 30-task training run with 30 measured-outcome updates and a saved model. See [V2_PARTIAL_EXECUTION_ACCEPTANCE.md](../../10_iFogSim_Simulation/Simulation_Source/V2_PARTIAL_EXECUTION_ACCEPTANCE.md).

The simulator reports a task as failed if a required branch does not return before the watchdog horizon; it never fabricates a successful merge. Python acknowledges failed outcomes and shutdown verifies zero orphaned tasks.

These are **integration/lifecycle acceptance tests**, not performance benchmarks. Exact-action baselines establish action-path coverage but do not establish policy convergence, generalization, or RL superiority. The current topology is Local → Edge → Cloud. Partition/merge overhead parameters remain provisional, and energy is not measured.


## Variable workload support (2026-11-15)

The iFogSim v2 runner now accepts a deterministic JSONL workload via `--workload`. Each task supplies its own compute MI, input/output payload bytes, deadline, urgency class, splittability, partition model, merge MI, and arrival gap. The generator and its field distributions are documented in [V2_VARIABLE_WORKLOAD_ACCEPTANCE.md](../../10_iFogSim_Simulation/Simulation_Source/V2_VARIABLE_WORKLOAD_ACCEPTANCE.md).

The observation state now includes `input_bytes` and `output_bytes`; the resulting provisional state space is 13,122 states and 118,098 Q values over nine actions. Optional `task_constraints.urgency_class` accepts `critical`, `high`, or `normal` and is retained for trace/analysis. The learner represents urgency through deadline bins (180/400 ms), aligned to the generator's critical/high/normal deadline ranges; urgency is not a separate feature.

The Java runner supports `train`, frozen `eval` with `--model-in`, and `baseline` with `--policy local|edge|cloud|random`. `run_v2_policy_comparison.ps1` replays one immutable workload file across these policies and produces paired per-task latency differences. A 60-task seed-42 training run and three 60-task held-out comparisons (seeds 43–45; 180 tasks total) passed; results and limitations are recorded in [V2_VARIABLE_WORKLOAD_ACCEPTANCE.md](../../10_iFogSim_Simulation/Simulation_Source/V2_VARIABLE_WORKLOAD_ACCEPTANCE.md). These are descriptive results from three held-out workload seeds but one training seed, not statistical proof of policy superiority.
