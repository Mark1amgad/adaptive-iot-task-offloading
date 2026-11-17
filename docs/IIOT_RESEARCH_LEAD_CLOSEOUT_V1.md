# Research Lead Closeout Pack — IIoT Smart Manufacturing V1

**Owner:** Mark — Research Lead & Integration  
**Review date:** 2026-11-17  
**Status:** Research-lead preparation complete; experiment and manuscript freeze remain blocked by supervisor approval and team-owned technical inputs.  
**Applies to:** `mark/iiot-scope-transition-v1`  
**This is a control document, not an approval to change the final research scope or to start the final test batch.**

## 1. Purpose and closeout boundary

This document closes the work that can responsibly be completed by the Research Lead before the remaining team members deliver their assigned artifacts. It converts the industrial scope draft into an auditable decision framework for final integration and manuscript writing.

Mark's role is not to invent the industrial workload values, claim dataset suitability, or certify simulator behavior owned by other members. Mark owns the research definition, policy/risk interpretation, evidence integrity, experiment design, claim boundaries, and final consistency review.

The following Mark-owned preparation artifacts now exist on this branch:

1. `MARK_RESEARCH_SPECIFICATION_IIOT_DRAFT_V1.md`
2. `deliverables/02_Methodology/METHODOLOGY_IIOT_DRAFT_V1.md`
3. `docs/IIOT_RESEARCH_LEAD_INTEGRATION_REPORT.md`
4. This closeout pack.

The documents are additive. The generic specification, historical results, existing simulator, model package, and other team members' work are not overwritten.

## 2. Research definition to take to approval

### Proposed working title

**Risk-Calibrated Contextual Full and Partial Task Offloading for Industrial IoT in Smart Manufacturing under Workload and Network Shifts**

"Contextual" is more precise than an unqualified "RL" label for the current implementation. The title remains provisional until the supervisor approves the IIoT transition.

### Bounded application scope

The evaluation domain is one smart-manufacturing cell / small factory setting with three task archetypes:

- Predictive maintenance: inference over one machine's vibration/temperature window; a single dependent window is indivisible.
- Visual quality inspection: inference over one product image; a homogeneous batch of independent images may be divisible.
- Production monitoring: one machine event/state inference is indivisible; independent machine/window records may be aggregated only with a declared merge rule.

The research problem remains execution placement among Local, Edge, and Cloud, including legal Local-plus-one-remote partial execution. The study is not a new defect detector, predictive-maintenance classifier, PLC control system, or factory digital twin.

### Research questions

- **RQ1 — Risk-filter value:** Does residual-calibrated feasibility filtering improve the deadline/latency trade-off over the same contextual policy without filtering and with an analytical-only feasibility screen?
- **RQ2 — Partial execution:** When do legal partial actions help or harm relative to full-only placement for the three industrial archetypes?
- **RQ3 — Shift behavior:** What happens under isolated network, workload, and Edge-capacity shifts, and how much deadline-miss burden occurs before A→B→A recovery?
- **RQ4 — Application dependence:** Do outcomes differ by application archetype and divisibility class after controlling for task demand, payload, deadline, and operating conditions?

No novelty claim is approved by this draft. The contribution is an empirical/methodological candidate: controlled evaluation of calibrated end-to-end completion-time feasibility across legal full and partial actions, with industrial task semantics and separated shift experiments.

## 3. Verified implementation truth — do not write beyond this

The following points were checked against the repository source and experiment scripts, not inferred from the project title.

