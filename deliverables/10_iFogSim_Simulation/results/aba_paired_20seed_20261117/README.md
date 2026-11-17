# A-B-A Paired-Seed Exploratory Pilot Bundle

This bundle contains the immutable inputs and compact per-seed outputs for the exploratory 20-run A-B-A pilot documented in `../../Simulation_Source/ABA_PAIRED_20_SEED_RESULTS_2026-11-17.md`.

- `workloads/`: 20 deterministic 90-task A1/B/A2 workloads, historical seed IDs 102–121. These IDs were used in earlier generic A→B→A work and are not eligible as final held-out test seeds.
- `summaries/seed_<n>/experiment_manifest.json`: per-seed immutable provenance manifest.
- `summaries/seed_<n>/policy_comparison_summary.json`: five-arm policy metrics and phase/recovery results.
- `paired_seed_inference.json`: paired comparisons for deadline misses, latency, and bandwidth.
- `aba_regime_inference.json`: phase-specific deadline-miss and recovery-time inference.

The simulator's full per-policy traces and logs remain in the local archive at `audit_output/aba_paired_20seeds_20261117_final/` on the experiment machine; they are not included in this compact repository bundle. The training model and risk sidecar are frozen external artifacts identified by SHA-256 in the report and manifests; they are not copied into this result bundle.

Within-batch statistical unit: workload seed / paired simulation run (n=20), not individual tasks. Because the seed IDs were reused, this bundle is exploratory pilot evidence, not confirmatory final-test evidence. See `docs/EXPERIMENTAL_EVIDENCE_VALIDITY_AUDIT_2026-11-17.md`.
