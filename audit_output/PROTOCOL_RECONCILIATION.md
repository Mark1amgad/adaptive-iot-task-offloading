# Protocol reconciliation for the first Java/Python test

## Evidence and recommendation

This comparison covers the root draft (`integration/protocol/agent-message-schema.json` and `docs/integration-contract.md`), the implemented Python service (`team-work/Ayoub/rl_model/rl_model/src/rl_model/{protocol.py,server.py}`), its three schemas, its JSONL example, and `docs/PROTOCOL.md`.

**Recommendation:** use the implemented `rl_model` JSON Lines protocol v1.0 as the canonical protocol for the first test. It is the only protocol that a server currently parses, validates, logs, and uses for learning. The root schema is explicitly a draft and cannot represent hello, outcomes, acknowledgements, errors, or the implemented field names. This is a recommendation only: this audit does not modify either protocol, schema, model behavior, or scientific assumptions.

Transport is one UTF-8 JSON object per newline over a single persistent Python subprocess. Lines may not exceed 1,000,000 UTF-8 bytes. Python stdout is protocol-only; Java must drain stderr. Requests and replies are synchronous and ordered.

## Draft versus implemented differences

| Concern | Root draft | Implemented Python service | Reconciliation |
|---|---|---|---|
| Framing | undecided | persistent stdin/stdout JSONL | use implemented JSONL |
| Version/type | absent | `protocol_version: "1.0"`, `type` required for all meaningful messages | add them Java-side |
| State values | `task_size`, `network_latency`, categorical values allowed | numeric `task_mi`, `wan_latency_ms`, `edge_utilization`, `deadline_ms` | use model names/units; do not send categorical bands |
| Deadline | `deadline_category` | raw relative `deadline_ms` | use raw milliseconds; Python bins it |
| Request/action | only request and action | hello, observation, action, outcome, acknowledgements, save/shutdown, errors, ping/pong | implement the full lifecycle below |
| Outcome feedback | absent | explicit post-execution outcome linked by `task_id` | required for training/logging |
| Action identity | action name only | action name plus `action_id` 0/1/2 and model metadata | Java must verify both name/id correspondence |
| Timeout/fallback | stated but unspecified | Java-side policy remains TO CONFIRM | record fallback separately; do not report it as agent-selected |

## Implemented message types and fields

### Java -> Python

| Type | Required fields | Optional fields / constraints |
|---|---|---|
| `ping` | `type: "ping"` | no version check in dispatcher; reply is `pong` |
| `hello` | `protocol_version: "1.0"`; `type: "hello"`; `run_id` matching `[A-Za-z0-9._-]{1,64}`; `phase` in `train`, `test`, `dev` | `sim_seed`: integer or null; `simulator`: object. Must occur once before observation/outcome/save/shutdown. Training mode allows train/dev; eval/baseline allows test/dev. |
| `observation` | version; `type: "observation"`; non-empty `task_id` <=128 chars; `features` | `available_actions`: non-empty unique names (`Local`, `Edge`, `Cloud`) or ids (0,1,2); omitted means all. `sim_time_ms`: finite number >=0, informational. Observation accepts enabled features only. |
| `outcome` | version; `type: "outcome"`; task id; `action_executed` (`Local`/`Edge`/`Cloud`); `status` (`completed`/`failed`); boolean `deadline_met`; object `resource_metrics` | completed outcomes require finite `latency_ms >=0`; failed outcome cannot have `deadline_met=true` and may omit/null latency. Optional `failure_reason` is only for failed; `terminal` defaults true; optional `next_observation` only with `terminal=false`; `sim_time_ms >=0`. Metric values are finite >=0 or null; `executing_node_utilization` is <=1. |
| `save` | actual implementation dispatches only on `type: "save"` after hello | training mode only. Documentation says all messages include the version, but `server.py` does not call a validator for save. Java should still send `protocol_version:"1.0"` for the canonical contract. |
| `shutdown` | actual implementation dispatches only on `type: "shutdown"` after hello | server reports orphaned pending tasks and exits. Java should still send version 1.0; the implementation currently does not validate it. |

### Python -> Java

| Type | Required / emitted fields | Meaning |
|---|---|---|
| `pong` | version, `type: "pong"` | reply to ping |
| `hello_ack` | version, type, `model_version`, mode, policy, `updates_enabled`, `state_count`, actions, features, placeholder_features, decision_model | validates the model/session capabilities before tasks are sent |
| `action` | version; type; task_id; `action_id` 0/1/2; `action` Local/Edge/Cloud; `model_version`; state_index; mode; epsilon; 3 `q_values` | placement request for the exact task id |
| `outcome_ack` | version; type; task_id; `updated`; reward; model_version; update_count | confirmation of accepted outcome and any training update |
| `saved` | version; type; path; model_version | training-model save acknowledgement |
| `shutdown_ack` | version; type; orphaned_tasks; model_path; model_version; tasks_reported | final session accounting |
| `error` | version; type; code; message; fatal; optional task_id | see failure behavior below |

