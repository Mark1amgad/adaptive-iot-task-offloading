# RL Agent (Python Q-Learning)

Owner: **Ibrahim** — Python Q-Learning agent, state/action/reward handling,
training logic, and agent-side testing.

> **Status: under development / not implemented.** There is **no agent code in
> `src/` yet** (it is a placeholder), and **no tests in `tests/` yet**. Nothing on
> this page should be read as a claim that training works or that the agent runs.
> Do not claim training functionality until real code is present **and** tested.

---

## 1. Purpose

Implement the adaptive decision component that, given a task's observed state,
selects one offloading action — **Local**, **Edge**, or **Cloud** — using
**Tabular Q-Learning**, and learns from the reward returned after each outcome.

The intended interface with the Java/iFogSim simulator is documented as a **draft**
in `../docs/integration-contract.md` and `../integration/protocol/`. Field names,
units, and encodings are **provisional** and require agreement between Ayoub and
Ibrahim.

## 2. Python environment setup

Recommended (subject to team standardization):

```bash
# From the repository root
cd rl-agent

# Create an isolated virtual environment (Python 3.10+)
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux/macOS:
# source .venv/bin/activate

# Install dependencies (currently minimal: see requirements.txt)
pip install -r requirements.txt
```

The `.venv/` directory is ignored by Git (see `.gitignore`). Do not commit your
virtual environment.

> Dependencies are intentionally minimal. Tabular Q-Learning can be written in pure
> Python; add libraries only when actual code requires them (see
> `requirements.txt`).

## 3. Planned package structure

Not yet created. A candidate layout (to be finalized by Ibrahim):

```
rl-agent/
├── src/                  # Agent source (currently empty placeholder)
│   ├── agent.py          #   Q-table, policy (e.g. epsilon-greedy), learn()
│   ├── state.py          #   State representation / discretization mapping
│   ├── reward.py         #   Reward computation (pending formula agreement)
│   └── main.py           #   Entry point / integration adapter
└── tests/                # Agent-side tests (currently empty placeholder)
```

This is a **proposal**, not a mandate; Ibrahim may adjust it. Keep the mapping of
continuous features to discrete states consistent with the simulator (single source
of truth for discretization boundaries).

## 4. Expected responsibilities of the agent

- Maintain a **Q-table** over the agreed state space (candidate 54 states; 162 if
  network load is added by agreement) × 3 actions.
- Implement **action selection** (e.g., ε-greedy exploration/exploitation).
- Implement the **Q-Learning update** using the reward for the taken action.
- Be configurable with a **random seed** for reproducibility.
- Expose a small, testable core (select_action, learn/update) decoupled from I/O so
  unit tests can validate learning behavior without the simulator.

> The relationship between the decision framing (one-step contextual vs. sequential
> MDP) and the Q-Learning update must be made explicit and consistent — see
> `../docs/state-action-reward.md`, Section 1.

## 5. How the agent receives state information

Per the draft contract, the agent receives a **state message** describing the task
and conditions. Illustrative request (values are examples only):

```json
{
  "task_id": "task-000123",
  "task_size": 250.0,
  "network_latency": 45.0,
  "edge_utilization": 0.62,
  "deadline_category": "Tight"
}
```

The agent maps these raw values to a **discretized state** (Low/Medium/High bands
plus deadline category) before consulting the Q-table. Units and boundaries are
**provisional** and must be agreed with Ayoub.

## 6. How the agent returns an action

The agent responds with the selected action, echoing the task id. Illustrative
response (example only):

```json
{
  "task_id": "task-000123",
  "action": "Edge"
}
```

`action` ∈ { `Local`, `Edge`, `Cloud` }. The simulator (Java) is responsible for
**actually applying** this action and **verifying** the real execution destination.

## 7. How to run tests (once implemented)

There are currently **no tests to run**. Once `tests/` contains code:

```bash
cd rl-agent
python -m pytest
```

Tests should cover the pure learning core (state mapping, action selection, Q update,
reward shaping) independent of the simulator transport.

## 8. Integration & honesty notes

- Do **not** implement a fake/production agent that pretends the end-to-end
  interface already works.
- Do **not** copy an experimental notebook/script into these production files
  unless that file is actually present here **and** the team has agreed to integrate
  it, and unless it does not silently replace an existing implementation.
- Only after code exists and both agent-side tests and an integration round-trip
  pass may functionality be described as working.
