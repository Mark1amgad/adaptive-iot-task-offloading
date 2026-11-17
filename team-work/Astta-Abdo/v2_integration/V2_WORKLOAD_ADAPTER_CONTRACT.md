# V2 Workload Adapter Contract — Draft for Ayoub Handoff

**Package:** Generator V1.2 → V2 Simulator  
**Status:** SOURCE SIDE VERIFIED; V2 JSONL TARGET KEYS PENDING AYОUB'S CHECKED-IN SCHEMA/SAMPLE  
**Scope:** Python-side contract only. This document does not change Java Simulator, V2 Action Contract, A1/A2 replay, or Seed Governance.

## 1. Evidence boundary

The generator source contract is defined by:
- `schemas/tasks.schema.json`
- `schemas/scenario_manifest.schema.json`
- `schemas/DATA_DICTIONARY.md`
- `configs/workload_profiles.yaml`
- `configs/scenario_profiles.yaml`

The checked-in Ayoub integration README at the inspected repository revision still describes preserved integration-source versions and historical **one-task** JSONL evidence. The topology JSON at that revision is a Local/Edge/Cloud three-executor topology (not the claimed 100/20/1 V2 runtime). No authoritative V2 multi-task JSONL schema, JSONL sample, or field-level runtime mapping contract was found in the checked-in paths inspected for this handoff. Therefore destination JSON keys and simulator-side types are intentionally **UNCONFIRMED** here. Do not implement guessed camelCase/snake_case aliases.

## 2. Source-to-target mapping register

| Generator CSV field | Source type | Canonical unit / semantics | Required? | V2 JSONL destination key | Rule |
|---|---|---|---|---|---|
| `task_id` | string | opaque stable identifier | yes | BLOCKED—Ayoub key confirmation | Copy byte-for-byte; never regenerate in adapter |
| `source_device_id` | string | logical source ID, e.g. `iot-001` | yes | BLOCKED—Ayoub key confirmation | Copy byte-for-byte; resolve via actual runtime source registry; unknown source is fatal |
| `arrival_time_ms` | integer | ms, absolute simulation-clock timestamp | yes | BLOCKED—Ayoub key confirmation | Copy integer unchanged; no seconds conversion unless V2 contract explicitly requires it |
| `relative_deadline_ms` | integer | ms, duration from arrival | yes | BLOCKED—Ayoub key confirmation | Preserve separately if target accepts it |
| `absolute_deadline_ms` | integer | ms, absolute simulation-clock timestamp = arrival + relative deadline | yes | BLOCKED—Ayoub key confirmation | Preserve exact value; do not replace with a duration |
| `input_size_bytes` | integer | bytes | yes | BLOCKED—Ayoub key confirmation | Copy integer unchanged; no bits/KB conversion |
| `required_mi` | number | MI, total task compute demand | yes | BLOCKED—Ayoub key confirmation | Copy numeric value unchanged; no conversion to instructions/cycles without confirmed simulator semantics |
| `urgency_class` | enum string | CRITICAL / TIME_SENSITIVE / DELAY_TOLERANT | yes | BLOCKED—Ayoub key confirmation | Exact enum mapping required; reject unknown values |
| `splittability` | enum string | INDIVISIBLE / DATA_PARALLEL_DIVISIBLE | yes | BLOCKED—Ayoub key confirmation | Exact enum mapping required; reject unsupported values |
| `partition_model_id` | string or null | named synthetic partition rule | yes column; null for indivisible | BLOCKED—Ayoub key confirmation | Preserve null/string; do not invent a default |
| `partition_overhead_ms` | number or null | ms | yes column; null for indivisible | BLOCKED—Ayoub key confirmation | Copy unchanged; applies only where profile/action semantics allow |
| `merge_overhead_ms` | number or null | ms | yes column; null for indivisible | BLOCKED—Ayoub key confirmation | Copy unchanged; applies only where profile/action semantics allow |
| `input_partition_model` | string or null | model identifier | yes column; null for indivisible | BLOCKED—Ayoub key confirmation | Preserve exact identifier/null |
| `output_partition_model` | string or null | model identifier | yes column; null for indivisible | BLOCKED—Ayoub key confirmation | Preserve exact identifier/null |
| `output_size_bytes` | integer | bytes, synthetic expected output size | yes | BLOCKED—Ayoub key confirmation | Preserve if V2 task input contract has this field; otherwise adapter must raise unsupported-required-attribute error pending explicit waiver |
| `seed` | integer | generator seed | yes | manifest/run provenance, exact key pending | Do not conflate with simulator RNG seed |
| `scenario_id` | string | scenario identity | yes | manifest/run provenance, exact key pending | Preserve exact |
| `run_id` | string | generated run identity | yes | manifest/run provenance, exact key pending | Preserve exact |
| `config_hash` | SHA-256 hex | generator configuration provenance | yes | run provenance, exact key pending | Keep distinct from byte-level task-file SHA-256 |
| `units_version` | string | `SI-ms-bytes-MI-v1` | yes | run provenance, exact key pending | Validate equality; no implicit unit conversion |
| `generator_version` | string | generator version | yes | run provenance, exact key pending | Preserve exact |

