# Java/iFogSim integration checklist

- [ ] Choose the canonical protocol; reconcile root draft fields (`task_size`, `network_latency`, `deadline_category`) with `rl_model` fields (`task_mi`, `wan_latency_ms`, `deadline_ms`).
- [ ] Implement one persistent Python subprocess per simulation run; UTF-8 JSONL, one synchronous reply per line, drain stderr.
- [ ] Before placement, send `hello` then an observation with finite, unit-consistent values and available actions.
- [ ] Apply the returned Local/Edge/Cloud action to real iFogSim routing; record the actual executed destination.
- [ ] After completion/failure, send measured `latency_ms`, `deadline_met`, status/reason, required `bandwidth_bytes`, and available energy/utilization.
- [ ] Define latency endpoints, which network links count toward bandwidth, energy model, and edge-utilization sampling instant.
- [ ] Calibrate state bins and reward references/weights from documented workload/topology ranges.
- [ ] Decide contextual bandit versus sequential MDP. For sequential use, define valid episodes and next states.
- [ ] Implement timeout/error fallback and ensure fallback tasks are not falsely reported as agent-selected outcomes.
- [ ] Run a one-task end-to-end trace and verify task id, action, destination, and feedback match.
- [ ] Run train/test separation with matched seeds and Local/Edge/Cloud fixed baselines; aggregate only genuine simulator logs.
