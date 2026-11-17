# Seed Registry V2 — explicit allocation and leakage guard

**Status:** HISTORICAL INVENTORY INCOMPLETE; no final held-out Test seed is approved.

This registry is the sole source of seed allocation for the industrial workload generator. It consolidates the repository-visible historical inventory from V1, preserves known uses as retired, records seed 61 (used in earlier network development samples), and reserves seed 1300 for development/CI only.

## Allocation rules

- A numeric seed may appear only once in this registry. Duplicate numeric seeds are rejected; assignment to more than one split is a hard cross-split leakage failure.
- Only allocated or approved entries may be used. Test generation requires status approved.
- All known historical seeds are retired, including seed 81, which was used for workload-generator development and is never eligible for final held-out testing.
- Seeds used in older Train, Validation, Development, pilot, debug, or test-labelled runs remain historical records and cannot be recycled for another split.
- Seed 1300 is allocated only to Development for generator verification and CI. It is not a Train, Validation, or Test seed.
- The registry currently contains no approved Train, Validation, or Test allocations. The generator must fail closed when a requested split has no allocated/approved seed.
- Record experiment family, split, status, date, source artifact, purpose and notes for every future allocation before use. Freeze the registry and record its SHA-256 in each future experiment manifest.

## Historical coverage limitation

This file consolidates the repository-visible V1 inventory and the known development seed 61. It does not prove that every local machine, unpushed branch, temporary folder, or team member archive has been inspected. Do not assume an unlisted seed is unused. Before approving final seeds, scan local experiment archives and each team workstream, append all discovered use, then allocate fresh non-overlapping Train/Validation/Test ranges.

The V1 source inventory remains unchanged for audit history at research/experiments/SEED_REGISTRY_V1.csv.
