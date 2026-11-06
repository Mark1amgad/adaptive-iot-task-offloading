# Experiment Reproducibility Plan

## 1. Experimental unit and factors

Use one simulation run as the basic experimental unit. A run is identified by:

- topology seed and topology fingerprint;
- workload seed / `rl.simSeed`;
- policy name;
- agent seed (for training and any stochastic policy);
- simulator time horizon;
- exact topology and RL configuration;
- code revision and runtime environment.

Separate the roles of the three random seeds:

| Seed | Controls | Current source behavior |
|---|---|---|
| `topology.seed` | Topology structure and per-device workload profile (task classes and arrival-rate profile) | `RandomTopologyGenerator` |
| `workload.seed` or fallback `rl.simSeed` | Random sensor inter-arrival realizations | Seeded sensor distributions |
| `rl.agentSeed` | Python agent RNG | Passed to `rl_model.server` |

The curriculum script sets training workload seed to `train-workload-base + topology-seed` and test workload seed to `test-workload-base + topology-seed`. It also rejects overlap between train and test topology seed sets.

## 2. Proposed scenario matrix

Do not freeze the exact ranges until the methodology and dataset assessment are approved. A practical preparation matrix is:

| Scenario family | Controlled factor | Purpose |
|---|---|---|
| Fixed reference topology | One fixed topology and fixed workload profile | Debugging, integration checks, and continuity with the existing fixed example |
| Random topology evaluation | Multiple unseen topology seeds | Test generalization across network structures and capacities |
| Workload variation | Multiple workload seeds per topology | Separate arrival randomness from topology effects |
| Network sensitivity | Explicit `-Dtopo.*` latency/bandwidth settings | Examine sensitivity to LAN/WAN conditions |
| Resource/load sensitivity | Explicit device MIPS and offered-load/pressure settings | Examine sensitivity to compute capacity and congestion |
| Simulation-horizon check | At least one longer horizon / drain check | Quantify tasks pending at cutoff and avoid biased completion metrics |

The V5 generator defaults are development ranges, not calibrated dataset values. Preserve them as the initial engineering scenario only; do not describe them as realistic or representative without evidence.

## 3. Training and test separation

1. Define training topology seeds before training.
2. Define disjoint test topology seeds before evaluation.
3. Keep model-bound topology ledger checks enabled; do not use `topology.allowOverlap=true` in normal experiments.
4. Train sequentially across the designated training topologies using the curriculum runner's model chaining.
5. Freeze the resulting model for all test runs.
6. Evaluate every policy on identical test topology/workload pairs.
7. Do not tune thresholds, reward weights, or model settings on the final test seeds.

The existing curriculum runner already implements sequential model chaining and new-topology evaluation. It also writes topology fingerprints and model topology ledgers.

## 4. Repeated runs and sample size

The current runner uses one test workload seed per test topology by default. For stronger reproducibility and uncertainty estimates, use multiple workload seeds per test topology, and multiple independent test topology seeds.

A recommended structure is:

- several training topology seeds;
- a disjoint set of test topology seeds;
- multiple workload seeds within each test topology;
- each of Local, Edge, Cloud, and the approved adaptive policy evaluated on every same topology/workload pair.

Choose the number of repetitions before examining comparative results. The repository's `aggregate.py` calculates run-level means, sample standard deviations, and 95% Student-t confidence intervals across runs. Avoid treating individual tasks within one simulation as independent experimental replications.

The current curriculum script does not expose a list of repeated workload seeds for each test topology; it computes one workload seed from the test base plus topology seed. Additional repetitions can be orchestrated with explicit runs after the training model has been produced, or added to the runner only after approval.

## 5. Controlled conditions and paired comparisons

Within each evaluation pair, hold constant:

- topology seed and fingerprint;
- workload seed / sensor arrival realization;
- simulation horizon and start configuration;
- device MIPS, RAM, bandwidth, link latency, and power model;
- task profile and deadline formula;
- application/module placement;
- all `-Dtopo.*` settings;
- Java/Python package versions and code revision.

Change only the policy. Use paired differences per topology/workload pair where possible. Report both raw per-run values and across-run statistics.

## 6. Configuration and environment capture

For every run, archive:

- exact `edge_cloud_scenario.json` used;
- all JVM `-D` properties / full command line;
- topology JSON and topology fingerprint;
- topology/workload/agent seeds;
- model file identifier/hash for frozen evaluation;
- Git commit hash or source archive hash;
- Java version, Python version, OS, and Python dependencies;
- simulation cutoff and whether GUI/headless mode was used.

The current JSONL `run_start` record stores run ID, policy, mode, phase, seeds, simulator metadata, config/reward fingerprints, and agent settings. The topology registry stores topology metadata. Preserve these logs with the results.

## 7. Output organization

Suggested directory structure:

```text
artifacts/
  experiment_<study-id>/
    config/
      edge_cloud_scenario.json
      run_manifest.json
    models/
      model_after_train_seed_*.json
    topologies/
      topology_seed*_*.json
    logs/
      run_<run-id>.jsonl
      events_<run-id>.jsonl
      topologies.jsonl
      *.stdout
      *.stderr
    results/
      per_run_metrics.csv
      aggregate_metrics.csv
      evaluation.md
      evaluation.json
```

The supplied curriculum runner currently writes models, logs, topology records, and `summary.csv` under `rl_model/artifacts/curriculum` by default. The richer `aggregate.py` output is a separate workflow and should be included in the final experiment pipeline if approved.

## 8. Statistical analysis and reporting

For each policy and metric:

1. Compute the metric for each complete run.
2. Report number of runs and total tasks separately.
3. Across runs, report mean, sample standard deviation, and 95% confidence interval.
4. For paired comparisons, compute the per-pair difference and summarize its mean and confidence interval.
5. Report missing/censored tasks and failed runs; do not silently discard them.
6. Compare physical metrics first. Reward is configuration-dependent and should be reported as a secondary composite measure unless the research objective explicitly approves it.

Potential inferential tests (paired t-test or a non-parametric paired alternative) should be selected after the final experimental unit and distribution assumptions are decided. Avoid selecting a test after inspecting which one gives the most favorable result.

## 9. Readiness checks before a full experiment

- [ ] Confirm approved methodology and final dataset/workload assumptions.
- [ ] Confirm metric definitions, especially E2E latency and cutoff handling.
- [ ] Confirm whether energy and utilization are primary metrics and define their semantics.
- [ ] Confirm baseline set and whether a separate static rule is required.
- [ ] Set training and test seed sets in advance.
- [ ] Set epsilon decay from the actual number of training decisions across the curriculum. The supplied scenario config currently has `epsilon_decay_steps = 8000`; the curriculum guide itself warns that this can be consumed in the first topology.
- [ ] Run a short smoke test, then a full dry-run command review.
- [ ] Verify no train/test topology overlap and no model-ledger refusal.
- [ ] Verify task accounting reconciles: generated = completed + pending/undecided (with any explicitly failed outcomes accounted for).
- [ ] Run aggregation and check that all policies used the same test pairs.
- [ ] Preserve the run manifest, source revision, and raw logs.

## 10. Constraints respected

This plan does not implement the final adaptive algorithm, modify/generate the final dataset, or change simulator code. Any implementation change should first be proposed with its rationale and approved.
