# Integration (Java ↔ Python)

This area holds the **draft** interface between the Java/iFogSim simulator (Ayoub)
and the Python Q-Learning agent (Ibrahim).

> **Status: draft, not verified.** No integration method is final until the team
> agrees on the protocol. Nothing here is claimed to work end-to-end. This area
> deliberately contains **no** fake production agent and does **not** pretend the
> interface already functions.

## Contents

- `protocol/agent-message-schema.json` — a **draft** JSON Schema describing a
  request (state, simulator → agent) and a response (action, agent → simulator),
  combined via `oneOf`.
- `examples/` — placeholder for illustrative example messages once the protocol is
  agreed (currently empty).

## Related documentation

- Human-readable contract and requirements:
  [`../docs/integration-contract.md`](../docs/integration-contract.md)
- State/action/reward definitions:
  [`../docs/state-action-reward.md`](../docs/state-action-reward.md)

## Key rules (from the draft contract)

1. Field names, units, and encodings are **provisional** until Ayoub and Ibrahim
   agree.
2. Discretization boundaries must be documented and shared (single source of truth).
3. The selected action **must affect actual task execution**; Java must verify the
   real execution destination.
4. Outcomes **must be linked to the original `task_id`**.
5. Timeout and invalid-response behavior must be defined before integration is
   considered functional.

## Changing this protocol

- Treat the schema as a proposal. Discuss first (issue/PR), then edit.
- Record agreed decisions in [`../docs/decisions/`](../docs/decisions/).
- Because this file is shared, coordinate edits to avoid merge conflicts
  (see [`../CONTRIBUTING.md`](../CONTRIBUTING.md)).
