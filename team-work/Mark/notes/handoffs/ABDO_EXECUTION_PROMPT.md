# Execution Prompt for Abdo — Final Workload Dataset and Generator

You are responsible for completing the workload-dataset workstream for our research project. Work directly in the current repository and treat the repository's latest pushed state as the source of truth. Do not start from scratch and do not duplicate Mostafa's dataset inventory work.

## Project

**Risk-Calibrated Adaptive Task Partitioning and Offloading under Repeated Workload and Network Shifts in the IoT–Edge–Cloud Continuum**

The research evaluates full task placement and constrained partial offloading, with per-task deadline feasibility and adaptation under repeated workload/network shifts.

## Your exact objective

Deliver a reproducible, validated **synthetic IoT workload input dataset and dataset-generation pipeline** that covers both indivisible and divisible tasks, plus the formal schemas/contracts required for the simulator-generated decisions and outcomes.

Important distinction: your generator creates task inputs and scenario manifests. It must NOT invent actual execution sites, completion times, latency, deadline success, rewards, energy, or resource outcomes. Those are measured by the iFogSim2 integration and experiment runs. Therefore, do not label generated workload samples as the final measured experiment-results dataset. Your workstream is complete when the input dataset, generator, schemas, validation, provenance, and handoff are complete and reproducible; the final outcomes dataset is completed only after simulator runs.

## 1. Mandatory first actions

1. Inspect the current repository, `FILE_INDEX.md`, `WORKSPACE_AUDIT_REPORT.md`, `research/references/REFERENCES_INDEX.md`, the relevant methodology documents, and all existing files under `team-work/Astta-Abdo/`.
2. Inspect your previous audit outputs and code before changing anything. Preserve valid work. Do not overwrite or delete previous reports; create versioned updates where needed.
3. Read `MARK_RESEARCH_SPECIFICATION_V2.md` and this handoff. If the V2 specification is not in the repository, use the provided copy in the handoff package and report that it needs to be added.
4. Review the dataset source audits and Mostafa's provenance package. Do not repeat the literature-level inventory or claim ECW/SMD are task-offloading datasets.
5. Before locking numerical workload/deadline settings, inspect the simulator topology/capacity and the simulator team's verified service-time and event-hook findings. Coordinate with Ayoub where necessary. If those facts are unavailable, keep affected values marked `PROPOSED` and clearly identify the blocker; do not fabricate a final calibration.

## 2. Fixed system and task model

### Execution tiers

Use `LOCAL`, `EDGE`, and `CLOUD`.

### Task categories

Use exactly these task divisibility labels in this milestone:

- `INDIVISIBLE`: only full actions are legal: `LOCAL`, `EDGE_FULL`, `CLOUD_FULL`.
- `DATA_PARALLEL_DIVISIBLE`: independent data-parallel work that may be split between Local and exactly one remote tier (Edge OR Cloud).

Do not split one task across Edge and Cloud simultaneously. Do not create arbitrary DAGs, dependency graphs, dependent subtasks, multi-remote splits, or a defer/wait action.

### Partial split options

For divisible tasks, support remote computation fractions:

- `0.00`: Local-only
- `0.25`: 75% Local + 25% remote
- `0.50`: 50% Local + 50% remote
- `0.75`: 25% Local + 75% remote
- `1.00`: full execution at the selected remote tier

Remote tier is either Edge or Cloud. Use action names consistently, e.g. `EDGE_PARTIAL_25`, `EDGE_PARTIAL_50`, `EDGE_PARTIAL_75`, and corresponding Cloud actions.

For divisible task total compute demand `required_mi` and remote fraction `alpha`:

- `local_required_mi = (1 - alpha) * required_mi`
- `remote_required_mi = alpha * required_mi`

The default input/output byte partition fractions may equal `alpha` only for a declared synthetic data-parallel workload profile that explicitly assumes proportional partitioning. Do not generalize this to arbitrary IoT tasks. Every divisible profile must define a `partition_model_id`, input/output partition rules, `partition_overhead_ms`, and `merge_overhead_ms`. Clearly mark unverified numerical overheads as `PROPOSED`.

Keep a configurable mix of divisible and indivisible tasks, but justify the proportions as workload assumptions and report both categories separately. Never label a task divisible merely to increase partial-offloading sample count.

### Task semantics

Separate:

- `application_profile`: what kind of computational/data workload the task represents.
- `urgency_class`: its deadline urgency.

Use only these urgency labels:

- `CRITICAL`
- `TIME_SENSITIVE`
- `DELAY_TOLERANT`

Each task gets its own relative and absolute deadline at generation time, before any policy decision:

`absolute_deadline_ms = arrival_time_ms + relative_deadline_ms`

Deadline assignment must depend on the task's configured urgency distribution and workload profile only, never on a selected action, policy, measured outcome, or future scenario label.

