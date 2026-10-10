# Team Responsibilities

Three-member university research team. Ownership boundaries are defined to reduce
overlap and merge conflicts (see `CONTRIBUTING.md`).

---

## Mark — Repository, coordination, documentation, integration

- Repository management and Git hygiene (branches, PRs, reviews).
- Project coordination and schedule.
- Documentation (`README.md`, `docs/`, this file, decision log).
- Cross-cutting integration support and consistency between components.
- Maintaining `experiments/` and `results/` structure and reporting.

Primary areas: repository root files, `docs/`, `integration/`, `experiments/`,
`results/`.

## Ayoub — iFogSim & Java simulation

- iFogSim setup and Java implementation.
- Task generation and **task execution**.
- **Dynamic, task-level offloading** (applying the selected Local/Edge/Cloud
  action to actual execution).
- **Measurement collection** and linking outcomes to `task_id`.
- **Simulator-side integration** (sending state, receiving and validating action,
  verifying the actual execution destination, timeout/fallback handling).

Primary area: `simulator/`.

## Ibrahim — Python Q-Learning agent

- Python Q-Learning agent implementation.
- **State / action / reward** handling on the agent side.
- Training logic and learning updates.
- **Agent-side testing**.

Primary area: `rl-agent/`.

---

## Shared decisions (require agreement)

**Interface decisions between the simulator and the agent must be agreed by both
Ayoub and Ibrahim** before implementation. This includes, at minimum:

- Final field names, units, and encodings in the integration message
  (`integration/protocol/agent-message-schema.json`, `docs/integration-contract.md`).
- Where feature **discretization** happens (Java vs. Python) and the boundaries used.
- The transport mechanism and timeout/fallback policy.
- The reward terms and where reward is computed.

These shared items are a common source of merge conflicts; coordinate **before**
editing the protocol or interface files, and record agreed outcomes in
`docs/decisions/`.

## Responsibility overlap map

| Concern | Lead | Consulted |
| --- | --- | --- |
| Repository & docs | Mark | Ayoub, Ibrahim |
| Java simulator | Ayoub | Mark (integration), Ibrahim (interface) |
| Python agent | Ibrahim | Mark (integration), Ayoub (interface) |
| Integration protocol | Ayoub **+** Ibrahim (joint) | Mark (facilitates) |
| Experiments & metrics | Mark | Ayoub (data), Ibrahim (policy) |

> Roles describe intent and current assignment; they are not a claim that any
> area's functionality is complete.