| Area | Verified current behavior | Consequence for claims |
|---|---|---|
| Learner update | The V2 agent applies a one-step update of the form (Q(s,a) \leftarrow Q(s,a)+\alpha(r-Q(s,a))). It does not bootstrap from a next state or use a Bellman target. | Describe it as a masked tabular contextual-bandit-style action-value learner. Do not call it DQN, deep RL, or conventional bootstrapped Q-learning. |
| Evaluation mode | The V2 server freezes the agent in evaluation. For a state with no previously visited legal action, it uses the configured fallback order. | Frozen A→B→A recovery is context-conditioned return to earlier behavior, not online learning or retraining. |
| State/action size | The current configuration has 13,122 discrete states and nine actions: 118,098 state-action cells. | Report state/action visitation and fallback, not only aggregate policy metrics. |
| Prior training coverage | The seed-42 / 60-task artifact reports 45 visited states (0.343%), 60 updated state-action cells (0.0508%), and 108 fallback decisions among 180 held-out decisions (60%). | That result is a fallback/greedy hybrid; it is not evidence of a broadly trained policy. |
| Separate 20-seed batch | A different 20-seed combined A→B→A batch reports 765 fallbacks among 1,800 RL decisions (42.5%). | Do not combine this rate with the seed-42 artifact. They are different model/run batches. Every coverage statistic must be tied to its model SHA, run ID, and workload set. |
| Baseline fairness | `run_v2_policy_comparison.ps1` runs Local, Edge, Cloud, and Random without `--risk-filter`; only `policy_rl_eval` receives `--risk-filter` and the risk sidecar. | The existing five-arm comparison is a comparison of a **combined contextual learner + risk-filter bundle** against unfiltered reference arms. It does not isolate the learner effect from the filter effect. |
| Risk calibration | The calibrator uses completed training outcomes, action → family → pooled backoff, and an empirical one-sided residual quantile. Evaluation is frozen. | This is an empirical feasibility margin, not a hard deadline guarantee. Report sample counts, calibration source, and false-safe/false-reject behavior. |
| Queue input | The current Java adapter supplies zero for Local, Edge, Cloud, and merge queue wait, with an explicit zero-predecision-estimate label. | Do not call queueing measured. Residuals may capture some subsequent bias but do not turn a zero queue snapshot into an observed queue measurement. |
| Link units | The V2 risk parser expects `bandwidth_bytes_per_second`; the current Java adapter sends that field. | Reports and manifests must use bytes/s for this input, not an undocumented Mbps number. |
| Topology | The current V2 experiment creates one Local, one Edge, and one Cloud executor, with Local→Edge→Cloud hierarchy. | Do not describe a multi-Edge factory topology as implemented until Ayoub supplies source and trace evidence. |
| State observability | The nine V2 state features do not include partition overhead, merge overhead, or merge MI. These arrive as task constraints/risk context. | The learner cannot distinguish otherwise identical encoded states solely by different split/merge costs. This is a known limitation; test sensitivity and only expand the state after a coverage study. |
| Partial execution | The current simulator has explicit Local and one remote branch, branch completion barrier, and Local merge Cloudlet for supported divisible tasks. | Industrial divisibility and proportional byte-splitting remain application assumptions until each profile is mapped and reconciled. |
| Seed declaration | The experiment manifest builder currently writes `evaluation_split: test` as a constant. It does not consult a versioned approved seed registry. The inference analyzer checks the label, not whether a seed belongs to an authorized held-out allocation. | A manifest label alone is not proof of clean train/validation/test separation. Add a seed-registry gate before final inference. |
| Statistical unit | The paired inference script correctly treats a workload seed / paired simulation run as the independent unit. | Do not use task counts as independent sample size for between-run inference. |

### Consequential interpretation

The current implementation should be positioned as a **contextual placement policy with a risk-calibrated feasibility layer**, not as a demonstrated deep-RL agent that learned a general factory policy. This is not a cosmetic wording issue: the one-step update and frozen fallback behavior determine what the experiments can support.

## 4. Policy comparison protocol to freeze

The current five-arm comparison remains useful as a reference benchmark:

- Local full placement
- Edge full placement
- Cloud full placement
- Random over each task's legal action mask
- Frozen contextual learner plus residual-calibrated filter

However, it cannot answer whether improvement comes from the contextual learner, the analytical estimator, or residual calibration. The following paired ablation sequence is required before making a filter-specific claim.

