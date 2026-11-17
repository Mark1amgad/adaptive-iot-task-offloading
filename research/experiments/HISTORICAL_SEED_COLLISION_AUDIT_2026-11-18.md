# Historical Seed Collision Audit — 2026-11-18

## Decision

**No seeds 2050–2069 are allocated.** The interval remains a proposed Calibration range only. Final Test seeds remain unallocated and unapproved. No Final Benchmark run is authorized.

## Repository-visible evidence reviewed

- `research/experiments/SEED_REGISTRY_V1.csv` and `SEED_REGISTRY_V2.csv`.
- V2 registry README and its explicit incompleteness warning.
- Abdo Development data/manifests and archive directory README.
- Repository-visible `audit_output` workload/policy runs.
- `deliverables/10_iFogSim_Simulation/results/aba_paired_20seed_20261117` manifests/workloads.
- Omar V26 `Results/manifest.csv`, which records the seed sets used in that workstream.

The V2 registry preserves known historical uses including workload-development seeds 7, 61, 81 and 1300 (1300 is Development/CI only); pilot/policy seeds 42–45; A-B-A historical seeds 101–121 (including historical test-labelled reuse); Omar workstream seed sets 201–205, 301–305, 401–405, 901–904, 906, 951–954 and 956; and training seed 909. Historical entries are retired. The registry contains no approved Test allocation.

## Collision check for 2050–2069

The registry itself has no allocated row in 2050–2069. This is **not** a complete collision clearance. The repository includes ZIP archives under `team-work/Astta-Abdo/archives` and other team archive folders; their internal manifests were not enumerated by this GitHub source audit. Local experiment-machine folders, unpushed branches, external copies, and team members' working directories are also outside the available repository evidence.

Consequently, the full historical collision check is **PENDING**, and no seed in 2050–2069 may be allocated yet. The interval is a proposed Calibration candidate range only, not an approved range.

## Required completion before allocation

1. Enumerate every ZIP/archive and inspect contained manifests, CSVs, JSONL and experiment logs.
2. Scan local experiment machines and all team workspaces/branches.
3. Extract every seed from run manifests and artifact metadata, not only filenames.
4. Add every newly discovered use to V2 registry as retired, with exact source and purpose; preserve V1 unchanged.
5. Re-run duplicate/cross-split checks and freeze the registry hash.
6. Obtain Mark's Experimental Protocol approval before any Calibration allocation. Final Test remains separately unallocated pending explicit approval.

## Registry changes in this commit

No seed row was added, removed, renumbered, allocated, or approved. Only the V2 registry README was extended to record the 2050–2069 proposal and the no-allocation gate. V1 is unchanged.
