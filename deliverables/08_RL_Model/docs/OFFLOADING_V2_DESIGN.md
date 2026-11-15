# Offloading Action Space v2: Feasibility and Analytical Cost Model

## Decision

The proposed nine-action catalogue is retained as a candidate v2 action space, but it is not wired into protocol v1 or the existing three-column Q-table. The new implementation lives in `src/rl_model/offloading.py` so existing models and simulator contracts remain loadable until the coordinated migration is complete.

## Stable action catalogue

| ID | Action | Remote fraction | Local fraction |
|---:|---|---:|---:|
| 0 | LOCAL | 0.00 | 1.00 |
| 1 | EDGE_PARTIAL_25 | 0.25 | 0.75 |
| 2 | EDGE_PARTIAL_50 | 0.50 | 0.50 |
| 3 | EDGE_PARTIAL_75 | 0.75 | 0.25 |
| 4 | EDGE_FULL | 1.00 | 0.00 |
| 5 | CLOUD_PARTIAL_25 | 0.25 | 0.75 |
| 6 | CLOUD_PARTIAL_50 | 0.50 | 0.50 |
| 7 | CLOUD_PARTIAL_75 | 0.75 | 0.25 |
| 8 | CLOUD_FULL | 1.00 | 0.00 |

The remote fraction is the fraction of compute demand assigned to the remote branch. Partial actions use Local plus exactly one remote tier. Edge and Cloud are alternatives, not a two-hop chain.

## Feasibility masking

- `LOCAL` is legal only when the source device can execute the task.
- Edge full/partial actions are legal only when an Edge tier is available.
- Cloud full/partial actions are legal only when a Cloud tier is available.
- Partial actions additionally require `splittability=DATA_PARALLEL_DIVISIBLE` and a non-empty `partition_model_id`.
- An indivisible task receives only feasible full-placement actions.
- If no action is feasible, the request must fail explicitly; it must not silently fall back to an unavailable executor.

This mask is task- and topology-dependent. It is not learned by Q-learning; the agent learns among actions that the execution contract has already declared feasible.

## Analytical completion-time estimator

For full Local:

`T_local = MI / MIPS_local * 1000` ms.

For full remote placement:

`T_remote = T_up(input) + L_up + MI / MIPS_remote * 1000 + T_down(output) + L_down`.

For partial placement with remote compute fraction `alpha`:

`T_local_branch = (1-alpha) * MI / MIPS_local * 1000`

`T_remote_branch = T_up(alpha * input) + L_up + alpha * MI / MIPS_remote * 1000 + T_down(alpha * output) + L_down`

`T_partial = max(T_local_branch, T_remote_branch) + T_partition + T_merge`.

Bandwidth is interpreted as decimal Mbps. Byte volumes are proportional to compute fraction only for workload profiles whose declared partition model explicitly guarantees that assumption. The estimator rejects partial actions without divisible semantics and a partition model identifier.

## Explicit model limitations

The estimator is an analytical baseline and debugging aid, not a replacement for CloudSim execution. It currently omits queueing, contention, shared-link interference, CPU scheduling, cache effects, energy, failures/cancellation, data-dependent partition imbalance, and semantic merge cost. It also assumes the two branches run concurrently. The simulator's measured task completion time remains the source of truth for training reward and reported evaluation.

The synthetic partition/merge overhead values in the workload YAML remain proposed assumptions; this implementation accepts overheads as explicit inputs and does not approve or calibrate those values.

## Migration boundary

Protocol v1 and its legacy three-action Q-table are unchanged. A coordinated v2 migration must update, together:
1. protocol version and JSON schemas;
2. action IDs/names and action mask validation;
3. Q/visit table dimensions and model format version;
4. fallback and random baselines;
5. Java action decoding and compound execution lifecycle;
6. action-executed outcome reporting and failure semantics;
7. tests proving old models are rejected, not remapped.

The existing three-action model must not be padded, truncated, or silently reused.


## Implemented v2 engine boundary (2026-11-15)

The nine-action catalogue now has an isolated v2 learner, strict JSONL protocol parser, model persistence, configuration loader, and server entrypoint. See [PROTOCOL_V2.md](PROTOCOL_V2.md).

The v2 state configuration now uses nine features and 13,122 provisional states:
- task MI, input bytes, output bytes, WAN latency, Local utilization, Edge utilization, Cloud utilization, deadline, splittability
- 9 actions × 13,122 states = 118,098 Q-values

Payload-size, Local/Cloud utilization, and splittability bins are provisional. The deadline thresholds (180 and 400 ms) currently align with the generator's critical/high/normal deadline ranges; urgency class remains trace metadata rather than a separate feature. Partition/merge overheads are passed as task constraints and are not yet Q-state features. This is a deliberate sparsity trade-off, not a claim that overhead variation is irrelevant.

The v2 parser independently derives the feasible action mask from task constraints and checks that the simulator-advertised mask matches exactly. It also checks that the numeric splittability state feature agrees with the categorical workload declaration.

**Integration status (2026-11-15):** The Java/iFogSim v2 integration now has two accepted vertical slices. The full-placement experiment connects indivisible tasks to the live Python service. The partial executor connects divisible tasks to all nine actions, creates Local+Edge or Local+Cloud branches at 25/50/75, enforces per-task result barriers, executes merge Cloudlets, accounts for provisional partition/merge delays, and reports compound-action outcomes. A watchdog sends failed outcomes when required branch results do not arrive; the failure injection test verified zero orphaned Python tasks and a non-zero simulator acceptance result. See [V2_PARTIAL_EXECUTION_ACCEPTANCE.md](../../10_iFogSim_Simulation/Simulation_Source/V2_PARTIAL_EXECUTION_ACCEPTANCE.md).

These tests prove action-path and lifecycle integration, not benchmark performance, policy convergence, generalization, or RL superiority. The 3 ms partition and 2 ms merge overheads are provisional; the current topology remains Local → Edge → Cloud, and energy is not measured.


## Variable workload milestone (2026-11-15)

The iFogSim runner now consumes seeded per-task JSONL workload rows, including variable MI, input/output sizes, deadlines, urgency, splittability, and arrival gaps. Payload sizes are part of the nine-feature v2 state (13,122 states; 118,098 Q values). The same output-profile-aware AppEdges are carried by one worker module per action/tier, avoiding extra device-side module instances. A seed-42 training run (60 tasks) and three paired holdout comparisons on seeds 43/44/45 (180 tasks total) across Local/Edge/Cloud/Random/frozen Q-table/fallback hybrid passed. See [V2_VARIABLE_WORKLOAD_ACCEPTANCE.md](../../10_iFogSim_Simulation/Simulation_Source/V2_VARIABLE_WORKLOAD_ACCEPTANCE.md). The results are descriptive across three held-out seeds but use only one training seed; they are not evidence of statistical superiority. The seed-42 model updated only 60/118,098 state-action cells, visited 45 states, and used the `EDGE_FULL` fallback for 108/180 held-out decisions; therefore the evaluated policy is fallback/greedy hybrid, not a converged RL policy.
