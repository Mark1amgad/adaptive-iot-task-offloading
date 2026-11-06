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
