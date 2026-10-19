# Dataset audit

## Scope and method

Inspected every file under `team-work/Mostafa/Dataset` (99 files), parsed all accessible CSV/TSV files (10) in full with a standard-library CSV reader, parsed JSON, inspected ZIP/OOXML containers, and verified PDF signatures. Exact per-file inventory, quality results, and numeric results are in the companion CSVs. No original teammate file was modified. The official UCI page for dataset 859 was independently checked: it states 4,000 instances, two features (`Time` and turnaround task execution time in seconds), four edge servers, no missing values, and CC BY 4.0. Other remote dataset claims were not independently verified.

## Locally present data

The actual measurement data are the four UCI CSVs below and three EUA CSVs. Google Cluster has only JSON schema files. The other named candidate datasets are represented by research documentation/metadata and mapping workbooks, not their raw records. Network-security traffic data must not be treated as computational task traces.

## UCI Image Recognition MEC (local, fully parsed)

The extracted archive contains `MacBookPro1.csv`, `MacBookPro2.csv`, `VM.csv`, and `RasberryPi.csv`. The filename supports only an environment label, not Local/Edge/Cloud semantics. The documentation states that `Execution Time` is turnaround time for an image-recognition task; it must therefore not be decomposed into, or added to, separate network and computation delays without a source-supported methodology. It has no action label, task size, deadline, bandwidth, energy, or resource-utilization field. It is calibration/reference data, not a complete offloading dataset.

| File | n | mean | median | sd | min | p25 | p75 | p95 | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| MacBookPro1.csv | 1000 | 0.1081534534 | 0.1074373722 | 0.007636875407 | 0.09291887283 | 0.1036193371 | 0.1115930676 | 0.1178728342 | 0.226392746 |
| MacBookPro2.csv | 1000 | 0.3482916541 | 0.3069785833 | 0.09227901481 | 0.2685930729 | 0.3053584695 | 0.3976003528 | 0.4875399709 | 1.607155323 |
| RasberryPi.csv | 1000 | 1.016930801 | 1.017480612 | 0.1292433089 | 0.8511631489 | 0.9338339567 | 1.037090182 | 1.166437304 | 3.167850971 |
| VM.csv | 1000 | 0.4268136818 | 0.4117746353 | 0.646625659 | 0.166891098 | 0.3982815742 | 0.4266543984 | 0.4477659464 | 20.78938699 |

The official UCI page confirms that the time is the turnaround from the edge node beginning to send an image after connection establishment until recognition result return, and that the unit is seconds. The full computed values, missing counts, duplicates, and schema are in `UCI_DEVICE_STATISTICS.csv` and `DATASET_QUALITY_REPORT.csv`.

## Candidate suitability

| Dataset | Verified local availability | Relevant fields available | Missing fields | Measured vs derived | Confidence | Role / recommendation |
|---|---|---|---|---|---|---|
| UCI Image Recognition MEC | Four parsed execution-time CSVs + nested archives | time, execution time | task size, action/location, network, deadline, energy, utilization | measured turnaround time; no derived labels | local files high; external license/source not independently checked | Calibration/reference only; do not invent tiers |
| EUA | Three parsed location/user CSVs | user/site coordinates/context | task execution/outcomes, network measurements, actions | local tabular records; mapping requires assumptions | local availability high | topology/context, not policy labels |
| Google Cluster | schemas only | field definitions only | raw records locally | metadata only | local availability low | download/verify before workload use |
| ToN-IoT, CICIoT2023, UNSW-IoTraffic, Bot-IoT, UNSW-NB15 | documentation/metadata only | security/network context described | computational task outcomes and tier actions | no local raw data inspected | documentation-only | security/network traffic only; not direct offloading evidence |

## Practical strategy and provenance

1. **Immediate:** use UCI only to sanity-check a simulated image-recognition turnaround-time distribution and EUA only for geography/topology context; retain file/environment provenance.
2. **Further work:** verify official dataset pages, license/access conditions, and download a workload source only when its field definitions match the simulation.
3. **Simulator-generated:** task MI, deadlines, tier placement, link delay/bandwidth, queueing, outcome, utilization, and energy must be generated/measured by iFogSim and recorded as `SIMULATED` unless a validated external measurement is used.
4. **Derived:** any conversion/distribution fit must state the formula and source as `DERIVED`; manually selected values are `ASSUMED`; raw recorded values are `MEASURED`. Never merge these labels.

## Quality notes

CSV results are exact full-file values. Numeric type inference is conservative: an all-nonempty-numeric column is numeric; otherwise it is string. This audit did not silently discard malformed rows (their count is reported). Excel containers were inspected for workbook structure but not cell values because the declared `openpyxl` dependency was unavailable in the audit environment. PDF signatures were checked but content was not text-extracted for the same reason.
