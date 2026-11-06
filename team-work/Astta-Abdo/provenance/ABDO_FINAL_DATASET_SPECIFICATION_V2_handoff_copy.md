# Abdo Handoff — Synthetic Workload Dataset Specification (V2: Full + Constrained Partial Offloading)

**Project:** Risk-Calibrated Adaptive Task Partitioning and Offloading under Repeated Workload and Network Shifts in the IoT–Edge–Cloud Continuum  
**Prepared by:** Mark  
**Version:** 2.0 — implementation handoff  
**Date:** 3 November 2026

## 1. Your objective

Build the reproducible **synthetic IoT task-workload generator and dataset schema** for full and constrained partial offloading. The generator must create task records, mixed urgency classes, task-specific deadlines, explicit divisible/indivisible workload profiles, and controlled scenario manifests before any policy makes a decision.

This is not permission to invent execution outcomes. Actual selected sites, completion times, deadline success, energy, and resource outcomes must be captured by the integrated iFogSim2 experiments. Abdo owns the workload generator/schema and data validation; the simulator integration must supply measured execution logs. The final combined experimental dataset cannot exist until those simulator runs have occurred.

## 2. Read first

Use the current pushed repository as the single source of truth. Start with:

- `FILE_INDEX.md`
- `research/references/REFERENCES_INDEX.md`
- `research/literature_review/research_gaps/`
- `deliverables/02_Methodology/`
- `WORKSPACE_AUDIT_REPORT.md`
- Your existing files under `team-work/Astta-Abdo/`

Follow the latest selected Core Journal classification. Do not return to the old paper split or duplicate Mostafa's literature-level dataset inventory.

The controlling research design is `MARK_RESEARCH_SPECIFICATION_V2.md`. If it is not yet in the repository, use this handoff and ask Mark to add the specification before creating the locked dataset.

## 3. Fixed research decisions

- System: IoT–Edge–Cloud.
- Execution tiers: `LOCAL`, `EDGE`, `CLOUD`.
- Indivisible tasks: full placement only (`LOCAL`, `EDGE_FULL`, `CLOUD_FULL`).
- Divisible tasks: full placement plus partial split between Local and exactly one remote tier (Edge or Cloud). Remote fractions: `0.25`, `0.50`, `0.75`; full remote is `1.0`, local-only is `0.0`.
- Do not split a task across Edge and Cloud simultaneously; do not create DAG dependencies or arbitrary subtasks.
- Each task has its own deadline, generated before the policy decision.
- Urgency classes: `CRITICAL`, `TIME_SENSITIVE`, `DELAY_TOLERANT`.
- Workload and network regimes must include stable conditions, bursts, network degradation, edge-capacity degradation, task-mix shifts, and repeated A→B→A shifts.
- No explicit `DEFER/WAIT/EXECUTE_LATER` action in Milestone 1.
- No arbitrary DAG workflow model, dependency-aware scheduling, multi-remote splitting, or federated learning in this dataset version. Constrained Local+one-remote partial offloading is included only for explicitly divisible synthetic task profiles.
- Every policy receives identical task streams and exogenous scenario conditions for paired comparison.

## 4. Work to perform

### A. Reconcile source metadata

1. Preserve ECW and SMD as independent source datasets.
2. Do not concatenate or row-wise merge them.
3. For ECW, record the original source, version, channel dictionary, axis meaning, units, normalization, sampling period, and licence. Only use mapped fields as scenario context if the authoritative source documentation supports the mapping.
4. For SMD, preserve its 28 machine sequences and test anomaly labels as a separate anomaly-context source. Do not convert anomaly labels into task failures, deadline violations, network outages, or CPU failures.
5. Keep source-derived context separate from synthetic task attributes and simulator-measured outcomes.

### B. Implement a configurable task generator

The generator must support:

- Stable task identifiers.
- Multiple source IoT devices.
- Configurable application/workload profiles.
- Input size, computational demand, and optional output size/memory demand.
- Explicit `splittability` and, for divisible profiles, a partition model with split/merge overhead and data partition rules.
- Per-task arrival timestamps.
- The three urgency classes.
- Relative and absolute deadlines.
- Steady Poisson and bursty/on-off arrivals.
- Reproducible random seeds and scenario IDs.

Separate `application_profile` from `urgency_class`. For example, application profile describes the workload's data/compute characteristics; urgency class describes its deadline class. Do not conflate the two.

