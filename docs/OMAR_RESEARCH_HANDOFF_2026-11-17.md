# Omar Handoff — Research Scope, Gap, and Methodology Inputs

**Date:** 2026-11-17  
**Prepared by:** Mark — Research Lead  
**Status:** Handoff for manuscript drafting; not final scope/methodology approval.

## 1. Canonical files

Use these exact repository files as the handoff set:

1. [References Index](../research/references/REFERENCES_INDEX.md) — bibliography classification and retained-file status.
2. [Research Gap v29 workbook](../research/literature_review/research_gaps/Research_Gap_Excel_v29.xlsx) — 21-record targeted overlap matrix, explicitly not systematic.
3. [Research Gap v29 report](../research/literature_review/research_gaps/Research_Gap_Report_v29.docx) — companion narrative report. It was not independently re-opened during this handoff pass; the workbook sheet was directly inspected.
4. [Generic Research Specification V2](../MARK_RESEARCH_SPECIFICATION_V2.md) — original working research definition.
5. [IIoT Research Specification Draft V1](../MARK_RESEARCH_SPECIFICATION_IIOT_DRAFT_V1.md) — proposed Smart Manufacturing adaptation, still conditional on supervisor approval.
6. [IIoT Methodology Draft V1](../deliverables/02_Methodology/METHODOLOGY_IIOT_DRAFT_V1.md) — methodology candidate.
7. [Research Positioning and TMC-7 Audit](RESEARCH_POSITIONING_AND_TMC7_AUDIT_V1.md) — exact overlap audit and revised research framing.
8. [Research Lead Closeout Pack](IIOT_RESEARCH_LEAD_CLOSEOUT_V1.md) — ownership, acceptance rules, and freeze gates.

The IIoT branch and proposed changes are in PR #4: https://github.com/Mark1amgad/adaptive-iot-task-offloading/pull/4. It remains a Draft PR and has not been merged.

## 2. Do not mix the two literature artifacts

The References Index classifies repository sources by evidence role/type:
- 6 verified Core Journal full texts;
- 2 agreed Core journal records pending an authorized local full text;
- 2 Supporting sources;
- 5 Conference papers;
- 1 Unverified / incomplete source.

The Research Gap v29 workbook is a distinct **21-record targeted, non-systematic overlap matrix**. It includes journal, conference, supporting, supplementary, and selected prior-art records with different evidence grades. It is not “21 Core papers.” Use the Index to build the bibliography and the matrix to audit novelty overlap. Do not combine their counts.

## 3. IEEE TMC paper 7 — audit and full-text status

**Citation:** Bin Xu, Honggen Bian, Qiulan Cui, Xiaohui Yu, Jin Qi, and Yimu Ji, “Distributed Optimization of Task Offloading and Resource Allocation for Mobile Edge Computing With Multifactorial Uncertainty,” *IEEE Transactions on Mobile Computing*, 25(2), 1644–1659, 2026. DOI: 10.1109/TMC.2025.3603064.

- Official IEEE record: https://ieeexplore.ieee.org/document/11142343/
- DOI: https://doi.org/10.1109/TMC.2025.3603064

IEEE confirms the bibliographic metadata and abstract. The paper's technical content was reviewed from an accessible accepted-author-version repost that states it has not been fully edited and displays “All Rights Reserved.” This repost is not an authorized repository copy. The paper's official/authorized full text is therefore still pending for our local archive. **Do not cite the third-party repost as the paper's official copy or distribute it.** Obtain the accepted/final manuscript through university IEEE access or request it from the authors.

### Technical points relevant to our research

TMC paper 7:
- models multiple devices and multiple MEC servers;
- includes local computing, MEC-server computing, cooperative-device computing, and task dropping;
- models uncertainty in device energy, wireless channel/interference, MEC-server load, task sizes and task counts;
- jointly optimizes offloading and computing-resource allocation to minimize device energy under maximum task-latency, energy, and resource constraints;
- proposes TOPRFM, which evaluates feasible allocation modes and prioritizes tasks with fewer feasible modes;
- uses TODC for task decision construction;
- proposes DGOLB, combining static game-theoretic coordination with MEC-server load balancing/task migration;
- compares against BiJOR, DTSO, DAEE, MESON, and EPD;
- reports energy, dropped-task ratio, response time, and convergence under parameter sweeps; simulations are MATLAB R2021a and averaged across 30 runs.

This rules out broad claims that deadline feasibility, uncertainty-aware offloading, task prioritization from feasible options, or load balancing are new. The architecture and algorithms differ from our Local–Edge–Cloud iFogSim2 pipeline, but that difference alone does not prove novelty.

## 4. Other mandatory prior-art overlaps from Research Gap v29

The manuscript must explicitly distinguish:
- **LITO (2026):** Edge–Fog–Cloud, contextual-bandit feedback, heterogeneous deadlines, explicit feasibility filter/fallback, queue/resource feasibility, and failure/fallback tests.
- **E2DA (2023):** contextual neural multi-armed bandit for deadline-aware MEC offloading under partial observations.
- **O2C/CCMAB (IEEE ICC 2026):** chance-constrained multi-tenant assignment with target delay-success probability.
- **H-DQAC (2025):** hybrid DQL/Actor-Critic, local/fog/cloud, iFogSim2, deadline-miss reward.
- **Hierarchical partial offloading (IEEE TCE 2026):** DDQN + PPO for Device–Edge–Cloud splitting.
- **ESFMTO (2025):** failure-aware task offloading in IIoT.
- **Forecast-driven LinUCB / RELTO:** adaptive/contextual and reliability-aware offloading.

