# V2 Overhead Sensitivity — Engineering Validation

**Date:** 2026-11-15
**Status:** PASS — parameterized execution and trace validation completed for zero, nominal, and high overhead settings.

## Purpose

The v2 partial/full simulator previously embedded partition overhead, merge overhead, deadline, and WAN latency as Java constants. Those values can now be supplied per process, recorded in the run's `config` trace record, and checked by the existing validator.

This is a sensitivity/engineering check. It is **not** empirical calibration of real partition or merge costs.

## New command-line parameters

The Java experiment accepts:
- `--partition-overhead-ms` (finite, >= 0; default 3.0)
- `--merge-overhead-ms` (finite, >= 0; default 2.0)
- `--deadline-ms` (finite, > 0; default 1000.0)
- `--wan-latency-ms` (finite, >= 0; default 45.0)
- `--watchdog-ms` (finite, > 0; default 1000.0)

The PowerShell acceptance runner exposes the same parameters. The watchdog is deliberately separate from the per-task deadline: the deadline determines whether a completed task is on time; the watchdog is an execution-horizon safety mechanism for unresolved tasks.

Example:

```powershell
.\run_v2_partial_acceptance.ps1 -RunRoot "..\..\..\audit_output\custom-overhead-run" -DeadlineMs 1000 -PartitionOverheadMs 7 -MergeOverheadMs 4 -WanLatencyMs 45 -WatchdogMs 1500
```

Each invocation starts a fresh Java process. The current parameter implementation is process-scoped; do not run multiple scenarios concurrently inside one JVM.

## Sensitivity matrix executed

All scenarios retained the same task profile, topology, 45 ms configured WAN latency, 1000 ms deadline, and 1000 ms watchdog.

| Scenario | Partition overhead | Merge overhead | Exact-action baseline tasks | Learned-policy tasks |
|---|---:|---:|---:|---:|
| Zero overhead | 0 ms | 0 ms | 18 | 30 |
| Nominal | 3 ms | 2 ms | 18 | 30 |
| High overhead | 10 ms | 10 ms | 18 | 30 |

The nominal run was executed at `audit_output/v2_parameterized_acceptance_20261115_1646`. Zero- and high-overhead runs are under `audit_output/v2_overhead_sensitivity_20261115_1710`.

For each scenario:
- 9/9 exact action cases completed (2 tasks per action).
- The live learned-policy training episode reconciled 30 tasks.
- The deliberate dropped-Edge-branch case failed closed as expected.
- Python shutdown reported zero orphaned tasks.
- The trace validator passed after the final validator update.

## Validator precision correction

At 10 ms, CloudSim event timestamps can represent a nominal 10 ms interval as approximately 9.999999999999986 ms due to floating-point representation. The validator now uses a 1e-9 ms comparison tolerance for overhead-duration checks. This tolerance is far below the simulator's meaningful timing resolution and does not relax event ordering or branch-barrier assertions.

## Interpretation boundary

These runs show that overhead values are configurable, emitted into trace metadata, and enforced by simulation events and validation. They do **not** establish that 3/2 ms or 10/10 ms reflects a real application, nor that one action is faster or better.

The 2-task fixed-action cases are execution checks, not performance samples. The 30-task learner episodes are integration smoke tests, not convergence or policy-superiority evidence. Research benchmarking still requires calibrated workload profiles, paired task streams, multiple independent seeds, sufficient task counts, and held-out regimes.


## Preliminary timing observation (descriptive only)

Across the two-task exact-action traces, the full-placement actions retained the same mean latency across all three overhead settings, as expected because partition/merge overheads do not apply to them. For `EDGE_PARTIAL_25`, mean latency was 33.527 ms at 0/0 ms, 40.022 ms at 3/2 ms, and 56.222 ms at 10/10 ms. The increases (+6.495 ms and +22.695 ms relative to zero overhead) are larger than the nominal sum of the configured overheads in this overlapping two-task run.

This is consistent with an interaction effect: delaying branch dispatch changes when work reaches the shared Local/Edge queues, while merge Cloudlets also contend for the Local device. Therefore, partition + merge overhead cannot always be interpreted as a simple additive constant under concurrent load. This is a useful hypothesis for a proper arrival-rate × overhead sensitivity study, not a statistically supported performance conclusion from two tasks.
