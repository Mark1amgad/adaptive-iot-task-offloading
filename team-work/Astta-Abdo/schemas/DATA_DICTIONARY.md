# Data Dictionary and Contracts (v1.1.0)

All six machine-readable record contracts are in the adjacent JSON Schema files. CSV blank cells represent `null` only where the schema declares a nullable type. Do not infer outcomes or simulator observations from absent cells.

## A. `tasks.csv` — generator-produced inputs

| Field | Type / unit | Required / null rule | Meaning and generation source |
|---|---|---|---|
| `task_id` | string | required, non-empty | Stable ID derived from scenario, seed and task index. |
| `run_id` | string | required | Unique run identity; same value across the task rows in one generated run. |
| `seed` | integer | required, >=0 | Workload generator seed; policy randomness uses a separate seed. |
| `scenario_id` | string | required | Scenario configuration identifier. |
| `workload_profile_id` | string | required | Configured application mix/schedule identifier. |
| `source_device_id` | string | required | Logical IoT source identity; not a claim that an equivalent FogDevice has already been instantiated. |
| `application_profile` | string | required | Application/workload semantics, distinct from urgency. |
| `urgency_class` | enum | required | Exactly `CRITICAL`, `TIME_SENSITIVE`, `DELAY_TOLERANT`. |
| `arrival_time_ms` | integer, ms | required, >=0 | Synthetic arrival time from Poisson or on/off process. |
| `input_size_bytes` | integer, bytes | required, >0 | Synthetic input size drawn from application profile. |
| `output_size_bytes` | integer, bytes | required in v1.1 | Synthetic expected output-byte size drawn from application profile; not a measured result. |
| `required_mi` | number, MI | required, >0 | Total pre-decision compute demand for the task. |
| `splittability` | enum | required | Exactly `INDIVISIBLE` or `DATA_PARALLEL_DIVISIBLE`. |
| `partition_model_id` | string/null | required column; null for indivisible | Explicit data-parallel partition model. |
| `partition_overhead_ms` | number/null, ms | required column; null for indivisible | Proposed task-model overhead; applied only to mixed local/remote actions. |
| `merge_overhead_ms` | number/null, ms | required column; null for indivisible | Proposed merge overhead; applied only to mixed local/remote actions. |
| `input_partition_model` | string/null | required column; null for indivisible | `PROPORTIONAL_TO_COMPUTE_ALPHA` only for the configured synthetic frame/window profiles. |
| `output_partition_model` | string/null | required column; null for indivisible | Same scoped assumption for output bytes. |
| `relative_deadline_ms` | integer, ms | required, >0 | Assigned before decision from urgency-specific distribution. |
| `absolute_deadline_ms` | integer, ms | required | Exactly `arrival_time_ms + relative_deadline_ms`. |
| `units_version` | string | required | Constant `SI-ms-bytes-MI-v1`. |
| `config_hash` | SHA-256 hex | required | Hash of canonical workload/scenario configs plus generator/units versions. |
| `generator_version` | string | required | Generator software version. |

**Primary key:** `(run_id, task_id)`. The same exact tasks CSV is replayed for each policy.

## B. `scenario_manifest.csv` — generator-produced run metadata

| Field | Type / unit | Meaning |
|---|---|---|
| `run_id`, `seed`, `scenario_id`, `scenario_family` | string / integer | Run identity and evaluation family. |
| `scenario_status` | string | `PROPOSED`, `PROPOSED_OPTIONAL`, or `BLOCKED...`; not a policy input. |
| `workload_profile_id` | string | The configured task-mix schedule for this run. |
| `arrival_process_type` | enum | `poisson` or `on_off`. |
| `arrival_process_parameters_json` | JSON string | Arrival-rate and phase parameters with units recorded in YAML. |
| `task_count` | integer | Number of generated task rows. |
| `generation_window_end_ms` | integer, ms | End of task-generation arrival window; **not** simulator termination time or task completion horizon. |
| `regime_timeline_json` | JSON string | Evaluation-only regime labels and start/end times; every entry sets `policy_observation=false`. |
| `network_profile_id`, `network_profile_json` | string / JSON string | Exogenous network profile and factor values. |
| `edge_capacity_profile_id`, `edge_capacity_profile_json` | string / JSON string | Exogenous edge capacity/load profile and factor values. |
| `task_mix_profile_id`, `task_mix_profile_json` | string / JSON string | Application profile mix or A/B/A schedule. |
| `topology_id` | string | Intended target topology reference; V2 target status is proposed. |
| `dataset_split` | enum | `train`, `validation`, or `test`, based on family and seed band. |
| `split_strategy_id` | string | Versioned split definition. |
| `paired_seed_plan_json` | JSON string | Minimum/preferred paired seeds per scenario and run-plan status. |
| `config_hash`, `generator_version` | string | Reproducibility provenance. |
| `policy_replay_contract` | string | Explicit identical input/exogenous trace reuse requirement. |

