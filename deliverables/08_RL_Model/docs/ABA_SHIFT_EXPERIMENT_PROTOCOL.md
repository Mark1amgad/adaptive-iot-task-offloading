# A→B→A Regime-Shift Experiment Protocol

## Research question

Does an adaptive offloading policy recover after a temporary, joint workload/network regime shift, and what is the deadline-miss cost paid during stress and recovery?

This experiment evaluates response and recovery behavior. It does not by itself establish generalization or superiority.

## Regime construction

The deterministic generator is `deliverables/10_iFogSim_Simulation/Simulation_Source/generate_v2_aba_workload.py`.

| Phase | Regime | Workload | WAN latency |
|---|---|---|---:|
| A1 | A | 5,000–7,000 MI; 12–24 KB input; 4.0–5.0 s arrival gaps; 15 s deadline | 45 ms |
| B | B | 1.8× task MI, 1.5× input bytes, 2.5–3.5 s arrival gaps; 20 s deadline | 160 ms |
| A2 | A | Exact replay of A1's per-task compute, input/output, deadline, urgency and within-phase arrival-gap profile | 45 ms |

The generator uses one seeded baseline template and replays it in A2. This avoids confusing recovery with a newly sampled workload. B is a joint workload-and-network shift, so results must not be described as isolating network latency alone.

Default size is 30 tasks per phase (90 total). Use at least 20 distinct test seeds for inferential claims. The first run is a pipeline/trace validation pilot only.

## Runtime semantics

Each workload row carries `regime_id`, `regime_index`, and `wan_latency_ms`. At each task emission:
- the edge-to-cloud uplink latency is set to that task's regime latency;
- the observation's WAN feature and risk-context path use the same latency;
- a `regime_transition` trace record is emitted at each phase boundary;
- the decision trace records regime identity and WAN latency.

The local-to-edge link remains fixed. The shift therefore affects the cloud WAN path, while task MI, input volume and arrival cadence change jointly in B.

## Metrics

Per policy and phase:
- generated tasks, deadline-miss rate and completion coverage;
- median and p95 completed-task latency (conditional; always report coverage);
- task outcome counts and action mix.

Stress burden:
- deadline-miss rate across phase B, with A1 and A2 metrics shown beside it.

Recovery:
- reference is the A1 phase for the same policy;
- inspect consecutive 10-task windows in A2, sliding one task at a time;
- a window qualifies only if all 10 tasks complete, its deadline-miss rate is no more than A1 + 5 percentage points, and its median completed latency is no more than 110% of A1's median;
- recovery time is the final task completion time of the first qualifying window minus the A2 transition simulation time;
- if no qualifying window exists before A2 ends, report recovery as not observed, not as zero or an extrapolated value.

The window rule is an operational definition, not a theorem. Report the chosen tolerances and window size; sensitivity analyses should test alternative windows/tolerances before drawing strong conclusions.

## Pairing and inference

For each test seed, use the same immutable A→B→A workload file for all five current arms (Local, Edge, Cloud, Random, RL evaluation). Freeze model and risk sidecar before opening test seeds. Do not train or update the model on these evaluation traces. Use at least 20 distinct seeds per principal scenario, paired seed-level inference, bootstrap confidence intervals and Holm correction as documented in the paired-seed guide.

The current runner executes one seed per invocation. This protocol does not imply that the full nine-arm ablation matrix is already implemented.

## Interpretation safeguards

- A2 must be compared with A1, not only with B.
- Lower latency is not recovery if deadline misses or unresolved tasks rise.
- Completed-task latency is conditional and must be read with completion coverage.
- A2 recovery time is censored by the end of A2; no observed recovery means the threshold was not met in the observed horizon.
- The B phase changes compute demand, input size, arrival rate and WAN latency together. Separate-factor experiments are required to attribute effects to one cause.
- One run/seed is the inferential unit; tasks within a run are not independent replications.
