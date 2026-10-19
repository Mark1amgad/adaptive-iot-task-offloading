"""Generate descriptive statistics for copied CSV/TSV dataset files."""

import csv
import math
import statistics
from pathlib import Path


def numeric(values):
    result = []
    for value in values:
        try:
            number = float(value)
        except ValueError:
            return []
        if math.isfinite(number):
            result.append(number)
    return result if len(result) == len(values) else []


def outliers(values):
    if len(values) < 4:
        return 0
    ordered = sorted(values)
    q1, q3 = statistics.quantiles(ordered, n=4, method="inclusive")[0::2]
    spread = q3 - q1
    return sum(value < q1 - 1.5 * spread or value > q3 + 1.5 * spread for value in values)


def inspect(path, root):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
        columns = rows[0].keys() if rows else []
    columns = list(columns)
    duplicate_rows = len(rows) - len({tuple(row.get(column, "") for column in columns) for row in rows})
    missing = sum(1 for row in rows for column in columns if not row.get(column, "").strip())
    numeric_summary = []
    for column in columns:
        values = numeric([row.get(column, "").strip() for row in rows])
        if values:
            numeric_summary.append({
                "file": str(path.relative_to(root)).replace("\\", "/"),
                "column": column,
                "count": len(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "min": min(values),
                "max": max(values),
                "outlier_count_iqr": outliers(values),
            })
    return {
        "file": str(path.relative_to(root)).replace("\\", "/"),
        "rows": len(rows),
        "columns": len(columns),
        "column_names": "|".join(columns),
        "missing_cells": missing,
        "duplicate_rows": duplicate_rows,
        "numeric_columns": "|".join(item["column"] for item in numeric_summary),
    }, numeric_summary


def main():
    root = Path(__file__).parents[1] / "Original"
    output = Path(__file__).parent
    inventories = []
    numeric_rows = []
    for path in sorted(root.rglob("*.csv")) + sorted(root.rglob("*.tsv")):
        inventory, numeric = inspect(path, root)
        inventories.append(inventory)
        numeric_rows.extend(numeric)
    with (output / "dataset_file_statistics.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = list(inventories[0]) if inventories else []
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(inventories)
    with (output / "numeric_column_statistics.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = ["file", "column", "count", "mean", "median", "min", "max", "outlier_count_iqr"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(numeric_rows)
    print(f"files={len(inventories)} numeric_columns={len(numeric_rows)}")


if __name__ == "__main__":
    main()