| Arm | Policy | Feasibility layer | Why it is needed |
|---|---|---|---|
| P0 | Local / Edge / Cloud / Random reference policies | No risk filter | Retain existing reference baseline family |
| P1 | Same frozen contextual model | No risk filter | Isolate the learned/contextual action selection |
| P2 | Same frozen contextual model | Analytical predicted completion only; zero residual margin | Isolate the effect of deadline feasibility screening |
| P3 | Same frozen contextual model | Residual-calibrated feasibility filter | Measure incremental value of calibration beyond analytical screening |
| P4 | Deterministic minimum-predicted-completion heuristic over the same legal action set | No learned action values | Add a stronger state-aware, non-learning comparator |
| P5 | Full-only versus full-plus-partial action set | Same declared training/evaluation protocol | Isolate the value of partial execution |

P1–P3 should use the same frozen learner artifact and identical task/network/capacity traces for the direct test-time filter ablation. The calibrator must be built from training-only outcomes and frozen before held-out testing. If training itself uses a risk screen, disclose that design and do not present test-time P1–P3 as a clean ablation without a matched retraining protocol.

P4 is a proposed new comparator, not currently implemented. Its deterministic tie-break order and handling of infeasible predictions must be written and tested before use. It must not receive future information or post-decision measurements.

Online learner updates and online recalibration are optional secondary arms. They require a separate, explicitly defined online protocol, update timestamps, and a distinct interpretation. They must not be smuggled into the frozen evaluation or described as existing capability.

## 5. Scenario and recovery freeze

### Required progression

1. Stable industrial baseline.
2. Network-only shifts — vary WAN latency **or** bandwidth in a run, not both.
3. Workload-only shifts — vary one named factor per run (compute demand, payload, arrival rate, or application mix).
4. Edge-capacity-only shifts — only after capacity changes and utilization are traced correctly.
5. Combined workload/network stress after the isolated experiments pass.

For every A→B→A experiment:

- A2 must replay A1's task template and relevant exogenous inputs.
- The per-profile deadline mapping must remain identical in A1, B, and A2 for the primary controlled experiment.
- The primary IIoT test must not reproduce the old generic run's 15 s A / 20 s B deadline change.
- Task IDs, sequence IDs, generated task count, and all-task denominator must reconcile across policy arms.
- Keep network-only, workload-only, and capacity-only results separate; a combined run cannot identify which factor caused the change.

### Recovery definition

Retain the existing ten-task sliding-window rule as the starting operational definition: a window qualifies when all ten tasks complete, its deadline-miss rate is no more than five percentage points above the same policy's A1 baseline, and its median latency is no more than 10% above its A1 median. Recovery time is measured from the A2 transition to the completion of the last task in the first qualifying window.

These tolerances are operational choices, not physical constants. Use development/validation data to perform sensitivity checks (at least alternative window sizes and stricter/looser miss/latency tolerances), then freeze one rule before the final test. Report recovery rate and non-recovered seeds separately; do not assign zero recovery time to a non-recovered run. Recovery-time comparisons conditioned on both policies recovering must be labelled conditional.

## 6. Training, validation, and untouched test governance

The previously proposed split Train 1–60, Validation 61–80, Test 81–120 cannot be used as a clean final split without reconciliation. Seed 101 was used as a pilot and lies inside the nominal test range; the earlier generic batch used seeds 102–121, overlapping the same range for 102–120. Seed 121 is outside that proposed range and must not be reassigned post hoc as a clean test seed.

**Decision:** retire the old nominal test band for the final IIoT claim. First inventory every workload seed, training seed, model artifact, risk sidecar, and run manifest. Then reserve a new untouched IIoT test allocation from seeds not used in any pilot, training, validation, debugging, or exploratory run. Record the chosen explicit seed lists in a versioned registry before the first final test run.

Required rules:

- Training seeds may update the learner and calibration state.
- Validation seeds may choose configuration, calibration settings, thresholds, and the recovery definition.
- Test seeds may only be used after all model/policy/calibration settings are frozen.
- No test outcome may update the model, Q values, calibrator, reward weights, thresholds, task distributions, or topology.
- Every principal scenario should target at least 20 paired test seeds; 30 is preferred when runtime permits.
- The seed registry, not a free-text manifest label, is the authority for split membership.
- The analysis script must reject any test seed not present in the approved test list and reject duplicates or cross-split overlap.