Do not guess or tune final deadline ranges against test results. Propose class-specific distributions and justify them using verified simulator capacity and nominal service-time estimates. If the required simulator evidence is not available, write the proposed table with `PROPOSED` status and provide the exact evidence needed to finalize it. Current development values (200/1,000/4,000 MI and 2,000/10,000/50,000 input bytes) are for smoke tests only unless a documented audit justifies adopting them in the benchmark.

## 3. Generator and scenario requirements

Build a configurable, seed-reproducible generator supporting:

- Multiple source IoT devices and stable task IDs.
- Configurable application/workload profiles.
- Input bytes, computational demand in MI (or another consistently documented unit), and optional output bytes/memory demand only where modelled.
- Arrival timestamps and at least steady Poisson and bursty/on-off arrival processes.
- Urgency class and task-specific relative/absolute deadlines.
- Explicit divisibility class and partition configuration.
- Run ID, seed, scenario ID, workload profile ID, and configuration/version hash.
- Deterministic replay: same seed + same configuration must produce identical task records and manifest.

Provide configurable scenario profiles for:

1. Stable/steady workload.
2. Bursty/on-off arrivals.
3. Reduced bandwidth.
4. Increased WAN delay.
5. Reduced Edge capacity or increased Edge background load.
6. Task-size/computational-demand mixture shift.
7. Repeated A→B→A regime transitions.
8. Optional combined-stress and unseen-topology/capacity scenarios, clearly separated from the core scenarios.

Start with one-factor-at-a-time changes. Do not expose future regime labels or future shift boundaries as policy observations; those are experiment metadata only. The same exact generated tasks and exogenous conditions must be replayed for every policy in paired comparisons.

## 4. Data products and schema contracts

Choose one canonical format (CSV or Parquet) and document the choice. CSV is acceptable if types/null semantics are rigorously documented.

### A. `tasks` input table — implement and populate

At minimum:

- `task_id`, `run_id`, `seed`, `scenario_id`, `workload_profile_id`
- `source_device_id`, `application_profile`, `urgency_class`
- `arrival_time_ms`, `input_size_bytes`, `required_mi`
- `splittability`
- `partition_model_id` (required for divisible; null for indivisible)
- `partition_overhead_ms`, `merge_overhead_ms` (required for divisible)
- `input_partition_model`, `output_partition_model` or an explicit profile reference
- `relative_deadline_ms`, `absolute_deadline_ms`

Optional fields such as output size or memory requirement must be present only if their meaning, unit, and generation rule are documented.

### B. `scenario_manifest` — implement and populate

Include scenario/run/seed IDs, scenario family, regime IDs and time boundaries, arrival process and its parameters, network profile, Edge capacity profile, task-mix profile, topology ID, train/validation/test designation, and configuration hash. Regime labels are for evaluation only, not policy state.

### C. `decision_contexts` — schema/contract only; do not fabricate records

Define a machine-readable schema/data dictionary for per-task candidate action observations, including candidate tier/site, candidate action and split fraction, CPU capacity/utilization, queue, bandwidth/link delay, predicted transfer/execution/end-to-end time, calibration margin, conservative estimate, and feasibility flag. These values must be produced by the simulator adapter at decision time and must not use future outcomes.

### D. `decisions` — schema/contract only; do not fabricate records

Define the schema for policy decision records: requested action, offload fraction, local fraction, remote tier, selected execution site IDs, feasible-action set, fallback details, decision wall-clock time, and model version.

### E. `task_outcomes` — schema/contract only; do not fabricate records

Define the per-task, per-policy, per-run outcome schema. For partial execution, make both branches traceable independently (Local branch start/end; remote input transfer start/end; remote branch start/end; partition and merge events where modelled; result-transfer completion) and store one final joined task completion time. Include end-to-end latency, completion status, deadline result, and unresolved-at-horizon status. Energy fields are allowed only if Ayoub verifies the simulator's power model and units.

### F. `calibration_log` — schema/contract only; do not fabricate records

Define fields for predicted and actual completion times, residuals, residual-window size, quantile level, calibrated margin, conservative completion estimate, remaining deadline slack, and feasibility. Actual completion and residual values exist only after a simulator execution has completed.

Keep generated inputs, simulator decision logs, and simulator outcomes in separate tables/files. Include keys and join rules. Do not create fake placeholder outcomes that look like measurements; empty schema/header files are acceptable if clearly labeled as schemas only.

## 5. ECW and SMD handling

- Preserve ECW and SMD as separate source datasets; never concatenate or row-wise merge them.
- ECW currently has an array shape `(1022, 720, 16)`, but its channel meanings, axes/time semantics, physical units, normalization, provenance, and licence are not established by the available technical audit. Do not map its anonymous channels to CPU, memory, bandwidth, or latency. Exclude it from numerical workload generation unless authoritative documentation is obtained and the mapping is defensible.
- SMD is server-machine telemetry with 28 machine sequences and 38 dimensions, with test anomaly labels. It is not an IoT task dataset. Do not interpret anomaly labels as task failure, deadline miss, network outage, or CPU failure. If retained as optional abnormal-condition context, keep it separate and document domain limitations, sample timing/scaling gaps, and provenance.
- Do not fabricate missing feature dictionaries, timestamps, units, or labels.
- Do not duplicate Mostafa's inventory work. Update only the technical findings needed for this generator and handoff.

