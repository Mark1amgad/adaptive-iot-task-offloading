# Results Analysis

## Evidence Source

All values below come from the preserved run `audit_output/integration_prototype/runs/acceptance_20261013_220748/`. The copied JSONL traces and `policy_comparison.json` are not edited. The comparison was cross-checked against each original trace's decision, execution, terminal, and acceptance records.

| Case | Actual decision/execution | Latency | Deadline | Counted task bytes | Acceptance |
| --- | --- | ---: | --- | ---: | --- |
| RL train | Local / Local device `local#5` | 3.51 ms | Met | 0 | PASS |
| Local baseline | Local / Local device `local#5` | 3.51 ms | Met | 0 | PASS |
| Edge baseline | Edge / Edge device `edge#4` | 7.3028571428571425 ms | Met | 14,000 | PASS |
| Cloud baseline | Cloud / Cloud device `cloud#3` | 97.68580357142858 ms | Met | 28,000 | PASS |

The preserved `exit_codes.json` records `0` for the train, Local, Edge, Cloud, timeout fallback, malformed fallback, and deadline-miss cases in the accepted focused run.

## Interpretation

The RL row proves that a real Python action controlled actual iFogSim execution and that the resulting task outcome was returned to Python. The deterministic baseline rows provide route-specific integration references under the same configured task parameters. The observed route, latency, deadline flag, and counted bytes are credible measurements for these individual simulation runs.

The data do not prove that the RL policy is better than any baseline. There is one run per case, no repeated seeds, no confidence intervals, and no independent evaluation phase. The RL train action happened to select Local in this accepted run; that is an integration observation, not a policy-performance conclusion.

The Local zero-byte value means no bytes were counted on the documented instrumented parent-child links for that task. It does not mean the whole simulator or Python process exchanged no data.
