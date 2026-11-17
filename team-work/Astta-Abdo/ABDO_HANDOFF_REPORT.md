# Abdo handoff report — synthetic workload inputs and schemas

**Extension version:** 1.2.0  
**Historical repository baseline:** `main` at `39d6cd448ba5a15e690ac67ff777017a445ce577` (2026-11-03 16:45:53 UTC)  
**Current integration base:** `mark/iiot-scope-transition-v1`  
**Delivery form:** committed on `abdo/industrial-workload-replay-seed-v2`, based on `mark/iiot-scope-transition-v1`; not merged to `main`  
**Status:** V1.2.0 implementation and generated Development samples are on the research-based feature branch; CI passed 43 tests. Actual topology verification and the complete historical seed archive audit remain external dependencies.

## 1. Completed work

- Deterministic generator for task input rows and scenario manifests, with Poisson and on/off arrival processes, multiple logical source identities, stable IDs, urgency/deadline generation before decisions, seed/config hashes and independent RNG streams.
- Eight core scenarios: steady workload, on/off bursts, reduced bandwidth, increased WAN delay, reduced Edge capacity, task-size/compute shift, repeated network A→B→A, repeated workload-mix A→B→A. Combined stress is optional; unseen topology is explicitly blocked and excluded from core generation.
- Both `INDIVISIBLE` and `DATA_PARALLEL_DIVISIBLE` tasks. Divisible task profiles explicitly model independent frame/window shards and use profile-scoped proportional compute/byte partition rules. The action contract is in the data dictionary and schemas.
- Six JSON Schema contracts and six named table data dictionaries: tasks and scenario manifests are generated inputs; decision contexts, decisions, task outcomes and calibration logs are schema-only.
- CSV templates for the four simulator/policy-owned tables are header-only. They contain no fake execution rows.
- Validator covers task IDs, numeric units/values, task deadlines, manifest split and regime-observation leakage, decision-context leakage, legal action/split semantics, simulator outcome event chronology/status/reconciliation, calibration residuals, orphan rows, paired input hashes and deterministic replay.
- Pytest suite covers deterministic replay, scenario-family/seed splits, urgency/deadline rules, both divisibility classes, illegal splits, leakage, identical and mismatched paired inputs, completed/unresolved outcomes, branch/event chronology, required-field/header consistency, schema validity and CLI behavior.
- Dataset card, technical specification, baseline inspection, prior audit provenance copies, and this handoff report.

## 2. Exact overlay files

Paths below are scoped to `team-work/Astta-Abdo/`. The V1.2.0 branch modifies the workload configs, generator, validator, tests, schemas and documentation; regenerates the Development samples; and adds the seed registry and CI workflow. Existing simulator source, topology implementation, policy, training artifacts, ECW/SMD audit files, and other team workstreams are not replaced.

```text
WORKLOAD_DATASET_README.md
WORKLOAD_GENERATOR_SPEC.md
DATASET_CARD.md
ABDO_HANDOFF_REPORT.md
requirements.txt
pytest.ini
configs/workload_profiles.yaml
configs/scenario_profiles.yaml
scripts/generate_workloads.py
scripts/validate_dataset.py
schemas/tasks.schema.json
schemas/scenario_manifest.schema.json
schemas/decision_contexts.schema.json
schemas/decisions.schema.json
schemas/task_outcomes.schema.json
schemas/calibration_log.schema.json
schemas/DATA_DICTIONARY.md
tests/test_workload_pipeline.py
data/dev/*_tasks.csv
data/dev/*_scenario_manifest.csv
data/dev/schemas_only/{README.md,decision_contexts.csv,decisions.csv,task_outcomes.csv,calibration_log.csv}
provenance/*
reports/*
```

`reports/OVERLAY_FILE_MANIFEST.txt` is a historical V1.1 packaging inventory; use the GitHub branch comparison and pull-request file list as the authoritative V1.2 change list.

## 3. Reproduction commands

Run from `team-work/Astta-Abdo/` on branch `abdo/industrial-workload-replay-seed-v2`:

```bash
python -m pip install -r requirements.txt
python scripts/generate_workloads.py --scenario all-core --dataset-split development --seed 1300 --seed-count 1 --task-count 48 --output data/dev --hash-report reports/dev_hashes_v1_2.json
python scripts/validate_dataset.py --tasks data/dev/stable_steady__seed_1300_tasks.csv --manifest data/dev/stable_steady__seed_1300_scenario_manifest.csv --check-replay --report reports/stable_steady_validation.json
pytest -q
```

