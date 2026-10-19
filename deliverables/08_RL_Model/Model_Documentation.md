# RL Model Documentation

## Implementation

The copied Python implementation is a tabular Q-learning agent exposed through a persistent JSONL service. The default configuration identifies the decision model as `contextual_bandit` and sets `gamma=0.0`; therefore the accepted integration should not be described as a validated sequential MDP result. The sequential update branch exists in code and is tested, but it is not what the accepted one-task run demonstrates.

## State and Actions

The enabled state has four discretized features: `task_mi`, `wan_latency_ms`, `edge_utilization`, and `deadline_ms`. Their configured thresholds produce 54 states. `device_utilization` is present in configuration but disabled. Several thresholds are explicitly marked placeholder or design-derived and require calibration.

The action set is exactly `Local` (0), `Edge` (1), and `Cloud` (2). Baseline mode can select a fixed policy; train mode uses seeded epsilon-greedy decisions; eval mode loads a saved model and freezes updates.

## Training Configuration

The copied default configuration contains `alpha=0.1`, `gamma=0.0`, epsilon start/end `0.3/0.02`, decay over 16,000 decisions, `q_init=0.0`, agent seed `1`, fallback order Edge/Cloud/Local, and reward weights `w_latency=1.0`, `w_deadline=2.0`, `w_cost=0.5`. Cost reference values and several thresholds are marked placeholders in the source configuration; they are not presented as calibrated research settings.

The accepted Java run overrides the service seed to `123` and uses train mode. The saved artifact records one decision and one update.

## Persistence and Loading

`persistence.py` saves an atomic JSON model containing format version, kind, actions, state and reward fingerprints, agent configuration, counters, Q-table, visit table, and RNG state. Loading validates these fields, table shape, numeric values, action set, state fingerprint, and reward fingerprint unless an explicit mismatch override is supplied.

The accepted artifact `Saved_Models/python_model.json` has `kind=tabular_q_learning`, format version `1`, model version `q1-493627d1-u1`, a 54×3 Q-table, one update, one decision, and one visited/nonzero entry. It is a loadable saved model state/checkpoint produced after one training outcome. It is not a final trained policy and has not been validated for generalization or performance superiority.

## Service and Protocol

`server.py` starts with `python -m rl_model.server`. It accepts `hello`, `observation`, `outcome`, `save`, and `shutdown` JSONL messages. Observations create pending task decisions keyed by task ID; outcomes remove them and update the model in train mode. The integration trace proves this lifecycle for one real task.