# Seed Registry V1 — Initial Historical Inventory

**Status:** INCOMPLETE. No final test seeds are approved in this version.

This CSV is the initial repository-visible inventory of known seed use. It is deliberately conservative: any seed already used in a pilot, development run, prior test-labelled run, training run, or team experiment is recorded so it is not silently recycled.

## Rules

- The registry is organized by `experiment_family`; a seed's numeric value alone does not establish independence.
- `split` records historical use, not an assertion that the old allocation was methodologically valid.
- `historical_test_reused` means the seed appeared in an earlier test-labelled run but is now retired from final confirmatory allocation.
- No row with `split=test` and `status=approved` exists yet. Therefore this file does not authorize a final test run.
- Before allocating final seeds, inspect the experiment machine's local archive, all team branches, and run manifests. Add each discovered use with its source and date.
- After the inventory is complete, reserve fresh seed lists for train, validation, and test, freeze this CSV, and record its SHA-256 in every run manifest.
- A final-run validator must reject unregistered seeds, duplicate seeds within a family, cross-split reuse, and any seed already marked as used for development/pilot/debugging.

## Known limitations

This inventory is based on repository-visible artifacts and conversation-confirmed prior use as of 2026-11-17. It is not yet a complete scan of local archives or every team member's working directory. Do not infer that an unlisted number is unused.
