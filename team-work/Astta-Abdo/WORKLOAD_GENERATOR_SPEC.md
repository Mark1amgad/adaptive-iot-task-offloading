# Workload Generator Specification

**Project:** Risk-Calibrated Adaptive Task Partitioning and Offloading under Repeated Workload and Network Shifts in the IoT–Edge–Cloud Continuum  
**Workstream:** Synthetic task-input dataset and simulator handoff contracts  
**Specification version:** 1.1.0  
**Status:** Implementation complete for reproducible development inputs; numerical benchmark values remain `PROPOSED` / `BLOCKED` pending approval and simulator evidence.

## 1. Scope and data boundary

This package creates only (1) synthetic task-input rows and (2) scenario/run manifests. It does not create decisions, execution sites, queue measurements, task completion times, latency outcomes, deadline success, rewards, energy, or resource outcomes. Those records must come from the iFogSim2 adapter and executed experiments.

The generator output is **development synthetic input data**, not a measured IoT offloading dataset and not the final experiment-results dataset. The `decision_contexts`, `decisions`, `task_outcomes`, and `calibration_log` files provided here are JSON Schema contracts plus empty header-only CSV templates. No example measurement rows are supplied.

ECW and SMD are retained as separate source-dataset audits in `provenance/`. Neither is used to generate task values. No ECW/SMD rows are joined, copied, or relabelled.

## 2. Canonical format, units, and null semantics

Canonical storage is **UTF-8 CSV**, one header row, LF line endings, comma delimiter, no locale-dependent decimal separator. CSV is used because the downstream simulator adapter and review workflow can consume it without a Parquet runtime. CSV data types are defined in `schemas/*.schema.json` and `schemas/DATA_DICTIONARY.md`.

| Quantity | Canonical unit | Rule |
|---|---|---|
| Arrival / absolute simulation timestamps | `ms` | Non-negative integer simulation-clock milliseconds. |
| Relative deadline | `ms` | Positive integer duration assigned before any policy decision. |
| Input / output size | `bytes` | Positive integer byte count; output bytes are synthetic profile assumptions. |
| Task compute demand | `MI` | Positive million-instruction total for the complete task. |
| Compute capacity | `MIPS` | Million instructions per second, where actually exposed by the simulator. |
| Partition / merge overhead | `ms` | Non-negative model parameters; not measurements. |
| Link delay | `ms` | One-way configured link delay; not inferred RTT. |
| Bandwidth | **not locked** | Current topology lists raw numeric bandwidth values but does not establish a byte/s vs bit/s interpretation. A simulator context must leave value/unit null until Ayoub confirms it. |

`units_version=SI-ms-bytes-MI-v1` tags the input record's declared units. Empty CSV cells mean JSON `null` only for schema-declared nullable columns. Empty cells in required fields are validation failures. The generator does not use memory-demand fields because no defensible memory-demand model is established.

## 3. Simulator evidence reviewed and implications

The current pushed repository has a checked-in one-task integration and a three-device prototype. `deliverables/10_iFogSim_Simulation/Topology/Topology_Description.md` reports one `local`, one `edge`, and one `cloud` executor with capacities 1,000 / 2,800 / 44,800 MIPS respectively. The configured local-to-edge and edge-to-cloud uplink delays are 2 ms and 45 ms. The same document lists raw bandwidth values of 10,000 and 100,000 but does not specify their physical units; downlink delay is unspecified in the source description.

`deliverables/02_Methodology/Methodology.md` records a one-task prototype input of 2,500 MI, 12,000 input bytes, 2,000 result bytes and a configured 500 ms deadline. `deliverables/10_iFogSim_Simulation/Simulation_Source/FINAL_STATUS.md` reports preliminary one-task endpoint latencies of 3.51 ms (Local), 7.302857 ms (Edge), and 97.685804 ms (Cloud) in retained pilot traces. Those are single-run integration observations, not nominal service-time distributions and not a calibration basis for larger or multi-task workloads.

