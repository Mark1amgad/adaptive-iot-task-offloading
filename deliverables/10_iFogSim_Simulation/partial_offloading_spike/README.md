# Partial Offloading Feasibility Spike

## Purpose

A small, experiment-owned iFogSim2 proof of concept for one divisible task split concurrently across Local and Edge:

- Local receives 40% of task MI, input bytes, and output bytes.
- Edge receives 60%.
- Both branch results return to a Local branch-result endpoint.
- A coordinator waits for both correlated results, then submits a real merge Cloudlet to a Local `merge_worker` module.
- The final merged result returns through a separate final-result endpoint, producing one task-level terminal record.

## Current successful result

The current implementation passed two identical runs:

- `results/run_20261105_211737/`
- `results/run_20261105_211838/`

Both runs used the reproducible `run.ps1` runner, exited with code 0, and produced byte-identical `summary.txt` and `spike_trace.csv` artifacts.

### Configuration and measured event times

| Item | Value |
|---|---:|
| Original task | 10,000 MI |
| Local branch | 4,000 MI; 4,800 input bytes; 400 output bytes |
| Edge branch | 6,000 MI; 7,200 input bytes; 600 output bytes |
| Local MIPS | 1,000 |
| Edge MIPS | 2,800 |
| Local↔Edge link latency | 45 ms configured |
| Local branch result arrival | 10.010 ms |
| Edge branch result arrival | 98.933 ms |
| Branch-result skew | 88.923 ms |
| Merge Cloudlet | 1,200 MI on Local |
| Merge Cloudlet admission | 98.933 ms |
| Final merged-result arrival | 101.143 ms |
| End-to-end task latency | 96.143 ms |
| Counted parent-child transfer | 7,800 bytes over 2 hops |

The end-to-end latency is measured from task creation at 5.0 ms to final merged-result arrival at 101.142857 ms.

`merge_module_to_endpoint_ms = 2.21` is the interval from merge-module admission to final endpoint arrival. It includes the 1 ms actuator endpoint latency; it is **not** a pure CPU execution-time measurement.

## What PASS proves

The retained runs verify this narrow lifecycle:

1. The original task is split into two branches.
2. MI, input bytes, and output bytes are conserved across Local and Edge.
3. Each branch is routed to its intended module and has a unique propagated `actualTupleId`.
4. Both branch results arrive at the shared Local branch endpoint.
5. The merge barrier fires only after both branch results arrive.
6. The coordinator creates one merge tuple with 1,200 MI and 1,000 input bytes.
7. iFogSim submits that tuple to the Local `merge_worker` Cloudlet scheduler.
8. The merge module emits a `MERGED_RESULT` tuple to the separate final endpoint.
9. The final result is correlated to the merge tuple and creates exactly one task-level terminal record.

This proves simulator feasibility for a small Local+Edge partial-execution path. It does **not** prove partial offloading is superior to full placement, that arbitrary workloads are divisible, or that the current RL agent supports partial actions.

## Remaining modeling limitations

- The merge is now a real CloudSim Cloudlet, not a fixed timer.
- The coordinator represents the combined 400+600 byte branch output as one 1,000-byte merge input tuple. The actual data copy/serialization/merge algorithm is not modeled.
- The branch endpoint and merge worker are co-located on Local, so no extra network transfer is counted for handing the combined merge input to the merge module.
- The 40/60 MI/byte partition is a deterministic fixture. It assumes proportional divisibility and is not valid for every task type.
- Per-task energy attribution, task failure semantics, multiple concurrent tasks, Local+Cloud partial execution, and RL action integration remain unimplemented.

Do not use these results as comparative performance evidence.

## Reproduce

Run from PowerShell:

```powershell
.\deliverables\10_iFogSim_Simulation\partial_offloading_spike\run.ps1
```

The runner compiles the experiment-owned Java source into this package's `build/classes` directory and uses the external iFogSim `src` and `jars` as dependencies. It does not write into the external simulator's `out/production` directory or modify iFogSim core source. Each invocation writes a new timestamped directory under `results/`.

Default expected locations:

- Repository: `Research/adaptive-iot-task-offloading`
- Simulator: sibling folder `Research/iFogSim`
- JDK: `C:\Program Files\Eclipse Adoptium\jdk-25.0.3.9-hotspot`

## Retained failed and historical runs

- `results/run_001/`: failed initial setup; exposed a broker user-id mismatch and missing `cloud` root device.
- `results/run_20261105_211659/`: failed intermediate merge implementation; exposed that the coordinator must ignore normal `TUPLE_ACK` events.
- `results/run_002/` and `results/run_20261105_211023/`: successful historical prototype using a fixed 2 ms merge delay. They are not the current merge implementation.
- Current real-Cloudlet implementation: `run_20261105_211737/` and `run_20261105_211838/`.

## Next engineering gates

1. Define task-specific legality rules for partitioning computational work and input/output data; do not assume MI and bytes always split proportionally.
2. Model actual merge-data construction/serialization and verify that the merge tuple represents the output semantics of the two branches.
3. Test multiple split ratios and heterogeneous task sizes.
4. Add a Local+Cloud partial option.
5. Add overlapping tasks with task-scoped branch registries and one terminal state per task.
6. Only after those gates, connect the calibrated feasibility filter and learner.
