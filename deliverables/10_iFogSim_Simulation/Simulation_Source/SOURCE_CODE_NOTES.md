# Source Code Notes

Canonical experiment-owned files:

- `org/fog/test/perfeval/RlOffloadingIntegrationExperiment.java` — Java entry point, topology, task emitter, Python adapter, task correlation, execution/transfer hooks, terminal endpoint, and JSONL trace writer.
- `run_acceptance.ps1` — isolated build and acceptance runner.
- `validate_integration.py` — validates JSONL structure, task correlation, routing, transfer accounting, outcomes, fallback, deadline, and cleanup invariants.
- [`compare_policies.py`](../../04_Results/compare_policies.py) — summarizes retained traces without rerunning simulation.

## External dependencies

The Java source compiles against the external iFogSim source tree at sibling path `Research/iFogSim`, using its `src` and `jars` directories. The runner also requires a compatible JDK and the Python model package in [`deliverables/08_RL_Model/`](../../08_RL_Model/).

The integration experiment does not modify upstream iFogSim core source. No compiled class files are included.