## 6. Dataset integrity, splits, and validation

Implement automated validation that fails on at least:

- Duplicate `task_id` within a run.
- Missing, non-positive, or invalid relative/absolute deadlines; absolute deadline before arrival; mismatch in `absolute = arrival + relative`.
- Unknown urgency or splittability label.
- Partial action offered to an indivisible task.
- Divisible task missing partition model, input/output rules, or overhead parameters.
- Local + remote work fractions not summing to 1 within a documented tolerance.
- Invalid offload fractions outside `{0, .25, .50, .75, 1}`.
- More than one remote tier for a partial action.
- Missing/inconsistent units or invalid values.
- Non-deterministic output for identical seed/configuration.
- Paired policies receiving different generated task inputs for the same run.
- Decision-context leakage (actual completion, future regime label, test label, or other post-decision data present in agent input).
- Simulator outcomes with no matching task, if/when such outcome files are integrated.
- Multiple contradictory final statuses.
- Generated tasks silently disappearing from the on-time/late/failed/unresolved reconciliation denominator.

Split by seed and scenario family, not random rows from the same time series. Make the split strategy explicit and reproducible. Preserve held-out task profiles and shift sequences for generalization tests. Plan at least 20 paired seeds per principal scenario (30 preferred if runtime permits), but do not run the iFogSim experiments as part of this assignment.

Produce a reconciliation rule/report for eventual simulator results:
`generated tasks = on-time + late + failed + unresolved-at-horizon`.

## 7. Required repository deliverables

Keep everything under `team-work/Astta-Abdo/`, organized and discoverable. Deliver:

1. `WORKLOAD_GENERATOR_SPEC.md` — profiles, distributions, units, deadline mapping, divisibility classes, partition rules, assumptions, and unresolved evidence.
2. `configs/workload_profiles.yaml` — versioned task/urgency/deadline/divisibility profiles, split ratios, and overhead parameters; unapproved values marked `PROPOSED`.
3. `configs/scenario_profiles.yaml` — all required stable, burst, network, Edge-capacity, task-mix, and A→B→A scenarios.
4. `scripts/generate_workloads.py` — reproducible generator with clear CLI.
5. `scripts/validate_dataset.py` — integrity, deterministic replay, leakage and schema checks.
6. `schemas/` (or equivalent) — formal machine-readable schemas and data dictionaries for tasks, manifests, decision contexts, decisions, outcomes, and calibration logs.
7. `data/dev/` — small development samples only until parameter approval. Keep any approved benchmark-generation output in a clearly separate path and never call it simulator outcomes.
8. `DATASET_CARD.md` — data purpose, synthetic declaration, schema, generation, seeds/splits, provenance, limitations, license notes, and version.
9. `ABDO_HANDOFF_REPORT.md` — what is complete, exact reproduction commands, validation/test output, proposed numerical tables needing Mark's approval, blockers, and next integration requirements for Ayoub.
10. Automated tests (pytest or the repository's existing test framework) covering deterministic generation and all key validation rules.

Do not commit or push. Do not modify simulator topology or queue discipline. Do not implement the policy or train the model.

## 8. Definition of done

I will consider the dataset workstream complete only when:

- All required input and schema files exist in the repository in the specified structure.
- Generator and validator run from documented commands in a clean environment.
- Re-running the same seed/config produces identical task and manifest files (demonstrate with hashes).
- All required scenarios and both task divisibility classes are represented.
- Every task has a valid, pre-decision deadline.
- Partial-action semantics and partition assumptions are explicit and validated.
- Train/validation/test split is seed/scenario based and reproducible.
- All tests pass and their output is included in the handoff.
- ECW/SMD are treated with the limitations above.
- No execution outcome, reward, or energy value is fabricated.
- Every unverified numeric parameter is explicitly marked `PROPOSED`, with an evidence-based recommendation for Mark's approval.

## 9. Final handoff format

Send me:

1. The exact list of files created/modified.
2. The exact commands to generate and validate the dataset.
3. Test results and deterministic hash comparison.
4. A compact table of workload profiles, task-mix proportions, compute/input-size ranges, deadline distributions, split/merge overheads, arrival rates, and network/Edge shift parameters, each tagged `APPROVED`, `PROPOSED`, or `BLOCKED` with rationale.
5. A list of issues requiring Ayoub's simulator integration or Mark's decision.
6. Confirmation that no commits or pushes were made.

Do not stop after writing a plan. Implement the generator, configs, schema contracts, validation, tests, and documentation. If a required simulator fact is unavailable, complete everything that can be completed and mark only that fact-dependent parameter as `PROPOSED` or `BLOCKED` rather than fabricating it.
