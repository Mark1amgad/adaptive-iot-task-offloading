# Paired-Seed A-B-A Evaluation Guide — Historical Pilot and Future Test Governance

## Frozen design

The archived 102–121 batch evaluates the existing A -> B -> A protocol on paired workload seeds, but those IDs were used in earlier generic A→B→A work. It is retained as an exploratory pilot, not as a distinct held-out test allocation. Each seed produces one deterministic 90-task workload (30 tasks in each phase) and five policy arms: Local, Edge, Cloud, Random, and risk-calibrated RL evaluation. Within a seed, all five arms consume the exact same task stream and exogenous regime schedule.

The model and risk-calibration sidecar are frozen from the separate A-only training run (seed 909). Test workloads must never be used to update either artifact. The historical batch used seeds 102–121; seed 101 was also a development pilot. Do not rerun or describe 102–121 as fresh test seeds.

## Provenance semantics

A manifest's `evaluation_split: test` field is not proof of test isolation. The current manifest builder hardcodes this label and the inference analyzer does not consult an approved seed registry. The 102–121 bundle is therefore exploratory pending a fresh, audited seed allocation. See `docs/EXPERIMENTAL_EVIDENCE_VALIDITY_AUDIT_2026-11-17.md`.


Each per-seed manifest intentionally has a different workload seed, filename, SHA-256, experiment ID, and creation timestamp. These fields identify the per-seed test input and are validated against that seed's actual workload. They must not be compared for equality across seeds.

The paired inference analyzer compares the shared provenance payload instead: source commit and source inventory, model/risk hashes, Java version, simulator JAR inventory, frozen simulator parameters, policy arms, and test split. This ensures different test workloads are paired across policies without accidentally requiring different seeds to have identical file hashes.

## Execution

Run `run_v2_aba_paired_seeds.ps1` from the Simulation_Source directory. It creates immutable per-seed workload files, invokes the existing five-arm comparison runner once per seed, and then runs paired-seed inference. The output root contains `workloads/`, `evaluations/seed_<n>/`, and `paired_seed_inference.json`.

The wrapper refuses to reuse an existing output directory, duplicate seeds, missing model/risk artifacts, or missing simulator/JDK/Python dependencies. Before a future final test batch, seed IDs must also be approved by a versioned seed registry; this gate is not yet implemented in the current wrapper. A failed seed stops the batch; do not silently omit it and continue inference.

## Interpretation

The independent unit is the workload seed / paired simulation run, not an individual task. Bootstrap confidence intervals resample paired seeds. Wilcoxon tests compare paired per-seed policy metrics and Holm correction controls the family-wise error rate across the reported comparisons.

The 20-seed minimum is a protocol floor, not a guarantee of adequate statistical power. It does not cure seed reuse or an invalid train/validation/test split. Report effect sizes and confidence intervals alongside adjusted p-values. Latency is conditional on completed tasks and must be interpreted with deadline-miss rate and completion coverage. A→B→A recovery remains an operational metric whose thresholds should receive sensitivity analysis before strong claims.

## Scope

This batch tests the combined workload-and-network shift already defined by `aba_network_load_v1`. It does not isolate network-only and workload-only effects. Those require separate frozen workload profiles and should be reported as distinct experiments.

## Controlled shift profiles

The workload generator supports three controlled modes with an optional fixed deadline:

- `combined`: workload and WAN shift together; with `--fixed-deadline-ms 15000`, deadline relaxation is removed.
- `network_only`: task MI, input/output sizes, arrival pattern, urgency, and deadline remain fixed; only WAN latency changes A→B→A.
- `workload_only`: MI, input bytes, and arrival gaps shift in B; WAN latency and deadline remain fixed.

For controlled pilots use `run_v2_aba_paired_seeds.ps1 -ShiftMode network_only -FixedDeadlineMs 15000` or `workload_only`. Use a distinct output root per profile. The legacy default (`combined` with no fixed deadline) preserves the original profile for reproducibility.

The batch wrapper now writes both `paired_seed_inference.json` and `aba_regime_inference.json`; the latter analyzes A1/B/A2 deadline misses and paired A2 recovery times.
