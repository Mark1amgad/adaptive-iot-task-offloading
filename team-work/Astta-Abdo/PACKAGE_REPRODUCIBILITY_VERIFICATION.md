# Corrected package — reproducibility and integrity verification

**Package revision:** v1.1.1 (repackaging/verification only; generator remains v1.1.0)  
**Base repository revision:** `39d6cd448ba5a15e690ac67ff777017a445ce577` (`main`)  
**Scope:** packaging, replay, validation and test verification only. No generator, validator, YAML configuration, schema, test or workload profile logic was rewritten for this correction.

## Contents verified

- Both YAML configurations are present: `configs/workload_profiles.yaml` and `configs/scenario_profiles.yaml`.
- All six JSON Schemas are present and parse as valid JSON: calibration_log.schema.json, decision_contexts.schema.json, decisions.schema.json, scenario_manifest.schema.json, task_outcomes.schema.json, tasks.schema.json.
- All eight generated development task/manifest pairs are present under `data/dev/`.
- All four simulator/policy CSV templates are header-only, with zero data rows: calibration_log.csv, decision_contexts.csv, decisions.csv, task_outcomes.csv.
- Generator, validator, complete tests directory, `requirements.txt`, and `pytest.ini` are present.
- Provenance and previous technical audits are retained under `provenance/`.
- Actual per-scenario validation reports and their stdout captures are under `reports/package_verification/`.

## Commands run from this packaged folder

Working directory: `team-work/Astta-Abdo/`.

```bash
python -m pip install -r requirements.txt
python scripts/generate_workloads.py --scenario all-core --seed 7 --seed-count 1 --task-count 48 --output data/dev --hash-report reports/dev_hashes_v1_1.json
python scripts/validate_dataset.py --tasks data/dev/stable_steady__seed_0007_tasks.csv --manifest data/dev/stable_steady__seed_0007_scenario_manifest.csv --check-replay --report reports/package_verification/documented_stable_validation.json
pytest -q
```

**Observed result:** requirements already satisfied (`PyYAML 6.0.3`, `pytest 9.0.2`); generation exited 0 and emitted all eight core scenarios; stable sample validation/replay exited 0 with `validation_status=PASS`; pytest exited 0: `35 passed`.

The commands were executed from the extracted package directory, not from the earlier partial workstream view. Captured output files:

- `reports/package_verification/documented_requirements_install.stdout.txt`
- `reports/package_verification/documented_generation.stdout.txt`
- `reports/package_verification/documented_stable_validation.stdout.txt`
- `reports/package_verification/pytest_actual.stdout.txt` and `reports/pytest_results.txt`

## All-scenario validation and replay

Each of the eight independently generated scenario task/manifest pairs in `verification/package_run_a/` was run through `validate_dataset.py --check-replay`. All eight exited 0 and report `validation_status=PASS`, with zero errors. Summary: `reports/package_verification/scenario_validation_summary.csv`. Individual JSON and stdout captures are named `<scenario>_validation.json` and `<scenario>_validation.stdout.txt`.

## Independent deterministic comparison

The same generator/configuration/seed command was run into two separate destinations, `verification/package_run_a/` and `verification/package_run_b/`. All **16 CSV SHA-256 comparisons** (8 task tables + 8 manifests) matched byte-for-byte. Results and per-file digests: `reports/package_verification/determinism_comparison.json`. Canonical config hash: `68e2ba5ad5ab23fbbe32a418b81b14014791978eb3387a5aae3a7f6ed2641c64`.

## Dependency-environment note

A fully isolated virtual environment was also attempted, but this execution environment cannot resolve the configured Python package index (DNS/network unavailable), so it could not download PyYAML/pytest into an empty venv. This is an environment/network limitation, not a test failure. The documented `pip install -r requirements.txt` command completed successfully in the available Python environment because both declared dependencies were already installed. The failed empty-venv install log is retained as `reports/package_verification/fresh_venv_install_attempt.txt`. In a normal connected environment, the documented requirements command installs the two declared dependencies.

## Scope integrity

All workload numbers not confirmed by the simulator audit remain explicitly `PROPOSED` or `BLOCKED` in the YAML and handoff report. No simulator execution sites, completion times, latency outcomes, deadline success, rewards, energy or resource outcomes are generated. The four simulator-owned tables remain empty header templates.

No GitHub writes, commits or pushes were made.