The controlling V2 research specification describes a target development topology of four IoT devices, two Edge nodes and one Cloud node. That target is not established by the currently checked-in `Topology_Description.md`, which documents one local executor, one Edge and one Cloud. The four `source_device_id` values generated here are logical source identities; they do not assert that four distinct IoT FogDevices already exist.

The `MEASUREMENT_CONTRACT_V1.md` provides a one-task event/measurement contract and explicitly leaves task-local attribution, fresh utilization semantics, multi-task state, failure handling and energy attribution limited or unresolved. The current implementation does not verify two concurrent local/remote task branches, partition/synchronization/merge hooks, or their timing semantics. For that reason:

- deadline classes and workload ranges remain `PROPOSED`;
- split/merge overheads remain `PROPOSED` until the adapter can account for them;
- network bandwidth's physical unit is `BLOCKED` pending Ayoub's confirmation;
- the two-Edge selection/site mapping and 4-IoT source mapping are `BLOCKED` pending topology verification;
- energy is omitted from the outcome schema because current evidence says cumulative device energy is not defensible as per-task energy.

## 4. Task record semantics

Each row in `data/dev/*_tasks.csv` is one task before a policy decision.

- `task_id` is stable for a given `(scenario_id, seed, task index)` and is shared across all policies that replay the same run.
- `(run_id, task_id)` is the primary task key. The task ID string is not required to be globally unique across different run IDs.
- `application_profile` describes workload semantics; `urgency_class` describes the deadline class. They are separate fields.
- `workload_profile_id` names the configured task-mix profile used by the scenario.
- `source_device_id` cycles through `iot-01` to `iot-04` as logical task sources.
- `required_mi` is the total compute demand before any action is chosen.
- `output_size_bytes` is present only because each synthetic application profile defines an output-byte generation rule. It is a workload assumption, not a measured simulator output.

### Divisibility classes and legal action contract

Only these labels are used:

1. `INDIVISIBLE` — legal actions are `LOCAL`, `EDGE_FULL`, `CLOUD_FULL` only.
2. `DATA_PARALLEL_DIVISIBLE` — the synthetic profile explicitly represents independent data-parallel work. It supports Local and one remote tier (Edge **or** Cloud), never both remote tiers.

Remote computation fraction is `alpha`:

| Action | Remote fraction `alpha` | Local fraction `1-alpha` | Remote tier |
|---|---:|---:|---|
| `LOCAL` | 0.00 | 1.00 | none |
| `EDGE_PARTIAL_25` | 0.25 | 0.75 | Edge |
| `EDGE_PARTIAL_50` | 0.50 | 0.50 | Edge |
| `EDGE_PARTIAL_75` | 0.75 | 0.25 | Edge |
| `EDGE_FULL` | 1.00 | 0.00 | Edge |
| `CLOUD_PARTIAL_25` | 0.25 | 0.75 | Cloud |
| `CLOUD_PARTIAL_50` | 0.50 | 0.50 | Cloud |
| `CLOUD_PARTIAL_75` | 0.75 | 0.25 | Cloud |
| `CLOUD_FULL` | 1.00 | 0.00 | Cloud |

For a divisible task:

```text
local_required_mi  = (1 - alpha) * required_mi
remote_required_mi = alpha * required_mi
```

For the two explicitly named frame/window data-parallel profiles, input and output byte partition fractions are `alpha`. That proportionality assumption is not generalised to arbitrary IoT tasks. Every divisible application profile supplies a stable `partition_model_id`, an input rule, an output rule, `partition_overhead_ms` and `merge_overhead_ms`. Partition/merge overhead applies only when `0 < alpha < 1`; Local-only and full-remote actions do not split/merge. These numeric overheads are `PROPOSED` until the simulator adapter can represent and time the events.

### Workload mix assumptions

