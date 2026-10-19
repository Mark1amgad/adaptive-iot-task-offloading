# Methodology

## Actual Integration Lifecycle

The experiment runs one task per process. At simulation time 5.0, Java creates an observation containing `task_mi`, `wan_latency_ms`, `edge_utilization`, and `deadline_ms`. Python returns an action and action ID. Java verifies the task ID and action pair, routes the tuple through normal iFogSim module placement, and records actual execution. The result tuple reaches the selected local endpoint, where Java computes `latency_ms = terminal_sim_time - creation_sim_time` and derives `deadline_met` from the configured deadline. Accepted-agent runs send one terminal completed outcome to Python, then request save in training mode and shutdown.

Fallback runs inject a response-boundary error before an observation is sent. They select Edge, record the reason, execute the task, send no RL outcome, and shut down Python with zero orphaned pending decisions.

## Actual Parameters

| Parameter | Value | Classification |
| --- | ---: | --- |
| Task MI | 2,500 | Configured experiment input |
| Task PEs | 1 | Configured experiment input |
| Input bytes | 12,000 | Configured tuple input size |
| Result bytes | 2,000 | Configured tuple output size |
| Default deadline | 500 ms | Configured experiment input |
| Edge-to-cloud uplink latency | 45 ms | Configured one-way topology latency, not measured RTT |
| Local uplink latency | 2 ms | Configured topology value |
| Python timeout | 1,000 ms wall-clock | Adapter configuration |
| Agent/simulation seed | 123 | Run configuration |
| State table count reported by service | 54 | Service-reported configuration |

The accepted traces are one-task runs with an otherwise controlled topology. The default train run used Python `train` mode; baseline runs used `baseline` mode with fixed Local, Edge, or Cloud policy.

## Measurements

Latency is simulated-time difference between task creation and selected endpoint arrival. Task-attributed bandwidth is the sum of instrumented `Tuple.cloudletFileSize` values on parent-child uplink/downlink traversals only. Local reports zero because the task executes at the originating local device and no counted parent-child link is traversed for that task; this does not mean all system communication is zero.

Execution destination is measured from the actual module/device admission hook. Energy is sent as `null` because cumulative simulator energy is not a defensible per-task attribution in this experiment. Configured latency, task size, and deadline are inputs, not measured performance results.

## Comparison Scope

The preserved comparison contains one run for the RL train case and one deterministic run for each baseline. It demonstrates integration and produces preliminary observations. It does not support confidence intervals, general performance claims, or a claim that RL is superior.
