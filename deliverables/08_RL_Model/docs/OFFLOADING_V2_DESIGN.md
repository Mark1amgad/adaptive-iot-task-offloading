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