- `balanced_v1`: 50% indivisible `SENSOR_INFERENCE`, 25% divisible `VIDEO_FRAME_BATCH`, 25% divisible `PARALLEL_SENSOR_AGGREGATION`; resulting target mix 50% indivisible / 50% divisible.
- `heavy_shift_B_v1`: 20% indivisible `SENSOR_INFERENCE`, 40% divisible `BULK_VIDEO_FRAME_BATCH`, 40% divisible `LARGE_PARALLEL_SENSOR_AGGREGATION`; resulting target mix 20% indivisible / 80% divisible.

These are synthetic experimental design assumptions, not frequencies estimated from ECW, SMD, or Mostafa's dataset inventory.

## 5. Workload profile and deadline table

All task-size/compute values below are smoke-test or shift-stress values. They are not benchmark-calibrated or approved ranges.

| Application profile | Divisibility | Required MI values / range | Input bytes values / range | Output bytes values / range | Partition / merge overhead | Status |
|---|---|---|---|---|---|---|
| `SENSOR_INFERENCE` | Indivisible | 200, 1,000, 4,000 | 2,000, 10,000, 50,000 | 256, 1,024, 2,048 | n/a | `PROPOSED_SMOKE_ONLY` |
| `VIDEO_FRAME_BATCH` | Divisible | 1,000, 4,000 | 10,000, 50,000 | 1,024, 2,048, 4,096 | 5 / 5 ms | `PROPOSED_SMOKE_ONLY` |
| `PARALLEL_SENSOR_AGGREGATION` | Divisible | 1,000, 4,000 | 2,000, 10,000, 50,000 | 256, 1,024, 2,048 | 3 / 4 ms | `PROPOSED_SMOKE_ONLY` |
| `BULK_VIDEO_FRAME_BATCH` | Divisible | 4,000, 8,000, 16,000 | 50,000, 100,000, 250,000 | 2,048, 4,096, 8,192 | 5 / 5 ms | `PROPOSED_SHIFT_SMOKE_ONLY` |
| `LARGE_PARALLEL_SENSOR_AGGREGATION` | Divisible | 4,000, 8,000, 16,000 | 10,000, 50,000, 100,000 | 1,024, 2,048, 4,096 | 3 / 4 ms | `PROPOSED_SHIFT_SMOKE_ONLY` |

Deadlines are assigned before any policy action. Profile urgency weights are stored beside each application profile; deadline sampling uses only the resulting urgency class and its versioned distribution. No action, future shift, policy, outcome or test metric affects a deadline.

| Urgency class | Default probability | Relative deadline distribution | Status / rationale |
|---|---:|---:|---|
| `CRITICAL` | 0.20 | Uniform integer 200–800 ms | `PROPOSED`; illustrative bracket around the prototype's single configured 500 ms deadline only. Not a calibrated interval. |
| `TIME_SENSITIVE` | 0.50 | Uniform integer 800–3,000 ms | `PROPOSED`; requires nominal service-time and queueing evidence across task profiles and tiers. |
| `DELAY_TOLERANT` | 0.30 | Uniform integer 3,000–10,000 ms | `PROPOSED`; requires nominal service-time and queueing evidence across task profiles and tiers. |

The values must be approved and frozen before benchmark/test generation. No benchmark or test outcome was used to tune them.

## 6. Arrival process and deterministic generation

Supported arrivals:

- `poisson`: exponential inter-arrival times with configured rate in tasks/second.
- `on_off`: alternating on/off phases with separate arrival rates and phase durations, all expressed in tasks/second or milliseconds.

The generator uses separate deterministic pseudorandom streams for arrivals and task attributes derived from the user seed. This avoids changing the arrival stream when profile sampling code changes. The YAML configuration is normalised to canonical JSON, combined with generator and units versions, and hashed with SHA-256 into `config_hash`.

Same seed + same configs + same scenario + same `run_id` + same task count yields byte-identical tasks and manifest CSVs. The validator's `--check-replay` regenerates the exact run in a temporary directory and compares hashes.

