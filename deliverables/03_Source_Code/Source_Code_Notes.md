# Source Code Notes

Copied experiment-owned files:

- `org/fog/test/perfeval/RlOffloadingIntegrationExperiment.java` — Java entry point, topology, task emitter, Python subprocess adapter, task registry, execution/transfer hooks, endpoint, and JSONL trace writer.
- `compare_policies.py` — summarizes measured one-task traces without rerunning simulation.
- `validate_integration.py` — validates JSONL structure, task correlation, routing, bytes, outcomes, fallback, deadline, and cleanup invariants.
- `run_acceptance.ps1` is copied under `06_Reproduction/` because it is the build/run entry point.

## External Dependencies

The Java source is compiled against the external iFogSim source at:

`C:\Users\DELL\OneDrive\Desktop\Research\iFogSim`

The runner uses its `src` and `jars` directories. It also requires a JDK 25 installation and the Python RL service under:

`team-work\Ayoub\rl_model\rl_model`

The Python service is intentionally not copied here because it is teammate-owned and the milestone prohibits modifying or duplicating the original RL implementation as a replacement. The deliverables therefore document and copy the experiment-owned bridge, not a self-contained package.

No compiled class files or generic FogDevice source are included. The external simulator source is not modified by the experiment.
