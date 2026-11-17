# V2 Variable Workload and Paired Policy Evaluation

**Date:** 2026-11-15
**Status:** PASS — 60-task mixed workload integration and three 60-task held-out paired policy comparisons completed (180 evaluation tasks).

## Why this stage exists

The earlier acceptance fixtures proved that the nine actions could execute, but used one fixed task profile. That is insufficient for evaluating an adaptive offloading policy. This stage adds deterministic workload generation, per-task task properties, typed output-size profiles in iFogSim, and policy replay over an identical workload file.

## Workload generator

Script: `generate_workload_v2.py`

Example:

```powershell
python generate_workload_v2.py --seed 42 --tasks 60 --profile mixed --output workload_seed42.jsonl
```

Supported profiles: `mixed`, `divisible`, `indivisible`. The mixed profile samples approximately 70% divisible tasks and 30% indivisible tasks. Every row is JSONL and includes a contiguous sequence number, source seed, and profile name.

| Field | Generator behavior |
|---|---|
| Compute demand | Uniform integer 1,000–30,000 MI |
| Input bytes | Uniform integer 1,024–262,144 bytes |
| Output bytes | Categorical profile: 512, 2,048, or 8,192 bytes |
| Deadline / urgency | Critical: 90–180 ms; High: 180–400 ms; Normal: 400–1,000 ms |
| Splittability | Mixed profile: approximately 70% divisible, remainder indivisible |
| Merge compute | 4–12% of task MI for divisible tasks; zero for indivisible tasks |
| Arrival gap | First task 0 ms; subsequent gaps uniform 1–20 ms |

The generator uses a local seeded PRNG. Re-running the same seed, task count, and profile produces byte-for-byte equivalent workload rows.

### Important modeling boundary

`data-parallel-v1` still assumes input bytes and output bytes are partitioned in proportion to the compute fraction. The simulator now supports variable input and output sizes, but this proportional partition model is a workload assumption, not a universal property of applications. A later calibration stage must use workload-specific partition semantics and measured merge costs.

`urgency_class` is preserved in the workload and trace metadata, but is not a separate learner feature. The deadline state bins use thresholds at 180 and 400 ms, aligned to the generator's critical/high/normal deadline ranges. This lets the learner distinguish the three generated urgency bands through `deadline_ms`; the thresholds still require recalibration for real workloads.

## iFogSim execution changes

- Task MI, input bytes, output bytes, deadline, urgency, splittability, partition model, merge MI, and arrival gap are now read per task from the JSONL workload.
- Feasibility masks are recomputed per task. Indivisible tasks cannot select partial actions; divisible tasks may select any feasible action.
- Input and output payload sizes are now state features. The state space is 13,122 states, nine actions, and 118,098 Q-values. Existing models with the previous 972-state fingerprint are incompatible and must be retrained.
- Output payload classes use multiple typed AppEdges on one worker module. This preserves the original Local/Edge/Cloud device capacities and avoids multiplying VM/module instances for every output size.
- The Java trace records the typed input tuple used for each worker so the validator can check that the selected AppEdge matches the task's output profile. Local, Edge, and Cloud utilization features now come from each device's observed utilization snapshot at decision time rather than fixed Edge/Cloud constants.
- The runner supports `train`, frozen `eval`, and fixed/random `baseline` modes.

## Integration acceptance: training workload

Run artifact: `audit_output/v2_workload_seed42_20261115_2120`

| Item | Result |
|---|---:|
| Seed / tasks | 42 / 60 |
| Divisible / indivisible | Both present |
| Output profiles | 512, 2,048, 8,192 bytes |
| Urgency classes | Critical, High, Normal |
| Partial / full actions selected | 27 / 33 |
| Real merge Cloudlets | 27 |
| Measured-outcome updates | 60 |
| Deadline misses | 4 |
| State count / Q-values | 13,122 / 118,098 |
| Java contract checks | 80 passed |

The workload validator passed all per-task input/compute/output conservation checks, partial-action feasibility checks, typed AppEdge profile checks, merge barriers, deadline flags, outcome acknowledgements, and Python shutdown reconciliation (zero orphaned tasks).

## Paired policy comparison on three held-out workloads

Training model: seed 42, 60 tasks.

Held-out evaluation workloads: seeds 43, 44, and 45; 60 tasks per seed (180 total).

Aggregate artifact: `audit_output/v2_multiseed_holdout_20261115/multi_seed_summary.json`. Individual per-seed summaries remain under their respective `v2_policy_comparison_seed*` directories.

For each held-out seed, all five policies received the same 60 workload rows, arrival gaps, task deadlines, and configured network/overhead settings. The RL model trained on seed 42 was frozen during all evaluation runs. Baselines were Local, Edge Full, Cloud Full, and Random over each task's feasible mask.

