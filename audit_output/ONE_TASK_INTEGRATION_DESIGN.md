# One-task Java/Python integration design

## Scope

This is a design based on the implemented Python protocol v1.0 and inspected iFogSim2 source. It does not implement a Java client and does not treat example protocol numbers as measurements.

## Minimal architecture

Create a dedicated one-task experiment from the Adaptive topology. It needs: (1) a persistent JSONL Python-process adapter, (2) an adapter-owned task record keyed by composed Java task id, (3) one task emitter, (4) three explicitly deployed target modules representing Local/Edge/Cloud execution, and (5) a terminal completion observer. The chosen target module must be hosted only on its corresponding tier so normal classic `FogDevice` routing/execution determines the actual device.

## One-task sequence

1. Java starts one persistent `python -m rl_model.server --mode train` process, sets UTF-8 stdin/stdout, drains stderr, and sends protocol v1.0 `hello` with `phase:"dev"`.
2. Java validates `hello_ack`, including actions and placeholder-feature warning. Abort on fatal error.
3. At task emission, allocate `task_id = run_id + ":tuple:" + cloudletId`; record simulation creation clock, tuple/loop ids, task CPU/network specification, topology-derived WAN latency, and sampled edge utilization. Do not send values whose source/unit is not defined.
4. Java sends `observation`; validates returned action name/id/task id before placement.
5. Map Local/Edge/Cloud to the three tier-specific target modules. Record `action_decided`, Python model version, decision mode, and `decision_source=agent`.
6. Let normal FogDevice events route and execute the tuple. At execution, record actual device/module. At terminal completion, capture actual end clock and the defined end-to-end latency, plus only actual available byte/CPU data.
7. Send `outcome` containing the same task id, `action_executed` mapped from actual device, terminal status, latency, deadline flag only if a supervisor-approved deadline was modeled, and required `bandwidth_bytes` only if instrumented as an actual sum. Do not invent energy or failures.
8. Require matching `outcome_ack`; retain Java trace, Python run/events JSONL, and process exit/status. Send `save`/`shutdown` as appropriate.

## Timeout/error rule

Set a supervisor-approved wall-clock timeout for the Java JSONL read. On timeout, malformed reply, mismatched task id/action, process exit, or fatal error: record `decision_source=fallback_timeout|fallback_error`; execute an approved fallback; record its actual destination; and do **not** send its outcome to Python because there was no valid pending agent decision. If a valid Python decision is later overridden by simulator constraints, send the truth as `action_executed` and preserve override reason.

## Required trace fields

`run_id`, `sim_seed`, `task_id`, `cloudlet_id`, `actual_tuple_id`, creation clock, observation fields with units/sources, action decided/id/model version, decision source, chosen target module, execution device/module, action executed, CPU start/end where captured, terminal clock, latency definition/value, measured link bytes, deadline policy/value/result, outcome acknowledgement, fallback/override/error details.

## Minimal acceptance test

One deterministic `dev` task passes only when retained logs prove: hello acknowledged; valid observation/action for one task id; selected tier maps to a deployed tier module; actual executor is recorded; a terminal real simulator timestamp yields a defined outcome; Python acknowledges that same id; shutdown has zero orphaned tasks. It is an integration trace, not policy-performance evidence.

## Approvals required before execution

- The exact Local/Edge/Cloud module mapping and task semantics.
- Definition/units for task MI, WAN latency, edge utilization, latency endpoint, and counted bandwidth links.
- Task deadline and failure model, if `deadline_met` / failures are sent.
- Java wall-clock timeout and fallback action.
- Whether to begin with training/dev mode and retain its learned update.
