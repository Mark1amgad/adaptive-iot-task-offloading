# Member 2 v26 — final current work package

## Validation
- 192 Python tests passed in the v26 working copy.
- 448 Java source files compiled successfully (two existing deprecation warnings in ControllerComponent.java).
- 3 sequential training runs (seeds 801–803) trained a deadline-conditioned Q-table with 81 states; per-task deadlines were 20/50/120 simulation units by task class.
- 60 held-out test runs completed across two scenarios × six policies × five test seeds. All logs have one start/end, task counts reconcile, and zero orphaned tasks.
- Test policies: Q-learning, latency-greedy, deadline-greedy diagnostic, Edge-only, Local-only, Cloud-only.
- Scenarios: heterogeneous task deadlines; Edge-1 compute-service outage from simulation time 250 to 500 with recovery. During outage, new assignments cannot select Edge-1 for execution; router/network remains active and already-in-flight tasks are not forcibly killed.

## Key results (mean across five seed-level means)

### heterogeneous_deadlines
- qlearning: mean latency 10.894 (95% CI 10.179–11.610); P95 26.013; P99 74.819; deadline violations 0.000%; completion 100.00%; tasks 1427.
- latency_greedy: mean latency 8.158 (95% CI 7.661–8.654); P95 24.333; P99 41.007; deadline violations 0.000%; completion 100.00%; tasks 1427.
- deadline_greedy: mean latency 8.158 (95% CI 7.661–8.654); P95 24.333; P99 41.007; deadline violations 0.000%; completion 100.00%; tasks 1427.
- edge: mean latency 14.412 (95% CI 13.643–15.181); P95 40.583; P99 62.236; deadline violations 0.137%; completion 100.00%; tasks 1427.
- local: mean latency 18.985 (95% CI 18.351–19.620); P95 75.228; P99 119.215; deadline violations 1.403%; completion 100.00%; tasks 1427.
- cloud: mean latency 87.166 (95% CI 86.469–87.862); P95 130.077; P99 133.334; deadline violations 88.092%; completion 100.00%; tasks 1427.

### edge1_compute_outage_recovery
- qlearning: mean latency 12.983 (95% CI 11.907–14.059); P95 34.198; P99 106.198; deadline violations 0.209%; completion 100.00%; tasks 1441.
- latency_greedy: mean latency 11.272 (95% CI 10.255–12.290); P95 33.966; P99 89.356; deadline violations 0.141%; completion 100.00%; tasks 1441.
- deadline_greedy: mean latency 11.272 (95% CI 10.255–12.290); P95 33.966; P99 89.356; deadline violations 0.141%; completion 100.00%; tasks 1441.
- edge: mean latency 15.250 (95% CI 14.526–15.973); P95 40.659; P99 84.650; deadline violations 0.070%; completion 100.00%; tasks 1441.
- local: mean latency 18.846 (95% CI 17.784–19.908); P95 76.346; P99 116.709; deadline violations 0.765%; completion 100.00%; tasks 1441.
- cloud: mean latency 87.029 (95% CI 85.825–88.234); P95 129.969; P99 133.113; deadline violations 88.263%; completion 100.00%; tasks 1441.

## Interpretation
- Q-learning is not the best policy in these two new tests. In heterogeneous-deadline mode, latency-greedy and the deadline-greedy diagnostic are identical by construction and both have lower mean latency than Q-learning. The deadline-greedy method is not an independent baseline and should not be counted as a separate algorithm.
- Under the Edge-1 compute-service outage, latency-greedy is again faster on mean latency than Q-learning. Q-learning has a slightly higher miss rate in this five-seed test.
- The outage is a compute-service availability/failover model for new assignments. It is not a physical host crash: in-flight tasks are not forcibly terminated, and network routing remains active.
- These findings do not establish a new algorithm or general reliability guarantee.

## Research gap verdict
No broad algorithmic gap is confirmed. Close prior art already covers deadline-aware contextual bandits (E2DA), chance-constrained bandit offloading (O2C/CCMAB), forecast-driven LinUCB, LITO with heterogeneous deadlines/fallback/failure tests, H-DQAC in iFogSim2, reliability-oriented PPO (RELTO), and CVaR/tail-risk RL. See `prior_art_evidence_matrix.csv` and `FINAL_RESEARCH_GAP_VERDICT_v26.md`.

## Metric caveats
- Deadline/latency: Sensor emission to first processing-module completion; not full multi-module application-loop completion.
- `executing_node_utilization` remains a backlog proxy, not measured CPU utilization.
- `bandwidth_bytes` remains a payload-size proxy, not total per-hop network traffic/cost.
- Energy is not present in the RL task outcome, so no energy benefit claim is supported.
- Single synthetic topology; fixed task-class deadline profile; five held-out seeds per policy/scenario.
