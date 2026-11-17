# Research Positioning and IEEE TMC Paper 7 Audit — V1

**Prepared by:** Mark — Research Lead  
**Date:** 2026-11-17  
**Status:** Evidence-grounded positioning draft; not a supervisor-approved novelty claim.  
**Scope:** Existing repository references, the 21-record Research Gap v29 workbook, and the accessible author-version text of IEEE TMC paper 7. No new paper is added to the reference corpus by this audit.

## 1. Two repository artifacts that must not be mixed

There are two different classification systems in the repository.

### A. Bibliographic inventory: `research/references/REFERENCES_INDEX.md`

This is the project's source-of-record inventory. It classifies the literature assets actually retained and audited in the repository:

- **6 verified Core Journal full texts** (`CORE-01` through `CORE-06`).
- **2 agreed Core journal references pending locally archived full text**: IEEE TMC paper 7 and the time-varying-statistical-characteristics MEC paper.
- **2 Supporting sources**: an IEEE Access survey and an IEEE Internet of Things Magazine article.
- **5 Conference papers** (`CONF-01` through `CONF-05`).
- **1 unverified / incomplete review record** (`UNV-01`).

The Core/Supporting labels are evidence-role and source-type classifications. A conference paper does not become a Core Journal paper because it is relevant to the research gap.

### B. Related-work screening matrix: Research Gap v29

The workbook `Research_Results_Literature_and_Workplan_2026-10-28.xlsx`, sheet **Research Gap v29**, is titled **“Targeted research-gap matrix v29 — 21 records; not systematic.”** It is a claim-overlap and search-evidence matrix, not a replacement for the References Index and not a list of 21 Core papers.

Its 21 records are grouped by search/source families (ScienceDirect, SpringerLink, IEEE, and selected prior art). It includes different evidence grades: some publisher full texts, some publisher abstracts/metadata, some previously reviewed user-supplied PDFs, and some secondary-index-only records. The matrix itself records when full equations, tables, or official publisher records were not fully available.

**Required rule for Omar:** use the References Index to classify and cite the retained bibliography; use Research Gap v29 to assess methodological overlap and claim boundaries. Do not combine their counts or relabel Supporting/Conference/secondary records as Core journals.

The companion files are retained in the repository under `research/literature_review/research_gaps/`:
- `Research_Gap_Report_v29.docx`
- `Research_Gap_Excel_v29.xlsx`

The workbook's research-gap sheet was directly inspected for this audit. The DOCX report has not been independently re-opened in this pass; use the workbook as the directly verified v29 matrix source until the DOCX is read alongside it.

## 2. IEEE TMC paper 7 — bibliographic identity

**Title:** Distributed Optimization of Task Offloading and Resource Allocation for Mobile Edge Computing With Multifactorial Uncertainty  
**Authors:** Bin Xu, Honggen Bian, Qiulan Cui, Xiaohui Yu, Jin Qi, and Yimu Ji  
**Venue:** IEEE Transactions on Mobile Computing, Volume 25, Issue 2, February 2026, pp. 1644–1659  
**Date of publication shown by IEEE:** 26 August 2025  
**DOI:** 10.1109/TMC.2025.3603064  
**IEEE Xplore record:** https://ieeexplore.ieee.org/document/11142343/  
**DOI:** https://doi.org/10.1109/TMC.2025.3603064

IEEE's record confirms the publication metadata and abstract. The indexed author-version text located for the technical audit states that it was accepted for IEEE TMC but not yet fully edited. It was found on a third-party repost that displays “All Rights Reserved”; it is not an authorized repository or publisher download. This audit uses the accessible text to identify overlap, but **does not treat the repost as the archival full-text copy required for the project library**. Omar should obtain the final or accepted version through institutional IEEE access or from the authors and archive it under the paper's canonical filename after verifying metadata.

## 3. TMC paper 7 — technical audit

The following is a paraphrase of the inspected author-version text, not a reproduction of the paper.

### 3.1 Problem and system model

The paper constructs **MECTOS-MU**, a multi-device / multi-MEC-server system. A task is represented by:
- required CPU cycles;
- input data size;
- output-result size;
- maximum allowable latency.

The model considers multiple uncertainty sources, including:
- device energy / energy-harvesting conditions;
- wireless channel quality and interference;
- MEC-server load condition;
- task sizes and task counts.

The task-processing modes include:
1. Local computing on the originating device;
2. MEC-server computing;
3. Cooperative computing on another device with available resources;
4. Task dropping when the latency or energy conditions cannot be met.

