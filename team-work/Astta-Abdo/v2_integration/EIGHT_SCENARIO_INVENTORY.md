# Eight-Scenario V2 Workload Integration Inventory

**Generator branch:** `abdo/industrial-workload-replay-seed-v2`  
**Generator version:** 1.2.0  
**Development seed:** 1300 (Development/CI only; existing Seed Registry remains authoritative)  
**Expected task rows:** 48 per scenario, 384 total  
**Target contract:** 100 logical IoT sources / 20 target Edge / 1 target Cloud  
**Actual topology:** `null`; `NOT_VERIFIED_PENDING_AYOUB_CONFIRMATION`  
**Simulator validation:** NOT RUN BY THIS PACKAGE; pending Ayoub's integrated V2 adapter execution.

| Scenario ID | Task input | Manifest | Seed | Expected rows | Intended varied dimension | Held fixed / caveat |
|---|---|---|---:|---:|---|---|
| stable_steady | `data/dev/stable_steady__seed_1300_tasks.csv` | matching `*_scenario_manifest.csv` | 1300 | 48 | Stable Poisson arrival baseline | Nominal reference profiles; numerical settings remain proposed/reference |
| bursty_on_off | `data/dev/bursty_on_off__seed_1300_tasks.csv` | matching manifest | 1300 | 48 | On/off arrival process | Network and Edge profile IDs held at nominal reference |
| reduced_bandwidth | `data/dev/reduced_bandwidth__seed_1300_tasks.csv` | matching manifest | 1300 | 48 | Network bandwidth profile | Workload generation and Edge profile held; bandwidth unit remains blocked |
| increased_wan_delay | `data/dev/increased_wan_delay__seed_1300_tasks.csv` | matching manifest | 1300 | 48 | WAN delay profile | Workload generation and Edge profile held; target link interpretation needs Ayoub |
| reduced_edge_capacity | `data/dev/reduced_edge_capacity__seed_1300_tasks.csv` | matching manifest | 1300 | 48 | Edge capacity profile | Workload generation and network profile held; capacity is proposed |
| task_size_compute_shift | `data/dev/task_size_compute_shift__seed_1300_tasks.csv` | matching manifest | 1300 | 48 | A/B task-mix and size/compute shift | Network and Edge profile held at nominal reference |
| repeated_a_b_a | `data/dev/repeated_a_b_a__seed_1300_tasks.csv` | matching manifest | 1300 | 48 | Existing repeated network A→B→A condition schedule | Preserve current exact A1/A2 task-template replay and current seed governance |
| repeated_aba_task_mix | `data/dev/repeated_aba_task_mix__seed_1300_tasks.csv` | matching manifest | 1300 | 48 | Existing repeated task-mix A→B→A schedule | Preserve existing A1/A2 replay; do not reinterpret as network-only |

The table describes the scenario intent/configuration dimensions, not a claim that the simulator has run. The generator's task CSV and scenario manifest are separate immutable inputs. For each run, the verification script computes SHA-256 over the exact bytes of both files and records the manifest's scenario ID, seed, task count, and config hash. It also hashes the config files and verifier script. Git blob SHA values are not substituted for SHA-256.

## Common source fields preserved

`task_id`, `run_id`, `seed`, `scenario_id`, `source_device_id`, `urgency_class`, `arrival_time_ms`, `input_size_bytes`, `output_size_bytes`, `required_mi`, `splittability`, `partition_model_id`, `partition_overhead_ms`, `merge_overhead_ms`, `input_partition_model`, `output_partition_model`, `relative_deadline_ms`, `absolute_deadline_ms`, `units_version`, `config_hash`, `generator_version`.

## Expected target source mapping

Five logical IoT IDs per target Edge, in ascending contiguous groups:
`iot-001..iot-005 → edge-001`; … ; `iot-096..iot-100 → edge-020`.
This is a target contract only. Runtime source IDs and actual parent Edge IDs must be exported by Ayoub's simulator and checked against it.

## Network / capacity configuration status

Scenario manifest values are carried as proposed/reference inputs. The physical bandwidth unit and transfer conversion, uplink/downlink semantics, target IoT–Edge / Edge–Cloud link definitions and latencies, and final network-shift parameters remain BLOCKED pending Ayoub. Per-device V2 capacity is also not assumed from the target counts. No parameter is promoted to confirmed by this integration package.
