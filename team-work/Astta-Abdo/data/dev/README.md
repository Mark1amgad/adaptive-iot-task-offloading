# Development synthetic input samples

These eight small CSV task/manifest pairs are deterministic development and smoke-test inputs generated with configuration version 1.1.0. They contain 48 tasks per scenario and are **not** approved benchmark distributions or simulator experiment results.

- `*_tasks.csv`: generated task inputs only.
- `*_scenario_manifest.csv`: scenario/run metadata, including evaluation-only regime boundaries.
- No decisions, decision-time observations, actual site assignments, completion times, latency, deadline success, reward, energy, or resource outcomes are contained here.
- The generator can reproduce the samples exactly using `python scripts/generate_workloads.py --scenario all-core --seed 7 --seed-count 1 --task-count 48 --output data/dev --hash-report reports/dev_hashes_v1_1.json`.
- All scenario/task development values remain `PROPOSED` until Mark approves them and Ayoub supplies the required simulator calibration evidence.