| Policy | Mean latency | Median | P95 | Deadline misses | Mean bandwidth bytes |
|---|---:|---:|---:|---:|---:|
| Local | 257.890 ms | 235.995 ms | 597.865 ms | 58/180 (32.2%) | 0 |
| Edge Full | 119.759 ms | 114.541 ms | 257.979 ms | 12/180 (6.7%) | 134,956 |
| Cloud Full | 224.968 ms | 215.792 ms | 371.876 ms | 52/180 (28.9%) | 269,913 |
| Random | 92.152 ms | 80.004 ms | 175.927 ms | 11/180 (6.1%) | 131,857 |
| Q-table + fallback (frozen) | 60.065 ms | 54.291 ms | 128.601 ms | 3/180 (1.7%) | 105,556 |

### What the comparison does and does not say

- Across 180 paired tasks, RL reduced mean latency by 59.694 ms versus Edge Full and by 32.087 ms versus Random.
- RL was faster than Edge Full on 139 tasks, slower on 22, and tied on 19. Against Random it was faster on 112 tasks, slower on 63, and tied on 5.
- RL had 3 deadline misses versus 12 for Edge Full and 11 for Random. Its aggregate P95 was 128.601 ms versus 257.979 ms for Edge Full and 175.927 ms for Random.
- RL used less mean bandwidth than Edge Full (105,556 vs 134,956 bytes). Energy remains unmeasured.
- The per-seed RL-minus-Edge mean latency differences were -6.310, -69.683, and -103.089 ms for seeds 43, 44, and 45. The variation across workload seeds is substantial.

This is stronger descriptive evidence than a single test seed, but it is still not proof of RL superiority. There is only one training seed/model, three held-out seeds from the same synthetic generator distribution, and no confidence intervals or hypothesis tests. It does not establish convergence, robustness to a different application regime, or generalization beyond this simulator profile.

## Reproduction commands

Training / mixed workload:

```powershell
.\run_v2_workload_smoke.ps1 -Seed 42 -Tasks 60 -Profile mixed -OutputRoot ..\..\..\audit_output\my-training-run
```

Paired comparison using the frozen trained model:

```powershell
.\run_v2_policy_comparison.ps1 -WorkloadFile ..\..\..\audit_output\holdout\workload_seed43.jsonl -ModelIn ..\..\..\audit_output\v2_workload_seed42_20261115_2120\train_policy\python_model.json -OutputRoot ..\..\..\audit_output\my-comparison
```

## Remaining research work

1. Run multiple independent training seeds and multiple held-out evaluation seeds; report paired confidence intervals and effect sizes.
2. Add arrival-rate × overhead sensitivity and calibrate partition/merge overheads from a real workload or defensible source.
3. Validate the proportional data-parallel partition assumption against at least one concrete application.
4. Add measured energy and a target topology with multiple IoT sources and Edge nodes.
5. Evaluate on held-out workload regimes (not only new random seeds from the same generator distribution).
6. Investigate why the learned policy selects Edge Full for 114/180 tasks and how its behavior changes across workload seeds.



Multi-seed replay can be reproduced in one command with `run_v2_multiseed_holdout.ps1`:

```powershell
.\run_v2_multiseed_holdout.ps1 -ModelIn ..\..\..\audit_output\v2_workload_seed42_20261115_2120\train_policy\python_model.json -TrainingSeed 42 -EvaluationSeeds 43,44,45 -TasksPerSeed 60 -OutputRoot ..\..\..\audit_output\my-multiseed-study
```

The script regenerates each held-out workload from its seed, runs Local/Edge/Cloud/Random/frozen-RL comparisons, and writes a combined `multi_seed_summary.json`.


## Q-table coverage and fallback audit

The saved seed-42 model was inspected directly, not inferred from the training log:

| Coverage measure | Observed value |
|---|---:|
| Q-table entries (13,122 states × 9 actions) | 118,098 |
| Training decisions / measured-outcome updates | 60 / 60 |
| Unique states visited during training | 45 / 13,122 (0.343%) |
| Unique state-action cells updated | 60 / 118,098 (0.0508%) |
| Non-default Q cells | 60 |
| Maximum visits to any one state-action cell | 1 |

During the 180-task held-out evaluation, the frozen agent reported **108 fallback decisions and 72 greedy decisions**. All 108 fallback decisions selected `EDGE_FULL`, because that is first in the configured fallback order when feasible. The final action count was 114 `EDGE_FULL` selections, of which 108 came from fallback and only 6 from greedy selection.

This changes the interpretation materially: the measured policy is a **fallback/greedy hybrid**, not a well-trained tabular RL policy. The 60 Q updates cover only 0.0508% of the state-action table, with no repeated sample for any updated cell. The aggregate latency/deadline results describe this hybrid implementation and must not be presented as proof that RL learned a superior offloading strategy. The next experiment must increase training episodes substantially, track state/action visitation, and compare learned decisions separately from fallback decisions.
