# Workload / Network / Capacity Replay Matrix

This file defines input-generation and pairing rules only. It does not declare any scenario simulator-validated.

| Replay experiment | Workload task CSV | Network config/trace | Edge capacity config/trace | Expected invariant |
|---|---|---|---|---|
| Workload-only A→B→A | A1, B, A2 task streams differ by registered workload shift; A1/A2 exact task replay per current contract | Identical fixed network input across A/B/A | Identical fixed Edge capacity input across A/B/A | Network and Edge capacity byte-identical; A1/A2 task attributes + exogenous conditions replay exactly |
| Network-only A→B→A | Exact same task file for A1/B/A2 | A→B→A network profile changes | Identical fixed Edge capacity input | All task fields byte-identical across A/B/A; only network config/trace changes |
| Edge-capacity-only A→B→A | Exact same task file for A1/B/A2 | Identical fixed network input | A→B→A Edge capacity profile changes | All task fields byte-identical; network config byte-identical |
| Combined shift (separate experiment) | Explicit combined workload schedule only if declared in its own manifest | Network changes | Edge capacity changes | Label combined; do not use it to infer single-factor effects |

## Existing Generator V1.2 replay boundary

The checked-in eight Development scenario set includes stable_steady, bursty_on_off, reduced_bandwidth, increased_wan_delay, reduced_edge_capacity, task_size_compute_shift, repeated_a_b_a, and repeated_aba_task_mix. The current `repeated_a_b_a` manifest identifies a bandwidth A/B/A condition schedule and its task CSV; `repeated_aba_task_mix` is a separate workload-mix replay. Preserve their current files and seed registry allocations. Do not reinterpret or regenerate them to simulate the four-factor replay matrix above.

## Pairing protocol

- Every policy/action comparison consumes the exact same task file and same exogenous trace/config for that experiment.
- Record SHA-256 for the exact task CSV, manifest CSV, network config/trace, capacity config/trace, simulator config, and simulator commit.
- A network-only comparison is invalid if any task input field differs.
- A workload-only comparison is invalid if any network or Edge-capacity input differs.
- Keep the combined-shift run separate from the one-factor runs.
- Do not expose future regime labels/boundaries to the policy observation.