This is not the same architecture as a Local–Edge–Cloud continuum with a distinct Cloud execution tier. The inspected model is focused on devices, base stations, and multiple MEC servers.

### 3.2 Objective and constraints

The paper jointly optimizes task offloading decisions and computing-resource allocation. Its stated system objective is to minimize total energy consumed by devices while respecting maximum task-latency constraints, device energy constraints, and computing-resource constraints. The authors formulate the joint problem as an NP-hard optimization problem.

This is important prior art: deadline/latency feasibility and uncertainty-aware resource/offloading decisions are already explicit in a recent IEEE TMC study. A generic claim that the project is the first to screen offloading choices against deadlines under uncertain load would be indefensible.

### 3.3 Proposed method: DGOLB

The proposed **Distributed Game Offloading based on Load Balancing (DGOLB)** has two main stages:

- **TOPRFM — Task Offloading Priority Ranking Based on Feasible Modes.** For each task, it evaluates feasible allocation modes using resource and latency conditions. The number of remaining feasible modes is used to rank task priority: tasks with fewer feasible modes are prioritized.
- **TODC — Task Offloading Decision Construction.** Devices iteratively choose feasible processing modes and resource assignments using the task-priority ordering.
- **Distributed game and load balancing.** The method models competition among devices for limited MEC resources as a static game, then uses MEC-server load levels and task migration to move work from overloaded servers to less-loaded compatible servers until allocation stabilizes at a Nash equilibrium.

Therefore, feasibility filtering, prioritization by remaining feasible choices, distributed offloading, and load balancing under uncertain device/network/server conditions are not new at a broad level.

### 3.4 Baselines and evaluation

The inspected manuscript names five baselines:

| Baseline | Method family identified in the paper |
|---|---|
| BiJOR | Centralized ant-colony-system and monotonic-optimization method |
| DTSO | Distributed two-stage offloading using queueing theory and sequential quadratic programming |
| DAEE | Online perturbed Lyapunov optimization with delay-aware offloading |
| MESON | Deep deterministic policy-gradient / neural-network approach |
| EPD | Periodic scheduling with probabilistic deadline guarantees |

The manuscript reports MATLAB R2021a simulations with a custom wireless-channel model. The stated default environment includes 10 MEC servers, 50 GHz MEC-server capacity, 100 devices, device compute capacity sampled in [0.6, 1] GHz, task compute demand in [100, 1000] Megacycles, input data in [60, 120] KB, output data in [0.1, 10] KB, and maximum latency of 1 s. Results are averaged over 30 runs. The paper studies device count, number/capacity of MEC servers, bandwidth, communication latency, SINR, task data size, energy harvesting, dropped-task ratio, energy, and average response time.

These are the paper's simulation settings and reported results; they are not directly comparable to our iFogSim2 synthetic IIoT workloads. Do not copy its numeric performance figures into our results or benchmark table as if produced under the same environment.

### 3.5 What is and is not distinct from our project

| Dimension | TMC paper 7 | Our current V2 / IIoT proposal | Implication |
|---|---|---|---|
| System | Multi-device, multi-MEC-server wireless MEC | Local–Edge–Cloud abstraction in iFogSim2 | Different architecture; our Cloud tier and industrial profiles must be justified explicitly |
| Task model | CPU cycles, input/output sizes, max latency | MI, input/output bytes, deadline, divisibility / partition metadata | Similar task-level compute/data/deadline ingredients |
| Uncertainty | Energy, wireless channel/interference, MEC-server load, task/task-count variability | Workload/network/capacity shifts and residual prediction error | Uncertainty-aware offloading is prior art |
| Feasibility | Pre-ranks tasks using feasible execution modes under resource/latency constraints | Predicts end-to-end completion time and filters legal actions using residual margins | A possible distinction is the residual calibration source/model, but this is not proven unique |
| Optimization | Energy minimization plus joint resource allocation; static game and load balancing | Contextual action-value selection with a residual-calibrated feasibility layer | Different decision architecture; we must compare the incremental effect of the calibrator |
| Partial execution | Local, MEC, cooperative-device processing, or drop; no inspected Local-plus-one-remote split/merge action catalogue | Local + exactly one remote tier partial execution for declared data-parallel tasks | Different execution semantics; do not call partial offloading itself novel |
| Recovery | Inspected experimental section varies conditions and capacity; no explicit A1→B→A2 recovery protocol was identified in the inspected text | A1→B→A2 replay and recovery-window analysis is proposed | Potential experimental distinction, not proof of unique algorithmic novelty |
| Evaluation | MATLAB/custom wireless simulation, 30 repeated runs, energy/drop/response time | iFogSim2, paired seeds, task-level outcomes, latency/deadline misses, calibration diagnostics | Cross-simulator results are not directly comparable |

