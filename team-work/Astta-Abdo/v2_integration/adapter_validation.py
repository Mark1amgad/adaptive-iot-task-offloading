"""Fail-closed source-side validation primitives for the V2 workload adapter.

No V2 JSONL destination keys or simulator IDs are guessed here. The runtime
inventory must be supplied explicitly by the simulator integration owner.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Mapping, Any

REQUIRED_FIELDS = (
    "task_id", "source_device_id", "arrival_time_ms", "relative_deadline_ms",
    "absolute_deadline_ms", "input_size_bytes", "required_mi", "urgency_class",
    "splittability", "partition_model_id", "partition_overhead_ms",
    "merge_overhead_ms",
)
URGENCY = {"CRITICAL", "TIME_SENSITIVE", "DELAY_TOLERANT"}
DIVISIBILITY = {"INDIVISIBLE", "DATA_PARALLEL_DIVISIBLE"}


def _decimal(value: Any, field: str, errors: list[str], task_id: str) -> Decimal | None:
    try:
        result = Decimal(str(value))
        if not result.is_finite():
            raise InvalidOperation
        return result
    except (InvalidOperation, ValueError, TypeError):
        errors.append(f"INVALID_VALUE task_id={task_id} field={field} value={value!r}")
        return None


def validate_records(
    records: list[Mapping[str, Any]],
    *,
    expected_target_parent: Mapping[str, str] | None = None,
    runtime_inventory: Mapping[str, Mapping[str, str]] | None = None,
) -> list[str]:
    """Validate task inputs. runtime_inventory maps original source ID to
    {'simulator_device_id': ..., 'parent_edge_id': ...}; no alias normalization.
    """
    errors: list[str] = []
    seen: set[str] = set()
    for index, row in enumerate(records, start=1):
        task_id = str(row.get("task_id", "") or "")
        prefix = f"row={index} task_id={task_id or '<missing>'}"
        missing = [f for f in REQUIRED_FIELDS if f not in row or row[f] in (None, "")]
        # Partition columns are nullable for indivisible tasks, but their columns
        # must exist in the source schema.
        for field in missing:
            errors.append(f"MISSING_REQUIRED_FIELD {prefix} field={field}")
        if not task_id:
            continue
        if task_id in seen:
            errors.append(f"DUPLICATE_TASK_ID {prefix}")
        seen.add(task_id)

        source = str(row.get("source_device_id", "") or "")
        if source and runtime_inventory is not None:
            resolved = runtime_inventory.get(source)
            if resolved is None:
                errors.append(f"UNKNOWN_SOURCE {prefix} source_device_id={source}")
            elif expected_target_parent is not None:
                expected_parent = expected_target_parent.get(source)
                actual_parent = resolved.get("parent_edge_id")
                if expected_parent is not None and actual_parent != expected_parent:
                    errors.append(
                        f"SOURCE_MAPPING_MISMATCH {prefix} source_device_id={source} "
                        f"expected_parent={expected_parent} actual_parent={actual_parent}"
                    )
            if resolved is not None and not resolved.get("simulator_device_id"):
                errors.append(f"MISSING_SIMULATOR_DEVICE_ID {prefix} source_device_id={source}")

        urgency = row.get("urgency_class")
        if urgency and urgency not in URGENCY:
            errors.append(f"INVALID_URGENCY {prefix} value={urgency!r}")
        split = row.get("splittability")
        if split not in DIVISIBILITY:
            errors.append(f"INVALID_DIVISIBILITY {prefix} value={split!r}")

        arrival = _decimal(row.get("arrival_time_ms"), "arrival_time_ms", errors, task_id)
        relative = _decimal(row.get("relative_deadline_ms"), "relative_deadline_ms", errors, task_id)
        absolute = _decimal(row.get("absolute_deadline_ms"), "absolute_deadline_ms", errors, task_id)
        size = _decimal(row.get("input_size_bytes"), "input_size_bytes", errors, task_id)
        compute = _decimal(row.get("required_mi"), "required_mi", errors, task_id)
        if arrival is not None and arrival < 0:
            errors.append(f"INVALID_ARRIVAL {prefix} arrival_time_ms must be >= 0")
        if relative is not None and relative <= 0:
            errors.append(f"INVALID_DEADLINE {prefix} relative_deadline_ms must be > 0")
        if absolute is not None and absolute <= 0:
            errors.append(f"INVALID_DEADLINE {prefix} absolute_deadline_ms must be > 0")
        if arrival is not None and relative is not None and absolute is not None:
            if absolute != arrival + relative:
                errors.append(f"INVALID_DEADLINE {prefix} absolute_deadline_ms != arrival_time_ms + relative_deadline_ms")
        if size is not None and size <= 0:
            errors.append(f"INVALID_INPUT_SIZE {prefix} input_size_bytes must be > 0")
        if compute is not None and compute <= 0:
            errors.append(f"INVALID_COMPUTE_DEMAND {prefix} required_mi must be > 0")

        ratio = row.get("partition_ratio")
        if split == "INDIVISIBLE":
            for field in ("partition_model_id", "partition_overhead_ms", "merge_overhead_ms"):
                if row.get(field) not in (None, ""):
                    errors.append(f"INVALID_DIVISIBILITY {prefix} indivisible task has {field}")
            if ratio not in (None, ""):
                errors.append(f"INVALID_PARTITION_RATIO {prefix} indivisible task must not declare partition_ratio")
        elif split == "DATA_PARALLEL_DIVISIBLE":
            if not row.get("partition_model_id"):
                errors.append(f"MISSING_REQUIRED_FIELD {prefix} field=partition_model_id")
            for field in ("partition_overhead_ms", "merge_overhead_ms"):
                value = _decimal(row.get(field), field, errors, task_id)
                if value is not None and value < 0:
                    errors.append(f"INVALID_OVERHEAD {prefix} field={field} must be >= 0")
            if ratio not in (None, ""):
                value = _decimal(ratio, "partition_ratio", errors, task_id)
                if value is not None and not (Decimal(0) < value < Decimal(1)):
                    errors.append(f"INVALID_PARTITION_RATIO {prefix} partition_ratio must be strictly between 0 and 1")
    return errors


def target_parent_crosswalk(source_ids: list[str]) -> dict[str, str]:
    """Construct only the declared target mapping; does not claim runtime truth."""
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("duplicate source IDs in target crosswalk input")
    expected = {f"iot-{i:03d}" for i in range(1, 101)}
    if set(source_ids) != expected:
        raise ValueError("target source list must be exactly iot-001..iot-100")
    return {
        source: f"edge-{((int(source[-3:]) - 1) // 5) + 1:03d}"
        for source in source_ids
    }
