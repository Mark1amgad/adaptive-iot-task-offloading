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
python scripts/generate_workloads.py --scenario all-core --dataset-split development --seed 1300 --seed-count 1 --task-count 48 --output data/dev --hash-report reports/dev_hashes_v1_2.json
python scripts/validate_dataset.py --tasks data/dev/stable_steady__seed_1300_tasks.csv --manifest data/dev/stable_steady__seed_1300_scenario_manifest.csv --check-replay --report reports/stable_steady_validation.json
pytest -q
```

The generator creates task inputs and scenario manifests only. `decision_contexts`, `decisions`, `task_outcomes`, and `calibration_log` have schema contracts and header-only templates; only simulator/policy runs may populate them.

Existing `README.md` and all files in `adaptive_offloading/` are intentionally left untouched.


## Industrial archetype coverage

Predictive Maintenance is represented by indivisible inference tasks. Visual Inspection includes indivisible single-product-image inference and divisible independent frame batches. Production Monitoring includes indivisible single-event processing and divisible aggregation-window batches. The bulk frame and large aggregation profiles provide proposed shifted-load variants.

## A-B-A exact recovery replay

For both repeated A-B-A scenarios, A1 and A2 are generated from the same task-attribute random stream and relative arrival-time template. Their task attributes and relative arrival offsets must match exactly. B uses a separate task-template stream; in the workload-mix-shift scenario, B also uses the heavier synthetic profile distribution. A1/A2 condition-profile identifiers are required to match. The absolute arrival and deadline timestamps differ only by phase offset.

## Seed registry and split eligibility

The registry at research/experiments/SEED_REGISTRY_V2.csv is the only seed allocator. Historical seeds, including seed 81 (development) and the earlier A-B-A batch seeds 102-121, are retired and cannot be reused for final held-out testing. Seed 1300 is allocated only to development/CI. There are currently no approved Train, Validation, or Test seed allocations. The inventory remains incomplete until local experiment archives and each team workstream have been inspected.

## Topology provenance

Manifests use target_topology_id for the proposed 4-IoT / 2-Edge / 1-Cloud design and actual_topology_id for the implemented simulator layout. actual_topology_id remains null with status NOT_VERIFIED_PENDING_AYOUB_CONFIRMATION until Ayoub confirms the running topology. Logical source IDs do not prove instantiated FogDevices.

All sizes, compute demands, deadlines, rates, profile proportions and partition overheads remain proposed synthetic configurations. They are not factory measurements, industrial traces or measured performance. The generator never creates simulator outcomes.
