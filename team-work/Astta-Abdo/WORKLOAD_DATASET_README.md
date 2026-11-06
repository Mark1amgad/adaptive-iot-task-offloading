# Astta-Abdo workload dataset extension

This folder contains the versioned synthetic workload-input generator and simulator handoff contracts for the IoT–Edge–Cloud task-partitioning study.

## Start here

- [`WORKLOAD_GENERATOR_SPEC.md`](WORKLOAD_GENERATOR_SPEC.md) — generation model, units, deadlines, divisibility, scenarios, and evidence status.
- [`DATASET_CARD.md`](DATASET_CARD.md) — synthetic data provenance, use, limitations, splits, and reproducibility.
- [`ABDO_HANDOFF_REPORT.md`](ABDO_HANDOFF_REPORT.md) — implementation inventory, commands, verification results, proposed values, and integration questions.
- [`configs/workload_profiles.yaml`](configs/workload_profiles.yaml) and [`configs/scenario_profiles.yaml`](configs/scenario_profiles.yaml) — versioned workload/scenario configurations.
- [`scripts/generate_workloads.py`](scripts/generate_workloads.py) and [`scripts/validate_dataset.py`](scripts/validate_dataset.py) — CLI tools.
- [`schemas/`](schemas/) — six JSON Schema contracts and the data dictionary.
- [`data/dev/`](data/dev/) — small synthetic development inputs only; no simulator outcomes.
- [`provenance/`](provenance/) — prior technical audits and supplied V2 handoff copies, retained as versioned references.
- [`reports/`](reports/) — validation, hash, and test evidence generated during this workstream.

## Quick start

From this directory:

```bash
python -m pip install -r requirements.txt
python scripts/generate_workloads.py --scenario all-core --seed 7 --seed-count 1 --task-count 48 --output data/dev --hash-report reports/dev_hashes_v1_1.json
python scripts/validate_dataset.py --tasks data/dev/stable_steady__seed_0007_tasks.csv --manifest data/dev/stable_steady__seed_0007_scenario_manifest.csv --check-replay --report reports/stable_steady_validation.json
pytest -q
```

The generator creates task inputs and scenario manifests only. `decision_contexts`, `decisions`, `task_outcomes`, and `calibration_log` have schema contracts and header-only templates; only simulator/policy runs may populate them.

Existing `README.md` and all files in `adaptive_offloading/` are intentionally left untouched.
