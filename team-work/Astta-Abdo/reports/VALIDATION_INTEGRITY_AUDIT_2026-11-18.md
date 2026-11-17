# Validation and Reproducibility Integrity Audit — 2026-11-18

## Changes

- CI generates all eight Development scenarios under an isolated runner-temp staging directory.
- Each staged task/manifest pair is validated, replay-checked, and SHA-256 inventoried before publication.
- The source-input verifier accepts an explicit staging directory and writes its JSON report to a sibling temporary file, flushes it, then publishes with `os.replace`.
- The workflow runs pytest before replacing the existing `data/dev` directory. On successful validation only, the previous directory is moved aside and restored if the staged directory move fails.
- Artifacts are uploaded only after the validation-and-publication job succeeds. Failed validation therefore cannot publish newly generated partial scenario files as the current Development dataset.
- Source-side verification remains explicitly separate from Simulator validation; the verifier does not create simulator outcomes or claim runtime source mapping.

## Reproduction procedure

The workflow is the authoritative reproducibility procedure: seed 1300, Development split, eight scenarios, 48 tasks each, scenario/manifest validation with replay, source SHA-256 verification, then pytest. The report paths remain canonical `data/dev/...` paths even when the bytes are first validated in staging.

## Limits

- This protects the CI publication path. It does not claim atomicity for arbitrary manual invocations of the generator outside this workflow.
- A process/runner crash during the two-directory rename window is not a transactional filesystem guarantee; the previous directory is retained until the new directory is in place, and the script rolls back on a reported move failure.
- No Final Benchmark or Simulator run is invoked by this workflow.
- The previously committed CI result (56 passed) predates this integrity change. A new CI run on the resulting commit is required before calling the change validated.
