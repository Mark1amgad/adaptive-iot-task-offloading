# Abdo — Workload Engineering and Dataset Handoff

Confirmed contributions:

- `research/audits/` — ECW and SMD technical audits, task-offloading feature coverage, and dataset suitability/integration assessment.
- `archives/marks.zip` — package identified by Mark as Abdo's contribution.
- `archives/Astta-Abdo_Final_Workload_Dataset_Overlay_v1_1_1_COMPLETE.zip` — final workload-dataset overlay.
- `adaptive_offloading/` — earlier offloading-related Python code and tests.
- Workload package — deterministic synthetic workload generator, validator, YAML profiles, JSON Schemas, data dictionary, development scenarios, provenance, verification evidence, and handoff documentation.

`ABDO_DATASET_HANDOFF_PACKAGE.zip` is stored under Mark because Mark assembled it and sent it to Abdo as a handoff. Its contents are inputs, not an archive authored by Abdo.

No simulator decisions, completion times, rewards, energy values, or final task outcomes are fabricated in this package.


Target topology contract: `v2_target_100iot_20edge_1cloud` = 100 logical IoT sources, 20 target Edge nodes and one target Cloud node, with five source IDs assigned to each target Edge. This is not an actual deployment assertion. `actual_topology_id=null` and `actual_topology_status=NOT_VERIFIED_PENDING_AYOUB_CONFIRMATION` remain until Ayoub verifies the simulator. Bandwidth units, uplink/downlink, IoT–Edge and Edge–Cloud links, latency and network-shift parameters remain BLOCKED pending his confirmation.


Latest topology update verification: Development scenarios/manifests are regenerated with seed 1300 under the 100-IoT/20-Edge/1-Cloud target contract. The latest successful pipeline run reports 47 passing tests and 8/8 scenario-manifest validation passes. These checks validate the generator contract only; actual simulator topology and network parameters remain pending Ayoub confirmation.
