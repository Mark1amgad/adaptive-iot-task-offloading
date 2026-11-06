# iFogSim Integration Work — Preserved Versions

## Source versions

- `versions/root_src/RlOffloadingIntegrationExperiment.java` — custom experiment source found at the root of the external iFogSim source tree.
- `versions/integration_src/org/fog/test/perfeval/RlOffloadingIntegrationExperiment.java` — separate source variant found under `integration_src`.

The two source files have different SHA-256 hashes. They are deliberately not merged or overwritten. Their exact provenance is the external iFogSim workspace; the custom files were untracked there.

## Supporting material

- `topology/research_topology.json` — Local/Edge/Cloud topology configuration.
- `upstream_iFogSim2_README.md` — upstream iFogSim2 setup information.
- `evidence/one_task_prototype/latest/` — historical Java/Python JSONL traces and stderr from the one-task integration run.

This folder does not vendor the full iFogSim upstream source or JARs. The traces establish a prototype integration only; they do not establish statistically supported performance or final benchmark results.
