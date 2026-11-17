# Multi-task acceptance run manifest

- Date: 2026-11-15
- Git branch: `work/multi-task-lifecycle`
- Base revision: `fe91665`
- Java compiler/runtime: Eclipse Temurin JDK 25.0.3 (`jdk-25.0.3.9-hotspot`)
- Python: CPython 3.15.0b1
- Simulator: external iFogSim source tree at `Research/iFogSim`
- Experiment source: `deliverables/10_iFogSim_Simulation/Simulation_Source/org/fog/test/perfeval/RlOffloadingIntegrationExperiment.java`
- Runner: `deliverables/10_iFogSim_Simulation/Simulation_Source/run_acceptance.ps1`
- Command: `run_acceptance.ps1 -RunRoot audit_output/multi_task_final_acceptance_20261115_151500 -RunErrorTests`
- Build output: isolated under this run directory; no compilation into `Research/iFogSim/out/production`
- Result: all ten Java cases exited 0; standard, fallback, and deadline validators passed
- Standard suite: single-task train; Local, Edge, Cloud regressions; four-task baseline overlap; four-task training; fixed-seed training repeat
- Error/deadline suite: timeout fallback; malformed-response fallback; zero-deadline miss
- Fixed-seed repeat comparison: PASS for action, executor/module, execution-admission time, latency, counted bytes, transfer count, and deadline result
- Python shutdown: one acknowledgement per run, `orphaned_tasks=0`, clean process exit

The retained traces are integration acceptance evidence only. They do not establish calibrated performance or policy superiority. Partial offloading, multi-task merge barriers, failure/horizon semantics, energy attribution, and the target 4 IoT / 2 Edge / 1 Cloud topology remain unverified.