## 7. Outcome and statistics contract

### Primary outcomes

1. Deadline-miss rate over **all generated tasks**: late + failed + unresolved-at-horizon / all generated tasks.
2. Completion coverage and explicit on-time, late, failed, and unresolved counts.
3. End-to-end latency distribution among completed tasks, always accompanied by completion coverage.
4. Recovery rate, recovery-time distribution, and cumulative miss burden during B and after the A2 transition.

### Secondary outcomes

- Task-attributed transmitted bytes with explicit link directions/counting.
- Backlog/queue and throughput, only where measurement hooks support them.
- Action proportions, fallback rate, greedy/known-state rate, state and state-action coverage.
- Calibration sample counts, calibration source, margin, residual distributions by action/application/phase.
- False-safe rate (the filter allowed an action but the task missed its deadline) and false-reject rate (a filtered action would have met the deadline, assessed from valid counterfactual/paired evidence).
- Decision latency and model/calibrator overhead.
- Energy is excluded from claims until the simulator's power model and per-task attribution are validated.

### Statistical reporting

The independent unit is the workload seed / paired simulation run. Report per-seed results, paired differences, effect sizes, and 95% paired-seed bootstrap confidence intervals. Use paired non-parametric tests where appropriate and Holm correction across a predeclared comparison family. Distinguish statistical significance from practical effect size. If fewer than 20 test seeds are available, label results as pilot/limited evidence rather than complete the final protocol by simply treating tasks as independent samples.

## 8. Run-manifest and evidence requirements

The existing manifest records workload/model/risk/source hashes and simulator JAR inventory, but the split label is currently hardcoded rather than checked against a seed registry. Before final test:

- Add a versioned seed registry with explicit train, validation, and test seed lists.
- Add a manifest field for registry version/hash and the assigned split.
- Validate the workload's seed against that registry before launch and again in inference.
- Record workload-profile version, topology/config version, per-profile deadlines, task generator version, policy-arm version, model hash, risk-sidecar hash, reward/config hash, source commit, source inventory, simulator JAR hashes, Java version, and all scenario parameters.
- Retain raw task, decision, outcome, acknowledgement, and calibration traces for each policy/run.
- Verify that all policies used identical workload and exogenous profiles for each paired seed.
- Preserve an immutable copy of all final manifests and results before manuscript tables/figures are generated.

A run labelled `test` without verified seed-registry membership is not an eligible final test result.

## 9. Team handoff acceptance contract

| Owner | Required handoff | Mark's acceptance check |
|---|---|---|
| Supervisor / TA | Explicit approval or rejection of IIoT / Smart Manufacturing domain and bounded scope | Record decision, date, exact approved wording, and any scope restrictions |
| Ayoub — simulator/topology | Actual device IDs/counts, parent links, MIPS, directional bandwidth units, uplink/downlink delays, utilization timestamps, queue measurement/estimate basis, multi-Edge mapping if used, task lifecycle, branch barrier, merge, failure and watchdog reconciliation | Match the topology to source/trace evidence; no unimplemented target topology in the paper |
| Abdo — workload generator | Versioned industrial profile IDs, schema, deterministic seed/replay, MI/byte/deadline/arrival units and distributions, divisibility, partition/merge definitions, task IDs and manifests | Check application semantics, fixed deadlines across A/B/A, deterministic replay, and exact correspondence between workload values and Java execution |
| Mostafa — datasets/source mapping | Dataset title/version/source, license, downloaded files, exact columns and units, data dictionary, suitability decision, permitted/prohibited use | Ensure no network/security/host dataset is misrepresented as a measured factory task-offloading trace |
| Omar — manuscript | Draft built from approved scope, validated methodology, frozen result set, existing reference index | Audit every quantitative statement, table, figure, novelty claim, and limitation against trace/manifests |
| Mark — research lead/integration | Final RQs, protocol freeze, policy/risk interpretation, seed governance, evidence audit, claim review, cross-document consistency | Sign off only when every gate below is met |

