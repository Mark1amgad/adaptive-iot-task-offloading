# Results Analysis

## Evidence source

The retained one-task acceptance run is `audit_output/integration_prototype/runs/acceptance_20261013_220748/`. Its JSONL traces and acceptance records remain unchanged. The derived comparison table is [`policy_comparison_20261013.json`](policy_comparison_20261013.json), with the summarizer in [`compare_policies.py`](compare_policies.py).

| Case | Actual decision/execution | Latency | Deadline | Counted task bytes | Acceptance |
| --- | --- | ---: | --- | ---: | --- |
| RL train | Local / Local device `local#5` | 3.51 ms | Met | 0 | PASS |
| Local baseline | Local / Local device `local#5` | 3.51 ms | Met | 0 | PASS |
| Edge baseline | Edge / Edge device `edge#4` | 7.302857 ms | Met | 14,000 | PASS |
| Cloud baseline | Cloud / Cloud device `cloud#3` | 97.685804 ms | Met | 28,000 | PASS |

The retained `exit_codes.json` records zero exit codes for the train, Local, Edge, Cloud, timeout-fallback, malformed-fallback, and deadline-miss cases in this focused run.

## Interpretation and limits

The RL row shows that a Python action controlled actual iFogSim execution and that the terminal task outcome was returned to Python. The baseline rows provide route-specific integration references for the same configured task.

These are individual one-task simulation measurements. There is one run per case, no repeated seeds, no confidence intervals, and no independent evaluation phase. They do **not** prove adaptive-policy superiority or generalization.

The Local zero-byte value means no bytes were counted on the instrumented parent-child links for that task; it does not mean the entire simulator or Python process exchanged no data.