To validate each of the eight dev scenario files with deterministic replay from a Bash shell:

```bash
for f in data/dev/*_tasks.csv; do
  stem="${f%_tasks.csv}"
  python scripts/validate_dataset.py --tasks "$f" --manifest "${stem}_scenario_manifest.csv" --check-replay
 done
```

Seed selection is registry-only. Seed 1300 is Development/CI only; historical seed 81 and all other repository-known prior-use seeds are retired. The current registry has no approved Train, Validation or Test seeds, and full coverage awaits local/team archive review. Do not request 20/30 seed benchmark schedules until fresh non-overlapping seeds are inventoried and approved. No iFogSim experiment was run for this handoff.

## 4. Verification results

- `pytest -q`: **43 passed** on the V1.2.0 CI run. The workflow regenerates all eight Development pairs, validates each pair including exact A→B→A replay, runs the tests, then verifies that the committed Development inputs and reports already match the generated outputs.
- Eight core scenarios generated; each development sample has 48 task rows and a one-row run manifest.
- Each sample has a successful task/manifest validation and deterministic replay check; no outcome or decision records are generated.
- All six JSON Schemas parse and validate structurally.
- The precise task/manifest SHA-256 pairs and canonical config hash are in `reports/dev_hashes_v1_2.json`. Independent regeneration into two separate output directories reproduced all eight task hashes and all eight manifest hashes byte-for-byte; replay is also checked inside the automated tests. The canonical configuration hash is `68e2ba5ad5ab23fbbe32a418b81b14014791978eb3387a5aae3a7f6ed2641c64`.
- The test suite includes positive and negative A1/A2 replay checks, distinct B-stream checks, industrial divisibility coverage, cross-split duplicate rejection, exclusion of every historical registry seed from final Test, topology provenance validation, and the existing outcome/chronology and schema checks.

`reports/pytest_results_v1_2.txt`, eight seed-1300 per-scenario validation JSON files, and `reports/dev_hashes_v1_2.json` retain the current V1.2.0 evidence. V1.1 report files remain archived and are not current inputs.

## 5. Configuration summary and status

| Parameter | Configured value | Status | Rationale / approval needed |
|---|---|---|---|
| Current topology reference | 1 Local / 1 Edge / 1 Cloud; 1,000 / 2,800 / 44,800 MIPS | `APPROVED` as existing prototype reference only | Checked-in topology document; not the V2 target layout. |
| V2 topology | 4 IoT / 2 Edge / 1 Cloud | `PROPOSED` target; capacities `BLOCKED` | Target from V2 spec; current prototype has only one Local, Edge and Cloud executor. Ayoub must provide site IDs and capacities. |
| Source IDs | `iot-01`…`iot-04` logical sources | `PROPOSED` | Does not assert four physical iFogSim FogDevices. Mapping needed from Ayoub. |
| Application compute values | Sensor: 200/1,000/4,000 MI; normal divisible: 1,000/4,000 MI; shifted divisible: 4,000/8,000/16,000 MI | `PROPOSED` smoke/stress only | 2,500 MI is the one-task pilot value; it does not justify broader distributions. Mark must approve calibrated ranges. |
| Input sizes | 2,000/10,000/50,000 bytes; shifted 50,000/100,000/250,000 bytes | `PROPOSED` smoke/stress only | The prototype pilot used 12,000 bytes. Ranges are deliberately development assumptions. |
| Output sizes | Profile values 256–8,192 bytes | `PROPOSED` synthetic profile rule | Only present because each profile explicitly models output size; not simulator-observed output. |
| Divisibility mix | 50% indivisible / 50% divisible; shifted B 20% / 80% | `PROPOSED` | Divisible work is confined to declared independent frame/window shards. Mark must approve the mix as a study assumption. |
| Urgency mix | Per-profile; overall reference 20% / 50% / 30% Critical/Time-sensitive/Delay-tolerant | `PROPOSED` | Design distribution, not observed application frequency. |
| Relative deadlines | Critical 200–800 ms; Time-sensitive 800–3,000 ms; Delay-tolerant 3,000–10,000 ms | `PROPOSED` | 500 ms is one configured pilot deadline; 3 pilot latencies are not a service-time distribution. Freeze only after multi-task nominal service-time evidence. |
| Partition / merge overheads | Frames 5/5 ms; sensor windows 3/4 ms | `PROPOSED` | Adapter hooks and branch-level timing not confirmed; only apply to 0<alpha<1. Need measured or simulator-modeled hook durations from Ayoub. |
| Arrival processes | Stable 0.5 tasks/s Poisson; burst On 2.0 / Off 0.15 tasks/s, 5,000/10,000 ms state durations | `PROPOSED` | Scenario levels for stress design only; not fitted to a sourced workload trace. Mark approves task rates/window. |
| Network factor | Bandwidth scale 0.5; WAN uplink 90 ms vs prototype 45 ms | `PROPOSED` | Relative bandwidth factor is testable only after units established; 90 ms is a one-factor stress setting, not measured. |
| Bandwidth units / downlink delay | raw 10,000/100,000 values have no confirmed unit; downlink unspecified | `BLOCKED` | Ayoub to verify iFogSim bandwidth unit, transfer calculation and child/downlink delay semantics. |
| Edge capacity factor | 0.5 × 2,800 MIPS = 1,400 MIPS effective reference | `PROPOSED` | Capacity stress only on current single-edge reference; target two-Edge capacities need confirmation. |
| Run repetitions | Not allocated | `BLOCKED` pending archive audit and approval | No Train/Validation/final Test seed is currently approved; seed 1300 is Development/CI only. No simulator runs included. |

