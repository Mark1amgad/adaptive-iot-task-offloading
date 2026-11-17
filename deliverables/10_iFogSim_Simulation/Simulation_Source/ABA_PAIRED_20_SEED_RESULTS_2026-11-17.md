# A-B-A Paired-Seed Pilot Results — 2026-11-17 (Exploratory; Not Final Held-Out Evidence)

## Executive result

The 20-run A -> B -> A pilot completed successfully. It compares five policy arms on the same 90-task workload within each run, using a frozen model and risk-calibration sidecar trained separately on A-only seed 909. A subsequent evidence audit found that seed IDs 102–121 had already been used in the earlier generic A→B→A work. This bundle is therefore exploratory pilot evidence, not an untouched confirmatory test set. See `docs/EXPERIMENTAL_EVIDENCE_VALIDITY_AUDIT_2026-11-17.md`.

- Reused historical seed IDs: 102–121 (20 paired simulation runs; not eligible as final held-out test seeds)
- Workload profile: `aba_network_load_v1`
- Tasks: 90 per policy per seed; 1,800 tasks per policy; 9,000 policy-task executions total
- Policy arms: Local, Edge, Cloud, Random, RL Evaluation
- Every seed passed the Java contract checks (80 checks; 9 execution plans) and per-seed evaluation validation.
- Exploratory paired inference calculation: PASS; 20/20 runs; 10,000 bootstrap resamples per comparison; Wilcoxon signed-rank tests with Holm correction. These inferential outputs are exploratory because the seed allocation was reused.
- Frozen model SHA-256: `0b45a649ee6b47b937d0db2a4002147b7d98b2941741a3a0d8ead7b64844115c`
- Frozen risk-state SHA-256: `7307dd1bf19755da8c0ddd12775c5a11f402e7652901bf488529acf585e97d63`
- Source commit recorded in manifests: `076e45bf25ae6b05d91e7cb21fc6ba815d3e30a9`
- Shared provenance fingerprint: `47dc44bc7e4e0fb57e69ace161badbab2f9e78ab5c28d76ea76c2abd2bd9a00d`

Artifacts are archived under `audit_output/aba_paired_20seeds_20261117_final/`: one immutable workload and manifest per seed, five policy run folders per seed, `paired_seed_inference.json`, and `aba_regime_inference.json`.

## Aggregate policy results

Means are across 20 paired runs from a reused historical seed allocation; treat these as descriptive pilot summaries, not independent final-test evidence. Latency is conditional on completed tasks only; interpret it together with completion coverage and deadline-miss rate. Bandwidth is the simulator's mean transmitted-byte metric, not energy or monetary cost.

| Policy | Deadline-miss rate | Mean completed latency | Mean bandwidth metric | Completion coverage | A2 recovered |
|---|---:|---:|---:|---:|---:|
| Local | 97.56% | 74.99 s* | 0 B | 33.33% | 0/20 |
| Edge | 35.11% | 17.01 s | 22,014 B | 100% | 20/20 |
| Cloud | 0.00% | 6.14 s | 44,028 B | 100% | 20/20 |
| Random | 55.17% | 38.65 s | 20,554 B | 100% | 0/20 |
| Risk-calibrated RL | 3.89% | 8.20 s | 27,009 B | 100% | 20/20 |

*Local completed only one third of generated tasks on average; its conditional latency is not directly comparable to policies with full completion coverage. Sixty unresolved tasks per seed on average were retained as deadline misses in the all-generated-task denominator.

## Paired inference: RL versus baselines

Differences are RL minus baseline. Negative is favorable for deadline misses, latency, and bandwidth; positive is unfavorable. Confidence intervals are paired-seed bootstrap 95% intervals. P-values shown are Holm-adjusted across the 12 primary policy/metric comparisons.

| Comparison | Mean paired difference | 95% CI | Holm-adjusted p |
|---|---:|---:|---:|
| Deadline misses vs Cloud | +3.89 pp | [+3.28, +4.50] pp | 0.000316 |
| Latency vs Cloud | +2.061 s | [+1.979, +2.140] s | 0.0000229 |
| Bandwidth vs Cloud | -17,019 B | [-17,758, -16,306] B | 0.0000229 |
| Deadline misses vs Edge | -31.22 pp | [-32.72, -29.72] pp | 0.000316 |
| Latency vs Edge | -8.806 s | [-9.766, -7.857] s | 0.0000229 |
| Bandwidth vs Edge | +4,995 B | [+4,460, +5,553] B | 0.0000229 |
| Deadline misses vs Random | -51.28 pp | [-52.44, -50.06] pp | 0.000316 |
| Latency vs Random | -30.446 s | [-31.647, -29.272] s | 0.0000229 |
| Bandwidth vs Random | +6,455 B | [+5,845, +7,087] B | 0.0000229 |
| Deadline misses vs Local | -93.67 pp | [-94.39, -92.94] pp | 0.000316 |
| Latency vs Local* | -66.787 s | [-71.280, -62.242] s | 0.0000229 |
| Bandwidth vs Local | +27,009 B | [+25,978, +28,133] B | 0.0000229 |

*The Local latency comparison is conditional on completion and is confounded by Local's 33.33% completion coverage. The deadline-miss comparison uses all generated tasks and remains valid under the declared outcome denominator.

### Interpretation

