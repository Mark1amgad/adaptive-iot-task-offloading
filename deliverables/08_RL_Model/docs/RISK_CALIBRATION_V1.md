# Risk-Calibrated Feasibility Filter — V1

## Status and scope

This module adds a pre-decision completion-time estimator, an online residual calibrator, and a feasibility filter to the isolated protocol-v2 path. It does not alter protocol v1 or the nine-action catalogue.

The filter is an empirical decision aid, **not a deterministic deadline guarantee**. Its quality depends on the accuracy and freshness of the resource/link snapshot, the validity of the execution-time model, and the representativeness of prior outcomes. All initial simulator capacity and network-profile values are provisional until checked against trace measurements.

## Decision path

For each incoming task:

1. Java sends task features, the legal action mask and constraints, plus a pre-decision \`risk_context\`.
2. Python estimates end-to-end completion time for every legal full or partial action.
3. Python adds a one-sided residual margin from completed *earlier* tasks. Backoff is exact action → action family (e.g. Edge partial ratios) → pooled residuals.
4. Actions whose conservative estimate exceeds remaining deadline are removed before the policy selects.
5. If no legal action passes the filter, Python chooses the available action with the smallest conservative deadline violation (or earliest estimate when all estimates are unavailable), marks \`risk_fallback\`, and does not update the Q-table from that forced choice.
6. After a successful completed outcome, training mode adds \`observed_duration - predicted_duration\` to the residual windows. Failed tasks and evaluation runs do not update calibration.

The outcome timestamp is checked before either learner or calibrator state is mutated. Python also rejects an outcome whose executed action is outside the risk-filtered mask.

## Completion-time model

Protocol, trace, deadline, latency, and overhead fields use milliseconds. CloudSim itself advances in seconds; Java converts clock values to milliseconds at the protocol/trace boundary and converts millisecond event delays to seconds before scheduling. Capacity is MIPS (million instructions per simulator second); payload sizes are bytes and FogDevice bandwidth is bytes per simulator second.

For tier \(s\):

\[
MIPS^{eff}_s = MIPS_s(1-U_s)
\]

\[
T_{compute}(s,MI)=Q_s + 1000\frac{MI}{MIPS^{eff}_s}
\]

For each network hop \(h\), where bandwidth is in bytes per simulator second:

\[
T_{transfer}(B,h)=1000\frac{B}{BW_h}+L_h
\]

A path is the sum of its hop transfer times. A full remote action adds input-path transfer, remote compute/queue time, and output-path transfer. A Local action uses the Local compute/queue estimate.

For a partial action with remote share \(\alpha\):

\[
T_{partial} =
\max(T_{local}((1-\alpha)MI),T_{remote}(\alpha MI))
+T_{partition}+T_{merge\_overhead}
+T_{merge\_queue}
+1000\frac{MI_{merge}}{MIPS^{eff}_{local}}
\]

The partial predictor models input and output payload bytes in proportion to the remote share. The merge compute term is explicit because the iFogSim implementation creates a real Local merge Cloudlet with \`merge_mi\`; merge is not represented only by a constant delay.

An action is not eligible if any required tier has zero effective MIPS. That action receives no finite estimate and cannot pass the filter.

## \`risk_context\` contract

\`risk_context\` is an optional member of a protocol-v2 observation. When supplied while risk filtering is enabled, it must contain:

- \`remaining_deadline_ms\`
- \`resources\`: profiles for every currently available tier (\`LOCAL\`, \`EDGE\`, and/or \`CLOUD\`)
- \`partition_overhead_ms\`, \`merge_overhead_ms\`
- \`merge_compute_mi\`, \`merge_queue_wait_ms\`
- optional \`queue_wait_basis\`, a non-empty provenance/assumption label

Each tier profile contains \`compute_mips\`, \`utilization\` in [0,1], and \`queue_wait_ms\`. Remote tier profiles additionally contain \`uplink_path\` and \`downlink_path\`, each an ordered list of hops with \`bandwidth_bytes_per_second\` and \`latency_ms\`. This is the field required by the V2 parser and populated by the current Java adapter; do not substitute Mbps without an explicit conversion.

The parser checks that the utilization values match the observation features, that remaining slack does not exceed the original task deadline, and that partition/merge overheads match the task constraints. Divisible tasks require a partition model and positive merge MI. Indivisible tasks must declare zero merge MI.

## Residual calibration

For each completed training task:

\[
e_t = T^{observed}_t - T^{predicted}_t
\]

The calibrator retains a bounded rolling window per exact action, action family and pooled group. For a group with \(n\) samples, configured upper-tail error \(\epsilon\), and \(k=\lceil(n+1)(1-\epsilon)\rceil\), the margin is the empirical \(k\)-th order statistic, without interpolation. The implementation requires \`min_samples\`; if the exact action has too few samples, it backs off to its family and then the pooled window. If no group is ready, it uses the configured \`uncalibrated_margin_ms\` and explicitly reports \`calibrated=false\`.

Negative residual quantiles are clipped to zero: calibration may increase the estimated completion time but never make the analytical estimate more optimistic. This avoids turning a period of unusually fast execution into a negative safety margin.

The initial values in \`config/v2.json\` (\`epsilon=0.10\`, \`window_size=200\`, \`min_samples=20\`, and \`uncalibrated_margin_ms=0\`) are **provisional settings**, not tuned scientific parameters. They must be selected using training/validation data, then frozen before held-out evaluation. Because tasks may be temporally correlated and workloads may shift, the empirical quantile should not be described as a distribution-free guarantee without separately validating the assumptions.

## Persistence and experiment protocol

Training writes a calibration sidecar next to the model:
- model: \`<model-out>\`
- residual state: \`<model-out>.risk.json\`

Evaluation automatically loads \`<model-in>.risk.json\` when present, or accepts \`--risk-state-in\`. It does not update calibration. Keep the model and its sidecar together; a configuration fingerprint prevents loading residual state under a different risk configuration.

In Java/iFogSim, add \`--risk-filter\` to include the risk context. Add \`--risk-state-in <path>\` to evaluate with a frozen residual state. The training runner saves both artifacts. **Current comparison-runner behavior:** \`run_v2_policy_comparison.ps1\` runs Local, Edge, Cloud, and Random without \`--risk-filter\`; only \`policy_rl_eval\` receives \`--risk-filter --risk-state-in\`. Therefore, the existing five-arm comparison is a combined learner-plus-filter comparison against unfiltered reference baselines. It does not isolate the learner effect from the filter effect, and it does not apply one common filter to all policies. To make a filter-specific claim, add paired learner ablations (no filter; analytical-only feasibility with zero residual margin; residual-calibrated feasibility) using identical workload traces and the same frozen learner artifact.

The current simulator adapter uses:
- explicit provisional MIPS values for Local, Edge and Cloud;
- zero pre-decision queue-wait estimates;
- directional link profiles that follow the actual FogDevice uplink/downlink bandwidth values;
- configured link capacities/latencies and partition/merge delays.

These are model inputs, not claims that queue waiting is actually zero. The current links are directional: Local↔Edge uses 10,000 bytes/s in each direction, Edge→Cloud uses 10,000 bytes/s, and Cloud→Edge uses 100,000 bytes/s; Edge/Local and Cloud/Edge propagation latencies are 2ms and 45ms respectively. The \`queue_wait_basis\` field records the zero-queue assumption. Residual updates can learn observed end-to-end bias after completed training tasks, but they cannot correct a missing or incorrect input before enough representative outcomes exist. Replace the provisional values with measured/simulator-derived snapshots before final experiments.

## Required reporting

For every run with filtering enabled, retain the action response and decision trace fields:
- predicted completion time and remaining deadline;
- residual margin and conservative completion estimate;
- calibration group/source and sample count;
- per-action candidate estimates and feasible set;
- whether no action passed and which fallback was used;
- queue-wait provenance.

Report the fraction of decisions made before calibration reaches \`min_samples\`, fallback frequency, deadline-miss rate, false-safe decisions (predicted safe but deadline missed), false-reject decisions (filtered action would have met deadline), and calibration coverage/quantile error on held-out traces. Do not report the filter as "safe" based only on its internal feasible mask.

## Limitations / next calibration work

1. The current context has zero queue estimates; implement a measured pre-decision queue estimator or simulator-derived queue snapshot.
2. Verify the assumed Local/Edge/Cloud MIPS and link path values against the actual iFogSim topology and trace timestamps.
3. Validate the model separately for each action family and under A→B→A workload/network shifts.
4. Tune the cold-start margin, residual window, minimum sample count and epsilon on training/validation only.
5. Compare the predictor's residual distribution by action, urgency class, workload profile and regime; pooled backoff can hide action-specific bias.
6. Treat missed deadlines and infeasible-at-arrival outcomes as outcomes to report, not observations to erase from the denominator.
