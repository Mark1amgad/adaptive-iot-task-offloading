# A-B-A Paired-Seed Result Bundle

This bundle contains the immutable inputs and compact per-seed outputs for the 20-seed A-B-A evaluation documented in `../../Simulation_Source/ABA_PAIRED_20_SEED_RESULTS_2026-11-17.md`.

- `workloads/`: 20 deterministic 90-task A1/B/A2 workloads, seeds 102–121.
- `summaries/seed_<n>/experiment_manifest.json`: per-seed immutable provenance manifest.
- `summaries/seed_<n>/policy_comparison_summary.json`: five-arm policy metrics and phase/recovery results.
- `paired_seed_inference.json`: paired comparisons for deadline misses, latency, and bandwidth.
- `aba_regime_inference.json`: phase-specific deadline-miss and recovery-time inference.

The simulator's full per-policy traces and logs remain in the local archive at `audit_output/aba_paired_20seeds_20261117_final/` on the experiment machine; they are not included in this compact repository bundle. The training model and risk sidecar are frozen external artifacts identified by SHA-256 in the report and manifests; they are not copied into this result bundle.

Independent unit: workload seed / paired simulation run (n=20), not individual tasks.
