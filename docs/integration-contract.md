# Integration Contract (DRAFT)

> **Status: DRAFT — not an agreed contract.**
> This document defines a **preliminary** interface between the Java/iFogSim
> simulator (Ayoub) and the Python Q-Learning agent (Ibrahim). Field names, units,
> encodings, and even the transport mechanism are **provisional** and become
> binding only after **Ayoub and Ibrahim agree** on them and the behavior is
> tested. No integration method described here is final, and none is claimed to be
> working.

The machine-readable schema lives in
`integration/protocol/agent-message-schema.json`.

---

## 1. Purpose

For each task, the simulator observes a **state**, sends it to the agent, and
receives an **action** (Local / Edge / Cloud) that the simulator then applies to
actual task execution.

```
Java/iFogSim  --(state request)-->  Python agent
Java/iFogSim  <--(action response)--  Python agent
```

---

## 2. Illustrative request (Java → Python)

**Example values only — not final field names, units, or encodings.**

```json
{
  "task_id": "task-000123",
  "task_size": 250.0,
  "network_latency": 45.0,
  "edge_utilization": 0.62,
  "deadline_category": "Tight"
}
```

Field intent (provisional):

| Field | Meaning | Unit / encoding | Status |
| --- | --- | --- | --- |
| `task_id` | Unique task identifier | string | Provisional name |
| `task_size` | Size of the task | numeric (e.g. MB) **or** categorical Low/Medium/High | Unit/encoding TBD |
| `network_latency` | Observed network latency | numeric with units (e.g. ms) **to be documented** | Provisional |
| `edge_utilization` | Edge node utilization | numeric (e.g. 0–1 or 0–100%) | Unit TBD |
| `deadline_category` | Deadline band | string, e.g. `Tight` / `Relaxed` | Provisional |

## 3. Illustrative response (Python → Java)

```json
{
  "task_id": "task-000123",
  "action": "Edge"
}
```

- `action` is one of `"Local"`, `"Edge"`, `"Cloud"`.
- `task_id` must echo the request so the simulator can match the decision.

---

## 4. Contract requirements

1. **Field names are provisional** until agreed by **Ayoub and Ibrahim**.
2. **Units and feature discretization must be documented** for every numeric
   field (is `task_size` MB? is `edge_utilization` a fraction or a percentage?
   is discretization done in Java or Python?). A single source of truth is required.
3. **The selected action must affect actual task execution.** Returning "Edge"
   must cause the task to be routed to and run on the edge tier, not merely be
   logged.
4. **Java must verify the actual execution destination** and record where the task
   really ran, independently of the requested action.
5. **Task outcomes must be linked to the original `task_id`** so that
   state → action → outcome → reward can be joined for analysis.
6. **Timeout behavior must be defined** (illustrative only): if the agent does not
   respond within an agreed timeout, the simulator applies a documented **fallback
   action** (e.g., a chosen static default) and records that the fallback was used.
7. **Invalid-response behavior must be defined** (illustrative only): if the agent
   returns a malformed message or an out-of-range action, the simulator treats it
   like a timeout — use the documented fallback and log the anomaly.

> The specific timeout duration and fallback choice above are **illustrative**; the
> team must set the real values.

---

## 5. Request vs. response discrimination

The request and response share `task_id` but have different required fields. The
schema file uses a `oneOf` construct so a single document can be validated as
**either** a valid request **or** a valid response. If this proves ambiguous in
practice, it may be split into two schema files (`request` and `response`) once the
team finalizes the protocol.

## 6. Transport (undecided)

The physical integration mechanism is **not chosen**. Candidate options to be
evaluated by Ayoub and Ibrahim include:

- Synchronous subprocess call from Java to a Python script (stdin/stdout JSON).
- A local socket or HTTP request/response.
- A file-based exchange for tightly controlled, step-by-step runs.

No option is preferred or implemented here.

## 7. Explicit non-goals of this draft

- It is **not** a working implementation.
- It does **not** include a production agent or pretend the interface already
  functions.
- It does **not** fix units, thresholds, or encodings.

## 8. Next steps

1. Ayoub + Ibrahim agree on final field names, units, and encodings.
2. Agree on transport and timeout/fallback policy.
3. Record decisions in `docs/decisions/` and update the schema accordingly.
4. Implement a minimal round-trip test **before** claiming integration works.