All task attributes, splittability labels, partition-model parameters, and deadlines must be generated before a policy decision. The same generated task records must be replayed for every policy in a paired comparison.

### C. Divisibility and partial-offloading workload model

The generator must create at least two explicitly named workload categories:

1. `INDIVISIBLE`: the task cannot be split. Legal actions are `LOCAL`, `EDGE_FULL`, and `CLOUD_FULL`.
2. `DATA_PARALLEL_DIVISIBLE`: the task represents independent data-parallel work that can be divided into a local branch and one remote branch. Legal partial remote fractions are `0.25`, `0.50`, and `0.75`; `0.0` and `1.0` represent full Local and full remote execution, respectively.

For a divisible task with total computation `required_mi` and remote fraction `alpha`:

- `local_required_mi = (1 - alpha) * required_mi`
- `remote_required_mi = alpha * required_mi`
- `remote_input_bytes = input_size_bytes * input_partition_fraction(alpha)`
- `remote_output_bytes = output_size_bytes * output_partition_fraction(alpha)`

The default `input_partition_fraction(alpha) = alpha` and `output_partition_fraction(alpha) = alpha` may be used only for a declared synthetic data-parallel profile where proportional partitioning is part of the workload assumption. Do not generalize this assumption to all IoT tasks. If a profile needs a non-linear data-to-compute mapping, specify an explicit lookup/function in its config.

Every divisible profile must specify `partition_model_id`, `partition_overhead_ms`, `merge_overhead_ms`, and the input/output partition rule. These are workload-model parameters, not measured execution outcomes. Mark unvalidated parameter values as `PROPOSED` until the simulator integration audit confirms how they are represented.

No task may be labelled divisible merely to increase the partial-offloading sample count. Keep a documented proportion of indivisible and divisible tasks and report the two groups separately.

### D. Deadline generation

For each task:

`absolute_deadline_ms = arrival_time_ms + relative_deadline_ms`

Use the urgency class to select a deadline distribution from a version-controlled configuration file. The class-to-deadline mapping must be independent of the chosen destination and policy.

Do not guess final numerical deadline intervals. First inspect the actual simulator capacity, task units, nominal full/partial service-time calculations, then prepare a proposed class-to-deadline table and partition parameter table for Mark's sign-off. Use the current development workload values (200/1,000/4,000 MI and 2,000/10,000/50,000 input bytes) only for generator smoke tests unless the audit provides a documented reason to calibrate new ranges. Label all smoke-test files as development data, not as the final benchmark. Do not tune deadline ranges on final test results.

### E. Workload and shift scenarios

Create configurable scenario profiles for:

1. Stable/steady arrivals.
2. Bursty/on-off arrivals.
3. Reduced bandwidth.
4. Increased WAN delay.
5. Reduced Edge capacity or increased Edge background load.
6. Task-size / compute-demand mixture shift.
7. Repeated A→B→A regime transitions.
8. Optional combined stress and unseen topology/capacity scenarios.

Initially vary one factor at a time. Define combined stress only after single-factor scenarios are validated. The manifest must specify regime boundaries/timestamps, but the policy must not receive future regime labels.

### F. Dataset tables and required fields

Create the following logical tables (CSV or Parquet is acceptable; choose one canonical format and document it). Keep generated inputs distinct from simulator outputs.

#### 1. `tasks.csv` — one row per generated task

Required columns:

- `task_id`
- `run_id`
- `seed`
- `scenario_id`
- `workload_profile_id`
- `source_device_id`
- `application_profile`
- `urgency_class`
- `arrival_time_ms`
- `input_size_bytes`
- `required_mi` (or another unit only if documented and used consistently)
- `splittability` (`INDIVISIBLE` or `DATA_PARALLEL_DIVISIBLE`)
- `partition_model_id` (required for divisible tasks; null for indivisible tasks)
- `partition_overhead_ms` and `merge_overhead_ms` (required/configured for divisible tasks)
- `input_partition_model` and `output_partition_model` (or a profile/config reference)
- `relative_deadline_ms`
- `absolute_deadline_ms`

Optional columns only if modeled and measured consistently:

- `output_size_bytes`
- `memory_requirement_mb`
- `task_priority`
- `dependency_group_id` (keep null/not used in Milestone 1; do not introduce DAG dependencies)

#### 2. `scenario_manifest.csv` or `scenario_manifest.json`

Include:

