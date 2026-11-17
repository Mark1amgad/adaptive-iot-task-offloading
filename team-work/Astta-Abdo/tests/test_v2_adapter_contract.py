from adapter_validation import validate_records, target_parent_crosswalk

def valid_row(**overrides):
    row = {
        "task_id": "t-1", "source_device_id": "iot-001",
        "arrival_time_ms": 10, "relative_deadline_ms": 20,
        "absolute_deadline_ms": 30, "input_size_bytes": 1024,
        "required_mi": 100, "urgency_class": "CRITICAL",
        "splittability": "DATA_PARALLEL_DIVISIBLE",
        "partition_model_id": "frames-v1", "partition_overhead_ms": 2,
        "merge_overhead_ms": 3,
    }
    row.update(overrides)
    return row


def test_unknown_source_is_rejected():
    errors = validate_records([valid_row()], runtime_inventory={})
    assert any(e.startswith("UNKNOWN_SOURCE") for e in errors)


def test_duplicate_task_id_is_rejected():
    errors = validate_records([valid_row(), valid_row()], runtime_inventory={"iot-001": {"simulator_device_id": "id1", "parent_edge_id": "edge-001"}})
    assert any(e.startswith("DUPLICATE_TASK_ID") for e in errors)


def test_missing_required_field_is_rejected():
    row = valid_row()
    del row["required_mi"]
    assert any("MISSING_REQUIRED_FIELD" in e and "required_mi" in e for e in validate_records([row]))


def test_invalid_divisibility_is_rejected():
    assert any("INVALID_DIVISIBILITY" in e for e in validate_records([valid_row(splittability="MAYBE")]))


def test_invalid_partition_ratio_is_rejected():
    assert any("INVALID_PARTITION_RATIO" in e for e in validate_records([valid_row(partition_ratio=1.0)]))


def test_invalid_deadline_is_rejected():
    assert any("INVALID_DEADLINE" in e for e in validate_records([valid_row(absolute_deadline_ms=31)]))


def test_source_mapping_mismatch_is_rejected_without_alias_guessing():
    inventory = {"iot-001": {"simulator_device_id": "iot-1", "parent_edge_id": "edge-002"}}
    target = {"iot-001": "edge-001"}
    errors = validate_records([valid_row()], expected_target_parent=target, runtime_inventory=inventory)
    assert any(e.startswith("SOURCE_MAPPING_MISMATCH") for e in errors)


def test_target_crosswalk_has_100_sources_and_20_edges():
    mapping = target_parent_crosswalk([f"iot-{i:03d}" for i in range(1, 101)])
    assert len(mapping) == 100
    assert len(set(mapping.values())) == 20
    assert mapping["iot-001"] == mapping["iot-005"] == "edge-001"
    assert mapping["iot-006"] == "edge-002"
    assert mapping["iot-100"] == "edge-020"
