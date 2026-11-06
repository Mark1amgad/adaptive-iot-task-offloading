# Abdo handoff report — synthetic workload inputs and schemas

**Extension version:** 1.1.0  
**Repository baseline:** `main` at `39d6cd448ba5a15e690ac67ff777017a445ce577` (2026-11-03 16:45:53 UTC)  
**Delivery form:** additive local overlay under `team-work/Astta-Abdo/`; not written to GitHub  
**Status:** generator, development inputs, schemas, validator and tests implemented; benchmark numeric calibration awaits Mark/Ayoub evidence.

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

All paths below are relative to `team-work/Astta-Abdo/` in the repository and are new additive paths. Existing `README.md`, `adaptive_offloading/`, and old workspace files are not replaced.

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

The full exact file list is recorded in `reports/OVERLAY_FILE_MANIFEST.txt` and the downloadable ZIP contains the same additive path structure.

## 3. Reproduction commands

Run from `team-work/Astta-Abdo/` after applying the overlay:

```bash
python -m pip install -r requirements.txt
python scripts/generate_workloads.py --scenario all-core --seed 7 --seed-count 1 --task-count 48 --output data/dev --hash-report reports/dev_hashes_v1_1.json
python scripts/validate_dataset.py --tasks data/dev/stable_steady__seed_0007_tasks.csv --manifest data/dev/stable_steady__seed_0007_scenario_manifest.csv --check-replay --report reports/stable_steady_validation.json
pytest -q
```

To validate each of the eight dev scenario files with deterministic replay from a Bash shell:

```bash
for f in data/dev/*_tasks.csv; do
  stem="${f%_tasks.csv}"
  python scripts/validate_dataset.py --tasks "$f" --manifest "${stem}_scenario_manifest.csv" --check-replay
 done
```

For the minimum planned paired-seed schedule, use `--scenario all-core --seed-count 20 --task-count 48` on the generated per-scenario output. The seed bands are Train 1–60, Validation 61–80, Test 81–120; the current validation band is exactly 20 seeds. The preferred 30-seed plan therefore requires Mark to widen the Validation band without overlapping Train/Test and to approve the resulting seed allocation. No iFogSim experiment was run for this handoff.

## 4. Verification results

- `pytest -q`: **35 passed**.
- Eight core scenarios generated; each development sample has 48 task rows and a one-row run manifest.
- Each sample has a successful task/manifest validation and deterministic replay check; no outcome or decision records are generated.
- All six JSON Schemas parse and validate structurally.
- The precise task/manifest SHA-256 pairs and canonical config hash are in `reports/dev_hashes_v1_1.json`. Independent regeneration into two separate output directories reproduced all eight task hashes and all eight manifest hashes byte-for-byte; replay is also checked inside the automated tests. The canonical configuration hash is `68e2ba5ad5ab23fbbe32a418b81b14014791978eb3387a5aae3a7f6ed2641c64`.
- The test suite includes a negative partial-action timeline check and confirms the validator rejects merge-before-branch-completion chronology. It also verifies exactly 20 unique, disjoint seed values per split band and rejects a 30-seed request while Validation remains limited to 20 seeds.

`reports/pytest_results.txt`, per-scenario validation JSON, `reports/dev_generation.log`, and `reports/dev_hashes_v1_1.json` retain the command evidence.

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
| Run repetitions | 20 paired seeds minimum; 30 preferred | `PROPOSED` experiment plan | Validation band currently 20; widening needed for preferred 30. No simulator runs included. |

The 2,500 MI / 12,000-byte / 2,000-byte / 500-ms configuration is an existing **one-task input reference**, not an approved distribution. The pilot endpoint latencies are measurements from a one-task controlled run, not generated input parameters and not a deadline calibration dataset.

## 6. Questions for Mark

1. Approve or replace the proposed profile distributions, 50:50 divisibility mix, 20:50:30 urgency mix and per-class deadline brackets after Ayoub supplies nominal service-time evidence.
2. Approve the 0.5 tasks/s steady and 2.0/0.15 tasks/s on/off load levels or provide a target offered-load range.
3. Approve the 0.5 bandwidth/capacity stress multipliers and 90 ms one-way WAN-delay stress level.
4. Decide whether the Validation seed band should be expanded to support 30 paired seeds; current fixed 61–80 yields the 20-seed minimum only.
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

## 9. Git / scope confirmation

No commits, pushes, staging, branch changes, simulator topology or queue modifications, policy changes, or model training were performed. The GitHub connection was used read-only to inspect `main`. Because the available GitHub write actions create commits and the request explicitly prohibits commits/pushes, the deliverable is supplied as an additive overlay ZIP for local application/review.

## 10. Packaging correction addendum (v1.1.1)

The original overlay archive was reported as incomplete by the recipient. The implementation was not rewritten. It has been re-extracted, checked against the complete file manifest, and repackaged with the entire additive tree plus fresh verification evidence. The corrected archive is `Astta-Abdo_Final_Workload_Dataset_Overlay_v1_1_1_COMPLETE.zip`.

- The package contains both YAML configs, all six JSON Schemas, all eight development task/manifest pairs, all four empty simulator/policy CSV templates, generator, validator, the complete tests file, requirements, pytest config, provenance, and scenario validation reports.
- The expanded manifest is `reports/OVERLAY_FILE_MANIFEST.txt`; the package integrity summary is `reports/package_verification/package_integrity_report.json`.
- The commands printed in `WORKLOAD_DATASET_README.md` were rerun from the extracted package directory. Generation produced all eight core scenarios; stable-sample validation including replay passed; pytest output is retained as `reports/pytest_results.txt` and `reports/package_verification/pytest_actual.stdout.txt`.
- All eight regenerated scenario task/manifest pairs passed validation with deterministic replay. A second independent generation run matched all 16 CSV hashes (8 task tables and 8 manifests) byte-for-byte.
- Empty outcome/decision/calibration templates remain header-only. No simulator outcomes were added.
- A fully empty virtualenv could not download dependencies because the package index was unreachable from this execution environment. The documented `pip install -r requirements.txt` command did complete successfully in the available Python environment, where both declared dependencies were already installed. Exact failure output is recorded in `reports/package_verification/fresh_venv_install_attempt.txt`.

This is a packaging/verification correction only. All unverified numeric values retain their existing `PROPOSED` or `BLOCKED` designations. No simulator, policy, model, Git branch, commit or push was changed.