Task generation does not emit scenario regime labels into task rows. The manifest contains exact regime boundaries with flags `evaluation_metadata_only=true` and `policy_observation=false`. These are offline experiment metadata only.

## 7. Scenario catalogue

| Scenario ID | Factor / design | Arrival process | Condition change | Split | Status |
|---|---|---|---|---|---|
| `stable_steady` | Stable reference | Poisson 0.5 tasks/s | Reference network/Edge profile | train | `PROPOSED` |
| `bursty_on_off` | Arrival bursts only | On: 2.0 tasks/s for 5,000 ms; Off: 0.15 tasks/s for 10,000 ms | Reference network/Edge profile | train | `PROPOSED` |
| `reduced_bandwidth` | Bandwidth scale 0.5 vs reference | Poisson 0.5 | WAN delay held at 45 ms; bandwidth scale only | validation | `PROPOSED`; bandwidth unit still blocked |
| `increased_wan_delay` | WAN one-way configured delay 90 vs 45 ms reference | Poisson 0.5 | Bandwidth scale held at 1.0 | validation | `PROPOSED` |
| `reduced_edge_capacity` | Edge capacity scale 0.5 relative to 2,800 MIPS single-Edge prototype reference | Poisson 0.5 | Network profile held nominal | validation | `PROPOSED`; target two-Edge capacities not verified |
| `task_size_compute_shift` | A balanced profile mix, then B heavy profile mix | Poisson 0.5 | Mix A→B at 50% of arrival window | test | `PROPOSED` |
| `repeated_a_b_a` | Network bandwidth A→B→A (1.0→0.5→1.0) | Poisson 0.5 | One-third / one-third / one-third | test | `PROPOSED`; bandwidth unit still blocked |
| `repeated_aba_task_mix` | Workload profile mix A→B→A | Poisson 0.5 | Balanced→heavy→balanced | test | `PROPOSED` |
| `combined_stress_optional` | Bursts + lower bandwidth + lower Edge capacity + heavy mix | On/off | Combined factors | optional | `PROPOSED_OPTIONAL`; not principal one-factor scenario |
| `unseen_topology_optional` | Unseen topology/capacity | Poisson 0.5 | Capacity 0.75 of a not-yet-verified topology | held-out | `BLOCKED`; do not generate until target topology/capacity is specified |

Scenario arrival rates, shift factors and task mixes are configurable assumptions, not observed source-dataset values. Network/Edge settings are manifest inputs for the simulator team to implement identically across policies; the workload generator itself does not modify simulator topology, link capacity, queue discipline or background load.

## 8. Split protocol and paired policy replay

The split is assigned by **scenario family and seed band**, never by random rows:

- train families: `stable`, `bursty`; seeds 1–60;
- validation families: `network_bandwidth`, `network_wan_delay`, `edge_capacity`; seeds 61–80;
- test families: `task_mix_shift`, `repeated_aba`, `combined_stress`, `unseen_topology`; seeds 81–120.

A scenario family cannot be assigned to more than one split. The all-core CLI's `--seed-count 20` uses seeds 1–20 for train scenarios, 61–80 for validation scenarios and 81–100 for test scenarios. `--seed-count 30` uses 1–30, 61–80 (validation has a 20-seed band, so the current split definition must be expanded by Mark before requesting 30 validation seeds), and 81–110 for test. The automated tests verify that the 20-seed schedule is disjoint and reproducible and reject a 30-seed validation request against the current band. Thus the config currently guarantees 20 paired seeds per principal validation scenario; 30 requires Mark's approval to widen validation's seed band and adjust split ranges.

Every policy in a paired comparison must receive the exact same `tasks.csv` and exogenous network/resource trace/config for its `(run_id, scenario_id, seed)`. Policy random seeds are separate from workload-generation seeds. No policy may receive future `regime_id`, regime boundaries, test labels, or outcome-derived data as observations.

