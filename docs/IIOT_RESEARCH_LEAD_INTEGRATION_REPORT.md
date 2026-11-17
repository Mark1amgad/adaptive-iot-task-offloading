# Mark — IIoT Research Lead Integration Report

**Status:** Initial Research Lead review completed; industrial transition draft prepared; technical integration gates remain open.  
**Branch:** mark/iiot-scope-transition-v1  
**Base revision:** mark/paired-seeds-v1 at 6f0d59d514dce7390f7c3f6107294960d3ff9624  
**Approval:** The IIoT / Smart Manufacturing domain change is not final until supervisor / teaching-assistant approval.

## 1. Executive decision

The project can be adapted to Industrial IoT / Smart Manufacturing without discarding the existing simulator, nine-action contract, risk-calibration code, task lifecycle, or paired evaluation framework. The adaptation should be additive and evidence-gated.

The proposed application layer contains three industrial task archetypes:

1. Predictive maintenance — machine vibration / temperature window inference.
2. Visual quality inspection — product-image inference and independent image batches.
3. Production monitoring — machine-state/event inference and independent window aggregation.

These archetypes provide the semantics for synthetic industrial workloads. They do not imply that the repository currently contains measured factory task traces.

The strongest defensible research direction is a controlled empirical study of risk-calibrated end-to-end feasibility over legal Local / Edge / Cloud full and constrained partial execution options, evaluated under separated industrial workload, network, and Edge-capacity shifts. A claim that the learning algorithm itself is novel is not approved.

## 2. Repository audit and reuse decision

| Existing asset | Current evidence | Decision for IIoT transition |
|---|---|---|
| MARK_RESEARCH_SPECIFICATION_V2.md | Existing controlling generic-IoT research definition and scope limits | Preserve as historical baseline; use the additive IIoT draft for review; do not overwrite before approval |
| Python V2 agent and protocol | Nine-action masked tabular learner, persistence, schemas, training/evaluation modes | Reuse initially; accurately name the learner; audit state coverage and fallback before claiming adaptation |
| Risk Calibration V1 | Per-action / family / pooled residual windows, one-sided margin, feasibility mask, frozen evaluation support | Reuse mechanism; recalibrate only on approved development / validation data; verify industrial partition and queue inputs |
| Java V2 / iFogSim2 full and partial integration | Full Local / Edge / Cloud actions, partial Local+remote branches, two-result barrier, merge Cloudlet, watchdog and outcomes | Reuse as engineering foundation; repeat contract and event-timing checks under the industrial task schema |
| A→B→A generator and paired runner | Deterministic A/B/A, controlled network-only / workload-only options, fixed-deadline argument, five policy arms | Reuse generator / orchestration; industrialize task profiles and run separate controlled modes |
| Paired-seed inference and recovery analyzer | Seed-level bootstrap, Wilcoxon / Holm, phase metrics and recovery comparisons | Reuse as the analysis baseline; expand only for approved ablations and industrial application strata |
| Abdo workload package V1.1 | Deterministic synthetic tasks, scenario manifests, schema contracts, divisibility checks, replay validation | Adapt the existing package; do not create a second workload generator |
| Mostafa dataset inventory | Eight candidate datasets with measured / derived / simulated distinctions and access status | Reuse the audit as source-of-truth; do not promote uninspected files or generic traffic into task traces |
| Existing 20-seed A→B→A results | Generic workload, legacy B deadline differs from A, model / sidecar frozen | Preserve as historical generic evidence; not the final fixed-deadline IIoT result |
| Existing simulator topology | One Local, one Edge, one Cloud; known MIPS; bandwidth unit and downlink details unresolved | Reuse for Stage 0 smoke test only; the target 4-source / 2-Edge / 1-Cloud layout requires Ayoub verification |

## 3. Dataset-to-industrial-use decision

The existing eight-dataset audit does not contain a complete smart-factory offloading trace.

