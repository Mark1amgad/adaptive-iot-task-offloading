# Simulator (Java / iFogSim)

Owner: **Ayoub** — iFogSim simulation, Java implementation, task execution, dynamic
task-level offloading, measurement collection, and simulator-side integration.

> **Status: reported, not verified in this repository.**
> The team reports that the **original iFogSim example runs successfully** and that
> a **custom topology is preliminarily implemented**. However, **no simulator code is
> committed in this repository yet**, so these claims cannot be verified here.
> Dynamic task-level offloading is **not yet verified as fully implemented**.

---

## 1. Purpose

This area is intended to hold the Java/iFogSim side of the project:

- Generate IoT tasks (workload).
- Observe and expose the state for each task (size, network latency, edge
  utilization, deadline category, …).
- Send the state to the Python agent and receive an action.
- **Actually apply** the action (route the task to Local / Edge / Cloud) and execute
  it there.
- **Verify the real execution destination.**
- Collect outcomes and link them to the original `task_id`.

Design context: [`../docs/system-architecture.md`](../docs/system-architecture.md),
[`../docs/integration-contract.md`](../docs/integration-contract.md).

## 2. Relationship to the original iFogSim project

- iFogSim is an **external, upstream project** with its own license and repository.
- This project **does not modify the original iFogSim repository** — it is out of
  scope (see [`../LICENSE_STATUS.md`](../LICENSE_STATUS.md)).
- Customization (topology, offloading hooks, measurement) should live in this
  repository's `simulator/` area (or reference iFogSim as a dependency), not by
  editing upstream sources here.

## 3. Prerequisites (planned — to be confirmed by Ayoub)

- **Java JDK** matching the chosen iFogSim version.
- **Maven** (or the build tool used to bring in iFogSim).
- iFogSim dependency declared via the build tool rather than vendored binaries,
  unless the team decides otherwise and records it in `docs/decisions/`.

> Exact versions are intentionally not fixed here. Ayoub should record the chosen
> Java/iFogSim/build-tool versions in this file (and in `docs/decisions/`) once the
> setup is confirmed, so the environment is reproducible.

## 4. Planned contents (not yet added)

Suggested layout (to be finalized by Ayoub):

```
simulator/
├── README.md               # this file
├── pom.xml                 # build configuration (TBD)
└── src/main/java/...       # topology, task generation, offloading hooks,
                            # measurement, integration adapter (TBD)
```

## 5. Integration responsibilities (simulator side)

Per the draft contract:

- Provide state values with **documented units** and consistent discretization.
- Apply the returned action to **real** task routing/execution.
- Confirm and record the **actual** execution destination.
- Emit per-task outcomes keyed by `task_id`.
- Define and handle **timeout / invalid-response** behavior with a documented
  fallback.

## 6. Honesty note

Do **not** describe custom topology, dynamic offloading, or integration as working
until the corresponding Java code is present here and verified. Keep the planned /
implemented distinction clear in commits, PRs, and the root README status table.
