# Dataset Card — Synthetic IoT Task Inputs (Development v1.1.0)

## Summary

A reproducible **synthetic input dataset** for evaluating Local / Edge / Cloud full placement and constrained partial offloading on explicitly declared data-parallel tasks. It contains task workload inputs and scenario manifests only. It is not a measured IoT trace, not simulator execution output, and not the final experiment-results dataset.

## Intended use

Development, schema testing, deterministic replay testing, and preparation of paired iFogSim2 experiments after numerical profile approval. Benchmark-generation outputs must be kept in a separate directory and must not be confused with the development samples.

## Contents

- `data/dev/*_tasks.csv`: 8 scenario samples, 48 synthetic tasks each.
- `data/dev/*_scenario_manifest.csv`: one scenario manifest row per sample run.
- `data/dev/schemas_only/`: header-only CSV templates for simulator-produced decision contexts, decisions, outcomes, and calibration logs; they intentionally contain no records.
- `schemas/`: six JSON Schema contracts and a data dictionary.
- `configs/`: versioned workload and scenario profiles.

## Synthetic data declaration

All task rows and workload probabilities/ranges were generated from the configuration in this package using deterministic pseudorandom seeds. No real device/user/task traces are included. No values were derived from ECW or SMD. Output-byte sizes are explicit synthetic profile assumptions. No task memory requirement is emitted.

## Schema and units

Canonical format: UTF-8 CSV. `arrival_time_ms`, relative/absolute deadlines, split/merge overhead, and event-time contracts use milliseconds; task input/output use bytes; compute demand uses MI; simulator CPU capacity uses MIPS. Bandwidth units remain unconfirmed in the current iFogSim topology and are deliberately not assigned in the generator.

See `schemas/DATA_DICTIONARY.md` and individual JSON Schema files for field-level types, required/null semantics, keys and constraints.

## Generation and reproducibility

Use Python 3.10+ with `PyYAML` and `pytest`. From the workload-workstream directory:

```bash
python -m pip install -r requirements.txt
python scripts/generate_workloads.py --scenario all-core --seed 7 --seed-count 1 --task-count 48 --output data/dev --hash-report reports/dev_hashes_v1_1.json
pytest -q
```

Same seed/config/scenario/run ID/task count produces byte-identical CSVs. The deterministic replay validator is:

```bash
python scripts/validate_dataset.py \
  --tasks data/dev/stable_steady__seed_0007_tasks.csv \
  --manifest data/dev/stable_steady__seed_0007_scenario_manifest.csv \
  --check-replay --report reports/stable_steady_validation.json
```

## Train / validation / test split

Disjoint split by scenario family and seed band. Train: seeds 1–60 (`stable`, `bursty`); validation: 61–80 (`network_bandwidth`, `network_wan_delay`, `edge_capacity`); test: 81–120 (`task_mix_shift`, `repeated_aba`, combined stress and unseen topology if later approved). This prevents random-row leakage between regimes and seed groups. Each principal scenario is planned for at least 20 paired seeds. The validation band must be widened before a 30-seed validation plan can be claimed.

## Limitations

- All task-size, compute, output-byte, arrival-rate, deadline and split/merge values are proposed assumptions, not validated workload measurements.
- Four source-device IDs are logical identifiers only; mapping to four V2 IoT nodes is awaiting Ayoub's topology confirmation.
- The currently checked-in prototype describes one local, one Edge and one Cloud executor, not yet the V2 four-IoT/two-Edge/one-Cloud target.
- Bandwidth raw-unit semantics and downlink latency are unresolved.
- The current one-task pilot does not establish a service-time distribution or multi-task queue behaviour.
- Partial local/remote branch execution, synchronization, merge and per-branch failure hooks are not verified in current simulator code.
- ECW and SMD are not used to generate the synthetic tasks and remain separate data sources with documented limitations.
- No measured outcomes, rewards, energy values, or actual execution destinations are included.

## Provenance

Controlled by `configs/workload_profiles.yaml`, `configs/scenario_profiles.yaml`, generator version `1.1.0`, units version `SI-ms-bytes-MI-v1`, and per-run `config_hash`. Related source limitations are preserved under `provenance/`. Mostafa's dataset inventory remains in `team-work/Mostafa/Dataset/` and is not duplicated here.

## License and access

The repository's `LICENSE_STATUS.md` states that no project license has been selected and the repository should be treated as all-rights-reserved pending a team decision. This card does not grant a license to third parties. The generated samples contain synthetic values only; do not redistribute the repository package until the project licensing decision is recorded.

## Version

- Dataset / pipeline version: 1.1.0
- Status: development-only; numerical parameters awaiting Mark approval
- Base repository revision inspected: `main` at `39d6cd448ba5a15e690ac67ff777017a445ce577` (pushed 2026-11-03)
