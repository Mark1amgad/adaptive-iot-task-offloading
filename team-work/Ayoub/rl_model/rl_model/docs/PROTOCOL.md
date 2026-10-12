# 5. Java ↔ Python JSON-lines protocol, version 1.0

> **Status: implemented and tested on the Python side only** (scripted JSON lines over a real subprocess, `tests/test_server.py::test_protocol_integration_over_stdio`). **Not verified against iFogSim.** Every field marked `TO CONFIRM` needs the Java developer. No iFogSim API is assumed anywhere in this repo.

Schemas: `schemas/observation.schema.json`, `action.schema.json`, `outcome.schema.json` (JSON Schema 2020-12). Valid examples: `examples/*.json`, replayable session: `examples/session.jsonl`.

## 5.1 Transport and framing
* Java starts **one persistent Python process** per simulation run and talks over its **stdin/stdout**.
* One JSON object per line, UTF-8, terminated by `\n`, no embedded newlines (compact JSON), max 1,000,000 bytes/line. Blank lines are ignored.
* **stdout carries only protocol messages.** Logs go to files (`logs/`) and warnings to stderr; Java should drain stderr to avoid a full pipe.
* Request/response is **synchronous per message**: every Java line gets exactly one reply line, in order. Java must flush after each line. `NaN`/`Infinity` are invalid JSON and are rejected.
* Every message has `protocol_version` (`"1.0"`) and `type`. A version mismatch is fatal (error, then exit code 2).

## 5.2 Process lifecycle
```
Java                                         Python (python -m rl_model.server --mode ... )
 | start process (args choose mode)  ------>  loads config (+ model), validates compatibility
 | hello {run_id, phase, sim_seed}   ------>
 |                                   <------  hello_ack {model_version, state_count, features, placeholder_features, updates_enabled,...}
 | observation {task_id, features}   ------>  (state encoded, action chosen, decision stored)
 |                                   <------  action {task_id, action_id, action, model_version, ...}
 |   ... Java applies the action, simulates, MEASURES the result ...
 | outcome {task_id, action_executed, ...} ->  (reward computed, Q updated if mode=train)
 |                                   <------  outcome_ack {reward, updated, update_count}
 | save            (train only, optional) -->  <-- saved {path}
 | shutdown                           ------>  <-- shutdown_ack {orphaned_tasks, model_path}; process exits 0
```
* `hello` must be the first message (except `ping`→`pong`). Startup failure prints one `error` line (`startup_failed`, fatal) and exits 2.
* On **stdin EOF** (Java died/closed): the model is saved (train mode) and the process exits 0.
* Modes (CLI): `--mode train` (ε-greedy + updates), `--mode eval --model-in M` (frozen greedy, no updates), `--mode baseline --policy local|edge|cloud|random` (fixed policy, no learning; `random` is for data collection). `hello.phase` must agree: train↔`train`/`dev`; eval/baseline↔`test`/`dev`; otherwise fatal `phase_mode_mismatch` (this protects train/test separation).

