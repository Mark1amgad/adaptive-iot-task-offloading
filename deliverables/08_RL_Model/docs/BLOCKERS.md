# 10. Verified facts, assumptions, untested integration, blockers

## Verified (by running / tests in this workspace)
* 185 pytest tests pass (see README for the command and result). Includes a real-subprocess protocol test.
* Update rule, terminal handling, mask handling, frozen evaluation, persistence/compatibility, checkpoints, protocol validation, reproducibility (same seed ⇒ identical Q-table and action sequence; save/resume ⇒ identical to uninterrupted run), aggregation arithmetic, train/test separation checks.
* Default config yields exactly 54 states.

## Implementation assumptions (changeable in config)
* Contextual-bandit decision model, γ = 0 (STATE_SPEC 2.3).
* Feature set and the *from design note* thresholds (latency 20/80 ms, edge utilisation 0.4/0.8). Boundary rule `[t_i, t_{i+1})`.
* Reward weights 1 / 2 / 0.5, latency clip 1, cost = bandwidth + energy with placeholder reference values, failure penalty 0.
* Unvisited-state fallback order Edge → Cloud → Local; frozen policy ignores never-tried actions.
* ε: 0.3 → 0.02 linearly over 16000 training decisions; α = 0.1; q_init = 0 (optimistic because rewards ≤ 0).

## NOT tested (needs iFogSim)
* Everything on the Java side; real latency/overhead of the stdin/stdout round trip per task.
* That iFogSim can supply each observation field *before* the decision and each outcome field after it.
* Behaviour with overlapping/concurrent decisions in the real simulator (the Python side supports it via `task_id`).

## Blockers / decisions (owner)
| # | Item | Owner | Dependency |
|---|---|---|---|
| B1 | Calibrate `task_mi` and `deadline_ms` thresholds (placeholders) | Java dev + team | workload definition |
| B2 | Confirm source/units/timing of all features and metrics (placeholders marked `TO CONFIRM`) | Java dev | questionnaire Q4–Q9 |
| B3 | Calibrate `latency_ref_ms`, cost reference values and weights; decide whether energy/monetary cost count | team | simulator output ranges |
| B4 | Decide bandit vs sequential (needs a defined next decision point) | Java dev + team | Q10 |
| B5 | Decide default Java-side fallback and timeout when Python errors | Java dev | Q3 |
| B6 | Include `device_utilization` and/or network load? (state size 54 → 162) | team | Q7 |
| B7 | Set `epsilon_decay_steps` from real tasks per run; choose number of train/test seeds | team | Q1 |
| B8 | End-to-end iFogSim test (below) | Java dev | all of the above |

## End-to-end test required once iFogSim is available
1. Run one short simulation (`phase="dev"`) in each mode; assert every task gets exactly one `action` and one `outcome_ack`, `orphaned_tasks = 0`.
2. Replay the captured Java→Python lines through the Python server and confirm identical replies (determinism with fixed `--seed`).
3. Check `deadline_flag_inconsistent` and `action_override` never appear in `logs/events_*.jsonl`.
4. Confirm a frozen eval run leaves the model file byte-identical.
5. Run the train → test → `aggregate` pipeline on a tiny seed set and check the metrics against iFogSim's own totals (task count, mean latency).
