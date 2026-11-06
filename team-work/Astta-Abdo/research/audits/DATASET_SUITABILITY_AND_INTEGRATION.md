# Dataset Suitability and Integration Assessment

**Research target:** Adaptive AI-Based Task Offloading in IoT Edge-Cloud Networks Under Dynamic Conditions  
**Sources assessed:** ECW_09.npy and SMD from the supplied OmniAnomaly archive  
**Assessment status:** independent, evidence-based pre-integration assessment. No dataset merge, task-record synthesis, final preprocessing, model training, or offloading algorithm was performed.

## 1. Executive assessment

| Question | Assessment |
|---|---|
| Does ECW directly provide task-offloading records? | **No.** It is a 3-D numeric array with 16 unnamed channels and no supplied labels, timestamps, feature dictionary, or task fields. |
| Does SMD directly provide task-offloading records? | **No.** It is a 28-entity multivariate server time-series benchmark with 38 unnamed channels and test anomaly labels, not task arrivals/actions/outcomes. |
| Which is currently more useful? | **SMD**, for a limited purpose: it has identifiable machine-separated sequences, test anomaly labels, and dimension-attribution files. This makes it the stronger current source for studying abnormal time-series conditions. It is not a direct IoT workload dataset. |
| Is ECW usable? | **Potentially, but not yet interpretable.** Its numeric structure is inspectable, but the lack of provenance and channel definitions prevents a defensible mapping. |
| Can ECW and SMD be combined reliably now? | **No.** They have different structures, unknown/unnamed channel semantics, no shared key, no shared timestamp/cadence, and different label availability. |
| Can they help create a future IoT simulation dataset? | **Conditionally.** After metadata and mapping are resolved, either source could inform dynamic environment/condition traces while the simulator generates task records and measures task outcomes. This is a future option, not a completed or approved experiment design. |

## 2. Independent suitability assessment

### ECW

**Strengths**

- Numeric multivariate sequence structure: 1,022 groups, 720 positions, and 16 channels.
- All values are finite and bounded between 0 and 1.
- No exact duplicate windows were found.
- The array contains within-group temporal variation in some channels and group-level/static behavior in others, so it is not a flat single-vector file.

**Weaknesses / blockers**

- The supplied archive contains only `ECW_09.npy`; no source paper, dataset README, channel dictionary, units, timestamps, sampling interval, group identity, or labels were included.
- It is not possible to identify which channels, if any, represent task, compute, memory, network, or resource conditions.
- The axis meanings are undocumented. It is not safe to call each 720-position axis a time series with a known cadence or each 1,022 group a device/task.
- No task-level rows, arrivals, deadlines, tier actions, task execution outcomes, or task IDs exist.

**Suitability conclusion:** insufficiently documented for a scientific feature mapping at this stage. Retain it as a candidate source, but do not use its channels as specific simulator state inputs until its provenance and schema are obtained.

### SMD

**Strengths**

- The included README identifies the dataset as SMD and describes its 28 machine entities, 38 dimensions, and per-machine train/test setup.
- The archive contains paired train/test data and test point labels for all 28 entities.
- Test labels are binary and align row-for-row with their test matrices.
- Interpretation files provide anomalous ranges and dimension IDs.
- The point labels allow reproducible anomaly prevalence and event-duration summaries. The measured overall test anomaly prevalence is 4.1563%.
- An MIT license notice is included in the SMD folder.

**Weaknesses / blockers**

- All 38 columns are anonymous and have no physical units or documented normalization procedure.
- No timestamp column or sampling interval is supplied; the five-week description alone does not define elapsed time per row.
- The dataset is described as server-machine telemetry, not IoT device/edge/cloud workload measurements.
- No task input size, CPU cycles per task, memory requirement, deadline, task arrival process, selected placement, task latency, completion/failure, or reward is supplied.
- Labels exist for test but no `train_label/` folder was supplied.
- Train/test row totals differ by 15, despite the included README saying the two partitions are equal length.
- The interpretation annotations have index/boundary caveats and should not replace the point-level test labels.

