# V2 Integration Fixtures — Source-Side Acceptance Set

Status: **ready as adapter test design; V2 destination-key assertions await Ayoub's JSONL schema**.

## Small fixture

Use the first two rows from `data/dev/stable_steady__seed_1300_tasks.csv` without editing them. The source rows include:
- `stable_steady-s1300-t000001`, source `iot-001`, arrival 867 ms, deadline absolute 1362 ms, 50,000 bytes, 4,000 MI, divisible, partition overhead 3 ms, merge overhead 4 ms.
- `stable_steady-s1300-t000002`, source `iot-002`, arrival 5,527 ms, absolute deadline 7,283 ms, 2,000 bytes, 1,000 MI, divisible, partition overhead 3 ms, merge overhead 4 ms.

These are fixture examples only; retain exact source CSV values as fixture input. Expected source-parent target mapping: iot-001 → edge-001; iot-002 → edge-001.

## Full 100-source fixture

Expected source IDs: exactly `iot-001` through `iot-100`, unique and complete. Target mapping groups of five:
- edge-001: iot-001..iot-005
- edge-002: iot-006..iot-010
- …
- edge-020: iot-096..iot-100

Expected counts: 100 IoT source identities, 20 target Edge identities, one target Cloud identity. This is a target-contract fixture only. Actual runtime mapping must be read from Ayoub's simulator export and compared, not inferred from this fixture.

## Negative fixtures (each must fail closed)

| Fixture ID | Mutation | Expected validation error |
|---|---|---|
| missing_source | Replace source_device_id with an unregistered ID | UNKNOWN_SOURCE_DEVICE / MISSING_RUNTIME_SOURCE |
| duplicate_task_id | Duplicate task_id in the same run_id | DUPLICATE_TASK_ID |
| invalid_divisibility | Set splittability to an unknown enum, or mark INDIVISIBLE while retaining partition fields / requesting partial action | INVALID_DIVISIBILITY / PARTIAL_ACTION_FOR_INDIVISIBLE |
| missing_required_fields | Remove task_id, arrival_time_ms, required_mi, or other required schema field | MISSING_REQUIRED_FIELD |
| parent_edge_mismatch | Actual runtime parent Edge differs from the target mapping | SOURCE_PARENT_EDGE_MISMATCH |
| manifest_mismatch | task_count/config_hash/seed/scenario_id differs from manifest | MANIFEST_TASKSET_MISMATCH |
| deadline_mismatch | absolute_deadline_ms != arrival_time_ms + relative_deadline_ms | DEADLINE_IDENTITY_MISMATCH |
| unit_mismatch | units_version differs or target conversion is unknown | UNIT_CONTRACT_MISMATCH |

## Preservation assertions

For every input row and emitted V2 record, compare exact values for task_id, source_device_id, arrival_time_ms, relative_deadline_ms, absolute_deadline_ms, input_size_bytes, output_size_bytes, required_mi, urgency_class, splittability, partition_model_id, partition_overhead_ms, merge_overhead_ms, input_partition_model, and output_partition_model. Any missing destination mapping is an error, never a default.

For each run, reconcile generated row count = accepted records + explicitly rejected records. The adapter must not silently drop records.
