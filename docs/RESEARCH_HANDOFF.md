# Research Handoff — Adaptive Task Offloading V2
## Continuation notes and operational safety

**Last updated:** 2026-11-15  
**Repository:** `C:\Users\DELL\OneDrive\Desktop\Research\adaptive-iot-task-offloading`  
**Branch:** `work/multi-task-lifecycle`  
**Last implementation commit:** `c5e1c15`

This file is the compact technical handoff for the next work session. For the complete chronology and supervisor-facing account, see [WORK_LOG_2026-11-15.md](WORK_LOG_2026-11-15.md).

---

## 1. Current Git state and preservation rules

At the start of close-out:
- Branch was `work/multi-task-lifecycle`.
- HEAD was `c5e1c15`.
- Branch was 7 commits ahead of `origin/work/multi-task-lifecycle`.
- Eight tracked files had later edits not yet committed.
- Multiple new experiment folders existed under `audit_output/`.
- `team-work/Astta-Abdo/archives/marks-staging/` was untracked and must be preserved as user/team material.

Close-out policy:
- Commit the documentation, tracked implementation/documentation edits, and generated audit evidence belonging to this work.
- Do not add or alter `team-work/Astta-Abdo/archives/marks-staging/`.
- Do not push unless explicitly requested.
- Do not delete intermediate audit folders.
- Do not rewrite history or amend prior commits.

### External iFogSim checkout — strict no-touch boundary

External repository:
`C:\Users\DELL\OneDrive\Desktop\Research\iFogSim`

Its Git status previously showed 488 existing changed/untracked entries (5 Java source files, 479 class files, 4 other entries). Those changes pre-existed this work and must be preserved. Project runners compile against the external iFogSim source/jars, but project changes belong in this repository under `deliverables/10_iFogSim_Simulation/Simulation_Source`.

**Never reset, clean, checkout, stash, or otherwise modify the external iFogSim repository.** Do not attribute its pre-existing changes to this project session.

---

## 2. Repository map

| Path | Purpose |
|---|---|
| `deliverables/08_RL_Model/src/rl_model/` | Python RL implementation |
| `deliverables/08_RL_Model/config/v2.json` | V2 state/action/training configuration |
| `deliverables/08_RL_Model/schemas/` | JSON protocol schemas |
| `deliverables/08_RL_Model/tests/` | Python contract and server tests |
| `deliverables/08_RL_Model/docs/` | V2 design and protocol docs |
| `deliverables/10_iFogSim_Simulation/Simulation_Source/org/fog/test/perfeval/` | Project-owned Java integration classes |
| `deliverables/10_iFogSim_Simulation/Simulation_Source/*.ps1` | PowerShell experiment runners |
| `deliverables/10_iFogSim_Simulation/Simulation_Source/validate_*.py` | Trace/workload validators |
| `deliverables/10_iFogSim_Simulation/Simulation_Source/analyze_*.py` | Policy and multi-seed analysis |
| `audit_output/` | Run manifests, traces, logs, models, summaries, acceptance evidence |
| `docs/WORK_LOG_2026-11-15.md` | Full chronological engineering record |
| `docs/RESEARCH_HANDOFF.md` | This continuation note |

---

## 3. V2 action semantics

The Python and Java implementations share the same nine action IDs/catalogue:

| Action | Remote share | Local share | Partial? |
|---|---:|---:|---|
| LOCAL | 0% | 100% | No |
| EDGE_PARTIAL_25 | 25% Edge | 75% | Yes |
| EDGE_PARTIAL_50 | 50% Edge | 50% | Yes |
| EDGE_PARTIAL_75 | 75% Edge | 25% | Yes |
| EDGE_FULL | 100% Edge | 0% | No |
| CLOUD_PARTIAL_25 | 25% Cloud | 75% | Yes |
| CLOUD_PARTIAL_50 | 50% Cloud | 50% | Yes |
| CLOUD_PARTIAL_75 | 75% Cloud | 25% | Yes |
| CLOUD_FULL | 100% Cloud | 0% | No |

