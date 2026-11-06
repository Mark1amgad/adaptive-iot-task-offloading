# SMD Technical Audit

**Audit target:** `ServerMachineDataset/` inside the supplied `OmniAnomaly-master(1).zip`  
**Dataset identity:** Server Machine Dataset (SMD), distributed with the OmniAnomaly repository. OmniAnomaly is the repository/model project; the data inspected here is SMD.  
**Status:** inspected read-only; no model was trained and no source file was changed.

## 1. Dataset structure

The supplied SMD folder contains four directories, each with 28 machine-specific files:

| Directory | Files | Contents |
|---|---:|---|
| `train/` | 28 | Numeric training sequences; one file per machine |
| `test/` | 28 | Numeric test sequences; one file per machine |
| `test_label/` | 28 | Point-level binary anomaly labels for test sequences |
| `interpretation_label/` | 28 | Anomaly time ranges and dimension IDs associated with anomalies |

The 28 entities are named `machine-<group>-<index>` and are arranged in three groups. Every train and test matrix inspected has 38 columns.

| Measure | Observed value |
|---|---:|
| Machine/entity count | 28 |
| Feature dimensions per matrix | 38 |
| Train rows total | 708,405 |
| Test rows total | 708,420 |
| Test-label rows total | 708,420 |
| Test anomaly points | 29,444 |
| Test normal points | 678,976 |
| Test anomaly prevalence | 4.1563% |
| Contiguous positive-label segments | 327 |
| Interpretation range lines | 327 |

The supplied OmniAnomaly README describes SMD as a five-week dataset, collected from a large internet company, and says that the 28 machine subsets are trained/tested separately. It describes the train portion as the former half and the test portion as the latter half. The README does not specify the sampling interval or calendar timestamps.

The README says the two portions are of equal length, but the supplied files do not exactly match that statement: test contains 15 more rows than train in total. Fifteen machine files have one more test row than train; the other thirteen have equal train/test lengths. This is small in aggregate but should be documented rather than silently corrected.

There is no `train_label/` directory in the supplied archive. The absence of training labels means that the training labels must not be assumed or fabricated from this package.

## 2. Feature descriptions

The 38 dimensions are stored as comma-separated numeric values without column headers. Neither the data files nor the included README map the 38 channels to physical metric names or units. The safe audit labels are therefore `Metric_00` through `Metric_37` (zero-based array positions), not CPU, RAM, disk, network, or any other inferred metric.

The `interpretation_label` text files contain dimension identifiers in the range 1–38 (37 distinct identifiers were observed across the supplied annotations; identifier 8 was not observed). These identifiers look 1-based, whereas NumPy matrix columns are indexed from zero. The exact feature-ID convention must be confirmed before joining these annotations to columns.

All numeric values observed in train and test lie within `[0, 1]`. The source package does not state the normalization method, units, original raw ranges, or whether each dimension is continuous, categorical, or an encoded counter.

Detailed per-dimension statistics for train and test are in `reports/smd_feature_statistics.csv`. The report retains split and feature-index labels and provides min, percentiles, median, max, mean, standard deviation, and number of machines in which each channel is constant.

## 3. Data quality

### Checks that passed

- All 28 machine files are present in each of the four expected directories.
- All train/test matrices have 38 columns.
- The numeric train/test files contain no NaN or infinite values.
- Every test-label file has exactly the same number of rows as its matching test matrix.
- The observed test-label values are exactly `{0, 1}`.
- No exact duplicate rows were detected within any inspected machine/split matrix.
- All observed train/test values fall between 0 and 1.

### Findings and cautions

1. **Train/test length discrepancy:** 708,405 train rows versus 708,420 test rows (test is larger by 15). This conflicts with the README's equal-length description. Do not truncate or pad either split as part of this audit.
2. **No timestamp or cadence:** the README says five weeks, but the supplied matrices do not carry timestamps or a stated sampling interval. Row indices cannot safely be converted to seconds/minutes.
3. **Anonymous feature channels:** there is no semantic feature dictionary, no physical units, and no documented scaling provenance.
4. **Constant channels:** zero-based feature index 7 is exactly zero across all 708,405 training rows. Other dimensions are constant within some individual machines; the number is available in the statistics CSV. A constant feature may be machine-specific and does not prove a data corruption issue.
5. **Labels only for test:** no training-label directory was included.
6. **Interpretation annotations:** the 327 annotation lines and 327 contiguous positive-label segments match in total count, but this does not mean they match one-to-one per machine. For `machine-1-3`, `machine-3-2`, and `machine-3-3`, the annotation line count differs from the binary-label segment count. Some annotation ranges also cover only part of a longer positive-label interval. Treat `test_label` as the point-level anomaly mask and interpretation files as additional dimension-attribution context, not as interchangeable labels.
7. **Indexing convention:** annotation dimension IDs appear 1-based; matrix positions are 0-based. Do not offset IDs until the source convention is confirmed.

The supplied `ServerMachineDataset/LICENSE` contains an MIT license notice. Preserve its copyright/license notice if the dataset files are redistributed.

## 4. Anomaly analysis

The `test_label` files provide direct point-level anomaly labels. Across all machines:

- Normal points: 678,976 (approximately 95.8437%).
- Anomalous points: 29,444 (approximately 4.1563%).
- Consecutive anomalous regions: 327.
- The longest contiguous anomaly run is 3,161 points (`machine-1-6`).
- Per-machine anomaly prevalence ranges from approximately 0.422% (`machine-1-5`) to 15.653% (`machine-1-6`).

This indicates class imbalance and substantial variation in anomaly prevalence across entities. It also means that a single pooled anomaly percentage hides important machine-level differences. `reports/smd_machine_summary.csv` provides the per-machine anomaly rate, contiguous-segment count, longest run, and median run length.

Anomaly labels are useful as an abnormal-condition indicator for time-series analysis. They do **not** identify an offloading action, task failure, deadline violation, network congestion, or resource exhaustion cause. A label of `1` means the supplied benchmark marks that time point as anomalous; it does not prove which physical resource was responsible.

## 5. Limitations for the task-offloading research

The project currently proposes a task-level state with task size, network latency, edge utilization, and deadline category, plus task completion latency/deadline/resource outcomes (`docs/state-action-reward.md`, `docs/experiment-plan.md`). SMD supplies anonymous machine telemetry and test anomaly labels, not task-level records. It has no task IDs, task sizes, deadlines, selected destinations, actual execution tier, per-task latency, completion status, energy, or cloud cost.

SMD can be considered as a candidate source of *background condition/anomaly traces* only after the channel dictionary, units, time interval, and source provenance are resolved. Its server-machine context is not automatically representative of IoT devices, edge nodes, or cloud infrastructure.

## 6. Evidence files

- `reports/smd_summary.json` — counts, label totals, anomaly prevalence, and structural checks.
- `reports/smd_file_inventory.csv` — per-machine train/test dimensions and numeric quality.
- `reports/smd_machine_summary.csv` — per-machine row counts and anomaly statistics.
- `reports/smd_feature_statistics.csv` — per-channel statistics for train and test.
- `reports/smd_interpretation_ranges.csv` — parsed annotation ranges, preserving stored indices.
- `reports/smd_quality_findings.csv` — machine-level and global quality findings.
- `scripts/inspect_datasets.py` — reproducible read-only audit code.