1. **Cloud is the strongest policy on deadline reliability and latency in this scenario.** It records zero deadline misses and 100% completion coverage across all 20 seeds. RL is significantly worse on both metrics. The study must not claim that RL outperforms Cloud.
2. **RL dominates Edge and Random on deadline reliability and latency** in this workload profile, with paired differences in the same direction across all 20 seeds for the primary comparisons.
3. **RL reduces the logged bandwidth metric versus Cloud by about 38.7%**, but pays for that reduction with about 2.06 seconds higher mean completed latency and 3.89 percentage points more deadline misses. This is a measurable trade-off, not an unconditional win. Whether it is useful depends on the value assigned to bandwidth versus deadline reliability.
4. **RL has a strong return-to-A result:** 20/20 runs meet the operational recovery rule. Its median recovery time is 49.35 s versus 47.21 s for Cloud and 85.13 s for Edge.
5. RL recovery time is not statistically distinguishable from Cloud (mean paired difference +0.760 s; 95% CI [-10.531, +11.591] s; Holm-adjusted p=0.9993). RL recovers faster than Edge (mean paired difference -29.930 s; 95% CI [-37.918, -21.028] s; Holm-adjusted p=0.000620).

## Phase-specific results

Mean deadline-miss rates across seeds:

| Policy | A1 | B | A2 |
|---|---:|---:|---:|
| Cloud | 0.00% | 0.00% | 0.00% |
| Edge | 0.00% | 77.67% | 27.67% |
| Random | 30.00% | 62.50% | 73.00% |
| RL Evaluation | 6.83% | 0.00% | 4.83% |
| Local | 92.67% | 100.00% | 100.00% |

RL versus Cloud: A1 difference +6.83 pp (95% CI +5.33 to +8.33 pp; Holm-adjusted p=0.000787); B difference 0 pp (all 20 seeds tied); A2 difference +4.83 pp (95% CI +3.83 to +6.00 pp; Holm-adjusted p=0.000787).

The important nuance is that RL has zero deadline misses in B but some misses in A1 and A2. This does not show that B is intrinsically easier: B uses a 20-second deadline while A1/A2 use 15-second deadlines. Deadline relaxation is part of the current B profile and confounds phase-to-phase attribution.

## Recovery inference

Recovery definition: first sliding 10-task window in A2 with deadline-miss rate no more than A1 + 5 percentage points and median completed latency no more than 110% of A1; recovery time is measured from the A2 transition to the final completion in that window.

| Policy | Recovered | Median recovery time |
|---|---:|---:|
| Cloud | 20/20 | 47.21 s |
| RL Evaluation | 20/20 | 49.35 s |
| Edge | 20/20 | 85.13 s |
| Random | 0/20 | Not recovered in observed A2 |
| Local | 0/20 | Not recovered in observed A2 |

Recovery-time comparison is conditional on both policies recovering. RL versus Cloud is not significant; RL versus Edge is significantly faster after Holm correction. Recovery thresholds and window length remain operational choices and require sensitivity analysis.

## Threats to validity and what this does not prove

- The current A-B-A profile is a **joint shift** in task MI, input bytes, arrival gaps, WAN latency, and deadlines. It does not isolate workload-only or network-only effects.
- B deadlines are 20 s versus 15 s in A1/A2. This is a real confound for phase-wise deadline-miss comparisons and must be removed or separately controlled in the next experiment.
- The run/seed is the within-batch inferential unit; tasks within a run are not treated as independent statistical samples. However, reuse of seed IDs from prior work prevents this batch from serving as an untouched confirmatory test allocation.
- Mean latency is conditional on completion. Completion coverage and all-task deadline misses must be reported alongside it.
- The bandwidth metric does not establish energy savings, monetary savings, or a universal resource-efficiency improvement.
- This experiment has five policy arms only. It does not yet isolate the contribution of risk calibration from the learner or the contribution of partial execution from full-only actions.
- The risk model is trained on an A-only seed. The result is evidence for this frozen model/profile pair, not generalization to arbitrary industrial networks.

## Next experiments — required before a broad claim

1. **Deadline-controlled A-B-A:** repeat with one fixed deadline across A1/B/A2, preserving task/network shifts.
2. **Factor isolation:** network-only A-B-A with workload and deadlines fixed; workload-only A-B-A with WAN latency fixed.
3. **Ablations:** learner full-only versus learner partial-enabled; risk filter disabled versus enabled; same seeds and frozen training artifacts.
4. **Recovery sensitivity:** repeat the analysis with 5-, 10-, and 15-task windows and with +0/+5/+10 pp miss tolerance and +5/+10/+20% latency tolerance. Treat these as sensitivity analyses, not post-hoc opportunities to choose the most favorable threshold.
5. **Bandwidth trade-off framing:** report a Pareto frontier or constrained policy objective (e.g. minimize bandwidth subject to a predeclared deadline-miss ceiling). Do not call lower bytes an improvement without an explicit service constraint.

## Reproduction

Use `run_v2_aba_paired_seeds.ps1` for the per-seed five-arm batch and `analyze_v2_paired_seed_inference.py` for the primary inference. `analyze_v2_aba_regime_inference.py` adds phase-specific miss and recovery-time inference. All analysis inputs are the archived per-seed `policy_comparison_summary.json` files; no test seed was used to train the model.