## Canonical state fields

All values must be known *before* task placement and be finite. The default state is 54 bins over these four numeric features:

| Field | Type / constraint | Unit and timing | Status |
|---|---|---|---|
| `task_mi` | number >=0 | million instructions, known at task creation | threshold placeholder |
| `wan_latency_ms` | number >=0 | ms to Cloud, configured or measured before decision; freshness must be recorded | design assumption |
| `edge_utilization` | number in [0,1] | fraction of edge MIPS in use at decision time | source/timing unverified |
| `deadline_ms` | number >=0 | relative deadline from task creation | threshold placeholder |
| `device_utilization` | number in [0,1], disabled by default | originating device CPU fraction | not encoded unless configuration changes |

Do not substitute bytes/MB for `task_mi`, percentages for utilization, or `Tight`/`Relaxed` for `deadline_ms`. Do not place latency/result fields in observations.

## Valid first-test messages

The numeric values below are **protocol fixtures only**, not measured simulator values.

Observation Java sends after hello and before routing:

```json
{"protocol_version":"1.0","type":"observation","task_id":"run-001-task-0001","sim_time_ms":0.0,"features":{"task_mi":2500,"wan_latency_ms":45.0,"edge_utilization":0.62,"deadline_ms":400},"available_actions":["Local","Edge","Cloud"]}
```

Representative action response Java must validate and apply:

```json
{"protocol_version":"1.0","type":"action","task_id":"run-001-task-0001","action_id":1,"action":"Edge","model_version":"q1-<statehash>-u0","state_index":26,"mode":"explore","epsilon":0.3,"q_values":[0.0,0.0,0.0]}
```

Example completed outcome after actual execution (numbers are illustrative only):

```json
{"protocol_version":"1.0","type":"outcome","task_id":"run-001-task-0001","action_executed":"Edge","status":"completed","latency_ms":212.4,"deadline_met":true,"resource_metrics":{"bandwidth_bytes":48200,"energy_joules":0.8,"executing_node_utilization":0.71},"terminal":true,"sim_time_ms":212.4}
```

For the default contextual-bandit configuration, use `terminal:true`; do not introduce `next_observation` or change gamma as part of integration.

## Error, timeout, and fallback behavior

The Python server returns nonfatal `error` messages for malformed JSON/messages, invalid observations/outcomes, duplicate task ids, unknown/duplicate outcomes, handshake order errors, and disallowed save. Protocol-version and mode/phase mismatch errors are fatal and end with exit code 2 for messages whose parsers check version (`hello`, `observation`, and `outcome`). `save`/`shutdown` are a small implementation/documentation validation gap noted above; Java should nevertheless always send version 1.0. An invalid outcome leaves the task pending so Java may send a corrected outcome.

The Java timeout duration and fallback placement are not implemented or specified in this repository. For the first test, Java must define them before execution and emit an auditable Java-side trace with `decision_source` (`agent`, `fallback_timeout`, or `fallback_error`). If no valid `action` response arrives, Java may execute the approved fallback but **must not send an `outcome` for that task to the Python server**: Python has no pending agent decision, and reporting it would either be rejected as `unknown_task` or risk contaminating learning. If Python did send an action and Java later overrides it because a target is unavailable, Java may send the truth in `action_executed`; the server logs `action_override` and learns from the executed action. That override must be retained in the Java trace.

## Small implementation gap (not changed)

`server.py` dispatches `save` and `shutdown` directly without parsing their version or rejecting extra fields, unlike hello/observation/outcome. This does not change the RL algorithm or block the first test, but it is an unambiguous protocol-consistency issue. The smallest future fix is to add tiny validators that call `check_version` and enforce the expected key set before `_on_save` and `_on_shutdown`; add corresponding tests. It is intentionally not applied in this documentation-first pass.

## Unresolved decisions

1. Confirm exact Java/iFogSim sources and APIs for task routing and post-execution measurement.
2. Define the semantic endpoints of `latency_ms`, the links counted in `bandwidth_bytes`, energy model, and utilization sampling moment.
3. Calibrate `task_mi`/`deadline_ms` bins and reward references/weights; these are not changed here.
4. Choose a timeout, Java fallback, and action-availability mask source.
5. Decide whether the root draft is retired or updated after the first verified trace; coordinate that shared-file change separately.
