# Residual Calibration Coverage Audit — 2026-11-18

## Evidence boundary

Reviewed on PR #6 head `1bd25f364f17da8741348478d9b578648017ce34`.

The workload package's `data/dev/schemas_only/calibration_log.csv` contains only its header and **zero data rows**. It is a schema-only simulator-owned table, not an execution log. No persisted `*.risk.json` calibration sidecar is tracked in the reviewed PR tree. Therefore:
- directly logged calibration residual records in this workload package: **0**;
- live/persisted risk-window counts from the separate simulator acceptance run: **NOT AVAILABLE from this branch**;
- do not interpret unavailable sidecar counts as zero observations in the simulator.

## Per-action coverage in the tracked calibration log

| Action | Direct residual rows |
|---|---:|
| LOCAL | 0 |
| EDGE_FULL | 0 |
| CLOUD_FULL | 0 |
| EDGE_PARTIAL_25 | 0 |
| EDGE_PARTIAL_50 | 0 |
| EDGE_PARTIAL_75 | 0 |
| CLOUD_PARTIAL_25 | 0 |
| CLOUD_PARTIAL_50 | 0 |
| CLOUD_PARTIAL_75 | 0 |

## Execution-family coverage in the tracked calibration log

| Family key implemented by `risk.py` | Direct residual rows |
|---|---:|
| family:LOCAL | 0 |
| family:EDGE_FULL | 0 |
| family:CLOUD_FULL | 0 |
| family:EDGE_PARTIAL | 0 |
| family:CLOUD_PARTIAL | 0 |
| pooled | 0 |

All action and family calibration groups are **insufficient** in this dataset package. The runtime calibrator sidecar must be exported to report actual runtime window counts.

## Exact fallback hierarchy

For a requested action, `RiskCalibrator.margin_for` checks in this order:

1. `action:<ACTION_NAME>` — use only if the exact-action window has at least `min_samples=20`.
2. `family:<FAMILY>` — otherwise use the matching family window if it has at least 20 samples. Families do not mix Edge with Cloud or Full with Partial.
3. `pooled` — otherwise use pooled residuals if at least 20 samples exist.
4. `uncalibrated_prior` — otherwise return `calibrated=false` and `uncalibrated_margin_ms` (documented provisional value: 0 ms).

Each residual window is bounded by `window_size=200`. The documented provisional upper-tail setting is `epsilon=0.10`; the finite-sample rank is `ceil((n+1)(1-epsilon))`, without interpolation. Negative quantiles are clipped to zero. These are implementation/configuration facts, not approved scientific calibration settings.

## Observation rule and NO_FILTER limitation

`observe(action, predicted, observed)` records the signed residual `observed - predicted` for the **actually executed action**, and adds that same observed sample to its exact-action, corresponding family, and pooled windows. A trace that lacks a paired pre-decision prediction cannot yield a residual. A `NO_FILTER` execution does not magically calibrate all nine actions: only executed actions with valid paired predictions and completed outcomes can contribute direct observations. No controlled all-action calibration procedure is documented as completed here.

## Required next evidence

Export the exact runtime risk sidecar used by the risk-filtered training acceptance run, with its config fingerprint and run ID. Then report the `windows`/sample counts from that sidecar by exact action and family, and separately list which actions were actually executed. Do not infer these counts from task totals or NO_FILTER traces.
