# Package verification evidence

This directory contains execution evidence produced from the packaged `team-work/Astta-Abdo/` tree.

- `documented_requirements_install.stdout.txt`: documented dependency command; both declared packages were already satisfied.
- `documented_generation.stdout.txt`: documented eight-core-scenario generation command.
- `documented_stable_validation.stdout.txt` and `documented_stable_validation.json`: documented stable-sample validation with deterministic replay.
- `pytest_actual.stdout.txt`: actual full test output; duplicated at `reports/pytest_results.txt` for discoverability.
- `<scenario>_validation.json` plus `.stdout.txt`: validator output and JSON report for each of eight core scenarios, using separately regenerated files with `--check-replay`.
- `generation_a.stdout.txt`, `generation_b.stdout.txt`, `hash_a.json`, `hash_b.json`, and `determinism_comparison.json`: two independent output-directory runs and all task/manifest SHA-256 comparisons.
- `scenario_validation_summary.csv`: compact pass/error/task-mix summary.
- `package_integrity_report.json`: machine-readable checks for schema presence, header-only templates, per-scenario validation and deterministic comparisons.
- `fresh_venv_install_attempt.txt`: recorded failed attempt to install dependencies into an empty virtualenv because the execution environment could not resolve the package index. It is included as an environment limitation, not as a test failure.
