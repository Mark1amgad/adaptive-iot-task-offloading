# Dataset Source, Provenance & Availability Audit

**As of 2026-11-03. Scope: literature-level verification only. No raw-data inspection, schema validation, preprocessing, merge, or dataset selection.**

## Authority and classification

- `FILE_INDEX.md` is the navigation index. Classification source of truth: `research/references/REFERENCES_INDEX.md` (audit 2026-11-03): **six verified Core Journals**, **two agreed/pending core titles without local PDFs**, two supporting sources, five conference papers. Only `CONF-02` is tracked as a method-comparison reference and **never counted as a Core Journal**.
- `deliverables/02_Methodology/Proposed_Methodology_Experimental_Plan-1.docx` is a draft awaiting supervisor approval. Candidate direction: deadline-feasible contextual placement Local/Edge/Cloud. `deliverables/02_Methodology/Methodology.md` describes a one-task iFogSim test with **configured**, not measured-in-production, input bytes/MI/deadline/network latency. The experimental dataset required for repeated comparisons does not yet exist as a verified complete benchmark.
- Existing `research/datasets/documentation/MEC_Research_Datasets_and_Download_Links_2025_2026.docx` is a historical selection and remains unchanged. Its assertion that the Forecast-Driven paper did not name datasets is contradicted by its full text, §5.1.3 (PDF p.9–10), naming ECW and SMD. `DATASET_INVENTORY.csv` in this directory is the **updated canonical paper-based dataset inventory**; do not continue using the old eight-paper selection as current classification.
- `team-work/Mostafa/Dataset/MASTER_DATASET_COMPARISON.csv` is an earlier catalog of other potential sources; left unchanged. `team-work/Mostafa/Dataset/analysis/dataset_inventory.csv` is a sampling-quality inventory, **not** the canonical literature source inventory. `audit_output/DATASET_AUDIT.md` and similar QA files belong to Abdo's technical-validation responsibility.

## ECW — original primary source

- Origin: Shaoyuan Huang et al., **One for All: Unified Workload Prediction for Dynamic Multi-tenant Edge Cloud Platforms**, KDD 2023, DOI `10.1145/3580305.3599453`. Original dataset: https://github.com/hsy23/ECWDataset and code: https://github.com/hsy23/KDD23_DynEformer .
- Dataset README / Dataset list: real platform upload bandwidth workload for 797 edge servers in ECW-08 and 1,022 in ECW-09. Each tensor has 720 hourly slots and 16 normalized features: 4 dynamic (bandwidth workload + hour/day/week) and 12 static (server location, network and hardware descriptors). Record interval 1 hour. The README says the general collection spans Aug–Oct 2022, but size for October was **Not Reported** in the inspected released variants. `.npy` and min–max normalized for privacy; real original Mbps/CPU units **cannot be recovered merely by reverse scaling** without the authors' scalers and metadata.
- Availability: public dataset repository; separate dataset redistribution license **Not Reported** in inspected repository documentation; public read access is not a blanket permission to redistribute or commercialize. Need author clarification if terms unclear.
- Feasibility: **context/forecasting of edge upload load**, not a task-offloading data table; no task arrivals, CPU cycles, deadlines, actions, simulated/real completion outcomes. In particular `bw_upload` is measured upload load, not each task's input size; `cpu_num` is static core count, not dynamic CPU utilization.

## SMD — original primary source

- Origin: Ya Su et al., **Robust Anomaly Detection for Multivariate Time Series through Stochastic Recurrent Neural Network**, KDD 2019; canonical public project https://github.com/NetManAIOps/OmniAnomaly ; dataset folder https://github.com/NetManAIOps/OmniAnomaly/tree/master/ServerMachineDataset .
- OmniAnomaly README `Data` / `SMD`: five weeks; 28 machines in 3 groups; **38 metrics** (unnamed/anonymized), aggregate **708,405** train and **708,420** test observations. Separate train/test/test_label/interpretation_label. Original cadence commonly documented as ~1 minute; first-party README does not provide native wall-clock timestamps. A published 1-second index in a third-party TsFile adaptation is **synthetic indexing, not true source frequency**.
- Availability: public GitHub folder. Repo `LICENSE` says **MIT** for software and associated documentation; dataset-specific original-data ownership/usage terms require legal review, especially redistribution. Do not adopt a third-party CC BY 4.0 license for the original repository without confirmation.
- Feasibility: telemetry/anomaly detection, not validated server crashes or offloading outcomes. Forecast-Driven paper creates a **derived** failure-event/intensity series using SMD anomaly labels (PDF p.10 §5.1.3); this transforms an anomaly proxy into a modeled risk channel. It does not establish that anomalies are physical failure rates or that those intensities are reproducible without transformation details.