**Suitability conclusion:** the stronger of the two current sources for supplying abnormal time-series context and machine-separated dynamic patterns. It is still only an indirect environment-signal source; it cannot directly produce the task-level state or reward required by the offloading study.

## 3. ECW/SMD integration feasibility

### Direct concatenation or row-wise merge

**Not reliable and not recommended.**

- ECW shape: `(1022, 720, 16)`; SMD: 28 independent entities with 38-channel train/test sequences.
- There is no common channel schema, shared row identifier, entity key, timestamp, or sample interval.
- ECW has no supplied anomaly labels; SMD has test labels and interpretation files.
- Both contain normalized values, but matching `[0,1]` ranges do not imply matching units, scaling, semantics, or distribution meaning.
- A 16-channel ECW vector cannot be aligned to a 38-channel SMD vector on the evidence supplied.

A direct concatenation would produce a table with arbitrary feature alignment and no defensible physical meaning. It would not be a scientifically reliable IoT task dataset.

### Conditional use in a future simulator-generated dataset

A more defensible possibility — subject to the research team agreeing on the methodology — is to keep source data separate and use validated source information as **condition traces or scenario context** while iFogSim generates the IoT tasks and measures their outcomes.

Conceptual stages only:

1. Obtain authoritative metadata for ECW and SMD: provenance, feature meanings, units, time cadence, and index conventions.
2. Decide which specific channels, if any, have a defensible relation to dynamic edge/cloud conditions. Do not select channels merely because their numerical range looks plausible.
3. Define a simulator mechanism that can replay or model those validated conditions without changing the original source files.
4. Generate IoT tasks in the simulator from a separately specified workload model; the task size, compute demand, arrival, deadline, and other task properties must come from that model, not from anonymous telemetry columns.
5. Record task-level state, requested action, actual execution tier, and outcome with a stable task identifier. Preserve source-trace provenance separately where a source trace influenced a scenario.
6. Validate that the simulator actually applies the selected action and measures the requested outcomes before any learning or experiment claims are made.

This is a feasibility path, not a finalized protocol. No source channel mapping, task generation rule, trace replay method, simulator configuration, or experiment parameter is approved by this audit.

## 4. Missing information

### Required for ECW

- Original dataset title/meaning and authoritative source URL, paper, author, and version.
- Definitions for all 16 channels, physical units, encodings, and normalization/scaling process.
- Meaning of all three array axes, group/window identity, and whether axis 1 is chronological.
- Sampling frequency/interval and timestamp origin, if the second axis is temporal.
- Device/entity context and any labels or ground-truth annotations.
- License and redistribution conditions.

### Required for SMD

- The authoritative 38-dimension feature dictionary and original units.
- Normalization/scaling details and any preprocessing already applied before the supplied files were packaged.
- Sampling interval, timestamps, and the exact meaning of the five-week duration.
- Confirmed indexing rules for interpretation feature IDs and interval endpoints.
- Explanation for the 15-row train/test total discrepancy relative to the README's equal-split statement.
- The original provenance/version/checksum and citation to use in research reporting.
- Confirmation of how to interpret the server entity names in the context of the intended IoT-edge-cloud environment.

### Required for the IoT simulation dataset

- Agreed task schema: task ID, input/output sizes, computational demand, memory demand, arrival time, deadline, priority/QoS, and optional application/dependency fields.
- Local, edge, and cloud node specifications: processing capacity, cores, RAM, hierarchy, and any energy/cost model.
- Network topology and link parameters: delay, bandwidth, queueing, traffic/load, and loss/jitter if in scope.
- Verified simulator observations and per-task outcome hooks.
- Agreed units, normalization, discretization, and reward definition/weights.
- Agreed decision-process and experimental protocol. The parent repository still marks the contextual-bandit versus sequential-MDP framing, state thresholds, reward scales/weights, and several measurements as open decisions.

