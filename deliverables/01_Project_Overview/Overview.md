# Project Overview

## Research Problem

IoT tasks may execute on the originating device, a nearby edge/fog node, or a remote cloud node. These choices trade latency, network dependence, compute capacity, and resource use. The broader research question is whether a state-aware adaptive policy can choose among Local, Edge, and Cloud under changing conditions better than fixed placement policies.

## Objective

The project objective is to integrate an AI-based placement policy with an iFogSim edge-cloud simulation and measure task outcomes. The current milestone demonstrates the integration path for a controlled one-task scenario. It is not a final evaluation of the research hypothesis.

## Execution Choices

- **Local:** the task executes on the simulated local IoT device.
- **Edge:** the task executes on the simulated edge/fog device.
- **Cloud:** the task executes on the simulated cloud device.

Each tier has a statically deployed, tier-specific application module. Java records the actual execution module and device rather than assuming that the requested action was honored.

## Architecture

1. A Java task emitter creates a tuple with task MI, input/output sizes, and a task correlation ID.
2. Java samples edge utilization, configured edge-to-cloud latency, and the task deadline.
3. A persistent Python service receives a JSONL observation and returns Local, Edge, or Cloud with a matching task ID.
4. Java maps the action to the corresponding placed module and uses normal iFogSim routing.
5. Experiment-owned FogDevice subclasses record counted parent-child transfers and actual execution.
6. An experiment-owned result endpoint records terminal arrival, latency, deadline status, and bytes.
7. Python receives a completed outcome in accepted-agent runs, updates the model when training, saves, and shuts down.

## Implemented Versus Planned

Implemented and tested in this package: one-task Java/Python integration, action-dependent routing, task correlation, terminal measurements, deterministic baselines, fallback boundary tests, deadline-miss handling, JSONL validation, cleanup, and reproducible isolated execution.

Planned or deferred: multi-task registry support, native failure semantics, statistically repeated policy evaluation, validated RL superiority claims, per-task energy attribution, and broader dynamic workload experimentation.