**Evidence limitation:** statements about what TMC “does not” include are restricted to the inspected author-version manuscript text. They should be phrased as “not described in the inspected manuscript” unless the final publisher version is checked.

## 4. Mandatory overlap comparison from Research Gap v29

At minimum, Omar's Related Work and Mark's novelty review must distinguish the following sources:

| Matrix ID / source | Direct overlap | What we cannot claim |
|---|---|---|
| PRIOR-03 — LITO (2026) | Edge–Fog–Cloud; contextual-bandit feedback; heterogeneous deadlines; queue/resource feasibility filter; fallback; failure/fallback experiments | Contextual bandit + feasibility filter + fallback in a continuum is not new |
| PRIOR-01 — E2DA (2023) | Contextual neural bandit for task offloading with deadline-aware reward under partial observations | Deadline-aware contextual bandit selection is not new |
| PRIOR-02 — O2C/CCMAB (IEEE ICC 2026) | Chance-constrained multi-tenant assignment with target delay-success probability | Probabilistic reliability / chance-constrained deadline offloading is not new; our binary miss penalty is not a chance constraint |
| CORE-06 — hierarchical partial offloading (IEEE TCE 2026) | Hierarchical DDQN + PPO for Device–Edge–Cloud partial task execution | Partial offloading across tiers is not new |
| CONF-03 — Edge-IIoT DQN (2026) | DQN task offloading in an Edge-IIoT setting | RL offloading in IIoT is not new |
| PRIOR-04 — H-DQAC (2025) | Local/Fog/Cloud, hybrid DQL/Actor-Critic, iFogSim2, deadline-miss reward | Using iFogSim2 or deadline penalties with RL is not new |
| CORE-04 — ESFMTO (2025) | Failure-aware task offloading in IIoT | Reliability/failure-aware IIoT offloading is not new |
| CORE-01 — forecast-driven LinUCB (2026) | Forecasting + contextual bandit for adaptive MEC offloading | Adaptive contextual offloading under variable load/failure is not new |
| TMC-07 — MECTOS-MU / DGOLB (2026) | Multifactorial uncertainty, feasibility screening, resource allocation, load balancing, deadline constraints | Generic uncertainty-aware feasibility and offloading is not new |

The full matrix includes additional adjacent work (RELTO, chance-constrained offloading, deadline-aware joint optimization, CVaR-constrained RL, Lyapunov virtual queues, distributed MAB, and other prior art). Use the row-specific evidence grade from Research Gap v29; an abstract-only item must not be described as if its full equations were audited.

## 5. Revised problem formulation for the IIoT study

The following is the most defensible current formulation, subject to supervisor approval and final task/topology contracts.

### 5.1 Task and system model

Represent task (i) by:

[
\tau_i=(p_i, MI_i, B_i^{in}, B_i^{out}, d_i, s_i, \pi_i)
]

where (p_i) is the industrial application profile, (MI_i) is required computation, (B_i^{in}) and (B_i^{out}) are payload sizes, (d_i) is its relative deadline, (s_i) is the declared divisibility class, and (\pi_i) is a validated partition-model identifier where applicable.

At decision time (t_i), the controller may observe only pre-decision task and system information: Local/Edge/Cloud availability and capacity, pre-decision utilization, queue-wait estimate or measurement with provenance, directed network paths, bandwidth and latency, and remaining deadline slack. Future regime labels and post-decision outcomes are prohibited.

### 5.2 Legal execution actions

For an indivisible task:

[
\mathcal A_i=\{LOCAL, EDGE\_FULL, CLOUD\_FULL\}
]

For a validated data-parallel task, add the existing six partial options:

[
EDGE/CLOUD\_PARTIAL\_\{25,50,75\}
]

A partial action means a Local branch and exactly one remote branch. Both required branches and the merge must complete before the task is considered complete. A single dependent machine window or single product image is not divisible merely because MI/bytes can be split arithmetically.

### 5.3 Completion-time estimate and residual calibration

For each legal action (a), estimate the end-to-end completion time from pre-decision values:

[
\widehat T_{i,a}=T_{queue}+T_{input}+T_{compute}+T_{output}+T_{partition/merge}
]

Use the appropriate full- or partial-execution equation and avoid double-counting queue, network, or merge time.

For a completed training task, define the residual:

[
e_{i,a}=T^{observed}_{i,a}-\widehat T_{i,a}
]