## 5. Risks and assumptions

| Risk | Why it matters | Required control |
|---|---|---|
| Semantic mislabeling of anonymous channels | A numeric column could be falsely presented as CPU, memory, or latency. | Obtain codebooks and source provenance before mapping. |
| Incompatible time bases | Replaying unrelated row indices as synchronized time may create artificial correlations. | Confirm cadence/timestamps; document any later resampling or replay method. |
| Domain shift from servers to IoT/edge/cloud | SMD machine patterns may not represent constrained IoT devices or fog/cloud nodes. | Treat SMD as condition context only unless domain validity is established. |
| Misuse of anomaly labels | An anomaly is not automatically a resource bottleneck, network outage, task failure, or deadline miss. | Keep anomaly labels semantically separate from simulator outcomes. |
| Label/annotation mismatch | Interpretation ranges are not guaranteed to recreate every point-level anomaly interval. | Use `test_label` for point labels; preserve interpretation files as separate annotations and verify indexing. |
| Unspecified scaling | Equal numeric ranges do not make different sources comparable. | Recover scaling definitions before any cross-source calibration. |
| Synthetic data presented as measured data | Simulated task results could be misrepresented as real IoT observations. | Label simulator-generated rows and preserve source provenance distinctly. |
| Unverified simulator measurements | A metric may be aggregate-only or unavailable per task. | Verify measurement hooks and task-ID linkage before including it. |
| Unfixed research protocol | State/action/reward/MDP decisions remain open in project docs. | Do not lock data-generation rules until team decisions are recorded. |

## 6. Technical recommendation

1. **Do not merge ECW and SMD.** Keep their raw files and audit summaries independent.
2. **Treat SMD as the stronger current candidate** for abnormal-condition or telemetry-pattern context because its identity, dimensionality, point labels, and annotations are documented in the supplied OmniAnomaly README and source structure. Do not treat SMD as an IoT task dataset.
3. **Hold ECW pending documentation.** Its shape and numeric quality are known, but its scientific meaning is not. Ask the provider/team member who supplied it for the original source and 16-channel dictionary.
4. **Build task-level data through the simulator, not by concatenating telemetry.** After feature mapping and protocol agreement, define a separate simulation workload that creates tasks and measures actual Local/Edge/Cloud execution outcomes. Keep raw source identity separate from generated task fields.
5. **Verify the simulator before dataset generation.** In this repository archive, `simulator/` contains only a README and `.gitkeep`; the project documents describe task generation and measurement as planned/pending, and the integration contract is a draft. An earlier discovery report refers to an external iFogSim worktree, but that source tree is not included in the uploaded project archive and was not independently verified in this audit.
6. **Resolve the open experimental decisions first.** The parent project still marks the state boundaries, units, optional network-load feature, reward weights/normalization, and decision-process framing as undecided. This audit deliberately does not choose them.

## 7. Main technical blockers

- ECW provenance, channel semantics, axes, time basis, labels, and license are missing.
- SMD channel meanings, physical units, normalization method, and sample cadence are missing.
- Neither source provides task-level workload characteristics or offloading outcomes.
- There is no reliable key or temporal alignment for joining ECW to SMD.
- The supplied project archive does not contain a verifiable end-to-end iFogSim workload/measurement implementation; the project documents identify key components as planned or pending.
- Per-task task ID → action → actual execution site → outcome linkage is not established.
- The final state/reward/experiment protocol is not agreed.

## 8. Final decision

**SMD is the more useful current research input, narrowly for anomaly-aware condition traces. ECW is not yet interpretable enough to use responsibly. The two cannot be combined reliably as raw datasets. A future IoT dataset can still be built with information from both, but only through a documented, simulator-driven process after their metadata and the offloading measurement contract are resolved.**