## Paper-evidence audit

| Paper | Exact location | Dataset evidence | Public availability verdict |
|---|---|---|---|
| CORE-01 | Full PDF §5.1.3 pp.9–10; Data availability p.15 | **ECW + SMD**; simulations combine measured telemetry with modeled task-offloading responses | Original raw sources public; study-derived data *on request* |
| CORE-02 | §3–5; Data availability p.20 | Dependent-task stochastic/Monte-Carlo model | *Data available upon request*; no direct public task dataset identified |
| CORE-03 | §5; Data availability p.20 | Simulated MEC experiments | States **“No data was used for the research described in the article.”** |
| CORE-04 | §3–5; Data availability p.12 | Markov failure and recovery / IIoT simulated tasks | *Available on request* |
| CORE-05 | §VIII | Simulations and testbed | No public downloadable experimental task trace established |
| CORE-06 | §VI | Simulated device-edge-cloud partial task offloading | Named downloadable task-level data: **Not Reported** |
| PENDING-01 / 02 | `REFERENCES_INDEX.md`, Pending agreed core papers | No verified full text locally | **Not Reported** — cannot audit datasets yet |
| CONF-02 | §VI pp.6–7, code link in §I | Random synthetic server delays | Public code, no real-world task dataset established; **not core** |
| SUP-01 / 02 | Supporting index; survey / magazine PDF | Survey of sources / simulated MEC | Not original public task-level benchmark |

## Why source combination is *not* automatic

1. ECW edge server entities, SMD anonymized machine entities, and iFogSim logical node IDs have **no common identity key, site, geography or synchronized timestamp**. Concatenation or joining rows would create fabricated correspondence.
2. ECW reflects **edge upload workload**; SMD is primarily generic **datacenter machine anomaly/telemetry**; neither supplies task arrival/deadline/decision/outcome linked records. They may inform **separate** scenario generators or stress-test distributions, clearly identified as proxies.
3. A statistically defensible synthetic workload requires a published generator spec, units, seeds, mapping assumptions, independent train/test partitions, and sensitivity analysis; no synthetic observation may be labeled as real sensor/production execution.
4. No dataset or algorithm is selected. Supervisor approval is necessary before committing to feature mappings or outcome generation.

## Unresolved rights and reproducibility questions

- ECW: exact reuse/redistribution terms? availability of normalization bounds, raw units, privacy fields, version hash, and complete October data?
- SMD: explicit dataset license vs MIT code license, meanings of 38 anonymized channels, native timestamps and cadence, mapping of anomaly labels to reliability/failure?
- CORE-01: can authors share simulated task-level logs, failure-intensity construction code and normalization parameters?
- CORE-02/04: will authors supply experimental draws/results and machine-readable configs on request?
- Pending core papers: obtain full text to establish real datasets, data-availability statements and evidence.
- Methodology: final task requirements/allowed actions/measurement validity, how to estimate queueing and network dynamics, and whether energy is measurable per task?

## Source URLs and citations

- Project classification: `research/references/REFERENCES_INDEX.md` (2026-11-03).
- Project approved-draft methodology: `deliverables/02_Methodology/Proposed_Methodology_Experimental_Plan-1.docx` §§2–10; current integration `deliverables/02_Methodology/Methodology.md`.
- ECW primary README and metadata: https://github.com/hsy23/ECWDataset/blob/main/README.md ; corresponding paper DOI https://doi.org/10.1145/3580305.3599453 .
- SMD primary README: https://github.com/NetManAIOps/OmniAnomaly/blob/master/README.md ; license https://github.com/NetManAIOps/OmniAnomaly/blob/master/LICENSE .
- Independent SMD cadence explanation (secondary, not raw-file verification): https://www.mathworks.com/help/predmaint/ug/multivariate-time-series-anomaly-detection-for-server-monitoring.html .