**Primary key:** `run_id`. `regime_timeline_json`, `scenario_family` and `dataset_split` are analysis metadata and must not be sent as future policy observations.

## C. `decision_contexts.csv` — simulator adapter only; schema-only in this package

One row per task, policy and candidate action/site at decision time. This record must describe only facts observable or computed by an approved model at that time. The values `cpu_capacity_mips`, `cpu_utilization_fraction`, `available_cpu_capacity_mips`, `queue_length_tasks`, `estimated_queue_wait_ms`, `link_bandwidth_value`, `link_bandwidth_unit`, `link_delay_ms`, and predicted times are nullable when not actually available. A non-null bandwidth value requires a non-null explicit unit. `predicted_*` and `conservative_completion_estimate_ms` are durations remaining from the decision instant; `remaining_deadline_slack_ms` is the available deadline budget from that same instant.

**Logical key:** `(run_id, task_id, policy_id, decision_time_ms, candidate_action, candidate_site_id)`.

Forbidden decision-context fields include actual completion/latency, final status, deadline success, reward, energy, actual execution site, future regime identifiers/labels/boundaries, scenario family/ID, train/test split and test labels. `calibration_margin_ms` may only use calibration history available before the decision.

## D. `decisions.csv` — policy/adapter only; schema-only in this package

One row per task/policy/run. `requested_action` must be one of the nine legal full/partial actions. For partial action, exactly one remote tier is present along with one Local site. `feasible_action_set_json` is a JSON string array. `selected_action_feasible` and `fallback_used` are booleans; a used fallback requires `fallback_reason`. `decision_time_ms` is simulation time; `decision_wall_clock_ms` is wall-clock decision processing time.

**Primary key:** `(run_id, task_id, policy_id)`.

## E. `task_outcomes.csv` — simulator only; schema-only in this package

One final row per task/policy/run. Event timestamps are absolute simulation-clock milliseconds. Full Local/Edge/Cloud actions use `full_execution_site_id` and full-execution start/end. Partial actions require separate Local branch start/end, remote input transfer start/end, remote branch start/end, result-transfer start/end, and partition/merge events. The remote result transfer follows remote branch execution; the merge/join starts only after the Local branch and remote result transfer have completed. `arrival_time_ms` must match the generated input task exactly; `observed_until_ms` is required when status is unresolved at the simulation horizon. `completion_time_ms` is the final task-level completion after the required join; `end_to_end_latency_ms = completion_time_ms - arrival_time_ms`.

`final_status` is exactly `ON_TIME`, `LATE`, `FAILED`, or `UNRESOLVED_AT_HORIZON`. For unresolved-at-horizon, `completion_time_ms`, `end_to_end_latency_ms`, and `deadline_met` are null; `unresolved_at_horizon=true`. On-time and late require measured completion and latency. Failed tasks cannot be marked deadline-met. A no-feasible-site/fallback selection is retained in decisions; it does not remove the task from reconciliation.

**Primary key:** `(run_id, task_id, policy_id)`.  
**Reconciliation:** `generated = ON_TIME + LATE + FAILED + UNRESOLVED_AT_HORIZON` for each policy/run.

Energy fields are intentionally excluded from this schema. Ayoub must verify the iFogSim power model, units and per-task attribution before energy may be added.

## F. `calibration_log.csv` — calibration layer only; schema-only in this package

One row per task/policy/candidate site/action calibration record (add a time/window key if multiple records exist for the same tuple). Predicted and actual completion are durations from the decision instant. `prediction_residual_ms = actual_completion_time_ms - predicted_completion_time_ms`; actual and residual are null until a corresponding simulator execution has completed. `conservative_completion_estimate_ms` is compared with `remaining_deadline_slack_ms`. `evaluation_regime_id` is offline analysis metadata only and is prohibited from decision contexts.

**Logical key:** `(run_id, task_id, policy_id, candidate_site_id, candidate_action)` plus calibration time/window if repeated.

## Legal action table

| Action | `offload_fraction` | `local_fraction` | `remote_tier` | Splittability |
|---|---:|---:|---|---|
| `LOCAL` | 0 | 1 | null | Both |
| `EDGE_FULL` | 1 | 0 | `EDGE` | Both |
| `CLOUD_FULL` | 1 | 0 | `CLOUD` | Both |
| `EDGE_PARTIAL_25` | 0.25 | 0.75 | `EDGE` | Divisible only |
| `EDGE_PARTIAL_50` | 0.50 | 0.50 | `EDGE` | Divisible only |
| `EDGE_PARTIAL_75` | 0.75 | 0.25 | `EDGE` | Divisible only |
| `CLOUD_PARTIAL_25` | 0.25 | 0.75 | `CLOUD` | Divisible only |
| `CLOUD_PARTIAL_50` | 0.50 | 0.50 | `CLOUD` | Divisible only |
| `CLOUD_PARTIAL_75` | 0.75 | 0.25 | `CLOUD` | Divisible only |
