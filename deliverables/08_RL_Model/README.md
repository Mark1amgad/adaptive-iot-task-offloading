# Python Model Package

This is the received Python decision-model package retained with its source, configuration, JSON schemas, examples, tests, and protocol documentation.

## Package contents

- `src/rl_model/` — state mapping, action selection, reward, model, persistence, protocol, server, and aggregation.
- `config/default.json` — feature/state configuration and model parameters.
- `schemas/` and `examples/` — message schemas and sample protocol messages.
- `tests/` — unit and protocol tests.
- `docs/` — model audit, state specification, protocol, workflows, and known blockers.
- `legacy/` — original toy prototype, retained only as historical material; it is not simulator evidence.

## Relationship to current research design

The package describes a 54-state contextual-bandit-like configuration by default (γ = 0), with sequential-mode support also present in the code. The controlling research framing is [Specification V2](../../MARK_RESEARCH_SPECIFICATION_V2.md). Treat the package's implementation and claims as received technical material that must be reconciled with that specification before it is used for final experiments.

## Install and test

From this directory:

```powershell
python -m pip install -r requirements.txt
python -m pytest -q
```

The original package README reports 185 passing tests in its source workspace. That historical test count was not rerun during this repository cleanup.

## Run

The package exposes a JSON-lines server and command-line tools. See `docs/PROTOCOL.md`, `docs/WORKFLOWS.md`, and `docs/BLOCKERS.md` before connecting it to the simulator. Do not treat sample messages or synthetic fixtures as measured simulator results.


## Protocol v2.0 (nine-action research path)

The isolated v2 path is implemented in `src/rl_model/*_v2.py` plus `agent_v2.py`, `config_v2.py`, and `server_v2.py`. It uses `config/v2.json`, strict nine-action persistence, task-derived feasibility masks, and separate v2 JSON schemas. See [docs/PROTOCOL_V2.md](docs/PROTOCOL_V2.md).

Run the Python v2 server from this directory:

```powershell
python -m rl_model.server_v2 --mode train --config config/v2.json --model-out artifacts/model_v2.json
python -m rl_model.server_v2 --mode eval --config config/v2.json --model-in artifacts/model_v2.json
```

The Java/iFogSim v2 acceptance runners are `../10_iFogSim_Simulation/Simulation_Source/run_v2_full_acceptance.ps1` and `../10_iFogSim_Simulation/Simulation_Source/run_v2_partial_acceptance.ps1`. The latter executes all nine exact-action baselines (two overlapping tasks per action), including six ratio-specific partial paths and real merge Cloudlets, then runs a 30-task live learned-policy training episode. See `../10_iFogSim_Simulation/Simulation_Source/V2_PARTIAL_EXECUTION_ACCEPTANCE.md`. These are integration/lifecycle tests, not performance benchmarks or evidence of RL superiority.


## Variable workload and paired evaluation

The current v2 state has nine features (including input/output payload bytes and three deadline bands), 13,122 states, and 118,098 Q values. Use `../10_iFogSim_Simulation/Simulation_Source/generate_workload_v2.py` to generate seeded mixed/divisible/indivisible JSONL workloads. The iFogSim runner supports `train`, frozen `eval`, and Local/Edge/Cloud/Random baselines. `run_v2_policy_comparison.ps1` evaluates all policies against the same workload file. See [V2_VARIABLE_WORKLOAD_ACCEPTANCE.md](../10_iFogSim_Simulation/Simulation_Source/V2_VARIABLE_WORKLOAD_ACCEPTANCE.md) for the seed-42 training run, three held-out paired comparisons (seeds 43–45), aggregate results, and limitations.

The reproducible multi-seed holdout orchestrator is `../10_iFogSim_Simulation/Simulation_Source/run_v2_multiseed_holdout.ps1`; it regenerates each seeded workload, replays all policies, and aggregates paired per-task results. Important: the current 60-update model visited only 45 states and 60/118,098 state-action cells; 60% of held-out decisions used the `EDGE_FULL` fallback. Treat the comparison as a fallback/greedy hybrid result, not evidence of a trained RL policy's superiority.


## Risk-calibrated feasibility filter (V1)

The separate V2 risk layer is implemented in src/rl_model/risk.py. It predicts end-to-end completion time for the nine legal actions, applies a one-sided online residual margin, masks actions that exceed remaining deadline, and records a forced fallback when no candidate passes. Training writes a paired model sidecar named <model-out>.risk.json; evaluation loads the matching <model-in>.risk.json automatically when present or accepts --risk-state-in. See [RISK_CALIBRATION_V1.md](docs/RISK_CALIBRATION_V1.md) for the equations, observation context, calibration procedure, and limitations.

The simulator adapter is opt-in (--risk-filter). Its current zero queue-wait profile and MIPS/link values are provisional inputs, not measured facts or deterministic deadline guarantees. Use the same frozen residual sidecar for every policy in a paired evaluation.
