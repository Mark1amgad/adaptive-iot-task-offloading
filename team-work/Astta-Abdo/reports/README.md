# Reproducibility and validation reports

## Current V1.2.0 verification

- `dev_hashes_v1_2.json`: SHA-256 values for the eight seed-1300 Development task/manifest files and canonical configuration hash.
- `*_seed_1300_validation.json`: machine-readable validation and deterministic replay results for each current Development pair.
- `pytest_results_v1_2.txt`: current automated test result (**44 passed**; runtime intentionally omitted so the report is reproducible).
- The matching CI workflow run is recorded in the branch's pull request and GitHub Actions.

## Historical records

Older files that mention seeds 7, 61, 81, earlier generic profile identifiers, or the V1.1 pipeline are retained as historical evidence only. They do not describe the current Development dataset and must not be used as final Train/Validation/Test allocations or benchmark evidence.

- `dev_hashes_v1_1.json`, older `*_validation.json`, and `package_verification/`: historical V1.1 verification artifacts.
- `pytest_results.txt`: historical V1.1 test result.
- `LOCAL_VALIDATION_2026-11-05.md`: prior local validation notes.
- `OVERLAY_FILE_MANIFEST.txt`: prior overlay packaging inventory.