| Existing dataset | What the audit supports | IIoT research use |
|---|---|---|
| ToN-IoT | Laboratory IoT / IIoT telemetry, network captures, Linux / Windows logs; data files were not downloaded | Best existing IIoT context candidate, but no numerical workload use until files, fields, units, dates, and license are verified |
| UCI Image Recognition MEC | Four inspected CSVs, each with Time and Execution Time; image-recognition turnaround measurements on four compute environments | Limited image-execution-time reference; not a factory quality-inspection dataset and not a complete offloading workload |
| Google Cluster Data v3 | Five schemas inspected; actual trace rows not inspected | Potential cloud workload context only; not IIoT tasks |
| EUA | Site and user-location files inspected | Spatial context only; not factory task workloads |
| CICIoT2023 | Security traffic source described; data files not downloaded | Security/network context only; no task-size or execution labels |
| UNSW-IoTraffic | Some summary files inspected; full flow / PCAP data not downloaded | Potential network context after access and field validation, not compute-task workload |
| Bot-IoT | Security testbed traffic and derived flows described; data files not inspected | Security context only |
| UNSW-NB15 | Source page / index inspected; data rows not inspected; not established as IIoT | Exclude from primary IIoT workload construction |

**Decision:** the primary industrial task stream remains synthetic and explicitly labelled. ToN-IoT may be used as contextual evidence only after Mostafa confirms actual data access and field-level suitability. UCI MEC may be retained as an execution-time reference only; its turnaround time must not be added to separately estimated network or processing components if that would double-count time.

No dataset licence is inferred from a paper's open-access licence. Mostafa must record the data-source licence and redistribution conditions for the actual files.

## 4. Industrial task model recommended to the team

The initial six profile patterns below give Abdo and Mostafa explicit target semantics without inventing numerical task values:

| Profile ID | Description | Divisibility |
|---|---|---|
| PM_WINDOW_INFERENCE | One machine vibration / temperature window | Indivisible |
| PM_INDEPENDENT_WINDOW_BATCH | Independent windows from multiple machines or non-overlapping intervals | Divisible only with a declared merge rule |
| VISUAL_PRODUCT_INFERENCE | One product image inspection | Indivisible |
| VISUAL_IMAGE_BATCH | Homogeneous batch of independent product images | Divisible with a declared image-batch partition rule |
| PRODUCTION_EVENT_INFERENCE | One machine-state or production event inference | Indivisible |
| PRODUCTION_WINDOW_AGGREGATION | Independent machine/window state shards | Divisible only with a declared aggregation rule |

The generator should retain the existing canonical units: MI, bytes, milliseconds, MIPS where measured, and explicit nulls for unknown physical quantities. Application profile and machine/cell identity should first be metadata for stratification, not new Q-table state dimensions. This avoids expanding an already sparse state space before evidence supports it.

Single images and single dependent temporal windows must not be split merely because their MI and byte counts can be divided arithmetically. Independent batches are the first defensible partial-offloading candidates.

## 5. Policy / Risk / Recovery review

### 5.1 Policy

Keep the existing nine actions and legal-action mask for the initial industrial adaptation. The agent is a masked tabular/contextual learner; do not call it DQN or deep RL. The Edge tier may contain multiple physical nodes only after topology verification. If the model still emits one EDGE action, node selection must be an explicit deterministic mapping and the actual node must be logged.

The application profile stays in task metadata initially. Stratify metrics by predictive maintenance, visual inspection, production monitoring, divisibility, remote tier, and split ratio. Consider a semantic state feature only after a coverage study using development data.

### 5.2 Risk calibration

Reuse the exact-action → action-family → pooled residual calibration. Before industrial evaluation:

- confirm the execution-time estimator uses the same profile-specific split / merge rules as Java;
- verify queue-wait snapshots are pre-decision and meaningful;
- resolve bandwidth unit and downlink latency semantics;
- report calibration sample count and whether the chosen margin is actually calibrated or using the uncalibrated prior;
- keep the sidecar frozen for the primary test;
- test online recalibration as a separate arm, if included, with update times and residual provenance logged.

A zero queue estimate is not a measurement. The calibrated filter is an empirical feasibility screen, not a deadline guarantee.

### 5.3 A→B→A recovery

Keep A2 as an exact replay of A1's task and exogenous profile. Fix the per-profile deadline mapping across phases. Run network-only and workload-only pilots separately before combined stress. Add Edge-capacity-only recovery as its own factor if the simulator exposes capacity and queue semantics correctly.

The prior 20-seed generic run remains valuable as evidence that the runner / analyzer operate across five policies. It is not the final industrial benchmark: B had a 20 s deadline while A used 15 s, and that batch predates the controlled industrial workload profiles. Seed 121 also falls outside the current proposed 81–120 test band. Do not reuse the old batch as the untouched final IIoT test.

