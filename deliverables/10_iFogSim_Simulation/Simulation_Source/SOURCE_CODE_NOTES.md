# Source Code Notes

## Canonical experiment-owned files

- `org/fog/test/perfeval/RlOffloadingIntegrationExperiment.java` — Java entry point, topology, multi-task emitter, run-scoped task/tuple registry, Python adapter, execution/transfer hooks, terminal endpoint, and JSONL trace writer.
- `run_acceptance.ps1` — isolated build and acceptance runner. It creates a fresh output directory and compiles outside the external simulator's tracked output tree.
- `validate_integration.py` — validates single-task regressions, multi-task lifecycle, mixed-tier action routing, outcome/shutdown ordering, fixed-seed repeatability, fallback, and deadline behavior.
- `ONE_TASK_ACCEPTANCE_TEST.md` — retained single-task regression contract.
- `MULTI_TASK_ACCEPTANCE_TEST.md` — current multi-task acceptance scope and evidence.
- `FINAL_STATUS.md` — verified results and remaining limitations.

## External dependencies

The Java source compiles against the external iFogSim source tree at sibling path `Research/iFogSim`, using its `src` and `jars` directories. The runner also requires a compatible JDK and the Python model package in `deliverables/08_RL_Model/`.

The integration experiment does not modify upstream iFogSim core source. Compiled classes and run artifacts are written to a fresh `audit_output` directory; the external project's `out/production` folder is not used.
