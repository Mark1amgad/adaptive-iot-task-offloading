# rl_model — Tabular Q-Learning task offloading (Local / Edge / Cloud)

Python component for *Adaptive AI-Based Task Offloading in IoT Edge-Cloud Networks Under Dynamic Conditions*. Tabular Q-learning with ε-greedy only (no deep RL). A persistent Python process serves decisions to the Java/iFogSim simulation over JSON lines and learns **only from real simulator outcomes**.

> **Status.** Python side: implemented and unit/integration-tested with scripted messages. **Java/iFogSim side: not verified** (no simulator code was available). **No experiment results exist yet** and none are included; thresholds marked *placeholder* must be calibrated (`docs/BLOCKERS.md`).

## Layout
```
config/default.json     state features/thresholds, reward, agent hyper-parameters, seeds
src/rl_model/           state.py actions.py reward.py agent.py persistence.py protocol.py server.py
                        aggregate.py train_offline.py run_plan.py config.py logging_utils.py
schemas/ examples/      JSON Schemas (observation, action, outcome) + valid example messages
tests/                  185 tests (synthetic fixtures live ONLY here)
docs/                   AUDIT, STATE_SPEC (state+reward+decision model), PROTOCOL, WORKFLOWS,
                        JAVA_QUESTIONNAIRE, BLOCKERS
legacy/                 the original toy script, unchanged (invented simulator; not evidence)
artifacts/ logs/        models/checkpoints and run logs are written here
```

## Install and test
```bash
cd rl_model
pip install -r requirements.txt          # runtime needs only the standard library; pytest/jsonschema for tests
python -m pytest -q                      # last run in this workspace: 185 passed
```

## Run
```bash
export PYTHONPATH=src                    # or: pip install -e .
python -m rl_model.server --mode train    --model-out artifacts/model.json                    # learn + epsilon-greedy
python -m rl_model.server --mode eval     --model-in  artifacts/model.json                    # frozen greedy, no updates
python -m rl_model.server --mode baseline --policy edge                                       # local|edge|cloud|random
python -m rl_model.run_plan --train-seeds 1 2 3 --test-seeds 101 102 103                      # exact commands, seed separation
python -m rl_model.aggregate logs/run_*.jsonl --train-seeds 1 2 3                             # comparison table from real logs
python -m rl_model.train_offline logs/run_train-*.jsonl --out artifacts/model_offline.json    # optional replay
# Try the protocol by hand (stdout is JSON only):
python -m rl_model.server --mode train --log-dir /tmp/l --artifacts-dir /tmp/a < examples/session.jsonl
```
Useful flags: `--config`, `--seed` (agent RNG), `--allow-reward-mismatch`. Everything else is in `config/default.json`.

## Key design points
* **State**: 4 discretised pre-decision features → **54 states** (derived, not assumed). **Reward**: `−(w1·norm latency + w2·deadline miss + w3·resource cost)`. **Decision model**: contextual bandit by default (γ=0); the full `r + γ·max Q(s',:)` rule with terminal handling is implemented and tested for sequential mode. See `docs/STATE_SPEC.md`.
* **Protocol**: `observation` (before) / `action` / `outcome` (after) are separate messages; observations reject any unknown/post-execution field. See `docs/PROTOCOL.md`.
* **Reproducibility**: every random draw comes from a seeded RNG whose state is saved in the model, so resume == uninterrupted run.
* **Persistence**: atomic JSON write; loading validates format version, action set, state-spec fingerprint, table shape, finiteness, and (unless overridden) the reward fingerprint.
