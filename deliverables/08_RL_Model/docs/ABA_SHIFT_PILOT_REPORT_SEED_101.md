# A→B→A Pilot Results — Test Seed 101

**Branch:** `mark/risk-calibration-v1`  
**Workload:** `aba_network_load_v1`, 30 tasks per phase, 90 generated tasks  
**Training:** separate A-only workload, seed 909, 30 tasks; frozen model and risk sidecar  
**Evaluation:** test seed 101; five current policy arms; iFogSim2; Java 25.0.3  
**Status:** pipeline and descriptive pilot PASS; not inferential evidence

## Experiment integrity

- A1 and A2 replay the same seeded task template; B applies a joint compute/input/arrival/WAN shift.
- Every policy processed all 90 generated tasks. Completion coverage was 100% for all five arms in this run.
- All five traces contain the three expected regime transitions and per-task regime/WAN identities.
- The run used the same immutable workload and manifest across policy arms.
- The manifest records workload/model/risk hashes, source inventory, Java version, iFogSim JAR hashes and simulator parameters.

## Phase-level results

Deadline-miss rate is computed over every generated task in the phase. Latency is the median among completed tasks only.

| Policy | A1 miss rate | B miss rate | A2 miss rate | A1 median latency | B median latency | A2 median latency |
|---|---:|---:|---:|---:|---:|---:|
| Local | 93.3% | 100.0% | 100.0% | 73.65 s | 503.12 s | 339.75 s |
| Edge | 0.0% | 76.7% | 33.3% | 5.51 s | 32.46 s | 6.07 s |
| Cloud | 0.0% | 0.0% | 0.0% | 6.12 s | 10.37 s | 6.12 s |
| Random | 36.7% | 70.0% | 76.7% | 13.00 s | 52.14 s | 32.91 s |
| RL evaluation | 13.3% | 0.0% | 6.7% | 6.21 s | 9.05 s | 6.21 s |

## Return-to-A recovery

Operational rule: first sliding 10-task A2 window with all tasks completed, miss rate no more than A1 + 5 percentage points, and median latency no more than 110% of A1.

| Policy | Recovered within A2? | First qualifying window | Recovery time |
|---|---|---|---:|
| Local | No | — | Not observed |
| Edge | Yes | Tasks 71–80 | 87.16 s |
| Cloud | Yes | Tasks 61–70 | 44.12 s |
| Random | No | — | Not observed |
| RL evaluation | Yes | Tasks 61–70 | 43.97 s |

For RL, the qualifying A2 window had a 10% deadline-miss rate and 5.63 s median latency. Its A1 reference was 13.3% misses and 6.21 s median latency. The result satisfies the preregistered operational thresholds; it does not establish that RL has a faster recovery distribution than Cloud from one seed.

## Overall policy metrics

| Policy | Overall deadline-miss rate | Mean completed latency | Completion coverage |
|---|---:|---:|---:|
| Local | 97.8% | 312.38 s | 100% |
| Edge | 36.7% | 17.59 s | 100% |
| Cloud | **0.0%** | **6.88 s** | 100% |
| Random | 61.1% | 42.37 s | 100% |
| RL evaluation | 6.7% | 8.43 s | 100% |

## Interpretation

1. The runtime successfully executes and traces the A→B→A shifts. The recovery analyzer identifies recovery for Edge, Cloud, and RL, and does not invent recovery for Local or Random.
2. RL evaluation handled B without deadline misses and returned to the A1 performance band within the first 10 A2 tasks. Its measured recovery time (43.97 s) was essentially the same as Cloud's (44.12 s) in this seed.
3. **Cloud is the strongest policy in this pilot:** zero deadline misses across all phases and the lowest overall mean latency. RL does not beat Cloud here; its overall deadline-miss rate is 6.7% and its mean latency is higher.
4. The Local and Random arms demonstrate severe backlog sensitivity under this workload. Edge suffers heavily during B and recovers more slowly than Cloud/RL.
5. This is one seed, one joint-shift intensity, and one training run. No p-values, confidence intervals, generalization, or superiority claims are warranted.

## Limitations and next experiments

- Run at least 20 paired test seeds; 30 is preferred.
- Repeat at lower and higher WAN shifts and separately vary workload intensity versus WAN latency. The current B phase changes all four dimensions together, so it cannot identify the cause of an effect.
- Perform sensitivity analysis for the 10-task recovery window and +5 pp / +10% thresholds.
- Compare risk-filtered and unfiltered learner, and full-only versus partial-enabled ablations once those policy arms are added to the runner.
- Record training workload hash and training source provenance alongside the frozen model in the next runner revision.

## Artifacts

- Per-seed summary: `policy_comparison_summary.json`
- Root manifest: `experiment_manifest.json`
- Per-policy raw trace: `policy_<name>/partial_trace.jsonl`
- Workload: `aba_seed_101_tuned.jsonl`
- Training model and risk sidecar were generated from a separate seed-909 A-only workload.

The raw run output was produced in an isolated validation worktree on the connected Windows machine. The local original repository clone and its pre-existing uncommitted changes were not modified.
