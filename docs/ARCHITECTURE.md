# Architecture

The project studies per-task execution placement across three tiers:

- **Local:** IoT device.
- **Edge:** nearby fog/edge node.
- **Cloud:** remote cloud tier.

## Runtime boundary

1. iFogSim creates a task and exposes decision-time context.
2. The model selects a legal execution action.
3. The simulator applies the action to actual task execution.
4. The simulator records the actual destination and task outcome.
5. Decision, action, and outcome remain correlated by task identifier.

## Current evidence boundary

The repository contains a tested one-task integration prototype and a separate Local+Edge partial-execution feasibility spike. These do not establish multi-task support or comparative performance.

The controlling algorithm and research framing are defined in [Specification V2](../MARK_RESEARCH_SPECIFICATION_V2.md). Older Q-learning-oriented planning documents are historical and must not override it.

## Canonical implementation

- Python model: [deliverables/08_RL_Model/](../deliverables/08_RL_Model/)
- Java/iFogSim integration: [deliverables/10_iFogSim_Simulation/](../deliverables/10_iFogSim_Simulation/)
- Workload generation and validation: [team-work/Astta-Abdo/](../team-work/Astta-Abdo/)
- Experiment evidence: [audit_output/](../audit_output/)