### Acceptance rule for task profiles

Each profile must state: application ID; unit of work; whether it is indivisible or divisible; compute MI; input/output bytes; deadline and urgency mapping; arrival process; source/cell identity; partition-model ID; partition and merge overhead; merge MI; split ratio semantics; value provenance; and whether each numeric value is measured, dataset-derived, literature-derived, or synthetic assumption.

A divisible label is not accepted until the application-level split and merge semantics are valid. Numeric fields cannot be labelled measured unless the source and measurement procedure are provided.

## 10. Manuscript integration map

Omar can prepare section structure before final results, but should not write result claims until the run set is frozen.

1. **Introduction:** smart-manufacturing task placement problem; why deadline reliability changes under workload/network conditions; bounded contribution.
2. **Related work:** use only the current repository References Index; compare against IIoT failure-aware offloading, Edge-IIoT DQN, reliability-oriented adaptive offloading, forecast-aware contextual offloading, uncertainty-aware feasibility, and hierarchical partial offloading. Novelty remains a candidate gap until exact method-level comparison.
3. **System and workload model:** three tiers, task archetypes, workload assumptions, topology and measurement contract.
4. **Method:** contextual action-value learner, legal action mask, end-to-end prediction, residual calibration, full/partial split and merge.
5. **Experimental design:** topology, policy arms, isolated shifts, A→B→A, seed registry, manifests, metrics, recovery definition.
6. **Results:** policy outcomes, filter ablations, partial/full comparison, per-profile analysis, calibration/fallback/coverage, shift and recovery analysis.
7. **Threats to validity:** synthetic workload, simulator abstraction, zero/estimated queue context, proportional partition assumptions, limited state coverage, topology scale, calibration selection bias, and no energy measurement.
8. **Conclusion:** claims limited to the evaluated simulator, profile ranges, policy version, and seed/test population.

Do not claim measured factory generalization, algorithmic RL novelty, deterministic deadline guarantees, energy savings, or online learning unless a separate validated experiment establishes it.

## 11. Final freeze gates

The final IIoT test batch is authorized only after all of these are true:

- [ ] Supervisor / TA approves the IIoT scope.
- [ ] Existing references are enough for the related-work positioning; no unsupported novelty statement remains.
- [ ] Abdo and Mostafa submit accepted industrial profile definitions and data provenance decisions.
- [ ] Ayoub verifies the implemented topology and every measurement field used by the estimator.
- [ ] The risk-calibration documentation matches the implementation and the chosen policy-arm design.
- [ ] A strong deterministic heuristic and the core filter ablations are implemented and pass tests, or their omission is explicitly approved and reflected in narrower claims.
- [ ] A fresh test-seed allocation is reserved and enforced by a versioned registry.
- [ ] The small industrial pilot passes deterministic replay, task conservation, action legality, outcome reconciliation, fixed-deadline, A1/A2 replay, and trace completeness checks.
- [ ] Model, calibrator, reward, topology, generator, source, and scenario settings are frozen and hashed.
- [ ] The analysis plan, comparison family, metrics, recovery definition, and sensitivity checks are frozen before test results are inspected.

## 12. Current closeout status

**Mark-owned design and research-governance preparation: COMPLETE FOR TEAM HANDOFF.**

**Research freeze / final manuscript: NOT YET READY.** The blockers are explicit external dependencies, not unfinished Mark-owned drafting: supervisor scope approval; Abdo's industrial task profiles; Mostafa's source/license map; Ayoub's simulator/topology evidence; and the new clean test-seed registry plus required policy ablations.

The next integration action after those inputs arrive is to run the acceptance checks in Sections 9 and 11, update the controlling specification/methodology once with approved values, freeze the experiment protocol, and then hand Omar one canonical approved specification and one frozen result bundle.

---
*This document is a research-control artifact. It does not certify simulator behavior beyond the source and artifacts inspected on 2026-11-17.*
