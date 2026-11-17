# Experimental Evidence Validity Audit — 2026-11-17

**Owner:** Mark — Research Lead & Integration  
**Branch:** `mark/iiot-scope-transition-v1`  
**Status:** Historical A→B→A batch reclassified as exploratory pilot; final held-out evaluation remains blocked.

## 1. Decision

The result bundle at `deliverables/10_iFogSim_Simulation/results/aba_paired_20seed_20261117/` is retained as a reproducible **exploratory A→B→A pilot**, not as the final independent held-out test set.

The manifests label seeds 102–121 as `evaluation_split=test`. That label is not sufficient evidence of test-set isolation: `create_v2_experiment_manifest.py` currently writes the split label as a constant and does not check an approved seed registry. The inference analyzer checks the label and duplicate IDs within the supplied batch, but does not verify that each seed is authorized for the test split.

The Research Lead Closeout already records that seeds 102–121 were used in the earlier generic A→B→A batch. Therefore, reusing those IDs in this result bundle means the batch cannot be presented as an untouched confirmatory test allocation, regardless of the manifest label.

**Required manuscript treatment:** the numerical results and paired comparisons may be reported internally as pilot/development evidence, clearly labelled exploratory and tied to the frozen model/profile/provenance. Do not use the nominal p-values or confidence intervals as confirmatory final-test evidence or as proof of generalization.

## 2. What remains valid

The following engineering and descriptive evidence is still useful:

- Five policy arms were executed on a common 90-task A1/B/A2 stream within each seed.
- The model and risk sidecar were frozen during evaluation.
- Per-seed manifests, hashes, Java contract checks, and outcome reconciliation were produced.
- The paired inference scripts completed and treated the seed/run as the inferential unit.
- The results expose a real trade-off: Cloud has lower deadline-miss rate and latency than the risk-calibrated learner in this profile; the learner performs better than Edge and Random on those metrics.
- The reported recovery behavior is descriptive for this particular frozen model and combined-shift profile.

These facts support a pilot report and help design the next experiment. They do not repair the seed-allocation problem.

## 3. Additional limitations in this batch

1. **Deadline confound:** the legacy combined profile uses 15,000 ms deadlines in A1/A2 and 20,000 ms in B. Phase-wise deadline-miss comparisons are therefore confounded by deadline relaxation.
2. **Combined shift:** task MI, input size, arrival pressure, and WAN latency change together. The batch cannot identify a network-only or workload-only causal effect.
3. **No calibration ablation:** the five arms are Local, Edge, Cloud, Random, and learner + residual filter. They do not compare the same frozen learner with no filter, analytical-only feasibility, and residual-calibrated feasibility.
4. **No partial-execution ablation:** the batch does not isolate full-only versus partial-enabled policy behavior.
5. **Queue context:** the Java adapter supplies zero pre-decision queue-wait estimates. These are assumptions, not measured queue waits.
6. **Synthetic workload:** `aba_network_load_v1` is a synthetic generic workload, not measured smart-manufacturing trace data.

## 4. Seed governance correction

The final experiment must use a versioned seed registry as the authority for split membership.

The registry must:
- inventory seeds used for training, validation, pilots, debugging, development, and prior test-labelled runs;
- record experiment family, split, source artifact, and status for every known use;
- reject duplicate seed assignments across splits within the same experiment family;
- reject any seed previously used in a pilot/development run from final test allocation;
- record the registry version and SHA-256 in every run manifest;
- be checked both before simulation launch and again by the inference analyzer.

The old nominal ranges Train 1–60 / Validation 61–80 / Test 81–120 are retired for final claims. Seed 101 was a pilot, 102–121 were used in the earlier generic A→B→A batch, and seed 81 was used in workload-generator development. A new allocation must only be made after the experiment machine's local archive and all team run records have been inventoried. No fresh test seed range is approved by this audit.

## 5. Required next execution sequence

1. Preserve the existing 102–121 bundle unchanged as exploratory pilot evidence.
2. Complete the historical seed inventory and commit a versioned seed registry; do not guess a fresh range from numeric appearance alone.
3. Implement and test the matched frozen-learner arms:
   - P1: no feasibility filter;
   - P2: analytical completion-time feasibility with zero residual margin;
   - P3: residual-calibrated feasibility.
4. Add a deterministic minimum-predicted-completion comparator (P4), with predeclared tie-breaking and no future information.
5. Add a full-only versus full-plus-partial comparison (P5) if partial execution remains part of the research question.
6. Run controlled A→B→A profiles with fixed deadlines: network-only, workload-only, and capacity-only only after simulator capacity/measurement validation. Keep combined stress secondary.
7. Perform recovery-threshold sensitivity on development/validation runs, then freeze one rule before opening the new test allocation.
8. Run at least 20 paired seeds per principal scenario after the model, risk state, workload generator, topology, and analysis plan are frozen.

## 6. Claim boundary

Until the sequence above is complete, the defensible claim is limited to:

> A reproducible exploratory iFogSim2 pilot compared a frozen contextual placement policy with a residual-calibrated feasibility layer against fixed placement and random baselines under one synthetic combined A→B→A profile.

Do not claim that residual calibration itself caused the learner's observed performance, that the policy is superior to Cloud, that the system learned online during frozen evaluation, or that results generalize to measured industrial workloads.

---
*This audit changes the interpretation of the historical evidence; it does not modify the original manifests, raw traces, simulator outputs, or team-owned code.*
