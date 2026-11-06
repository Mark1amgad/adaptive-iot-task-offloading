# Baseline Strategies

**Purpose:** document the baseline set that can be compared fairly with the learned policy. This is a preparation document only; it does not select or finalize the research objective or adaptive algorithm.

## 1. Baselines already supported

The Python server's `baseline` mode accepts `local`, `edge`, and `cloud`. Java supplies an `available_actions` mask and the server selects the requested fixed action. The random-topology scenario maps the `processing` module to every device, so all three targets are normally available in the generated topology.

| Strategy | Policy rule | Current implementation | Notes |
|---|---|---|---|
| Local-only | Execute every task at its originating IoT device | `--mode baseline --policy local` | No offloading; local execution still uses the normal iFogSim processing path |
| Edge-only | Forward every task to its parent Edge | `--mode baseline --policy edge` | Uses the normal IoT→Edge link path |
| Cloud-only | Forward every task to the Cloud/top device | `--mode baseline --policy cloud` | Uses hop-by-hop forwarding through the Edge in the current random tree |
| Static offloading | One fixed, predeclared rule that does not adapt from task-by-task observations | Not implemented as a separate policy | Needs a precise rule and rationale before implementation |
| Adaptive policy | Select among Local/Edge/Cloud based on state | Existing Q-learning `eval` mode is present | The final adaptive design is explicitly pending approval; do not treat this document as approval |

## 2. How each run should be launched

The supplied `tools/run_topology_curriculum.py` already runs:

1. Sequential training over the requested topology seeds, carrying the model forward.
2. Frozen agent evaluation on each test topology.
3. Local, Edge, and Cloud baseline runs on the same test topology and workload seed.

The current defaults are `--baselines local,edge,cloud` and `--jobs 2`. The runner passes the same test `topology.seed` and `rl.simSeed` to the agent and all three baselines for each test topology. This is the correct paired-condition structure to preserve.

The runner does **not** currently create a separate nontrivial static threshold baseline. It also produces a compact reward/latency/deadline summary rather than calling the full `rl_model.aggregate` report.

## 3. Fair-comparison protocol

For each evaluation case, all policies must receive:

- The exact same topology structure (same `topology.seed`, ideally verify the same topology fingerprint).
- The same workload profile and arrival realization (`workload.seed` / `rl.simSeed`).
- The same simulation cutoff (`sim.time`) and all `-Dtopo.*` parameters.
- The same application, module placement, device capacities, link bandwidths, and propagation latencies.
- The same deadline formula and same outcome/censoring rules.
- The same logging and metric extraction version.

Only the policy should differ. The learned agent must be in frozen evaluation mode; no learning updates should occur during the test runs.

For random topologies, compare policies within each topology/workload pair first, then aggregate the paired differences across repeated runs. Do not compare an agent run on one workload seed with a baseline run on another and describe it as a controlled comparison.

## 4. Static offloading: decision required before implementation

“Static offloading” is ambiguous. Possible meanings include:

- **Single-tier static:** always use one tier. This duplicates Local-only, Edge-only, or Cloud-only.
- **Static threshold rule:** e.g., a fixed task-size or WAN-latency threshold routes tasks to a predetermined tier. This is a new baseline and requires a documented rule.
- **Static weighted rule:** a fixed cost/latency calculation selects a tier using fixed weights. This is also a new algorithm and requires approved inputs and weights.

Recommendation for preparation: keep the three implemented single-tier baselines as the minimum baseline set. Ask the supervisor/team to define whether “static offloading” means an additional rule-based baseline or simply refers to fixed Local/Edge/Cloud policies. Do not invent a threshold or weight.

## 5. Reporting

Report physical metrics separately from the RL reward. The reward depends on configurable weights and normalization and should not be the only basis for claiming that one policy is better.

At minimum, provide one row per policy and evaluation run with topology seed, workload seed, task count, completion rate, latency (with its definition), deadline violation rate, energy (if available), utilization (with its definition), and bandwidth. Across repeated runs, report mean, sample standard deviation, and confidence interval.

No baseline code was added or changed.
