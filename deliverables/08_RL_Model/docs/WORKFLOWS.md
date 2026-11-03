# 6. Training and evaluation workflows

No results are included in this repository: every number must come from run logs written while **iFogSim** executed tasks. Test fixtures with synthetic outcomes exist only inside `tests/`.

## 6.1 Workflow
1. `python -m rl_model.run_plan --train-seeds 1 2 3 4 5 --test-seeds 101 102 103 104 105` prints the exact server command and the `run_id`/`phase`/`sim_seed` for each run. Overlapping or duplicate seeds are refused.
2. **Train** (`--mode train`, `hello.phase="train"`): one iFogSim run per train seed; the model is chained (`--model-in` previous, `--model-out` next). ε-schedule and counters persist across runs.
3. **Test** (frozen / fixed policies, `hello.phase="test"`), *same* `sim_seed` set for every policy so results are paired: Local-only, Edge-only, Cloud-only (`--mode baseline --policy ...`) and trained Q-learning (`--mode eval --model-in <final model>`). Eval never updates and never writes the model.
4. `python -m rl_model.aggregate logs/run_*.jsonl --train-seeds <train seeds>` → `artifacts/evaluation.md/json`.

Every run writes `logs/run_<run_id>.jsonl` (`run_start`, one `task` record per reported outcome with the raw observation/outcome/reward, `run_end`) and `logs/events_<run_id>.jsonl` (structured events). Checkpoints: `artifacts/checkpoints/`.

## 6.2 Metric definitions (per run, then across seeds)
| Metric | Definition |
|---|---|
| Completion rate | completed tasks / all reported tasks |
| Avg end-to-end latency | mean `latency_ms` over **completed** tasks (failed tasks have no valid latency; they are counted in the two rates) |
| Deadline violation rate | (deadline missed **or** failed) / all tasks |
| Resource utilisation | mean `executing_node_utilization` over tasks that report it (definition **TO CONFIRM**) |
| Bandwidth consumption | mean `bandwidth_bytes` per task |
| Also reported | mean energy (if provided), mean reward (depends on config weights — compare physical metrics first) |

Aggregation: one value per run → mean, sample std (ddof 1) and 95 % CI (Student *t*, table verified against SciPy in tests) across seeds. Tasks never reported (orphans) are not counted — they are logged as `orphaned_tasks` and should be zero.

## 6.3 Train/test separation and failure handling (enforced in code)
* train seeds ∩ test seeds = ∅ (`run_plan` refuses; `aggregate` refuses when a test `sim_seed` equals a train `sim_seed`, or a test run has none).
* A Q-learning test run with updates enabled is rejected; only `phase="test"` runs are compared; policies evaluated on different seed sets get a warning; duplicate seeds per policy are an error.
* `train_offline` refuses test-phase logs.
* Failed tasks: reward uses the failure rule (STATE_SPEC 2.2); metrics as above. Invalid outcomes are rejected without learning.

## 6.4 Optional: offline replay
`python -m rl_model.train_offline logs/run_train-*.jsonl --out artifacts/model_offline.json` re-trains from logged real transitions, e.g. under a different reward weighting without re-running iFogSim. Q-learning is off-policy so any behaviour policy's log is usable, but unseen (state, action) pairs stay at their initial value; fixed-policy logs cover one action per state only. Collect exploratory data (train mode or `--policy random`).

## 6.5 Statistical caveats
Choose the number of seeds before looking at results; with few seeds the CI is wide. Q-table sample efficiency: 54 states × 3 actions need on the order of hundreds–thousands of tasks; the ε-decay length (`epsilon_decay_steps`) must be set from the real number of tasks per run.