## 6. Current engineering blockers

| Blocker | Why it matters | Owner / evidence required |
|---|---|---|
| IIoT scope approval | Transition is conditional in the team message | Mark: obtain supervisor / TA approval |
| Industrial task numeric profiles | Existing MI, bytes, deadlines, and arrival values are generic synthetic assumptions | Abdo + Mostafa: source / rationale / validation status for each field |
| Dataset suitability / licenses | Existing sources are not complete factory offloading traces | Mostafa: source and license matrix, field-level use decision |
| Target topology | Current code has 1 Local / 1 Edge / 1 Cloud, not the 4-source / 2-Edge / 1-Cloud target | Ayoub: device IDs, capacities, routes, deterministic Edge-node mapping |
| Bandwidth / downlink semantics | Raw topology bandwidth unit is unresolved; downlink latency unspecified | Ayoub: confirm simulator unit conversion and directional link values |
| Queue and utilization snapshots | Risk predictions rely on pre-decision system context | Ayoub: timestamped, source-grounded measurements / explicit estimate basis |
| Partial execution realism | Current code has branch barrier and merge Cloudlet, but industrial partition models still need validation | Ayoub + Abdo + Mostafa: profile-to-Java event mapping |
| Sparse learner / fallback | Existing state table has 13,122 states; prior 20-seed evaluations contain many fallback decisions | Mark: coverage audit, train/validation design, fallback reporting |
| Seed allocation | Pilot 101 and previous 102–121 batch conflict with clean untouched test allocation | Mark + Abdo: inventory prior seed use and reserve new test seeds |
| Raw evidence package | Full per-policy traces and final training artifacts are not all in the compact GitHub result bundle | Ayoub / Mark: archive raw traces, model, sidecar, and training provenance |

## 7. Experimental gates

**Gate 0 — approval:** supervisor / TA approves the IIoT / Smart Manufacturing domain and bounded application scope.

**Gate 1 — task and dataset contract:** Mostafa provides source / license / suitability decisions. Abdo supplies industrial profiles, schemas, deterministic task generation, and manifest metadata. Mark approves task semantics and the candidate contribution wording. No numerical value is promoted from PROPOSED to APPROVED without evidence.

**Gate 2 — simulator contract:** Ayoub confirms the chosen small topology, tier mappings, bandwidth units, link delays, queue / utilization snapshots, task completion endpoint, branch barrier, merge semantics, failure handling, and exact task accounting.

**Gate 3 — small pilot:** at least five development seeds per isolated regime. Validate task identity, deadlines, shared inputs across arms, A1/A2 replay, factor isolation, action legality, all-task outcome denominator, and raw trace completeness. Do not infer superiority from this pilot.

**Gate 4 — final evaluation:** freeze model, calibration sidecar, source revision, topology, parameters, application profiles, policy arms, seed allocation, and recovery definition. Run at least twenty paired seeds per principal scenario, preferably thirty.

**Gate 5 — paper integration:** Omar updates the paper only after the approved scope, validated methodology, and final results are available. Mark reviews all quantitative and novelty claims.

## 8. Mark's completed first-stage deliverables

This branch adds the following three documents:

1. **MARK_RESEARCH_SPECIFICATION_IIOT_DRAFT_V1.md** — proposed research definition, industrial scope, task semantics, candidate gap, policy/risk boundary, scenarios, metrics, and approval gates.
2. **deliverables/02_Methodology/METHODOLOGY_IIOT_DRAFT_V1.md** — end-to-end methodology for industrial tasks, topology, risk calibration, controlled shifts, metrics, and test integrity.
3. **docs/IIOT_RESEARCH_LEAD_INTEGRATION_REPORT.md** — repository reuse decisions, dataset suitability boundaries, integration blockers, ownership dependencies, and acceptance gates.

The original generic Specification V2, prior results, simulator code, model code, and team-owned workload package have not been overwritten by this draft.

## 9. Immediate next step

Mark should present the proposed title, three industrial task archetypes, bounded research questions, and explicit non-claims to the supervisor / teaching assistant for scope approval. After approval, merge the validated inputs from Mostafa, Abdo, and Ayoub into the industrial profile and methodology; do not start final seed runs before Gate 3 passes.
