# ECW Technical Audit

**Audit target:** `ECW_09.npy` from the supplied `ECW_09.zip`  
**Audit purpose:** determine what the supplied ECW file actually contains and how much of it can support the future IoT task-offloading study.  
**Status:** inspected read-only; no source file was changed.

## 1. Dataset structure

The supplied ECW archive contains exactly one data file: `ECW_09.npy`. No README, schema, feature dictionary, timestamps, labels, train/test split, device/entity identifiers, sampling interval, or license file accompanied it.

| Property | Observed value |
|---|---:|
| File format | NumPy `.npy` |
| Shape | `(1022, 720, 16)` |
| Data type | `float64` |
| Number of scalar values | 11,773,440 |
| Axis 0 | 1,022 groups/windows (meaning not documented) |
| Axis 1 | 720 positions per group (time interpretation not documented) |
| Axis 2 | 16 numeric channels |
| Global minimum / maximum | 0.0 / 1.0 |
| Global mean / standard deviation | 0.366588 / 0.327947 |
| Non-finite values | 0 |
| Exact duplicate windows | 0 |

The dimensions suggest a grouped, sequential structure, but the archive does not identify what one group represents or whether axis 1 is a regular time axis. This audit therefore uses *group/window* and *position* as neutral structural terms, not as confirmed domain semantics.

The SHA-256 of the supplied extracted file is recorded in `reports/ecw_summary.json` so that the inspected artifact can be identified exactly.

## 2. Feature descriptions

The file contains 16 numeric channels. **No semantic feature names or units are supplied.** Names such as `Feature_00` below are placeholders used only to index the array; they are not inferred labels.

| Zero-based index | Audit label | Min–max | Mean | Unique values | Windows with within-window std ≤ 1e-12 |
|---:|---|---:|---:|---:|---:|
| 0 | Feature_00 | 0–1 | 0.1019 | 735,663 | 0 / 1,022 |
| 1 | Feature_01 | 0–1 | 0.5000 | 24 | 0 / 1,022 |
| 2 | Feature_02 | 0–1 | 0.5056 | 7 | 0 / 1,022 |
| 3 | Feature_03 | 0–1 | 0.5167 | 5 | 0 / 1,022 |
| 4 | Feature_04 | 0–1 | 0.4770 | 28 | 1,022 / 1,022 |
| 5 | Feature_05 | 0–1 | 0.1614 | 2 | 1,022 / 1,022 |
| 6 | Feature_06 | 0–1 | 0.5675 | 2 | 1,022 / 1,022 |
| 7 | Feature_07 | 0–1 | 0.4418 | 3 | 1,022 / 1,022 |
| 8 | Feature_08 | 0–1 | 0.8948 | 5 | 1,022 / 1,022 |
| 9 | Feature_09 | 0–1 | 0.2138 | 167 | 1,022 / 1,022 |
| 10 | Feature_10 | 0–1 | 0.2434 | 386 | 1,022 / 1,022 |
| 11 | Feature_11 | 0–1 | 0.2789 | 16 | 1,022 / 1,022 |
| 12 | Feature_12 | 0–1 | 0.1912 | 145 | 1,022 / 1,022 |
| 13 | Feature_13 | 0–1 | 0.1214 | 335 | 1,022 / 1,022 |
| 14 | Feature_14 | 0–1 | 0.3297 | 1,022 | 1,022 / 1,022 |
| 15 | Feature_15 | 0–1 | 0.3203 | 1,022 | 1,022 / 1,022 |

The within-window statistic is calculated independently for each group and channel. In this supplied array, channels 4–15 have within-window standard deviation at or below the audit tolerance in every group; the values can still differ between groups. Channels 0–3 vary within each group. This is a structural observation only: it does **not** establish which channels are identifiers, categorical fields, measurements, or static configuration values.

Full per-channel percentiles, extrema, means, standard deviations, and distinct-value counts are in `reports/ecw_feature_statistics.csv`.

## 3. Data quality

### Checks that passed

- The file loads as a numeric 3-D NumPy array with `allow_pickle=False`.
- All 11,773,440 values are finite.
- All observed values are within `[0, 1]`.
- No two of the 1,022 groups are exact duplicate arrays under a SHA-256 content check.

### Quality and documentation gaps

- There are no feature names, units, definitions, value encodings, or authoritative mapping to physical system measurements.
- No timestamps, sampling period, sequence boundary definition, source entity IDs, or group meaning are supplied.
- No anomaly/normal labels or event boundaries are included in the supplied archive.
- No documented split or provenance/version information is included beyond the filename and uploaded archive.
- No license or redistribution terms are present in the supplied ECW archive.

Values in `[0, 1]` are consistent with normalization or bounded encoding, but the method and reference range are unknown. The audit does not reverse or reinterpret that scaling.

## 4. Statistical findings

- Global mean is approximately `0.3666`; global standard deviation is approximately `0.3279`.
- Feature_00 is highly variable in the aggregate (735,663 distinct values), unlike several low-cardinality channels.
- Feature_05 through Feature_08 each contain only 2–5 distinct values and are constant within every group over the 720 stored positions.
- Feature_14 and Feature_15 each have 1,022 distinct values across the array while remaining effectively constant within each group. This can indicate group-level variation, but cannot be assigned a real-world meaning without metadata.
- Channels 4 and 9–15 show varying degrees of within-group constancy; the detailed counts are preserved in the feature statistics CSV.

These findings describe numeric behavior only. No anomaly rate, workload rate, CPU utilization, network delay, or task metric can be calculated from this file without a semantic definition and appropriate labels/units.

## 5. Limitations for the task-offloading research

The target research state currently proposes task size, network latency, edge utilization, and a deadline category (`docs/state-action-reward.md`). ECW's 16 unnamed channels cannot be mapped to any of those inputs from the evidence supplied. The file also contains no task IDs, task arrivals, deadlines, tier identity, execution outcomes, or reward terms.

ECW may become useful as a source of dynamic numeric traces **only after** its provenance, feature dictionary, axis meanings, and time resolution are obtained and a defensible mapping is agreed. It is not presently a documented IoT task workload dataset, and it cannot directly supervise or evaluate an offloading decision.

## 6. Evidence files

- `reports/ecw_summary.json` — shape, dtype, global quality, hash, and metadata availability checks.
- `reports/ecw_feature_statistics.csv` — detailed statistics for all 16 channels.
- `scripts/inspect_datasets.py` — reproducible read-only audit code.
