# Integration status

## Verified

- `validate_integration.py` passes the retained real Python train trace and deterministic Local, Edge, and Cloud traces.
- Each retained trace is valid JSONL and has one correlated task lifecycle: decision, task creation, execution, terminal result, outcome acknowledgement, and clean shutdown.
- The retained byte totals are 0 bytes for Local, 14,000 for Edge, and 28,000 for Cloud. These are sums of the instrumented parent-child uplink/downlink rows only; Local's zero is therefore an intentional absence of counted transfers, not a missing measurement.
- The train trace records `updated=true`, a saved model, `orphaned_tasks=0`, and Python exit code 0. Baseline traces record no model save and no learning update.
- `run_acceptance.ps1` is the reproducible isolated runner. Its generated `exit_codes.json` records each Java case exit code.
- The focused run `acceptance_20261013_220748` passed all seven cases with exit code 0: train, Local, Edge, Cloud, timeout fallback, malformed-response fallback, and zero-deadline.
- Timeout and malformed-response fallback both selected Edge, recorded the injected reason, executed the Edge module, sent no `outcome`, reported `orphaned_tasks=0`, received `shutdown_ack`, and exited Python with code 0.
- The zero-deadline case completed normally with measured latency `3.51 ms`, configured deadline `0 ms`, `deadline_met=false`, a valid completed outcome, and clean shutdown.
- The validator now rejects duplicate decisions/outcomes, uncorrelated outcome sends, non-terminal normal outcomes, and non-boolean deadline flags.
- The strengthened validator was rerun against the retained `acceptance_20261013_220748` artifacts: standard, timeout fallback, malformed fallback, and deadline suites all exited 0. No simulator rerun was needed because only validation logic and documentation changed in this follow-up.
- `compare_policies.py` provides a reproducible one-task comparison artifact from existing traces: RL train chose Local with 3.51 ms and 0 bytes; deterministic Local matched 3.51 ms and 0 bytes; Edge measured 7.3028571428571425 ms and 14,000 bytes; Cloud measured 97.68580357142858 ms and 28,000 bytes. These are preliminary integration measurements, not a superiority result.

## Not verified

- The fault tests are safe adapter-boundary simulations, injected before observation transmission. A live Python action cannot be discarded and then shut down with zero orphans: the RL service retains an observation as pending until it receives an outcome. Sending that outcome for an invalid action would violate the fallback contract.
- Task failure behavior remains unverified. The current experiment only has a successful result endpoint and does not add failure semantics to generic iFogSim behavior; no failure status or fabricated measurements were added.
- Multi-task mode remains intentionally unsupported. The Java registry is a single-task record, terminal handling shuts down Python after that task, and shared tuple hooks are not yet keyed by a task-record map; adding a task count would risk duplicate shutdowns and cross-task byte attribution.
- Native task failure remains deferred. The inspected iFogSim tuple path has no failure transition or failure result event; adding one would be experiment semantics rather than an observed simulator behavior.
- Energy is intentionally sent as `null`; cumulative device energy is not a per-task measurement under the contract.

No claim above treats configured latency, task size, deadline, or static topology values as measured performance results.