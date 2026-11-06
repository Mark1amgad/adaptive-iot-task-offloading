# Repository baseline inspection — workload extension v1.1.0

**Repository:** `Mark1amgad/adaptive-iot-task-offloading`  
**Branch inspected:** `main`  
**Latest pushed commit inspected:** `39d6cd448ba5a15e690ac67ff777017a445ce577`  
**Committer timestamp:** `2026-11-03T16:45:53Z`  
**Tree entries reported:** 892  
**Inspection source:** authenticated GitHub connector, read-only.

## Existing repository sources inspected

- `FILE_INDEX.md`, `WORKSPACE_AUDIT_REPORT.md`, `research/references/REFERENCES_INDEX.md`.
- `deliverables/02_Methodology/Methodology.md`, `docs/experiment-plan.md`, `docs/system-architecture.md`, `docs/state-action-reward.md`.
- `deliverables/10_iFogSim_Simulation/Topology/Topology_Description.md`.
- `deliverables/10_iFogSim_Simulation/Simulation_Source/MEASUREMENT_CONTRACT_V1.md`, `FINAL_STATUS.md`, and `Simulation_Notes.md`.
- `audit_output/IFOGSIM_EVENT_FLOW.md`, `iFogSim_DISCOVERY_REPORT.md`, and `DATASET_AUDIT.md`.
- `team-work/Astta-Abdo/README.md`, its dataset/deliverable/draft/note/research placeholder readmes and current prototype code.
- `team-work/Mostafa/Dataset/README_AR.md` and `REPRODUCIBILITY_GUIDE_AR.md`, plus shared provenance and `LICENSE_STATUS.md`.

Mostafa's repository inventory and suitability work was treated as the source of truth; this workstream does not repeat it. The existing Astta-Abdo RL prototype and original audit reports are not replaced by this extension.

## Current state and scope boundary

At the inspected commit, `team-work/Astta-Abdo/` contains its README, the `adaptive_offloading/` prototype and placeholder folders (`datasets`, `deliverables`, `drafts`, `notes`, `research`). No synthetic workload generator, six-table schema set, or workload data card was present there. The local extension is designed as an additive overlay under that directory.

The repository root does not contain `MARK_RESEARCH_SPECIFICATION_V2.md`. The supplied handoff package's copies of `MARK_RESEARCH_SPECIFICATION_V2.md` and `ABDO_FINAL_DATASET_SPECIFICATION_V2.md` are retained under this extension's `provenance/` folder, with `_handoff_copy` names. The canonical V2 specification still needs to be added to the repository by the project owner.

## Simulator evidence and limits

The checked-in topology document describes one Local executor (1,000 MIPS), one Edge executor (2,800 MIPS), and one Cloud executor (44,800 MIPS); configured Local→Edge and Edge→Cloud uplink delays are 2 ms and 45 ms. Raw bandwidth values are not associated with a verified physical unit, and downlink delay is unspecified. The V2 research target (four IoT devices, two Edge nodes, one Cloud) is not proven by that prototype file.

The checked-in methodology describes a single 2,500 MI, 12,000-byte input, 2,000-byte output, one-PE task with a configured 500 ms deadline. Retained pilot traces report Local 3.51 ms, Edge 7.302857 ms, and Cloud 97.685804 ms. These are single-task prototype observations, not service-time distributions or benchmark calibration. The measurement contract gives one-task event semantics but does not establish concurrent partial-branch, merge, multi-task, or per-task energy support. Therefore task distributions, deadline bands, split/merge overhead, and scenario stress factors remain proposed; missing bandwidth units, target topology capacity, and site mapping remain blocked until Ayoub supplies implementation evidence.

## Dataset source boundary

- ECW and SMD remain separate, source-audited telemetry datasets and are not inputs to this generator.
- ECW's 16 channels are anonymous and its axes, time semantics, units, scaling, provenance and license remain unresolved.
- SMD is server-machine telemetry with anomaly labels, not IoT task data; anomaly labels are not task failures or deadline misses.
- Mostafa's dataset audits remain authoritative for the other candidate sources. This extension only records the minimum caveats needed to prevent misuse.

## Non-modification statement

This is a local overlay package, not a GitHub branch update. No repository file was committed, pushed, staged, or modified through GitHub. The existing checked-in Astta-Abdo prototype files remain outside the overlay and are not included as replacement files.
