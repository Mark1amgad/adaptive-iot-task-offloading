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

## Verified status

- A one-task Java/Python/iFogSim integration acceptance suite has retained passing traces for its tested cases.
- A Local+Edge partial-execution feasibility spike passed two reproducible runs.
- These are **narrow integration/feasibility checks**, not a completed multi-task benchmark.
- No claim that the adaptive method outperforms static baselines is established by these runs.
- Multi-task behavior, broader workloads, and final comparative experiments remain open.

## Working rules

1. Treat Specification V2 as the controlling research definition.
2. Keep one canonical copy of each document; member folders retain authored work, while project folders link to it.
3. Keep generated classes, caches, temporary IDE state, and empty scaffolding out of Git.
4. Preserve raw evidence and record its origin; never present illustrative or historical outputs as final results.
5. Do not modify upstream iFogSim core code as part of repository cleanup.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the minimal workflow.