### Requested attributes not directly represented as task columns

- `deadline`: ambiguous without a declared semantic. Source provides both `relative_deadline_ms` and `absolute_deadline_ms`; adapter must not collapse them. Ayoub must confirm which V2 field(s) are consumed.
- `partition_ratio`: not a generated task attribute in the current task schema. The workload profile defines splittability and partition model; the remote split ratio belongs to the selected action (the legal action contract uses 0.25/0.50/0.75 remote fractions). Do not fabricate a per-task ratio. If V2 JSONL requires one before action selection, integration is blocked pending a contract decision.
- `divisibility`: source name is `splittability`; any rename is a semantic-preserving enum mapping only after Ayoub confirms the destination field and enum values.

## 3. Units and conversion rules

Canonical source units are fixed by `SI-ms-bytes-MI-v1`: time = ms, sizes = bytes, compute demand = MI, compute capacity = MIPS, overheads = ms. For task-input fields listed above, the default adapter conversion is **identity**. Do not convert MI to instructions/cycles, bytes to bits, milliseconds to seconds, or bandwidth to bytes/s/bits/s unless the V2 contract documents the target unit and exact conversion.

Bandwidth is explicitly `NOT_LOCKED_UNIT_PENDING_AYOUB`. No bandwidth conversion can be specified. Network values and capacity profiles are manifest-side exogenous configuration, not task attributes; the adapter must not silently apply proposed profiles as measured/confirmed values.

## 4. Required validation (fail closed)

Reject the entire input batch, with row number + task_id + field + reason, on:
1. Missing required task field, empty required value, invalid type, or unknown enum.
2. Duplicate `(run_id, task_id)`; duplicate task IDs within one run are fatal.
3. Unknown `source_device_id`, missing runtime IoT device, or runtime parent Edge mismatch.
4. Indivisible task carrying non-null partition model/overheads or being offered a partial action.
5. Divisible task missing partition model, input/output partition model, partition overhead, or merge overhead.
6. Non-positive input size/MI/deadline, negative arrival/overhead, or deadline identity violation:
   `absolute_deadline_ms != arrival_time_ms + relative_deadline_ms`.
7. Unsupported or absent destination field in the confirmed V2 JSONL schema.
8. Any unit tag mismatch or conversion that is not explicitly listed in an approved versioned contract.
9. Manifest/task mismatch in run_id, scenario_id, seed, config_hash, task_count, topology target, or file digest.

No default values, inferred source IDs, synthesized task IDs, fallback urgency, default divisibility, or silent field drops are permitted.

## 5. Runtime source mapping check

The Generator V1.2 target contract declares 100 logical sources and a target-only mapping of five IoT IDs per Edge:
`iot-001..iot-005 → edge-001`, continuing in groups of five through `iot-096..iot-100 → edge-020`.

This is a **target contract**, not proof of actual runtime placement. The adapter must resolve every source against Ayoub's actual runtime registry and compare the actual parent Edge with the expected target parent. Do not populate actual topology metadata from this target mapping. Missing source or parent mismatch is a hard validation error and must be recorded in the integration report.

## 6. Required evidence from Ayoub to close this contract

Before destination mappings can be finalized, attach to the repository:
- Exact V2 JSONL schema or authoritative sample from the current integrated simulator commit.
- One record for each of the nine actions, including one valid partial action with both branches and merge events.
- Runtime registry export: IoT ID → actual IoT object ID → actual parent Edge ID; Edge and Cloud IDs.
- Explicit type/unit definitions for arrival/deadline, bytes, MI/cycles, partition/merge durations, and any bandwidth fields.
- Simulator commit SHA and command/config used to generate the JSONL.

Until those artifacts are available, this contract is a source-side handoff draft; no Simulator-Validated claim is permitted.
