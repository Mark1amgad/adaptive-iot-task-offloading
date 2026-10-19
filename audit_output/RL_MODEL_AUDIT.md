# RL model audit

## Actual implementation

`team-work/Ayoub/rl_model/rl_model` is a Python 3.10+ tabular Q-table service. It exposes exactly `Local` (0), `Edge` (1), and `Cloud` (2), reads JSON Lines over stdin/stdout, records a pending decision by task id, and learns only after a separate outcome. The action, observation, and outcome schemas/examples plus unit tests are present. There is no Java/iFogSim source/client in the repository; `simulator/README.md` explicitly says production Java code is not committed.

Default enabled state: `task_mi`, `wan_latency_ms`, `edge_utilization`, `deadline_ms`. Their bin counts 3×3×3×2 yield 54 states. Threshold boundaries use `bisect_right`: a value equal to a threshold enters the higher bin. Inputs must be finite and satisfy declared min/max; unknown features and empty action masks are rejected. Disabled `device_utilization` is accepted only as disabled input and is not encoded.

## Algorithm classification

The default config has `decision_model=contextual_bandit` and `gamma=0.0`; validation requires gamma zero for that mode. Thus its executed update is `Q(s,a) ← Q(s,a)+0.1*(reward-Q(s,a))`, not sequential Q-learning. The general bootstrapped rule exists for `decision_model=sequential`, positive gamma, non-terminal outcomes, and a valid next observation. That configuration needs a scientifically defined next decision point; it is not supplied by the repository. Training is epsilon-greedy (0.30 linearly to 0.02 over 16,000 decisions), while frozen evaluation is greedy with unvisited-state fallback Edge→Cloud→Local.

## Reward

`reward = -(1.0*clipped_latency + 2.0*deadline_miss + 0.5*resource_cost)`. Latency is clipped at 1 after normalizing by fixed 1000 ms; cost is a weighted capped combination of bandwidth (required, reference 1,000,000 bytes) and energy (optional, reference 10 J). Failures use max latency and a deadline miss; failure penalty is 0. All weights, references, task/deadline bins, and fallback order are placeholders or design choices—not calibrated scientific parameters. A completed task without required bandwidth is rejected, so no learning update occurs. There is no obvious arithmetic double count within the implemented reward, but using UCI turnaround time plus simulated communication time would double count if treated as separate components.

## Protocol and integration readiness

The protocol correctly separates pre-decision observation, selected action, and post-execution outcome; it handles malformed messages, duplicate task/outcome IDs, action masks, terminal/next-state conditions, model compatibility, and atomic persistence. However the repository has no verified Java client, no actual routing/action application, no outcome collector, and no iFogSim run log. `latency_ms`, bandwidth scope, energy, node utilization, failure semantics, Python timeout/fallback, and units/timing remain Java-side confirmations. The root `integration/protocol/agent-message-schema.json` is a preliminary draft using different field names from the model protocol, so a single contract must be selected before integration.

## Legacy code

`legacy/toy_prototype_original.py` is a synthetic illustration: it hardcodes an invented `run_task` environment and prints a baseline comparison. It must not be cited as experimental evidence.

## Test audit

The source contains pytest tests for actions, state, reward, agent, protocol, server, persistence, aggregation, and fixtures. This audit could not execute pytest because the workstation had no usable project interpreter and creation of an isolated venv failed (`venvlauncher.exe` missing from the only usable embedded Python distribution). No prior README claim is treated as a result. See `TEST_RESULTS.md`.