## 5.3 When Java must apply the action
1. Java sends an `observation` **before** dispatching the task and **must not** start/place the task until the `action` reply for the same `task_id` arrives.
2. On receipt Java **must execute that action** (Local/Edge/Cloud) for that task. If Java cannot (e.g. resource gone) it executes something else and reports the truth in `outcome.action_executed`; the agent then learns the executed action and logs a warning.
3. Java sends the `outcome` **after the task finished or failed** (measured values only). Until then the decision is *pending* in Python. Several tasks may be pending concurrently; match by `task_id` (unique per run).
4. Java-side fallback if no `action` arrives within a timeout, or on error replies to an observation: Java must pick a documented default (e.g. the experiment's static policy) and **not** send an outcome for that task. *Timeout value and fallback: TO CONFIRM.*

## 5.4 Messages

### Observation (Java → Python) — before the decision
```json
{"protocol_version":"1.0","type":"observation","task_id":"t-000123","sim_time_ms":15234.5,
 "features":{"task_mi":2500,"wan_latency_ms":45.0,"edge_utilization":0.62,"deadline_ms":400},
 "available_actions":["Local","Edge","Cloud"]}
```
`features` must contain exactly the enabled state features with the units in STATE_SPEC; anything else (including any post-execution value) is rejected `invalid_observation`. `available_actions` optional (names or ids 0/1/2; omitted = all). `sim_time_ms` informational only.

### Action response (Python → Java)
```json
{"protocol_version":"1.0","type":"action","task_id":"t-000123","action_id":1,"action":"Edge",
 "model_version":"q1-3f9a1c2e-u417","state_index":21,"mode":"exploit","epsilon":0.12,"q_values":[-0.8,-0.31,-0.52]}
```
Required: `task_id`, `action_id` (0 Local, 1 Edge, 2 Cloud), `action`, `model_version`. `mode` ∈ explore/exploit/greedy/fallback/baseline. `model_version` = `q1-<state-spec hash>-u<updates so far>`. (Values in the examples are illustrative.)

### Outcome (Java → Python) — after execution; separate from observations
Completed:
```json
{"protocol_version":"1.0","type":"outcome","task_id":"t-000123","action_executed":"Edge","status":"completed",
 "latency_ms":212.4,"deadline_met":true,
 "resource_metrics":{"bandwidth_bytes":48200,"energy_joules":0.8,"executing_node_utilization":0.71},
 "terminal":true,"sim_time_ms":15446.9}
```
Failed:
```json
{"protocol_version":"1.0","type":"outcome","task_id":"t-000124","action_executed":"Cloud","status":"failed",
 "failure_reason":"timeout","latency_ms":null,"deadline_met":false,"resource_metrics":{"bandwidth_bytes":48200},"terminal":true}
```
Rules: `latency_ms` required (and ≥ 0) when completed, may be null/absent when failed; failed ⇒ `deadline_met=false`; `resource_metrics` values are ≥ 0 numbers or null; `executing_node_utilization` ∈ [0,1]; metrics required by the reward config (`bandwidth_bytes` by default) must be present for completed tasks. `terminal` defaults to true. For the optional sequential mode: `"terminal":false` plus `"next_observation":{"features":{...},"available_actions":[...]}`; in `contextual_bandit` mode the next state is ignored (logged as a warning).
Units/definitions for `latency_ms` (creation→result back at the device?), `bandwidth_bytes` (which links?), `energy_joules`, `executing_node_utilization` are **TO CONFIRM**.

### Other messages
`hello` `{"protocol_version":"1.0","type":"hello","run_id":"train-q-seed1","phase":"train","sim_seed":1,"simulator":{"name":"iFogSim","version":"TO CONFIRM"}}` · `hello_ack` · `outcome_ack {task_id, updated, reward, model_version, update_count}` · `save`→`saved` · `shutdown`→`shutdown_ack` · `ping`→`pong` · `error`.

## 5.5 Errors
`{"protocol_version":"1.0","type":"error","code":"...","message":"...","task_id":"..."(optional),"fatal":false}`
The session continues after non-fatal errors; **an error never changes the Q-table.**

| code | cause | Java should |
|---|---|---|
| `invalid_json`, `line_too_long`, `invalid_message`, `unknown_type` | framing/schema problem | fix the sender; apply fallback policy for that task |
| `invalid_observation` | bad/missing/out-of-range feature, bad mask | fallback policy for the task; log |
| `invalid_outcome` | inconsistent outcome or missing required metric | resend a corrected outcome (the decision stays pending) |
| `duplicate_task` | `task_id` already pending | use unique ids |
| `unknown_task` / `duplicate_outcome` | no pending decision / already reported | do not resend |
| `handshake_required` / `duplicate_hello` | order violation | send `hello` once, first |
| `not_allowed` | `save` outside train mode | — |
| `internal_error` | bug in Python | report; the process keeps running |
| `protocol_version_mismatch`, `phase_mode_mismatch`, `startup_failed` (**fatal**, exit 2) | config/lifecycle error | stop the run, fix, restart |

Tasks still pending at shutdown are reported as `orphaned_tasks` and never learned from.

## 5.6 Minimal Java-side shape (illustrative, **not** tested, contains no iFogSim API)
```java
ProcessBuilder pb = new ProcessBuilder("python", "-m", "rl_model.server",
    "--config", "config/default.json", "--mode", "train", "--model-out", "artifacts/model.json");
pb.environment().put("PYTHONPATH", "src");
Process p = pb.start();                                   // stderr: drain in a thread
BufferedWriter in  = new BufferedWriter(new OutputStreamWriter(p.getOutputStream(), UTF_8));
BufferedReader out = new BufferedReader(new InputStreamReader(p.getInputStream(), UTF_8));
// rpc(line): in.write(line); in.write('\n'); in.flush(); return out.readLine();
// Build/parse JSON with whichever JSON library the project already uses (TO CONFIRM).
```