The exact evidence grade and limitations for each row are in the v29 sheet. Abstract-only records must not be described as if their equations or full tables were audited.

## 5. Recommended research framing

### Working title recommendation

**An Empirical Evaluation of Residual-Calibrated Full and Partial Task Offloading for Smart-Manufacturing IIoT under Workload and Network Shifts**

This is a recommendation, not an approved final title. It avoids presenting an unproven algorithmic novelty claim.

### Proposed problem formulation

Smart-manufacturing endpoints generate heterogeneous computational tasks with task-specific compute demands, input/output payloads, deadlines, and application semantics. The controller must select a legal Local, Edge, or Cloud execution option. For a task explicitly declared data-parallel and independently mergeable, the action set may additionally include partial execution between Local and exactly one remote tier. Execution-time predictions can be biased by changing workloads, network conditions, and resource contention. The study therefore evaluates whether a residual-calibrated completion-time feasibility margin changes the deadline/latency trade-off relative to an analytical feasibility screen and the same frozen contextual placement policy.

This is not a new visual-inspection or predictive-maintenance model. The three industrial applications are task archetypes that supply workload semantics to the existing offloading problem.

### Proposed primary research question

> Within declared synthetic smart-manufacturing task profiles executed in iFogSim2, what incremental effect does per-action residual calibration add beyond an analytical completion-time feasibility screen and the same frozen contextual placement policy, for legal full and constrained Local-plus-one-remote partial execution, in terms of all-task deadline-miss rate, completed-task latency, calibration errors, and recovery behavior under isolated workload/network/capacity shifts?

This is an empirical comparison question, not a claim that bandits, feasibility filters, risk calibration, partial execution, or A1→B→A testing are individually new.

## 6. Methodology conditions that must not be omitted

1. **Matched policy arms:** the current runner compares unfiltered Local/Edge/Cloud/Random arms against the learner with the risk filter. This does not isolate the filter contribution. To make a calibration-specific claim, evaluate the same frozen contextual model with (a) no filter, (b) analytical-only feasibility / zero residual margin, and (c) residual-calibrated feasibility on identical traces.
2. **Training-only calibration:** no final-test residual may update the calibrator. Report sample count, exact-action/family/pooled source, uncalibrated decisions, false-safe behavior, and fallback frequency.
3. **Honest model naming:** the current V2 update is one-step and has no next-state bootstrap; describe it as a masked tabular contextual-bandit-style action-value policy, not DQN or sequential deep RL.
4. **No fabricated observability:** current queue-wait inputs are zero estimates, not measured queue waits. The paper must call them assumptions until simulator telemetry confirms otherwise.
5. **Task divisibility:** one product image, one dependent vibration window, and one production event are indivisible by default. Only independent batches with explicit partition/merge semantics may use partial actions.
6. **Recovery wording:** frozen A1→B→A2 evaluation shows return to prior behavior when the regime returns; it does not prove online learning/adaptation. Any online update is a separate arm.
7. **Deadline rule:** for primary controlled shifts, per-profile deadline mapping is frozen and unchanged across A1, B, and A2.
8. **Seeds:** old nominal test band 81–120 is contaminated by pilot seed 101 and prior batch 102–121. Reserve a new untouched test allocation using a versioned seed registry; a manifest's literal `evaluation_split=test` is not enough.
9. **Synthetic benchmark:** use synthetic IIoT task inputs plus iFogSim2 outcomes. Do not describe the current benchmark as measured factory data.
10. **Scope approval:** IIoT / Smart Manufacturing transition remains draft until supervisor/TA approval.

## 7. What can be drafted now vs. what must remain open

| Manuscript content | Status |
|---|---|
| Introduction structure and industrial motivation | Can draft as proposed scope, clearly marked pending approval |
| Related Work using References Index and v29 matrix | Can draft with exact evidence grades and narrow distinctions |
| TMC-7 discussion | Can draft using metadata and provisional technical audit; replace/verify against authorized final text before submission |
| Problem formulation | Candidate wording is ready; freeze only after supervisor decision |
| Method equations | Existing implementation can be described accurately; calibration-specific novelty awaits LITO/E2DA/O2C comparison |
| Experimental Methodology | Candidate protocol ready; final freeze waits for Ayoub, Abdo, Mostafa, supervisor, and ablation/seed-registry gates |
| Results and claims | Must wait for industrial final test runs and frozen raw evidence |
| Conclusion | Must wait for validated results; no generalization/novelty claim in advance |

## 8. Mark's decision / handoff

Mark recommends that the team first agree whether the expected outcome is:
- a **rigorous empirical comparative study** using the existing V2 method, with a narrow calibrated-feasibility ablation; or
- a **new algorithmic contribution**, which would require a materially different method and a new implementation/audit, not just a different application label.

Given the actual V2 learner, sparse training coverage, current filter/baseline asymmetry, and close prior art, the empirical comparative direction is the more defensible path unless the supervisor specifically asks for a new algorithm and approves the additional development scope.

Do not freeze methodology or describe the novelty as established until the supervisor has made that contribution-level decision and the mandatory comparisons/ablations are addressed.
