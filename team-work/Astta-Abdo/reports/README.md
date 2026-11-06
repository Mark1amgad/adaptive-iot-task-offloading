# Reproducibility and validation reports

- `dev_generation.log`: stdout from the eight-scenario development generation command.
- `dev_hashes_v1_1.json`: SHA-256 values for all generated task/manifest files and canonical configuration hash.
- `*_validation.json`: machine-readable validation and deterministic replay results for each development pair.
- `*_validation.stdout.json`: matching command stdout.
- `pytest_results.txt`: full automated test summary.
- `determinism_verification.txt`: independent repeat-generation hash comparison.
- `scenario_validation_summary.csv`: task counts and divisibility mix by development scenario.
- `OVERLAY_FILE_MANIFEST.txt`: complete list of additive files packaged for local overlay application.
