# Final audit report

## Executive summary

Paths audited: `team-work/Mostafa/Dataset` and `team-work/Ayoub/rl_model/rl_model`. Git branch: `main`; pre-existing unrelated modifications were present in `team-work/Astta-Abdo/adaptive_offloading/adaptive_offloading.py` and `test.py` and were not touched. No repository instruction (`AGENTS.md`) was found.

The dataset package contains useful research documentation plus local UCI execution-time and EUA context data, but no locally complete empirical Local/Edge/Cloud task-offloading dataset. The UCI dataset's official page was checked and confirms 4,000 two-field turnaround-time records and CC BY 4.0. The RL component is a substantially implemented tabular contextual-bandit service with a clear protocol and safeguards, but it has no Java/iFogSim client or genuine simulator evidence. It is code-ready for a controlled bridge implementation, not research-evaluation ready.

## Dataset

See `DATASET_AUDIT.md`, `DATASET_FILE_INVENTORY.csv`, `DATASET_QUALITY_REPORT.csv`, `DATASET_SUMMARY.csv`, and `UCI_DEVICE_STATISTICS.csv`. All CSV/TSV data files were fully parsed. Exact summary values are generated from source files rather than copied from documentation.

## Model and tests

See `RL_MODEL_AUDIT.md` and `TEST_RESULTS.md`. The test suite could not be executed because a compliant isolated environment could not be created; that is an environment blocker, not a pass/fail claim. The supplied JSONL session did complete one scripted update and persistence cycle; see `DEMONSTRATION_RESULTS.md`; it is not simulator evidence.

## Fair experiment design

Compare Local-only, Edge-only, Cloud-only, and frozen adaptive policy using identical generated workload traces, topology/dynamic-condition schedules, and simulator seeds. Record: end-to-end latency in ms (task creation to result at device), deadline violation rate (failed or deadline missed / all tasks), completion rate (completed / all), bandwidth bytes/task, node utilization (defined sampling/aggregation), and energy J/task only if the model truly supplies it. Run repeated distinct test seeds, separate training seeds, and never compare a learning policy while it is updating in test.

## Priority next steps

1. Reconcile and implement one canonical Java/Python protocol and prove a single task’s selected action changes iFogSim routing.
2. Document/measure every state and reward metric’s units, endpoint, timing, and availability.
3. Obtain supervisor approval for contextual bandit versus MDP, workload/deadline assumptions, and reward calibration.
4. Install a normal CPython environment, run the complete pytest suite, and retain its actual output.
5. Implement matched fixed baselines and repeated-seed simulator experiments before any performance conclusion.