The 2,500 MI / 12,000-byte / 2,000-byte / 500-ms configuration is an existing **one-task input reference**, not an approved distribution. The pilot endpoint latencies are measurements from a one-task controlled run, not generated input parameters and not a deadline calibration dataset.

## 6. Questions for Mark

1. Approve or replace the proposed profile distributions, 50:50 divisibility mix, 20:50:30 urgency mix and per-class deadline brackets after Ayoub supplies nominal service-time evidence.
2. Approve the 0.5 tasks/s steady and 2.0/0.15 tasks/s on/off load levels or provide a target offered-load range.
3. Approve the 0.5 bandwidth/capacity stress multipliers and 90 ms one-way WAN-delay stress level.
4. After local/team archive review, approve a fresh, non-overlapping Train/Validation/Test seed allocation in Registry V2; no old seed may be reused.
5. Add the canonical `MARK_RESEARCH_SPECIFICATION_V2.md` to the repository root and confirm this extension's supplied handoff copy is the correct version.
6. Select a project license before public distribution; repository `LICENSE_STATUS.md` currently records no selected license.

## 7. Required items from Ayoub before benchmark calibration / outcome adapter

1. Confirm whether the V2 4-IoT / 2-Edge / 1-Cloud topology is implemented; provide actual site IDs, MIPS, RAM and per-tier node capacity.
2. Confirm units and transfer-delay conversion for the topology's bandwidth values, plus both uplink and downlink latency/child latency semantics.
3. Provide nominal service-time traces/distributions by task profile and execution tier, including task MI/PE meaning and queueing/load assumptions, to calibrate deadline distributions without test tuning.
4. Specify stable per-task identifiers and adapter joins from generated `task_id` through iFogSim tuples and simulator result endpoint.
5. Verify event hooks for concurrent Local and remote divisible branches, remote input transfer, branch completion, partition, join/merge, and result transfer; define when partial `completion_time_ms` becomes final.
6. Confirm whether output bytes affect the simulator model, and confirm output-size rule and input/output fractional partition behavior.
7. Keep task failures and unresolved-at-horizon distinguishable; the current one-task integration does not verify native task failure handling.
8. Do not add per-task energy until power model, units and concurrency-safe attribution are verified. Current schema omits energy.

## 8. ECW/SMD and other candidate datasets

ECW and SMD are retained as separate versioned technical audit references and are not numerically sampled, concatenated, or relabelled as workload tasks. ECW channel mapping remains unknown; SMD anomaly labels remain telemetry anomaly labels, not task outcomes. Mostafa's dataset inventory is not reproduced here; its dataset audit remains the reference for candidate-source claims.

## 9. Git / integration scope confirmation

The V1.2.0 changes are committed on `abdo/industrial-workload-replay-seed-v2`, based directly on `mark/iiot-scope-transition-v1`. The earlier PR #5 targeting `main` is not the integration route and must not be merged into `main`. A separate review PR targets the current research branch. No merge was performed. The change set does not alter simulator source, topology/queues, offloading policy, model training, or other team workstreams.

## 10. Historical packaging correction addendum (v1.1.1 — superseded)

The original overlay archive was reported as incomplete by the recipient. The implementation was not rewritten. It has been re-extracted, checked against the complete file manifest, and repackaged with the entire additive tree plus fresh verification evidence. The corrected archive is `Astta-Abdo_Final_Workload_Dataset_Overlay_v1_1_1_COMPLETE.zip`.

