# Adaptive Task Offloading in the IoT–Edge–Cloud Continuum

Research project studying adaptive execution placement across **Local, Edge, and Cloud** under changing task, network, and resource conditions.

## Source of truth

- **Research definition:** [MARK_RESEARCH_SPECIFICATION_V2.md](MARK_RESEARCH_SPECIFICATION_V2.md)
- **Current task status:** [TASK_TRACKER.md](TASK_TRACKER.md)
- **Team ownership:** [team-work/README.md](team-work/README.md)
- **Architecture and implementation boundaries:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

Older generic Q-learning plans and draft schemas are not authoritative over Specification V2.

## Repository map

| Path | What belongs here |
|---|---|
| `research/references/` | Classified research papers and reference index |
| `research/literature_review/` | Literature review, extraction, and research-gap documents |
| `research/datasets/` | Dataset inventories, provenance, and suitability evidence |
| `deliverables/08_RL_Model/` | Preserved Python model package, tests, and protocol documentation |
| `deliverables/10_iFogSim_Simulation/` | Java integration, topology, and partial-execution experiments |
| `deliverables/06_Reproduction/` | Reproduction instructions and experiment plan |
| `team-work/` | Actual contributions, received packages, and member-owned working material |
| `audit_output/` | Focused validation evidence and historical audit records |

## Latest verified status (2026-11-15)

- The isolated V2 Python protocol and Java/iFogSim integration execute all nine Local / Edge / Cloud full and partial actions.
- Partial tasks execute two branches, synchronize at a two-result barrier, and create a real merge Cloudlet only after both results arrive. A dropped-branch fault test fails closed without false success.
- Partition/merge overhead, deadline, WAN latency, and watchdog settings are configurable and traceable.
- Deterministic variable workloads and paired policy evaluation are implemented. One 60-task training workload and three held-out 60-task workloads (180 paired tasks) were completed.
- The held-out controller is a **sparse Q-table + fallback hybrid**: 108/180 decisions used the EDGE_FULL fallback. Results are descriptive and do not establish RL convergence or superiority.
- Energy, real-workload calibration, multi-IoT/multi-Edge topology, and statistically supported generalization remain open.

## Documentation and handoff

- **Full chronological engineering log and commit-by-commit summary:** [docs/WORK_LOG_2026-11-15.md](docs/WORK_LOG_2026-11-15.md)
- **Technical continuation notes, commands, limitations, and preservation rules:** [docs/RESEARCH_HANDOFF.md](docs/RESEARCH_HANDOFF.md)
- **V2 variable-workload and paired evaluation evidence:** [V2_VARIABLE_WORKLOAD_ACCEPTANCE.md](deliverables/10_iFogSim_Simulation/Simulation_Source/V2_VARIABLE_WORKLOAD_ACCEPTANCE.md)

## Working rules

1. Treat Specification V2 as the controlling research definition.
2. Keep one canonical copy of each document; member folders retain authored work, while project folders link to it.
3. Keep generated classes, caches, temporary IDE state, and empty scaffolding out of Git.
4. Preserve raw evidence and record its origin; never present illustrative or historical outputs as final results.
5. Do not modify upstream iFogSim core code as part of repository cleanup.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the minimal workflow.
