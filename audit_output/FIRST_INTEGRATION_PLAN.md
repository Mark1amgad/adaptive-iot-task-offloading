# First genuine Java/Python/iFogSim integration plan

## Current readiness

| Area | Status | Evidence |
|---|---|---|
| Python JSONL service, state validation, action selection, outcome/reward handling, logs and persistence | Implemented; Python-side scripted smoke test verified | `team-work/Ayoub/rl_model/rl_model/src/rl_model`, examples, prior audit demonstration |
| Default decision model | Implemented; scientific settings intentionally unchanged | contextual bandit, gamma 0, default config |
| Root Java/Python draft | Present but unverified and incompatible with implemented messages | `integration/protocol/agent-message-schema.json` |
| iFogSim Java build, topology, routing hook, measurement code, and client | Missing from this repository | no Java files, Maven/Gradle build, JAR, or source tree found; `simulator/README.md` says planned |
| Current placement decision location / applicable iFogSim APIs | Blocked by missing external simulator source | no source code available to inspect |
| Task identity across Java/Python | Present in Python contract, unverified Java-side | `task_id` protocol field and pending map |
| Python process lifecycle | Present in Python docs and server; unverified Java-side | persistent stdin/stdout JSONL service |

## Staged implementation for one task

1. **Obtain and identify the simulator project.** Provide the external repository/commit or copy the project’s build file, task-generation class, placement/orchestrator class, task-completion listener, and topology configuration. Record Java/JDK/iFogSim versions. Do not guess an iFogSim API.
2. **Create a Java integration adapter outside upstream iFogSim.** Start one persistent `python -m rl_model.server` child per simulation run with absolute config/log/model paths. Set `PYTHONPATH` to the model `src` directory; use UTF-8 readers/writers; read stderr continuously; write one JSON line and flush, then read exactly one response line. This design is documented, but Java code does not yet exist.
3. **Handshake.** Send `hello` (`phase:"dev"` for the first single-task test) and require a non-error `hello_ack` advertising protocol 1.0, 54 states, and Local/Edge/Cloud. Abort the test if it is fatal or mismatched.
4. **Create a traceable task.** At the real pre-placement decision hook, assign a run-unique task id such as `run-001-task-0001`. Capture `task_mi`, `wan_latency_ms`, `edge_utilization`, and `deadline_ms` before routing, with their defined units. Persist this Java-side observation trace.
5. **Request a placement.** Send `observation`; validate the returned action’s type, echoed task id, and matching `action_id`/action name. Record `decision_source=agent` and the Python model version.
6. **Apply the real placement.** Map Local/Edge/Cloud to the simulator’s actual task-routing mechanism only after the concrete API is inspected. Verify the final execution destination independently and record `action_executed`; this is the principal missing implementation step.
7. **Measure and send an outcome.** After actual completion/failure, compute the agreed end-to-end latency, deadline result, outcome status, and bandwidth. Send `outcome` with the same task id, actual destination, and only metrics the simulator actually measured. For the default contextual bandit, set `terminal:true`.
8. **Confirm correspondence and preserve trace.** Require matching task id in `outcome_ack`, check `updated:true` for a valid training/dev outcome, then send `save` and `shutdown`. Preserve Java adapter logs, Python `run_*.jsonl`, Python event log, and a simulator record showing selected versus executed destination.

## Timeout and failure path

The Java adapter needs an explicit response deadline (team decision) and a designated fallback. On timeout, malformed response, fatal error, process exit, or action/task-id mismatch: log the event; execute the configured fallback; mark `decision_source` as a fallback reason; and do not send that task’s outcome to Python because no valid pending agent decision exists. If a valid action was received but cannot be executed, send the actual destination as `action_executed` and preserve the override reason in the Java trace.

## Minimal acceptance test

Run exactly one simulation task in `dev`/train mode with a deterministic simulator seed and a documented pre-decision feature vector. The test passes only if all of the following are evidenced by retained logs:

1. Java starts one Python process and receives `hello_ack` without an error.
2. Java sends one valid observation with task id `T`; Python returns one valid action for `T`.
3. The simulator routes that same task according to the received action and records its actual execution destination.
4. Java sends exactly one post-execution outcome for `T` whose `action_executed` equals the measured destination.
5. Python replies with `outcome_ack` for `T`; the Python run log contains the same observation, `action_decided`, `action_executed`, and outcome; there are zero orphaned tasks at shutdown.
6. The resulting record is labelled a single integration trace, not a performance result. No comparison or latency claim is made from it.

## No source changes proposed in this pass

No small unambiguous Python-model bug blocks the first Java connection. The blockers are absent Java/iFogSim source and missing agreement on measurements/fallback. Changing the model’s state fields, thresholds, gamma, reward, or learning rule is neither necessary nor authorized for this integration pass.

## Exact materials required from the simulator owner

- Build descriptor and dependency coordinates (`pom.xml`/Gradle files) plus chosen JDK and iFogSim version.
- Task class/generator and its stable identifier mechanism.
- The exact method/class that selects a destination and any API for forced Local/Edge/Cloud placement.
- Topology/node identities that map to Local, Edge, and Cloud.
- Completion/failure callback or event stream, and available timestamp, byte-count, energy, and utilization measurements.
- The desired child-process timeout and approved fallback action.