Partial action suffix is the **remote compute fraction**, not local fraction. Integer remainder goes to Local to preserve exact totals.

Feasibility rules:
- Partial actions require `DATA_PARALLEL_DIVISIBLE` and Local availability.
- The selected remote tier must be available.
- Indivisible tasks cannot select partial actions.
- Full Edge / Cloud actions remain available for indivisible tasks when the tier is available.
- The Java side recomputes/checks feasibility per task; never assume a fixed mask across an entire workload.

Partial execution:
1. Partition task demand.
2. Dispatch Local and remote branch work.
3. Track both branch identities under the parent task.
4. Wait at a two-result barrier.
5. Only after both results arrive, apply merge overhead and create the merge Cloudlet.
6. Report one task-level outcome with the original compound action ID.
7. If a branch is missing, watchdog marks the task failed; no merge and no false success.

---

## 4. Main V2 implementation files

Python:
- `agent_v2.py`: tabular policy and action selection.
- `config_v2.py`: V2 configuration/state/action fingerprint.
- `persistence_v2.py`: save/load V2 model.
- `protocol_v2.py`: message parsing, schemas/contracts, task/action records.
- `server_v2.py`: live policy server.
- `config/v2.json`: concrete V2 config.
- `schemas/action.v2.schema.json`
- `schemas/observation.v2.schema.json`
- `schemas/outcome.v2.schema.json`

Java:
- `OffloadingActionV2.java`: catalogue, feasibility, response checks.
- `OffloadingActionV2ContractTest.java`: Java contract tests.
- `OffloadingActionV2ExecutionPlan.java`: exact action-to-branch plan and conservation.
- `RlOffloadingV2IntegrationExperiment.java`: full-placement integration.
- `RlOffloadingV2PartialIntegrationExperiment.java`: partial/full lifecycle, workload ingestion, barriers, merge, outcomes, watchdog, train/eval/baselines.

Workload and experiment scripts:
- `generate_workload_v2.py`
- `run_v2_workload_smoke.ps1`
- `run_v2_partial_acceptance.ps1`
- `run_v2_overhead_sensitivity.ps1`
- `run_v2_policy_comparison.ps1`
- `run_v2_multiseed_holdout.ps1`
- `validate_v2_partial_integration.py`
- `validate_v2_workload.py`
- `analyze_v2_policy_comparison.py`
- `analyze_v2_multiseed.py`

---

## 5. Current state representation and model compatibility

Current V2 state space:
- 13,122 discrete states.
- 9 actions.
- 118,098 Q-values.

State includes nine features, including input/output payload size and deadline bands. The exact authoritative bin definitions live in `deliverables/08_RL_Model/config/v2.json` and the encoder in `config_v2.py`.

Deadline thresholds are 180 ms and 400 ms, aligned to the synthetic generator's Critical / High / Normal ranges. `urgency_class` is retained in workload and trace metadata, not as a separate state feature.

**Compatibility:** Previous 972-state / 8,748 Q-cell model files are incompatible with the expanded state fingerprint. Retrain; do not force-load or silently reinterpret an old model.

---

## 6. Training and evaluation evidence currently available

Training model:
- Workload seed: 42.
- Tasks: 60 mixed.
- Partial/full: 27/33.
- Real merge Cloudlets: 27.
- Outcome updates: 60.
- Deadline misses: 4.
- Model: `audit_output/v2_workload_seed42_20261115_2120/train_policy/python_model.json`.

Held-out workloads:
- Seeds 43, 44, 45.
- 60 tasks per seed; 180 total.
- Five policies per workload: Local, Edge Full, Cloud Full, Random feasible, frozen Q-table + fallback.
- Aggregate: `audit_output/v2_multiseed_holdout_20261115/multi_seed_summary.json`.