- `scenario_id`
- `scenario_family`
- `regime_id`
- `regime_start_time_ms`
- `regime_end_time_ms`
- `arrival_process`
- `arrival_rate_or_profile_parameters`
- `network_profile_id`
- `edge_capacity_profile_id`
- `task_mix_profile_id`
- `topology_id`
- `seed`
- `train_validation_test_split`
- configuration/version hash

Do not include future `regime_id` as an agent observation feature. It is an experiment label for analysis only.

#### 3. `decision_contexts.csv` — one row per task and candidate execution option at decision time

This table is produced by the simulator adapter, not invented by the workload generator. Include:

- `task_id`, `run_id`, `policy_id`, `decision_time_ms`
- `candidate_site_type` (`LOCAL`, `EDGE`, `CLOUD`)
- `candidate_site_id`
- `candidate_action` (for example `EDGE_PARTIAL_50`)
- `offload_fraction` (`0.0`, `0.25`, `0.50`, `0.75`, `1.0`)
- `local_work_fraction`
- `remote_work_fraction`
- `partition_model_id` (null for indivisible/full-only tasks)
- `cpu_capacity_mips` or documented equivalent
- `cpu_utilization`
- `available_cpu_capacity` if supported
- `queue_length`
- `estimated_queue_wait_ms`
- `bandwidth_mbps` or bytes/s with units documented
- `link_delay_ms`
- `predicted_transfer_time_ms`
- `predicted_execution_time_ms`
- `predicted_end_to_end_time_ms`
- `calibration_residual_margin_ms`
- `conservative_completion_estimate_ms`
- `feasible_at_decision` (boolean)

Only log a field if it is genuinely observable or computed by a documented model at decision time. Never populate it from future outcomes.

#### 4. `decisions.csv` — one row per policy decision

Include:

- `task_id`, `run_id`, `policy_id`
- `decision_time_ms`
- `requested_action`
- `offload_fraction`
- `local_fraction`
- `remote_tier` (`EDGE`, `CLOUD`, or null for Local-only)
- `partition_model_id`
- `actual_execution_site_id` (plus local and remote execution site IDs for partial actions)
- `feasible_action_set`
- `selected_action_feasible`
- `fallback_used`
- `decision_reason`
- `decision_wall_time_ms`
- `model_version`

#### 5. `task_outcomes.csv` — one row per task-policy-run

Only populate from actual simulator logs. For partial actions, the local and remote branches must be traceable separately and the task must have one final joined completion time:

- `task_id`, `run_id`, `policy_id`
- `action_type`, `offload_fraction`, `local_fraction`, `remote_tier`
- `execution_site_id` (for full actions), `local_execution_site_id`, `remote_execution_site_id` (for partial actions)
- `execution_start_time_ms`
- `input_transfer_start_ms`, `input_transfer_end_ms`
- `execution_end_time_ms` (full action)
- `local_branch_start_ms`, `local_branch_end_ms` (partial action)
- `remote_branch_start_ms`, `remote_input_transfer_end_ms`, `remote_branch_end_ms` (partial action)
- `partition_start_ms`, `partition_end_ms`, `merge_start_ms`, `merge_end_ms` where modelled
- `result_transfer_end_ms`
- `completion_time_ms`
- `end_to_end_latency_ms`
- `completed` (boolean)
- `deadline_met` (boolean/null if unresolved)
- `final_status` (`ON_TIME`, `LATE`, `FAILED`, `UNRESOLVED_AT_HORIZON`)
- `failure_or_unresolved_reason`
- `cpu_energy_joules` and `network_energy_joules` only if the power model and units are validated
- resource/queue outcome fields if supported

Do not fabricate `completion_time`, `latency`, `deadline_met`, reward, energy, or execution-site labels in the task generator.

#### 6. `calibration_log.csv` — one row per task/execution-option calibration estimate

When the risk-calibration layer is integrated, include:

- `task_id`, `run_id`, `policy_id`, `candidate_site_id`, `candidate_action`, `offload_fraction`, `partition_model_id`
- `predicted_completion_time_ms`
- `actual_completion_time_ms` (only after completion)
- `prediction_residual_ms`
- `residual_window_size`
- `quantile_level`
- `calibrated_residual_margin_ms`
- `conservative_completion_estimate_ms`
- `remaining_deadline_slack_ms`
- `feasible_at_decision`
- `regime_id` (analysis label, not policy observation)