The current V2 calibrator keeps rolling residual windows and uses exact-action → action-family → pooled backoff. For a ready group with (n) samples and configured upper-tail level (\epsilon), the implementation uses:

[
k=\lceil(n+1)(1-\epsilon)\rceil
]

and selects the (k)-th ordered residual without interpolation. If the group has insufficient samples or (k>n), it falls back to the next eligible group or the explicitly configured uncalibrated prior. Negative empirical quantiles are clipped at zero.

[
T^{safe}_{i,a}=\widehat T_{i,a}+\max(0,q_{1-\epsilon,a})
]

The feasible set is:

[
\mathcal F_i(t_i)=\{a\in\mathcal A_i:T^{safe}_{i,a}\le d_i-t_i\}
]

The frozen contextual policy chooses among the feasible actions. If none is feasible, use a deterministic least-violation / fallback rule and log that no action was feasible at arrival. The task remains in the generated-task denominator.

This mechanism is an **empirical margin**, not a deterministic deadline guarantee or a distribution-free chance constraint. Report calibration sample counts, quantile source, calibration coverage, false-safe decisions, false-reject decisions where valid counterfactual evidence exists, and fallback frequency.

### 5.4 Primary empirical question

The most defensible research question is now:

> Within declared synthetic smart-manufacturing task profiles executed in iFogSim2, what incremental effect does per-action residual calibration add beyond an analytical completion-time feasibility screen and the same frozen contextual placement policy, for legal full and constrained Local-plus-one-remote partial execution, in terms of all-task deadline-miss rate, completed-task latency, calibration errors, and recovery behavior under isolated workload/network/capacity shifts?

This is an empirical comparative question. It does **not** assert that the underlying idea of contextual learning, feasibility screening, residual calibration, partial execution, or A1→B→A testing is globally novel.

### 5.5 Required policy arms before claiming incremental value

The current runner compares Local / Edge / Cloud / Random without a risk filter against a frozen learner with the risk filter. That design measures a combined policy bundle and cannot isolate the calibration's incremental contribution.

Before making a calibration-specific claim, evaluate matched test-time arms using identical task/exogenous traces and a frozen learner artifact:

1. Contextual learner without feasibility screening;
2. Same learner with the analytical completion-time feasibility screen and zero residual margin;
3. Same learner with the residual-calibrated feasibility margin.

If the learner was trained with a risk filter, training provenance must be matched or the ablation must be explicitly described as a test-time intervention rather than a complete end-to-end method ablation. Also include a deterministic minimum-predicted-completion heuristic over the same legal action set if it can be implemented and validated.

### 5.6 Recovery interpretation

The current evaluation mode freezes the model and calibration sidecar. A1→B→A2 under a frozen model measures return to earlier behavior after conditions return to A; it does not prove online learning or adaptive recovery. An online-update arm is a separate experiment with timestamped updates and a pre-registered rule.

For the proposed IIoT recovery analysis, A2 must replay A1's task template, exogenous inputs, and per-profile deadlines. The ten-task sliding window may remain the initial operational criterion only after sensitivity analysis on development/validation data. Non-recovered seeds are reported as not recovered/censored, not assigned zero recovery time.

## 6. Decision and recommendation

**Recommendation:** position the current study as a carefully controlled empirical evaluation of a residual-calibrated completion-time feasibility layer in an existing Local–Edge–Cloud full/partial execution pipeline, applied to clearly declared synthetic smart-manufacturing workloads. Do not currently claim a new generic task-offloading algorithm.

The current code's one-step action-value update and sparse state coverage also mean the learner must be named as a masked tabular contextual-bandit-style policy, not DQN or sequential deep RL. Any stronger learning claim requires a separately implemented and validated method.

Before freezing the methodology:
1. Obtain the authorized IEEE TMC full text and archive it.
2. Complete the equation-level comparison against LITO and E2DA, and check the O2C/CCMAB formulation from its retained full text.
3. Obtain supervisor/TA approval for whether the expected contribution is an empirical comparison or a new algorithmic contribution.
4. Implement the filter ablations and strong deterministic heuristic, or explicitly narrow the research question and claim scope.
5. Freeze industrial task profiles, simulator contract, recovery thresholds, and a fresh untouched test-seed registry.

---
*Audit limitation: the IEEE record was used for bibliographic authority; technical details were checked against an accessible accepted author-version repost, not an archived official IEEE PDF. The v29 workbook is a targeted scan, not a systematic review. Do not cite the repost as a licensed source in the paper.*
