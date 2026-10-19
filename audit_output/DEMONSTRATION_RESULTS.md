# Reproducible model demonstration

Command executed from repository root (Python 3.11.4, standard library only):

```text
$env:PYTHONPATH = <repo>/team-work/Ayoub/rl_model/rl_model/src
Get-Content -Raw team-work/Ayoub/rl_model/rl_model/examples/session.jsonl |
  <python> -m rl_model.server --mode train \
    --config team-work/Ayoub/rl_model/rl_model/config/default.json \
    --log-dir audit_output/demo_logs --artifacts-dir audit_output/demo_artifacts \
    --model-out audit_output/demo_artifacts/demo_model.json
```

Observed result: the supplied `hello` returned 54 states, three actions, contextual-bandit mode, and placeholder features `task_mi` and `deadline_ms`. The supplied observation encoded to state 26. With the fixed seed, the training policy selected Local through exploration (`epsilon=0.3`). The supplied outcome reported that Edge, rather than the chosen Local action, was executed; the server logged the override and updated the Q entry for Edge. It acknowledged reward `-0.24445`, update count 1, saved `audit_output/demo_artifacts/demo_model.json`, and shut down with zero orphaned tasks.

The session inputs are repository examples with scripted values. This proves Python protocol, update, and persistence behavior only; it does not demonstrate iFogSim integration or comparative performance.

Additional observed checks:

- `python -m compileall -q team-work/Ayoub/rl_model/rl_model/src`: exit 0.
- Import/config smoke check: default state-space count 54 and the example feature vector encoded to index 26; exit 0.