### F. Train/validation/test separation

- Split by seed and scenario family, not random rows from one time series.
- Keep test workload profiles and shift sequences unseen during model/calibration tuning where the generalization experiment requires it.
- Use the same task stream and exogenous network/resource trace for every policy in a paired run.
- Do not let test labels or future regime boundaries leak into the agent's state.
- The experiment plan targets at least 20 paired seeds per principal scenario; 30 is preferred if runtime permits.

## 5. Required quality checks

Build automated checks that fail if:

- `task_id` is duplicated within a run.
- A task deadline is missing, non-positive, or earlier than task arrival.
- An urgency class is outside the approved three values.
- An indivisible task is offered a partial action.
- A divisible task has a missing/unknown partition model or invalid split/merge configuration.
- Local and remote work fractions do not sum to 1 (within a documented numeric tolerance).
- An offload fraction is outside `{0.0, 0.25, 0.50, 0.75, 1.0}`.
- A partial action uses more than one remote tier.
- Task units are missing or inconsistent.
- Task generation changes when the same seed and configuration are replayed.
- Different policies in a paired run receive different tasks or deadlines.
- A simulator outcome has no matching generated task.
- A task has multiple contradictory final statuses.
- Pending/unresolved tasks disappear from the generated-task denominator.
- Future data (actual completion, future regime label, test label) appears in decision context.

Produce a reconciliation report: generated tasks = on-time + late + failed + unresolved at horizon, with rejected/no-feasible decisions retained as decision metadata and not silently dropped.

## 6. Deliverables

Place the work under `team-work/Astta-Abdo/` and organize it clearly. Required outputs:

1. `WORKLOAD_GENERATOR_SPEC.md` — generator design, distributions, units, deadline-class mapping, divisibility classes, partition rules, and assumptions.
2. `configs/workload_profiles.yaml` — versioned workload/task/deadline/divisibility configurations, including split ratios and overhead parameters. Mark unvalidated numerical ranges clearly as `PROPOSED`.
3. `configs/scenario_profiles.yaml` — stable, burst, network degradation, edge degradation, task-mix shift, A→B→A, and optional topology profiles.
4. `scripts/generate_workloads.py` — reproducible task and scenario generation.
5. `scripts/validate_dataset.py` — schema, integrity, reproducibility, leakage, and reconciliation checks.
6. `data/` — sample/development output only until the numerical profile is approved; do not label development samples as final benchmark data.
7. `DATASET_CARD.md` — purpose, synthetic-data declaration, schema, generation procedure, seed/split design, provenance, limitations, license notes, and version.
8. `ABDO_HANDOFF_REPORT.md` — concise findings, all proposed ranges needing Mark approval, technical blockers, and exact commands to reproduce the workload files.

## 7. Strict restrictions

- Do not merge ECW and SMD.
- Do not relabel anonymous source channels as CPU, RAM, bandwidth, or latency.
- Do not treat SMD anomalies as task failures or deadline misses.
- Do not generate simulator outcomes or reward labels synthetically.
- Do not choose arbitrary final deadline ranges or reward weights.
- Do not train models or implement the placement algorithm as part of this task. Do not fabricate execution times or simulate outcomes inside the workload generator. The simulator team owns actual branch execution and synchronization measurements.
- Do not change the simulator topology or queue discipline without approval.
- Do not commit or push.
- Preserve original datasets unchanged and preserve source licences/notices.

## 8. Acceptance criteria

This task is complete when:

1. The task generator deterministically produces task records and scenario manifests from a fixed seed/configuration.
2. Every generated task contains a valid urgency class and independently assigned relative/absolute deadline. Divisible/indivisible labels and partition parameters are valid and reproducible.
3. Workload and regime-shift profiles are configurable and reproducible.
4. Paired policies can replay identical task streams.
5. Validation scripts detect missing/duplicate IDs, invalid deadlines, data leakage, and reconciliation errors.
6. ECW/SMD remain separate and their provenance/limitations are documented.
7. All proposed numerical ranges and partition assumptions are listed for Mark's sign-off before final benchmark generation.
8. No execution outcome, reward, or energy value has been invented.

**Important boundary:** this deliverable creates the workload input dataset and the schema for full/partial experiment traces. It does not implement the task partitioner, branch scheduler, synchronization, or join logic inside iFogSim2. The final task-offloading results dataset is produced only after the simulator executes the tasks and records actual decisions and outcomes.