- The package contains both YAML configs, all six JSON Schemas, all eight development task/manifest pairs, all four empty simulator/policy CSV templates, generator, validator, the complete tests file, requirements, pytest config, provenance, and scenario validation reports.
- The expanded manifest is `reports/OVERLAY_FILE_MANIFEST.txt`; the package integrity summary is `reports/package_verification/package_integrity_report.json`.
- The commands printed in `WORKLOAD_DATASET_README.md` were rerun from the extracted package directory. Generation produced all eight core scenarios; stable-sample validation including replay passed; pytest output is retained as `reports/pytest_results.txt` and `reports/package_verification/pytest_actual.stdout.txt`.
- All eight regenerated scenario task/manifest pairs passed validation with deterministic replay. A second independent generation run matched all 16 CSV hashes (8 task tables and 8 manifests) byte-for-byte.
- Empty outcome/decision/calibration templates remain header-only. No simulator outcomes were added.
- A fully empty virtualenv could not download dependencies because the package index was unreachable from this execution environment. The documented `pip install -r requirements.txt` command did complete successfully in the available Python environment, where both declared dependencies were already installed. Exact failure output is recorded in `reports/package_verification/fresh_venv_install_attempt.txt`.

This paragraph records the historical V1.1.1 local-overlay phase and is superseded by the V1.2.0 branch delivery above. All unverified numeric values retain their `PROPOSED` or `BLOCKED` designations.


## 12. V2 research-branch handoff correction — 17 November 2026

The current revision is prepared additively on mark/iiot-scope-transition-v1, not main. The earlier PR targeting main remains separate and must not be merged into main as an integration shortcut.

Implemented in the V2 work branch:
- A1/A2 use identical task attribute RNG streams and relative arrival-time templates; B uses a separate workload stream. The validator and tests assert equality of A1/A2 inputs and their exogenous condition profile.
- Visual Inspection adds indivisible single-image inference; Production Monitoring adds indivisible single-event processing. Divisible frame-batch and aggregation-window variants remain available for partial-offloading comparisons.
- Seed registry V2 preserves known historical seed uses as retired, records seed 61's prior development use, and allocates seed 1300 for Development/CI only. Seed 81 and 102-121 are not final-test eligible. No final Train/Validation/Test allocations are approved. Registry coverage remains incomplete until local and all team archives are checked.
- Manifests distinguish target_topology_id from nullable actual_topology_id and label actual topology NOT_VERIFIED_PENDING_AYOUB_CONFIRMATION.
- The workload pipeline remains input-only. It does not generate simulator results, latency, energy, reward, queue measurements or execution decisions.

All workload ranges and mix proportions remain proposed synthetic configurations. They are not factory measurements or industrial traces. Numeric profile approval and actual topology confirmation remain with Mark/Ayoub.


## 12. V1.2.0 branch verification and acceptance status

- Current research integration base: `mark/iiot-scope-transition-v1`.
- Feature branch: `abdo/industrial-workload-replay-seed-v2`.
- Current development task/manifest CSVs were regenerated with seed 1300, generator 1.2.0, 48 tasks per scenario, and the industrial profile IDs. The previous seed-7/61/81 CSVs were removed from `data/dev/`; historical reports remain archived and are labelled as historical.
- A→B→A exact replay: A1/A2 use the same task templates, attribute stream and relative arrival offsets. The manifest records the same A condition-profile ID for A1/A2; B uses its own workload stream.
- Industrial archetypes: Predictive Maintenance indivisible inference; Visual Inspection indivisible single-image inference plus divisible frame batches; Production Monitoring indivisible single-event processing plus divisible aggregation windows.
- Seed allocation: seed 1300 is allocated to Development/CI only. Seed 81, seeds 102–121, and other known previous-use seeds are retired. There are no approved final Test seeds; repository-visible inventory is incomplete pending local and team archive scans.
- Topology: `target_topology_id` captures the proposed 4-IoT/2-Edge/1-Cloud target. `actual_topology_id` is null with `NOT_VERIFIED_PENDING_AYOUB_CONFIRMATION`; no implementation claim is made.
- CI: eight scenario generation and validation, deterministic replay, and 43 automated tests passed on the V1.2.0 CI run; generated Development inputs and reports are synchronized on the branch.
- No simulator outcomes, execution decisions, performance measurements, latency, energy, or rewards are created by this workstream.

All workload values remain proposed synthetic configurations, not factory measurements or industrial traces. Mark's approval of numerical profiles and Ayoub's verification of the actual topology remain prerequisites before benchmark use.