## 9. Six data contracts and join keys

1. **tasks** — generated inputs; primary key `(run_id, task_id)`; join to the manifest by `run_id` and to all downstream logs by `(run_id, task_id)`.
2. **scenario_manifest** — one row per generated run; key `(run_id)`; contains scenario, seed, split, config hash, arrival process and evaluation-only regimes.
3. **decision_contexts** — simulator-produced per-candidate decision-time observations; logical key `(run_id, task_id, policy_id, decision_time_ms, candidate_action, candidate_site_id)`.
4. **decisions** — policy/adapter output; key `(run_id, task_id, policy_id)`; one final decision record per task/policy/run.
5. **task_outcomes** — simulator-produced task result; key `(run_id, task_id, policy_id)`; exactly one final row per task/policy/run.
6. **calibration_log** — calibration candidate-level audit; logical key `(run_id, task_id, policy_id, candidate_site_id, candidate_action)` (with an additional timestamp/window key if the implementation allows repeated calibration estimates).

Decision contexts and calibration records are separate: calibration log may contain actual completion/residual only after simulation. The decision context must never contain actual completion, actual latency, reward, energy, final status, future regime, scenario split, test label or other post-decision fields.

For a completed task, `completion_time_ms` is the final task completion timestamp. For partial work, remote result transfer follows remote execution; the merge/join begins after the Local branch and remote result transfer have completed. `completion_time_ms` is the resulting final joined completion timestamp. `end_to_end_latency_ms = completion_time_ms - task arrival_time_ms`. Branch timestamps are absolute simulator-clock milliseconds. `ON_TIME`, `LATE`, `FAILED`, and `UNRESOLVED_AT_HORIZON` are mutually exclusive final statuses; unresolved deadline result is null rather than fabricated as a miss or success.

Final reconciliation must hold separately for every run and policy:

```text
Generated tasks = ON_TIME + LATE + FAILED + UNRESOLVED_AT_HORIZON
```

A no-feasible-site or fallback decision belongs in the decision record/reason. It must not make a generated task disappear from the final task-outcome denominator.

## 10. ECW / SMD provenance boundary

- ECW audit v1 records shape `(1022, 720, 16)`, but channel meanings, axis/time semantics, physical units, normalisation, provenance and licence remain unestablished. ECW is not used for generated task attributes or capacity/network parameters.
- SMD audit v1 records 28 server-machine sequences with 38 dimensions and test anomaly labels. SMD is not an IoT task dataset. Anomaly labels are not task failure, deadline miss, network outage or CPU-failure labels. If used for optional abnormal-context work later, it must remain a separate, domain-labelled context source.
- Mostafa's `team-work/Mostafa/Dataset/` inventory and `audit_output/DATASET_AUDIT.md` remain their source of truth. This package does not repeat that inventory; it uses only the prior ECW/SMD source audit caveats.

## 11. Unresolved evidence needed before benchmark approval

Ayoub must provide: (1) current V2 topology code and actual counts/site IDs for 4 IoT, 2 Edge, 1 Cloud; (2) local/edge/cloud MIPS and RAM per device; (3) explicit bandwidth raw-unit and transfer-time conversion; (4) uplink and downlink one-way latency semantics; (5) queue length/wait and available-capacity observation hooks; (6) per-task stable ID/correlation hooks; (7) measured nominal execution/transfer/E2E service-time distributions for each proposed task profile at each tier, including queueing under the nominated baseline load; (8) implemented partial branch concurrency, input/output transfer, split/merge, join timing and branch failure/unresolved behaviour; and (9) power model/per-task attribution evidence before energy can be added.

Mark must approve: workload mix proportions, profile distributions and output-byte rules, deadline class ranges, scenario rates, shift magnitudes, partition overheads, split/merge model assumptions, seed bands, and the exact held-out profiles/scenarios. Until then, `data/dev/` remains development-only.
