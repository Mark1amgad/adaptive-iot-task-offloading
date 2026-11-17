# Development synthetic input samples

These eight small CSV task/manifest pairs are deterministic development inputs generated with workload generator version 1.2.0 and registry-allocated development seed 1300. Each scenario contains 48 task rows. They are **proposed synthetic configurations**, not approved benchmark distributions, factory measurements, industrial traces, or simulator experiment results.

- `*_tasks.csv`: generated task inputs only.
- `*_scenario_manifest.csv`: scenario/run metadata, including evaluation-only regime boundaries, the target topology, and an explicitly unverified actual topology.
- The two A→B→A manifests use exact A1/A2 task templates and relative arrival offsets; B has a separate task-template stream.
- No decisions, decision-time observations, actual site assignments, completion times, latency, deadline success, reward, energy, or resource outcomes are contained here.
- Reproduce with `python scripts/generate_workloads.py --scenario all-core --dataset-split development --seed 1300 --seed-count 1 --task-count 48 --output data/dev --hash-report reports/dev_hashes_v1_2.json`.
- Seed 1300 is Development/CI only. Historical seed 81 and other recorded historical seeds are retired. No final Train, Validation, or Test allocation is approved.
- All scenario/task parameters remain `PROPOSED` until Mark approves them and Ayoub supplies topology confirmation and simulator calibration evidence.
