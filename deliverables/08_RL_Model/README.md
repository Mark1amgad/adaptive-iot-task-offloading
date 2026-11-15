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

The Java/iFogSim full-placement v2 acceptance runner is `../10_iFogSim_Simulation/Simulation_Source/run_v2_full_acceptance.ps1`. Partial-action Java execution remains the next integration milestone; the full-placement smoke test is not a partial-offloading benchmark.