Aggregate results:
| Policy | Mean latency | P95 | Misses | Mean bandwidth |
|---|---:|---:|---:|---:|
| Local | 257.890 ms | 597.865 ms | 58/180 | 0 bytes |
| Edge Full | 119.759 ms | 257.979 ms | 12/180 | 134,956 bytes |
| Cloud Full | 224.968 ms | 371.876 ms | 52/180 | 269,913 bytes |
| Random | 92.152 ms | 175.927 ms | 11/180 | 131,857 bytes |
| Frozen Q-table + fallback | 60.065 ms | 128.601 ms | 3/180 | 105,556 bytes |

### Mandatory caveat: sparse Q-table and fallback

Inspection of the model and traces:
- 60 training decisions and 60 updates.
- 45 unique states visited out of 13,122 (0.343%).
- 60 state-action cells updated out of 118,098 (0.0508%).
- No updated state-action cell was visited more than once.
- Held-out decisions: 108 fallback, 72 greedy.
- All 108 fallback decisions selected EDGE_FULL.
- 114 EDGE_FULL actions total, only 6 of them selected greedily.

So the measured controller is a sparse Q-table/fallback hybrid. Do not state “RL outperforms the baselines” as a scientific conclusion. The table describes this particular hybrid, synthetic generator, simulator topology, and seeds. Energy is not measured; no confidence intervals or hypothesis tests are available.

---

## 7. How to resume

### First action: audit the learning mechanism, not another benchmark

Inspect:
- State encoder and bin widths.
- Feasible action mask distribution by state.
- Exploration schedule and action selection in `agent_v2.py`.
- Whether model updates are occurring after valid measured outcomes.
- Fallback frequency and which states/actions trigger it.
- Q values and visit counts per state-action pair.
- Whether the reward scale and update equation are numerically sensible.

Avoid blindly increasing task count. With 13,122 states and 118,098 state-action cells, a few hundred tasks may still leave most states unseen. First decide whether to coarsen the state space or use a justified generalization mechanism.

### Suggested experiment protocol after redesign

1. Freeze the workload generator and write down the generator parameters.
2. Train multiple independent models on independent training seeds.
3. Log per episode: decisions, updates, unique states, unique state-action cells, visit histogram, action histogram, fallback fraction, reward/latency/deadline metrics.
4. Keep evaluation seeds unseen during model selection.
5. For each held-out workload, run every policy on the exact same workload rows and settings.
6. Report paired differences, confidence intervals, effect sizes, and per-seed variation.
7. Include ablations: fallback-only, greedy-only where defined, random feasible, and static placement baselines.
8. Add new workload regimes and topology only after the policy and evaluation pipeline are reliable.

### Reproduction commands

From `deliverables/10_iFogSim_Simulation/Simulation_Source`:

```powershell
python .\generate_workload_v2.py --seed 42 --tasks 60 --profile mixed --output workload_seed42.jsonl
```

```powershell
.\run_v2_workload_smoke.ps1 -Seed 42 -Tasks 60 -Profile mixed -OutputRoot ..\..\..\audit_output\my-training-run
```

```powershell
.\run_v2_multiseed_holdout.ps1 -ModelIn ..\..\..\audit_output\v2_workload_seed42_20261115_2120\train_policy\python_model.json -TrainingSeed 42 -EvaluationSeeds 43,44,45 -TasksPerSeed 60 -OutputRoot ..\..\..\audit_output\my-multiseed-study
```

After every code change, run the relevant Java contract tests, Python tests, integration runner, and validators. Capture exact output paths and commit hashes.

---

## 8. Do not lose these boundaries

- V1 remains separate from V2.
- Do not conflate exact-action execution acceptance with learned-policy performance.
- Do not present synthetic workloads as real-world traces.
- Do not claim energy improvements; energy is not measured.
- Do not generalize proportional data partitioning beyond the stated data-parallel workload assumption.
- Do not call 3/2 ms calibrated overheads.
- Do not claim convergence or generalization.
- Do not modify the external iFogSim checkout.
- Preserve `audit_output/` and the team staging folder.
- Do not push to remote unless Mark explicitly asks.
