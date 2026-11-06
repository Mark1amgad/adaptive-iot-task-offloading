# Experimental Framework Preparation — Summary

## Overall status
The supplied V5 package contains the main experimental infrastructure: random topology generation, Local/Edge/Cloud execution, Python RL integration, fixed baselines, model persistence, topology leakage guards, JSONL logs, and a curriculum runner.

## Main blockers / decisions needed
1. Confirm primary latency definition: decision-to-completion or sensor-to-completion E2E.
2. Define generated-task denominator and treatment of tasks pending at simulation cutoff.
3. Decide whether energy is required; current Java task outcomes do not emit per-task energy.
4. Decide utilization definition: backlog proxy or actual host CPU utilization.
5. Clarify whether “static offloading” means a new threshold/rule baseline; only Local/Edge/Cloud fixed baselines currently exist.
6. Approve/correct state thresholds, reward weights/normalization, workload ranges, and epsilon decay.
7. Supply the missing `FILE_INDEX.md`, `REFERENCES_INDEX.md`, and `deliverables/02_Methodology/` to reconcile this technical audit with the approved research plan.

## Important configuration observation
The curriculum runner defaults to `rl_model/config/edge_cloud_scenario.json`, whose `epsilon_decay_steps` is 8000. The same configuration uses latency reference 150 ms (clipped at 1) and bandwidth-only reward cost with reference 50,000 bytes. These are development settings and should not be assumed to be final research choices.

## Work not performed
No Java/Python simulator code was modified. No final adaptive algorithm or dataset was implemented. No Git commit or push was made. This review was static; no fresh simulation or compile was run.
